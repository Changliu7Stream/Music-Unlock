FROM python:3.11-slim

LABEL maintainer="Changliu7Stream"
LABEL description="Music-Unlock - 音乐解锁前端静态站 + FastAPI 后端解密服务"

WORKDIR /app

# 安装系统依赖（libtakiyasha 可能需要 gcc 编译）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 缓存层加速构建
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 复制后端代码
COPY backend/ /app/backend/

# 复制前端静态文件到根目录（后端会自动托管上级目录的 index.html）
COPY index.html css/ js/ fonts/ img/ favicon.ico loader.js \
     service-worker.js web-manifest.json precache-manifest.*.js \
     /app/

# 暴露端口
EXPOSE 8000

# 设置工作目录为 backend，使后端能找到上级目录的前端文件
WORKDIR /app/backend

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
