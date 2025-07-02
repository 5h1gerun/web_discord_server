const CACHE_NAME = 'wds-cache-v3';
const OFFLINE_PAGE = '/offline';
const OFFLINE_URLS = [
  '/',
  OFFLINE_PAGE,
  '/static/css/style.css',
  '/static/css/style-mobile.css',
  '/static/css/style-mobile-friendly.css',
  '/static/css/style-phone.css',
  '/static/js/main.js',
  '/static/favicon.png'
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
  const { request } = event;
  const url = new URL(request.url);

  if (request.mode === 'navigate') {
    event.respondWith(handleNavigate(request));
    return;
  }

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  event.respondWith(
    caches.match(request).then(res => res || fetch(request))
  );
});

async function handleNavigate(request) {
  try {
    const res = await fetch(request);
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, res.clone());
    return res;
  } catch (_) {
    const cached = await caches.match(request);
    return cached || caches.match(OFFLINE_PAGE);
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  const fetchPromise = fetch(request).then(res => {
    cache.put(request, res.clone());
    return res;
  }).catch(() => cached);
  return cached || fetchPromise;
}

self.addEventListener('push', event => {
  let data = {};
  if (event.data) {
    try { data = event.data.json(); } catch (_) { data = { title: event.data.text() }; }
  }
  const title = data.title || '通知';
  const options = {
    body: data.body,
    icon: '/static/favicon.png',
    data: data.url || '/'
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
  const url = event.notification.data;
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(winClients => {
      for (const client of winClients) {
        if (client.url === url && 'focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});
