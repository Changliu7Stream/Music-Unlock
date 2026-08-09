/**
 * api-decrypt.js — 前端补丁（最小侵入）
 *
 * 拦截 FileSelector 组件的文件处理逻辑，将原来的 Worker 解密
 * 改为 fetch /api/decrypt 上传文件，拿回解密后的原始格式 blob（FLAC/OGG/MP3）。
 *
 * 等价于注释掉 src/decrypt 内所有旧解密器注册——旧 Worker 解密链路被完全旁路。
 * 前端 UI 组件、下载逻辑、PWA 配置均不动。
 *
 * ─── 新旧解密器关联映射 ───────────────────────────────────────────
 *
 * 旧前端 (um-web legacy src/decrypt/)     →  新后端 (main.py / libtakiyasha)
 * ────────────────────────────────────────    ──────────────────────────────
 * src/decrypt/ncm.ts    → NCMDecrypt        →  FORMAT_REGISTRY["NCM"]
 *   扩展名: .ncm                               lt.NCM.open(core_key=...)
 *
 * src/decrypt/qmc/v2.ts → QMCv2Decrypt      →  FORMAT_REGISTRY["QMCv2"]
 *   扩展名: .mflac .mflac0 .mflach             lt.QMCv2.open(core_key=...)
 *           .mgg .mgg0 .mgg1 .mggl .mmp4
 *
 * src/decrypt/qmc/v1.ts → QMCv1Decrypt      →  FORMAT_REGISTRY["QMCv1"]
 *   扩展名: .qmc0 .qmc2 .qmc3 .qmc4            lt.QMCv1.open(mask=...)
 *           .qmc6 .qmc8 .qmcflac .qmcogg
 *           .tkm .bkcmp3 .bkcm4a .bkcflac
 *           .bkcwav .bkcape .bkcogg .bkcwma
 *
 * src/decrypt/kgm.ts    → KGMCrypto         →  FORMAT_REGISTRY["KGMorVPR"]
 *   扩展名: .kgm .kgma .vpr                    lt.KGMorVPR.open(table1=..., ...)
 *
 * src/decrypt/kwm.ts    → KWMDecrypt         →  FORMAT_REGISTRY["KWM"]
 *   扩展名: .kwm                               lt.KWM.open(core_key=...)
 *
 * ─── 旧前端支持但新后端暂不支持 ──────────────────────────────────
 * src/decrypt/xiami.ts    → XmDecrypt        .tm2   (虾米音乐，libtakiyasha 未实现)
 * src/decrypt/ximalaya.ts → XimalayaDecrypt  .xm .x2m .x3m (喜马拉雅，同上)
 *
 * 后端 /api/formats 端点可动态返回完整映射表。
 * ────────────────────────────────────────────────────────────────
 */
(function () {
    'use strict';

    var API_URL = '/api/decrypt';

    // 等待 Vue 应用挂载后查找 FileSelector 组件
    function init() {
        var appEl = document.getElementById('app');
        if (!appEl || !appEl.__vue__) {
            setTimeout(init, 100);
            return;
        }

        var vm = appEl.__vue__;
        var target = findComponent(vm, 'FileSelector');

        if (target) {
            patchFileSelector(target);
            console.log('[api-decrypt] FileSelector 已接管，解密请求将发送至 ' + API_URL);
            // 查询后端格式注册表，输出新旧解密器映射
            fetch('/api/formats').then(function (r) { return r.json(); }).then(function (data) {
                console.group('[api-decrypt] 格式注册表 (新后端 ↔ 旧前端)');
                data.supported.forEach(function (f) {
                    console.log('  ' + f.decryptor + ' [' + f.platform + '] .' + f.extensions.join(' .') + '\n' +
                        '    旧前端: ' + f.legacy_frontend + ' | libtakiyasha: ' + f.libtakiyasha);
                });
                if (data.unsupported_legacy && data.unsupported_legacy.length) {
                    console.warn('  旧前端支持但新后端暂不支持:');
                    data.unsupported_legacy.forEach(function (f) {
                        console.warn('    .' + f.extension + ' [' + f.platform + '] — ' + f.reason);
                    });
                }
                console.groupEnd();
            }).catch(function () {});
        } else {
            // 可能组件还未渲染，稍后重试
            setTimeout(init, 200);
        }
    }

    // 递归查找指定 name 的 Vue 组件
    function findComponent(vm, name) {
        if (vm.$options && vm.$options.name === name) return vm;
        var children = vm.$children || [];
        for (var i = 0; i < children.length; i++) {
            var found = findComponent(children[i], name);
            if (found) return found;
        }
        return null;
    }

    // 覆写 FileSelector.addFile
    function patchFileSelector(comp) {
        comp.addFile = function (fileObj) {
            var self = this;
            self.task_all++;

            // fileObj 可能是 {raw: File, name: string, ...} 或直接是 File
            var rawFile = fileObj.raw || fileObj;
            var fileName = fileObj.name || (rawFile && rawFile.name) || 'unknown';

            var formData = new FormData();
            formData.append('file', rawFile, fileName);

            fetch(API_URL, {
                method: 'POST',
                body: formData
            })
                .then(function (resp) {
                    var ct = resp.headers.get('content-type') || '';
                    // 后端失败时返回 JSON
                    if (ct.indexOf('application/json') >= 0) {
                        return resp.json().then(function (data) {
                            throw new Error(data.reason || '解密失败');
                        });
                    }
                    // 成功：读取 blob 和元数据头
                    return resp.blob().then(function (blob) {
                        var decodeHeader = function (name) {
                            var val = resp.headers.get(name) || '';
                            try {
                                return decodeURIComponent(val);
                            } catch (e) {
                                return val;
                            }
                        };

                        var title = decodeHeader('X-Title');
                        var artist = decodeHeader('X-Artist');
                        var album = decodeHeader('X-Album');
                        var ext = (resp.headers.get('X-Ext') || 'mp3').toLowerCase();
                        var mime = resp.headers.get('X-Mime') || 'audio/mpeg';

                        // 从原始文件名提取标题（去掉扩展名）
                        if (!title) {
                            title = fileName.replace(/\.[^.]+$/, '');
                        }

                        var result = {
                            title: title,
                            artist: artist,
                            ext: ext,
                            album: album,
                            picture: '',
                            file: URL.createObjectURL(blob),
                            blob: blob,
                            mime: mime,
                            rawExt: fileName.split('.').pop().toLowerCase(),
                            rawFilename: fileName
                        };

                        self.$emit('success', result);
                        self.task_finished++;
                    });
                })
                .catch(function (err) {
                    console.error('[api-decrypt]', err);
                    self.$emit('error', err, fileName);
                    self.task_finished++;
                });
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
