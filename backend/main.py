"""
MusicUnlock 后端解密服务
FastAPI + libtakiyasha 2.x

POST /api/decrypt: 接收上传的加密音频文件，按后缀路由解密，返回原始格式 blob。
GET /api/formats: 返回格式注册表（新后端 <-> 旧前端解密器映射）。

解密算法已提取至 decrypt_algorithms.py，本文件仅负责 HTTP 服务层。
前端静态文件在仓库根目录（上级目录），后端代码在 backend/ 文件夹。
"""
import urllib.parse
import warnings
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Request
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

# 文件大小限制：50MB
MAX_FILE_SIZE = 50 * 1024 * 1024  # 52,428,800 字节

# ---------------------------------------------------------------------------
# CORS 配置（仅允许关联的前端域名）
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://musicunlock.guxinze.us.ci",
        "https://changliu7stream.github.io",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Title", "X-Artist", "X-Album", "X-Ext", "X-Mime"],
)


# ---------------------------------------------------------------------------
# API 端点
# ---------------------------------------------------------------------------

@app.post("/api/decrypt")
async def decrypt_file(request: Request, file: UploadFile = File(...)):
    """接收上传的加密音频文件，解密后返回原始格式 blob。

    成功: 返回音频 blob（Content-Type 由格式决定），元数据在响应头中
    失败: 返回 JSON {"ok": false, "reason": "..."}
    """
    try:
        # 文件大小限制：先检查 Content-Length 头，提前拦截超大上传（避免读入内存）
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_FILE_SIZE + 1024:  # 容差：multipart 封装开销
                    return JSONResponse(
                        status_code=413,
                        content={"ok": False, "reason": "文件过大，最大支持 50MB"},
                    )
            except ValueError:
                pass

        file_data = await file.read()
        if not file_data:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "reason": "上传文件为空"},
            )

        if len(file_data) > MAX_FILE_SIZE:
            return JSONResponse(
                status_code=413,
                content={"ok": False, "reason": f"文件过大（{len(file_data)} 字节），最大支持 50MB"},
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

        if not audio_data:
            return JSONResponse(
                status_code=422,
                content={"ok": False, "reason": "解密后未得到任何音频数据"},
            )

        # 返回原始格式 blob
        mime = MIME_MAP.get(audio_format, "application/octet-stream")

        def _enc(val: str) -> str:
            """URL 编码元数据，避免响应头中的非 ASCII 字符问题。"""
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
    """返回格式注册表，供前端查询支持的解密格式。

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


@app.get("/api/health")
async def health():
    """健康检查端点。"""
    return {"ok": True, "service": "MusicUnlock API", "version": "2.0.0"}


# ---------------------------------------------------------------------------
# 静态文件服务（可选）：若上级目录存在 index.html 则托管前端静态文件
# ---------------------------------------------------------------------------
frontend_dir = Path(__file__).parent.parent
if (frontend_dir / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
