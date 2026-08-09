/**
 * api-decrypt.js — 前端补丁（最小侵入）
 *
 * 拦截 FileSelector 组件的文件处理逻辑，将原来的 Worker 解密
 * 改为 fetch /api/decrypt 上传文件，拿回解密后的原始格式 blob（FLAC/OGG/MP3）。
 *
 * 等价于注释掉 src/decrypt 内所有旧解密器注册——旧 Worker 解密链路被完全旁路。
 * 前端 UI 组件、下载逻辑、PWA 配置均不动。
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
