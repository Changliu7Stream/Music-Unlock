# Music-Unlock

音乐解锁 — um-web legacy v1.10.7 静态前端项目。

## 在线演示

- 主站：[https://musicunlock.guxinze.us.ci/](https://musicunlock.guxinze.us.ci/)
- 备用：[https://quiet-pie-063f08.netlify.app/](https://quiet-pie-063f08.netlify.app/)

## 简介

基于 um-web legacy v1.10.6 Vue2 项目，升级至 v1.10.7。

前端 UI、PWA 配置、下载逻辑均保留原样，不改动任何 UI 组件。

## 仓库结构

| 仓库 | 说明 |
|------|------|
| **[Music-Unlock](https://github.com/Changliu7Stream/Music-Unlock)**（本仓库） | 前端静态站：Vue.js + PWA + Element UI 编译产物 |
| **[Music-Unlock-Backend](https://github.com/Changliu7Stream/Music-Unlock-Backend)** | 后端解密服务：FastAPI + libtakiyasha 2.x |

## 项目结构

```
Music-Unlock/
├── public/            # 前端编译产物（静态文件）
│   ├── css/           # 样式文件
│   ├── js/            # JavaScript 文件
│   ├── fonts/         # 字体文件
│   ├── img/           # 图片资源
│   ├── index.html     # 入口页面
│   ├── loader.js      # 加载器
│   ├── service-worker.js  # PWA Service Worker
│   └── web-manifest.json  # PWA Manifest
├── .gitignore
├── LICENSE
└── README.md
```

## 支持格式

| 平台 | 扩展名 |
|------|--------|
| 网易云音乐 | `.ncm` |
| QQ音乐新版 | `.mflac` `.mflac0` `.mflach` `.mgg` `.mgg0` `.mgg1` `.mggl` `.mmp4` |
| QQ音乐旧版 | `.qmc0` `.qmc2` `.qmc3` `.qmc4` `.qmc6` `.qmc8` `.qmcflac` `.qmcogg` `.tkm` `.bkcmp3` `.bkcm4a` `.bkcflac` `.bkcwav` `.bkcape` `.bkcogg` `.bkcwma` |
| 酷狗音乐 | `.kgm` `.kgma` `.vpr` |
| 酷我音乐 | `.kwm` |
| 虾米音乐 | `.tm2` |
| 喜马拉雅 | `.xm` `.x2m` `.x3m` |

> 虾米音乐和喜马拉雅格式为旧前端支持但后端暂未迁移的格式。

## 部署

### Netlify

1. Fork 本仓库到你的 GitHub 账号
2. 登录 [Netlify](https://www.netlify.com/)，点击 "Add new site" → "Import an existing project"
3. 连接 GitHub 并选择你 Fork 的仓库
4. Build command 留空，Publish directory 设置为 `public`
5. 点击 "Deploy site"

### Vercel

1. Fork 本仓库到你的 GitHub 账号
2. 登录 [Vercel](https://vercel.com/)，点击 "New Project"
3. 导入你 Fork 的仓库
4. Framework Preset 选择 "Other"，Root Directory 设置为 `public`
5. 点击 "Deploy"

> 两个平台均提供免费套餐，支持自动 HTTPS 和自定义域名。

## 后端解密服务

后端解密服务已迁移至独立仓库 [Music-Unlock-Backend](https://github.com/Changliu7Stream/Music-Unlock-Backend)，基于 FastAPI + libtakiyasha 2.x 实现。

## 许可协议

本项目基于 [MIT License](./LICENSE) 开源。
