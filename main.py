"""
MusicUnlock 后端解密服务
FastAPI + libtakiyasha 2.x

POST /api/decrypt: 接收上传的加密音频文件，按后缀路由解密，返回原始格式 blob。
GET  /api/formats: 返回格式注册表（新后端 ↔ 旧前端解密器映射）。

解密算法已提取至 decrypt_algorithms.py，本文件仅负责 HTTP 服务层。
关联旧前端项目: https://github.com/Changliu7Stream/Music-Unlock-Web
"""

import urllib.parse
import warnings
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles

# 抑制 libtakiyasha 的 DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 导入解密算法模块（新算法，关联旧前端 src/decrypt/）
from decrypt_algorithms import (
    route_and_decrypt,
    FORMAT_REGISTRY,
    UNSUPPORTED_LEGACY_FORMATS,
    MIME_MAP,
)

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

        # 解密（路由逻辑在 decrypt_algorithms.py 中实现）
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


@app.get("/api/formats")
async def list_formats():
    """
    返回格式注册表，供前端查询支持的解密格式。
    建立新后端解密器与旧前端解密器的关联映射。
    """
    supported = []
    for name, entry in FORMAT_REGISTRY.items():
        supported.append({
            "decryptor": name,
            "platform": entry["platform"],
            "extensions": list(entry["extensions"]),
            "libtakiyasha": entry["libtakiyasha"],
            "legacy_frontend": entry["legacy_frontend"],
            "env_keys": entry["env_keys"],
        })

    unsupported = []
    for ext, info in UNSUPPORTED_LEGACY_FORMATS.items():
        unsupported.append({
            "extension": ext,
            "platform": info["platform"],
            "legacy_frontend": info["legacy_frontend"],
            "reason": info["reason"],
        })

    return {"supported": supported, "unsupported_legacy": unsupported}


# ---------------------------------------------------------------------------
# 静态文件服务（前端）
# ---------------------------------------------------------------------------

public_dir = Path(__file__).parent / "public"
if public_dir.exists():
    app.mount("/", StaticFiles(directory=str(public_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
