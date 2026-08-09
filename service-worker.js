/**
 * Music-Unlock Service Worker (轻量版)
 * 移除了 Google CDN 的 workbox 依赖，改为原生 Cache API
 * 策略：静态资源 cache-first，HTML 网络优先
 */

var CACHE_NAME = 'unlock-music-v1.10.7';

// 只预缓存小文件，大文件（worker 1.3MB、vendor 1.6MB）按需缓存
var PRECACHE_URLS = [
  'index.html',
  'loader.js',
  'css/app.5388e39c.css',
  'css/chunk-vendors.094863c6.css',
  'js/app.e29ffaed.js',
  'web-manifest.json',
  'favicon.ico',
  'img/icons/favicon-32x32.png',
  'img/icons/favicon-16x16.png'
];

// 安装：预缓存小文件，跳过大文件
self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(PRECACHE_URLS).catch(function () {
        // 部分缓存失败不阻塞安装
      });
    })
  );
  self.skipWaiting();
});

// 激活：清理旧缓存
self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (names) {
      return Promise.all(
        names.filter(function (name) {
          return name !== CACHE_NAME;
        }).map(function (name) {
          return caches.delete(name);
        })
      );
    })
  );
  self.clients.claim();
});

// 请求拦截：静态资源 cache-first，HTML network-first
self.addEventListener('fetch', function (event) {
  var url = new URL(event.request.url);

  // 只处理同源请求
  if (url.origin !== self.location.origin) return;

  // HTML 文件：网络优先（保证拿到最新版本）
  if (event.request.mode === 'navigate' || url.pathname.endsWith('.html')) {
    event.respondWith(
      fetch(event.request).then(function (response) {
        var clone = response.clone();
        caches.open(CACHE_NAME).then(function (cache) {
          cache.put(event.request, clone);
        });
        return response;
      }).catch(function () {
        return caches.match(event.request).then(function (cached) {
          return cached || caches.match('index.html');
        });
      })
    );
    return;
  }

  // 其他静态资源：cache-first，缓存未命中时从网络获取并缓存
  event.respondWith(
    caches.match(event.request).then(function (cached) {
      if (cached) return cached;
      return fetch(event.request).then(function (response) {
        // 只缓存成功的响应
        if (response && response.status === 200) {
          var clone = response.clone();
          caches.open(CACHE_NAME).then(function (cache) {
            cache.put(event.request, clone);
          });
        }
        return response;
      }).catch(function () {
        // 网络失败且无缓存，返回空
      });
    })
  );
});
