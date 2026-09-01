const CACHE_NAME = 'propflow-v1';
const urlsToCache = [
  '/',
  '/static/css/karobarplus.css',
  '/static/js/app.js',
  '/portal/tenant/'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
