# Music-Unlock

音乐解锁 Web 应用（um-web legacy build v1.10.6），解密逻辑已迁移至 FastAPI 后端。

## 在线演示

**[https://musicunlock.guxinze.us.ci/](https://musicunlock.guxinze.us.ci/)**

备用：**[https://quiet-pie-063f08.netlify.app/](https://quiet-pie-063f08.netlify.app/)**

## 简介

本项目基于 um-web legacy v1.10.6 Vue2 项目，保留前端 UI 与 PWA 配置不动，做最小升级：

- 前端 `public/api-decrypt.js` 拦截 FileSelector，将文件上传至后端 `/api/decrypt`
- 后端 `main.py` 使用 Python FastAPI + libtakiyasha 2.x，按后缀路由解密
- 密钥全部通过环境变量注入（`.env.example`），不硬编码私钥
- 解密成功返回原始 FLAC/OGG/MP3 blob，失败返回 JSON `{ok:false}`
- 前端拿到 blob 走原下载逻辑，UI 组件不动

## 支持格式

| 后缀 | 格式 | 解密器 |
|------|------|--------|
| `.ncm` | 网易云音乐 | NCM |
| `.mflac` `.mgg` 等 | QQ音乐新版 | QMCv2 |
| `.qmc*` `.tkm` 等 | QQ音乐旧版 | QMCv1 |
| `.kgm` `.kgma` `.vpr` | 酷狗音乐 | KGMorVPR |
| `.kwm` | 酷我音乐 | KWM |

## 技术栈

- **前端**：Vue.js + PWA (Service Worker) + Element UI（保留原样）
- **后端**：Python FastAPI + libtakiyasha 2.1.1.post1

## 部署

### 后端配置

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 复制环境变量模板并填入密钥：
```bash
cp .env.example .env
# 编辑 .env 填入实际密钥值
```

3. 启动服务：
```bash
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000
```

后端启动后，前端静态文件由 FastAPI 自动托管在根路径 `/`。

### 无服务器（Serverless）部署

前端为纯静态项目，支持以下平台部署：

#### Vercel

1. Fork 本仓库到你的 GitHub 账号
2. 登录 [Vercel](https://vercel.com/)，点击 "New Project"
3. 导入你 Fork 的仓库
4. Framework Preset 选择 "Other"（纯静态项目）
5. 点击 "Deploy"，等待部署完成即可获得在线访问地址

#### Netlify

1. Fork 本仓库到你的 GitHub 账号
2. 登录 [Netlify](https://www.netlify.com/)，点击 "Add new site" → "Import an existing project"
3. 连接 GitHub 并选择你 Fork 的仓库
4. Build command 留空，Publish directory 设置为项目根目录（即仓库根目录）
5. 点击 "Deploy site"，部署完成后即可获得在线访问地址

> 两个平台均提供免费套餐，支持自动 HTTPS 和自定义域名。
> 注意：无服务器平台仅托管前端静态文件，后端解密服务需另行部署（如 Railway、Render 等）。

## 许可协议

本项目基于 [MIT License](./LICENSE) 开源。
