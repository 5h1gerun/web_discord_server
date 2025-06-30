const CACHE_NAME = 'wds-cache-v1';
const OFFLINE_PAGE = '/offline';
const OFFLINE_URLS = [
  '/',
  OFFLINE_PAGE,
  '/static/css/style.css',
  '/static/css/style-mobile.css',
  '/static/css/style-mobile-friendly.css',
  '/static/css/style-phone.css',
  '/static/js/main.js',
  '/favicon.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(OFFLINE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(OFFLINE_PAGE))
    );
  } else {
    event.respondWith(
      caches.match(event.request).then(res => res || fetch(event.request))
    );
  }
});
