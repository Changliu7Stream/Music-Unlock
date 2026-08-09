# Music-Unlock

音乐解锁 — um-web legacy v1.10.7，前端静态站 + 后端解密服务。

## 在线演示

- 自定义域名：[https://musicunlock.guxinze.us.ci/](https://musicunlock.guxinze.us.ci/)
- GitHub Pages：[https://changliu7stream.github.io/Music-Unlock/](https://changliu7stream.github.io/Music-Unlock/)

## 简介

基于 um-web legacy v1.10.6 Vue2 项目，升级至 v1.10.7。保留前端 UI 与 PWA 配置不动，解密逻辑迁移至 FastAPI 后端，前端通过 `fetch /api/decrypt` 上传文件获取解密后的音频 blob。

### v1.10.7 更新内容

- 版本号从 1.10.6 升级至 1.10.7
- 解密逻辑迁移至后端 FastAPI + libtakiyasha 2.1.1.post1
- 密钥全部通过环境变量注入，不硬编码私钥
- 解密成功返回原始格式（FLAC/OGG/MP3），失败返回 JSON `{ok: false}`
- 前端 UI 组件不变，仅替换解密调用为后端 API
- 新增 GitHub Pages 部署支持（含 `.nojekyll`）
- 新增不支持的解密格式提示（虾米、喜马拉雅）

### 性能优化

- Service Worker 重写：移除 Google CDN workbox 依赖，改用原生 Cache API，静态资源 cache-first、HTML network-first
- 预缓存精简：大文件（worker 1.3MB、vendor 1.6MB）改为按需缓存，仅预缓存小文件
- 脚本加载优化：`index.html` 中为 `<script>` 添加 `defer` 属性，避免阻塞渲染
- 版本检查跳过：移除外部版本检查请求，减少不必要的网络请求
- Gzip 压缩：服务器端启用 gzip，减少传输体积

## 项目结构

```
Music-Unlock/
├── index.html                # 前端入口页面（仓库根目录）
├── css/                      # 样式文件
├── js/                       # JavaScript 文件
├── fonts/                    # 字体文件
├── img/                      # 图片资源
├── favicon.ico
├── loader.js                 # 加载动画逻辑
├── service-worker.js         # PWA Service Worker（轻量版，原生 Cache API）
├── web-manifest.json         # PWA Manifest
├── precache-manifest.*.js    # 预缓存清单（已精简）
├── .nojekyll                 # GitHub Pages：跳过 Jekyll 处理
├── backend/                  # 后端解密服务（单独文件夹）
│   ├── main.py               # FastAPI 服务层（HTTP 路由 + 静态文件托管）
│   ├── decrypt_algorithms.py # 解密算法模块（NCM/QMC/KGM/KWM + 格式注册表）
│   ├── requirements.txt      # Python 依赖
│   └── .env.example          # 环境变量模板（密钥配置）
├── .gitignore
├── LICENSE
└── README.md
```

## 新旧解密器关联

`backend/decrypt_algorithms.py` 中的 `FORMAT_REGISTRY` 建立了新后端解密器与旧前端 `src/decrypt/` 的完整映射：

| 新后端解密器 | 旧前端模块 | libtakiyasha | 平台 |
|-------------|-----------|--------------|------|
| `_decrypt_ncm()` | `src/decrypt/ncm.ts` → NCMDecrypt | `lt.NCM.open()` | 网易云音乐 |
| `_decrypt_qmcv2()` | `src/decrypt/qmc/v2.ts` → QMCv2Decrypt | `lt.QMCv2.open()` | QQ音乐新版 |
| `_decrypt_qmcv1()` | `src/decrypt/qmc/v1.ts` → QMCv1Decrypt | `lt.QMCv1.open()` | QQ音乐旧版 |
| `_decrypt_kgm()` | `src/decrypt/kgm.ts` → KGMCrypto | `lt.KGMorVPR.open()` | 酷狗音乐 |
| `_decrypt_kwm()` | `src/decrypt/kwm.ts` → KWMDecrypt | `lt.KWM.open()` | 酷我音乐 |

## 支持格式

### 已支持

| 解密器 | 平台 | 扩展名 | 所需环境变量 |
|--------|------|--------|-------------|
| NCM | 网易云音乐 | `.ncm` | `NCM_CORE_KEY` |
| QMCv2 | QQ音乐新版 | `.mflac` `.mflac0` `.mflach` `.mgg` `.mgg0` `.mgg1` `.mggl` `.mmp4` | `QMCV2_CORE_KEY` 或 `QMCV2_CORE_KEY_SALT` |
| QMCv1 | QQ音乐旧版 | `.qmc0` `.qmc2` `.qmc3` `.qmc4` `.qmc6` `.qmc8` `.qmcflac` `.qmcogg` `.tkm` `.bkcmp3` `.bkcm4a` `.bkcflac` `.bkcwav` `.bkcape` `.bkcogg` `.bkcwma` | `QMCV1_MASK` |
| KGMorVPR | 酷狗音乐 | `.kgm` `.kgma` `.vpr` | `KGM_TABLE1` `KGM_TABLE2` `KGM_TABLEV2`（`.vpr` 额外需要 `VPR_KEY`） |
| KWM | 酷我音乐 | `.kwm` | `KWM_CORE_KEY` |

### 旧前端支持但暂未迁移

| 扩展名 | 平台 | 原因 |
|--------|------|------|
| `.tm2` | 虾米音乐 | libtakiyasha 未实现虾米解密算法 |
| `.xm` `.x2m` `.x3m` | 喜马拉雅 | libtakiyasha 未实现喜马拉雅解密算法 |

## API 文档

### POST `/api/decrypt`

上传加密音频文件，解密后返回原始格式 blob。

**请求**：`multipart/form-data`，字段 `file` 为加密音频文件

**成功响应**：
- HTTP 200
- Body：解密后的音频数据（FLAC/OGG/MP3 等）
- 响应头：
  - `Content-Type`：音频 MIME 类型
  - `X-Ext`：音频格式扩展名
  - `X-Title`：歌曲标题（URL 编码）
  - `X-Artist`：艺术家（URL 编码）
  - `X-Album`：专辑名（URL 编码）

**失败响应**：
- HTTP 400/413/422/500
- Body：`{"ok": false, "reason": "错误原因"}`

**文件大小限制**：50MB

### GET `/api/formats`

返回格式注册表，包含支持的解密格式和不支持的旧格式信息。

### GET `/api/health`

健康检查端点。

## 部署

### 前端（静态站）

前端静态文件在仓库根目录，可直接部署到 GitHub Pages、Netlify、Vercel 等平台。

#### GitHub Pages

1. 仓库根目录已包含 `.nojekyll` 文件，跳过 Jekyll 处理
2. 进入仓库 Settings → Pages
3. Source 选择 `Deploy from a branch`
4. Branch 选择 `main`，文件夹选 `/ (root)`
5. 点击 Save，等待部署完成
6. 访问 `https://<username>.github.io/Music-Unlock/`

#### Netlify

1. 连接 GitHub 仓库 `Changliu7Stream/Music-Unlock`
2. Build command 留空，Publish directory 留空（或设为 `.`）
3. 点击 "Deploy site"

#### Vercel

1. 导入 GitHub 仓库 `Changliu7Stream/Music-Unlock`
2. Framework Preset 选择 "Other"
3. 点击 "Deploy"

### 后端（FastAPI）

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置密钥
cp .env.example .env
# 编辑 .env 填入实际密钥值（密钥为各加密格式规范中的公开常量）

# 启动服务
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000
```

后端启动后，会自动托管上级目录的前端静态文件（若存在 `index.html`）。

启动时控制台会打印各密钥的加载状态（不输出实际值），方便排查配置问题。

#### 后端无服务器部署

后端可通过 Vercel Serverless Functions 或 Netlify Functions 部署，需确保：

1. 环境变量在平台后台正确配置（参考 `.env.example`）
2. CORS 允许的前端域名与实际部署域名匹配（在 `backend/main.py` 中配置）

### 密钥配置说明

所有密钥均为各加密格式规范中的**公开常量**，可从 unlock-music、parakeet-crypto-rs 等开源项目获取。后端不硬编码任何私钥，全部通过环境变量注入。

| 环境变量 | 格式 | 说明 |
|---------|------|------|
| `NCM_CORE_KEY` | 字符串 | NCM 核心密钥 |
| `NCM_TAG_KEY` | 字符串 | NCM 标签密钥（可选，留空用库默认值） |
| `QMCV2_CORE_KEY` | hex (16位) | QMCv2 核心密钥（方式一：直接提供） |
| `QMCV2_CORE_KEY_SALT` | 整数 | QMCv2 派生盐值（方式二：与 LENGTH 配合使用） |
| `QMCV2_CORE_KEY_LENGTH` | 整数 | QMCv2 派生长度（默认 8） |
| `QMCV1_MASK` | hex (512位) | QMCv1 mask，256 字节 |
| `KGM_TABLE1` | hex (544位) | KGM 解码表1，272 字节 |
| `KGM_TABLE2` | hex (544位) | KGM 解码表2，272 字节 |
| `KGM_TABLEV2` | hex (544位) | KGM 解码表v2，272 字节 |
| `VPR_KEY` | hex | VPR 密钥（仅解密 `.vpr` 时需要） |
| `KWM_CORE_KEY` | 字符串 | KWM 核心密钥 |

## 安全说明

- 密钥全部通过环境变量注入，不硬编码在代码中
- CORS 仅允许关联的前端域名，不使用通配符 `*`
- 文件上传限制 50MB，防止内存耗尽
- 前端使用 `textContent` 替代 `innerHTML`，防止 XSS
- 下载完成后调用 `URL.revokeObjectURL` 释放内存
- 解密后通过 magic bytes 检测真实音频格式，不依赖文件名猜测

## 技术栈

- **前端**：Vue.js 2 + PWA + Element UI（um-web legacy v1.10.7）
- **后端**：Python FastAPI + libtakiyasha 2.1.1.post1
- **部署**：GitHub Pages / Netlify / Vercel

## 许可协议

本项目基于 [MIT License](./LICENSE) 开源。
