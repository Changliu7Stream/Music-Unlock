"""
MusicUnlock 后端解密服务
FastAPI + libtakiyasha 2.x

POST /api/decrypt: 接收上传的加密音频文件，按后缀路由解密，返回原始格式 blob。
所有解密密钥通过环境变量注入，代码中不硬编码任何私钥。
"""

import io
import os
import urllib.parse
import warnings
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles

import libtakiyasha as lt

# 抑制 libtakiyasha 的 DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)

app = FastAPI(title="MusicUnlock API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Title", "X-Artist", "X-Album", "X-Ext", "X-Mime"],
)


# ---------------------------------------------------------------------------
# 密钥加载：全部从环境变量读取，不硬编码
# ---------------------------------------------------------------------------

def _env_hex(name: str) -> Optional[bytes]:
    """从环境变量读取 hex 编码的密钥，返回 bytes；未设置则返回 None"""
    val = os.environ.get(name)
    if not val:
        return None
    return bytes.fromhex(val.strip().replace(" ", "").replace("\n", ""))


def _env_str(name: str) -> Optional[bytes]:
    """从环境变量读取字符串密钥，返回 bytes；未设置则返回 None"""
    val = os.environ.get(name)
    if not val:
        return None
    return val.encode("utf-8")


def _env_int(name: str, default: int) -> int:
    """从环境变量读取整数"""
    val = os.environ.get(name)
    if not val:
        return default
    return int(val)


# 启动时加载密钥
NCM_CORE_KEY = _env_str("NCM_CORE_KEY")
NCM_TAG_KEY = _env_str("NCM_TAG_KEY")  # 可选，库有默认值

QMCV2_CORE_KEY = None
if os.environ.get("QMCV2_CORE_KEY"):
    QMCV2_CORE_KEY = _env_hex("QMCV2_CORE_KEY")
elif os.environ.get("QMCV2_CORE_KEY_SALT"):
    # 也可以通过 salt+length 派生
    from libtakiyasha.qmc._qmckeyciphers import make_core_key
    QMCV2_CORE_KEY = make_core_key(
        _env_int("QMCV2_CORE_KEY_SALT", 106),
        _env_int("QMCV2_CORE_KEY_LENGTH", 8),
    )

QMCV1_MASK = _env_hex("QMCV1_MASK")

KGM_TABLE1 = _env_hex("KGM_TABLE1")
KGM_TABLE2 = _env_hex("KGM_TABLE2")
KGM_TABLEV2 = _env_hex("KGM_TABLEV2")
VPR_KEY = _env_hex("VPR_KEY")

KWM_CORE_KEY = _env_str("KWM_CORE_KEY")

# 启动时打印已加载的密钥状态（不输出实际值）
_loaded = {k: ("已加载" if v else "未设置") for k, v in {
    "NCM_CORE_KEY": NCM_CORE_KEY,
    "NCM_TAG_KEY": NCM_TAG_KEY,
    "QMCV2_CORE_KEY": QMCV2_CORE_KEY,
    "QMCV1_MASK": QMCV1_MASK,
    "KGM_TABLE1": KGM_TABLE1,
    "KGM_TABLE2": KGM_TABLE2,
    "KGM_TABLEV2": KGM_TABLEV2,
    "VPR_KEY": VPR_KEY,
    "KWM_CORE_KEY": KWM_CORE_KEY,
}.items()}
print(f"[MusicUnlock] 密钥加载状态: {_loaded}")


# ---------------------------------------------------------------------------
# MIME 类型映射
# ---------------------------------------------------------------------------

MIME_MAP = {
    "mp3": "audio/mpeg",
    "flac": "audio/flac",
    "ogg": "audio/ogg",
    "m4a": "audio/mp4",
    "wav": "audio/wav",
    "ape": "audio/ape",
}


# ---------------------------------------------------------------------------
# 文件类型路由
# ---------------------------------------------------------------------------

def get_file_ext(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def route_and_decrypt(filename: str, file_data: bytes) -> tuple[bytes, str, dict]:
    """
    根据文件后缀路由到对应的解密器。
    返回 (解密后音频数据, 音频格式, 元数据)。
    """
    ext = get_file_ext(filename)

    if ext == "ncm":
        return _decrypt_ncm(file_data, filename)
    elif ext in ("mflac", "mflac0", "mflach", "mgg", "mgg0", "mgg1", "mggl", "mmp4"):
        return _decrypt_qmcv2(file_data, filename)
    elif ext.startswith("qmc") or ext in ("tkm", "bkcmp3", "bkcm4a", "bkcflac",
                                           "bkcwav", "bkcape", "bkcogg", "bkcwma"):
        return _decrypt_qmcv1(file_data, filename)
    elif ext in ("kgm", "kgma", "vpr"):
        return _decrypt_kgm(file_data, filename)
    elif ext == "kwm":
        return _decrypt_kwm(file_data, filename)
    else:
        raise ValueError(f"不支持的文件格式: .{ext}")


def _decrypt_ncm(file_data: bytes, filename: str) -> tuple[bytes, str, dict]:
    if not NCM_CORE_KEY:
        raise ValueError("NCM_CORE_KEY 环境变量未设置，无法解密 NCM 文件")

    fd = io.BytesIO(file_data)
    fd.name = filename
    kwargs = {"core_key": NCM_CORE_KEY}
    if NCM_TAG_KEY:
        kwargs["tag_key"] = NCM_TAG_KEY
    ncmfile = lt.NCM.open(fd, **kwargs)
    audio_data = b"".join(ncmfile)

    audio_format = "mp3"
    metadata: dict = {}
    try:
        tag = ncmfile.ncm_tag
        if tag:
            if tag.format:
                audio_format = tag.format
            if tag.musicName:
                metadata["title"] = tag.musicName
            if tag.artist:
                artists = []
                for a in tag.artist:
                    if isinstance(a, list):
                        artists.extend(str(x) for x in a if x)
                    else:
                        artists.append(str(a))
                metadata["artist"] = " / ".join(artists) if artists else ""
            if tag.album:
                metadata["album"] = tag.album
    except Exception:
        pass

    return audio_data, audio_format, metadata


def _decrypt_qmcv2(file_data: bytes, filename: str) -> tuple[bytes, str, dict]:
    if not QMCV2_CORE_KEY:
        raise ValueError("QMCV2_CORE_KEY 环境变量未设置，无法解密 QMCv2 文件")

    fd = io.BytesIO(file_data)
    fd.name = filename
    qmcfile = lt.QMCv2.open(fd, core_key=QMCV2_CORE_KEY)
    audio_data = b"".join(qmcfile)

    ext = get_file_ext(filename)
    if "flac" in ext:
        audio_format = "flac"
    elif "ogg" in ext:
        audio_format = "ogg"
    elif "m4a" in ext or "mp4" in ext:
        audio_format = "m4a"
    else:
        audio_format = "mp3"

    return audio_data, audio_format, {}


def _decrypt_qmcv1(file_data: bytes, filename: str) -> tuple[bytes, str, dict]:
    if not QMCV1_MASK:
        raise ValueError("QMCV1_MASK 环境变量未设置，无法解密 QMCv1 文件")

    fd = io.BytesIO(file_data)
    fd.name = filename
    qmcfile = lt.QMCv1.open(fd, mask=QMCV1_MASK)
    audio_data = b"".join(qmcfile)

    ext = get_file_ext(filename)
    if "flac" in ext:
        audio_format = "flac"
    elif "ogg" in ext:
        audio_format = "ogg"
    else:
        audio_format = "mp3"

    return audio_data, audio_format, {}


def _decrypt_kgm(file_data: bytes, filename: str) -> tuple[bytes, str, dict]:
    if not (KGM_TABLE1 and KGM_TABLE2 and KGM_TABLEV2):
        raise ValueError("KGM_TABLE1/TABLE2/TABLEV2 环境变量未设置，无法解密 KGM 文件")

    fd = io.BytesIO(file_data)
    fd.name = filename
    ext = get_file_ext(filename)

    kwargs = {
        "table1": KGM_TABLE1,
        "table2": KGM_TABLE2,
        "tablev2": KGM_TABLEV2,
    }
    if ext == "vpr":
        if not VPR_KEY:
            raise ValueError("VPR_KEY 环境变量未设置，无法解密 VPR 文件")
        kwargs["vpr_key"] = VPR_KEY

    kgmfile = lt.KGMorVPR.open(fd, **kwargs)
    audio_data = b"".join(kgmfile)

    return audio_data, "mp3", {}


def _decrypt_kwm(file_data: bytes, filename: str) -> tuple[bytes, str, dict]:
    if not KWM_CORE_KEY:
        raise ValueError("KWM_CORE_KEY 环境变量未设置，无法解密 KWM 文件")

    fd = io.BytesIO(file_data)
    fd.name = filename
    kwmfile = lt.KWM.open(fd, core_key=KWM_CORE_KEY)
    audio_data = b"".join(kwmfile)

    return audio_data, "mp3", {}


# ---------------------------------------------------------------------------
# API 端点
# ---------------------------------------------------------------------------

@app.post("/api/decrypt")
async def decrypt_file(file: UploadFile = File(...)):
    """
    接收上传的加密音频文件，解密后返回原始格式 blob。

    成功: 返回音频 blob（Content-Type 由格式决定），元数据在响应头中
    失败: 返回 JSON {"ok": false, "reason": "..."}
    """
    try:
        file_data = await file.read()
        if not file_data:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "reason": "上传文件为空"},
            )

        filename = file.filename or "unknown"

        # 解密
        try:
            audio_data, audio_format, metadata = route_and_decrypt(filename, file_data)
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "reason": str(e)},
            )
        except Exception as e:
            return JSONResponse(
                status_code=422,
                content={"ok": False, "reason": f"解密失败: {type(e).__name__}: {str(e)[:200]}"},
            )

        # 返回原始格式 blob
        mime = MIME_MAP.get(audio_format, "application/octet-stream")

        def _enc(val: str) -> str:
            return urllib.parse.quote(val or "", safe="")

        headers = {
            "X-Ext": audio_format,
            "X-Mime": mime,
            "X-Title": _enc(metadata.get("title", "")),
            "X-Artist": _enc(metadata.get("artist", "")),
            "X-Album": _enc(metadata.get("album", "")),
        }

        return Response(content=audio_data, media_type=mime, headers=headers)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "reason": f"服务器内部错误: {str(e)[:200]}"},
        )


# ---------------------------------------------------------------------------
# 静态文件服务（前端）
# ---------------------------------------------------------------------------

public_dir = Path(__file__).parent / "public"
if public_dir.exists():
    app.mount("/", StaticFiles(directory=str(public_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
