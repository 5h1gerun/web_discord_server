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
  '/static/favicon.png',
  '/manifest.json',
  // CDN assets for faster LCP on PWA
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/mdb-ui-kit/6.4.0/mdb.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css',
  'https://cdnjs.cloudflare.com/ajax/libs/hover.css/2.3.1/css/hover-min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.7.2/vanilla-tilt.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/mdb-ui-kit/6.4.0/mdb.min.js',
  'https://cdn.jsdelivr.net/npm/hls.js@latest'
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

  if (
    url.pathname.startsWith('/download/') ||
    url.pathname.startsWith('/shared/download/') ||
    url.pathname.startsWith('/zip/') ||
    (url.pathname.startsWith('/f/') && url.searchParams.get('dl') === '1')
  ) {
    return; // let the browser handle file downloads
  }

  if (request.mode === 'navigate') {
    event.respondWith(handleNavigate(request));
    return;
  }

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // それ以外の API や部分 HTML などは新しい内容を優先
  event.respondWith(networkFirst(request));
});

async function handleNavigate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  if (cached) {
    fetch(request).then(res => cache.put(request, res.clone())).catch(() => {});
    return cached;
  }
  try {
    const res = await fetch(request);
    cache.put(request, res.clone());
    return res;
  } catch (_) {
    return caches.match(OFFLINE_PAGE);
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

async function networkFirst(request) {
  try {
    const res = await fetch(request);
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, res.clone());
    return res;
  } catch (_) {
    return caches.match(request);
  }
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
