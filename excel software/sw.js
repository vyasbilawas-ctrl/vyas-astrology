// VYAS Service Worker for Offline Execution
const CACHE_NAME = 'vyas-astrology-v2.5';
const ASSETS = [
  './vyas_astrology_system.html',
  './manifest.json',
  './watermarked_img_1944548633781185789.jpg'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((res) => res || fetch(e.request).catch(() => caches.match('./vyas_astrology_system.html')))
  );
});
