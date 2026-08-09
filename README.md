# Music-Unlock

音乐解锁后端解密服务（FastAPI + libtakiyasha 2.x），um-web legacy v1.10.7。

## 仓库结构

| 仓库 | 说明 |
|------|------|
| **[Music-Unlock](https://github.com/Changliu7Stream/Music-Unlock)**（本仓库） | 后端解密服务：`main.py`（FastAPI 服务层）+ `decrypt_algorithms.py`（新解密算法） |
| **[Music-Unlock-Web](https://github.com/Changliu7Stream/Music-Unlock-Web)** | 旧前端项目：um-web legacy v1.10.7 编译产物 + `api-decrypt.js` 前端补丁 |

## 在线演示

**[https://musicunlock.guxinze.us.ci/](https://musicunlock.guxinze.us.ci/)**

备用：**[https://quiet-pie-063f08.netlify.app/](https://quiet-pie-063f08.netlify.app/)**

## 简介

本项目基于 um-web legacy v1.10.6 Vue2 项目，升级至 v1.10.7，保留前端 UI 与 PWA 配置不动，做最小升级：

- 旧前端项目已迁移至独立仓库 [Music-Unlock-Web](https://github.com/Changliu7Stream/Music-Unlock-Web)
- 旧前端 `api-decrypt.js` 拦截 FileSelector，将文件上传至后端 `/api/decrypt`
- 后端 `main.py` 为 FastAPI 服务层，`decrypt_algorithms.py` 为新解密算法模块
- `FORMAT_REGISTRY` 格式注册表建立新后端解密器与旧前端 `src/decrypt` 解密器的完整映射
- 密钥全部通过环境变量注入（`.env.example`），不硬编码私钥
- 解密成功返回原始 FLAC/OGG/MP3 blob，失败返回 JSON `{ok:false}`
- 前端拿到 blob 走原下载逻辑，UI 组件不动

## 项目结构

```
Music-Unlock/
├── main.py                  # FastAPI 服务层（HTTP 端点 + 静态文件托管）
├── decrypt_algorithms.py    # 新解密算法（密钥加载 + 解密器 + 格式注册表）
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量模板（密钥配置）
├── .gitignore
├── LICENSE
└── README.md
```

## 新旧解密器关联

`decrypt_algorithms.py` 中的 `FORMAT_REGISTRY` 建立了新后端解密器与旧前端 `src/decrypt/` 的完整映射：

| 新后端解密器 | 旧前端模块 | libtakiyasha | 平台 |
|-------------|-----------|--------------|------|
| `_decrypt_ncm()` | `src/decrypt/ncm.ts` → NCMDecrypt | `lt.NCM.open()` | 网易云音乐 |
| `_decrypt_qmcv2()` | `src/decrypt/qmc/v2.ts` → QMCv2Decrypt | `lt.QMCv2.open()` | QQ音乐新版 |
| `_decrypt_qmcv1()` | `src/decrypt/qmc/v1.ts` → QMCv1Decrypt | `lt.QMCv1.open()` | QQ音乐旧版 |
| `_decrypt_kgm()` | `src/decrypt/kgm.ts` → KGMCrypto | `lt.KGMorVPR.open()` | 酷狗音乐 |
| `_decrypt_kwm()` | `src/decrypt/kwm.ts` → KWMDecrypt | `lt.KWM.open()` | 酷我音乐 |

## 支持格式

### 已支持（新后端 ↔ 旧前端解密器映射）

| 解密器 | 平台 | 扩展名 | 旧前端模块 | libtakiyasha |
|--------|------|--------|-----------|--------------|
| NCM | 网易云音乐 | `.ncm` | `src/decrypt/ncm.ts` → NCMDecrypt | `lt.NCM.open()` |
| QMCv2 | QQ音乐新版 | `.mflac` `.mflac0` `.mflach` `.mgg` `.mgg0` `.mgg1` `.mggl` `.mmp4` | `src/decrypt/qmc/v2.ts` → QMCv2Decrypt | `lt.QMCv2.open()` |
| QMCv1 | QQ音乐旧版 | `.qmc0` `.qmc2` `.qmc3` `.qmc4` `.qmc6` `.qmc8` `.qmcflac` `.qmcogg` `.tkm` `.bkcmp3` `.bkcm4a` `.bkcflac` `.bkcwav` `.bkcape` `.bkcogg` `.bkcwma` | `src/decrypt/qmc/v1.ts` → QMCv1Decrypt | `lt.QMCv1.open()` |
| KGMorVPR | 酷狗音乐 | `.kgm` `.kgma` `.vpr` | `src/decrypt/kgm.ts` → KGMCrypto | `lt.KGMorVPR.open()` |
| KWM | 酷我音乐 | `.kwm` | `src/decrypt/kwm.ts` → KWMDecrypt | `lt.KWM.open()` |

### 旧前端支持但暂未迁移

| 扩展名 | 平台 | 旧前端模块 | 原因 |
|--------|------|-----------|------|
| `.tm2` | 虾米音乐 | `src/decrypt/xiami.ts` → XmDecrypt | libtakiyasha 未实现虾米解密算法 |
| `.xm` `.x2m` `.x3m` | 喜马拉雅 | `src/decrypt/ximalaya.ts` → XimalayaDecrypt | libtakiyasha 未实现喜马拉雅解密算法 |

> 后端 `GET /api/formats` 可动态返回完整格式注册表（含新旧解密器映射）。

## 技术栈

- **前端**：[Music-Unlock-Web](https://github.com/Changliu7Stream/Music-Unlock-Web) — Vue.js + PWA + Element UI（保留原样）
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

后端启动后，若 `public/` 目录存在则由 FastAPI 自动托管前端静态文件。
前端项目也可从 [Music-Unlock-Web](https://github.com/Changliu7Stream/Music-Unlock-Web) 仓库单独部署。

### 无服务器（Serverless）部署

前端为纯静态项目，支持以下平台部署：

#### Vercel

1. Fork [Music-Unlock-Web](https://github.com/Changliu7Stream/Music-Unlock-Web) 仓库到你的 GitHub 账号
2. 登录 [Vercel](https://vercel.com/)，点击 "New Project"
3. 导入你 Fork 的仓库
4. Framework Preset 选择 "Other"（纯静态项目）
5. 点击 "Deploy"，等待部署完成即可获得在线访问地址

#### Netlify

1. Fork [Music-Unlock-Web](https://github.com/Changliu7Stream/Music-Unlock-Web) 仓库到你的 GitHub 账号
2. 登录 [Netlify](https://www.netlify.com/)，点击 "Add new site" → "Import an existing project"
3. 连接 GitHub 并选择你 Fork 的仓库
4. Build command 留空，Publish directory 设置为项目根目录（即仓库根目录）
5. 点击 "Deploy site"，部署完成后即可获得在线访问地址

> 两个平台均提供免费套餐，支持自动 HTTPS 和自定义域名。
> 注意：无服务器平台仅托管前端静态文件，后端解密服务需另行部署（如 Railway、Render 等）。

## 许可协议

本项目基于 [MIT License](./LICENSE) 开源。
