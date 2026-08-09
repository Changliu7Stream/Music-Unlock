# Music-Unlock

音乐解锁 — um-web legacy v1.10.7，前端静态站 + 后端解密服务。

## 在线演示

- 主站：[https://musicunlock.guxinze.us.ci/](https://musicunlock.guxinze.us.ci/)
- 备用：[https://quiet-pie-063f08.netlify.app/](https://quiet-pie-063f08.netlify.app/)

## 简介

基于 um-web legacy v1.10.6 Vue2 项目，升级至 v1.10.7。保留前端 UI 与 PWA 配置不动，解密逻辑迁移至 FastAPI 后端。

## 项目结构

```
Music-Unlock/
├── index.html                # 前端入口页面（仓库根目录，Netlify 直接识别）
├── css/                      # 样式文件
├── js/                       # JavaScript 文件
├── fonts/                    # 字体文件
├── img/                      # 图片资源
├── favicon.ico
├── loader.js
├── service-worker.js         # PWA Service Worker
├── web-manifest.json         # PWA Manifest
├── precache-manifest.*.js
├── backend/                  # 后端解密服务（单独文件夹）
│   ├── main.py               # FastAPI 服务层
│   ├── decrypt_algorithms.py # 解密算法模块
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

| 解密器 | 平台 | 扩展名 |
|--------|------|--------|
| NCM | 网易云音乐 | `.ncm` |
| QMCv2 | QQ音乐新版 | `.mflac` `.mflac0` `.mflach` `.mgg` `.mgg0` `.mgg1` `.mggl` `.mmp4` |
| QMCv1 | QQ音乐旧版 | `.qmc0` `.qmc2` `.qmc3` `.qmc4` `.qmc6` `.qmc8` `.qmcflac` `.qmcogg` `.tkm` `.bkcmp3` `.bkcm4a` `.bkcflac` `.bkcwav` `.bkcape` `.bkcogg` `.bkcwma` |
| KGMorVPR | 酷狗音乐 | `.kgm` `.kgma` `.vpr` |
| KWM | 酷我音乐 | `.kwm` |

### 旧前端支持但暂未迁移

| 扩展名 | 平台 | 原因 |
|--------|------|------|
| `.tm2` | 虾米音乐 | libtakiyasha 未实现虾米解密算法 |
| `.xm` `.x2m` `.x3m` | 喜马拉雅 | libtakiyasha 未实现喜马拉雅解密算法 |

## 部署

### 前端（静态站）

前端静态文件在仓库根目录，Netlify/Vercel 直接识别，无需额外配置 Publish directory。

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
# 编辑 .env 填入实际密钥值

# 启动服务
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000
```

后端启动后，会自动托管上级目录的前端静态文件。

## 技术栈

- **前端**：Vue.js + PWA + Element UI（um-web legacy v1.10.7）
- **后端**：Python FastAPI + libtakiyasha 2.1.1.post1

## 许可协议

本项目基于 [MIT License](./LICENSE) 开源。
