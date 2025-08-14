// Service Worker for Sindikat Sonce Koper website
const CACHE_NAME = 'sonce-cache-v3';
const OFFLINE_URL = '/index.html';
const urlsToCache = [
  '/',
  '/index.html',
  '/pogoji-uporabe.html',
  '/pravilnik-o-zasebnosti.html',
  '/pravilnik-o-piskotkih.html',
  '/favicons/favicon.ico',
  '/images/soncelogo.jpg'
];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    try {
      await cache.addAll(urlsToCache);
    } catch (e) {
      // Ignore failures for cross-origin or opaque responses
    }
    self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(name => name !== CACHE_NAME ? caches.delete(name) : undefined)
    );
    self.clients.claim();
  })());
});

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

function staleWhileRevalidate(request) {
  return caches.open(CACHE_NAME).then(cache =>
    cache.match(request).then(cachedResponse => {
      const networkFetch = fetch(request).then(networkResponse => {
        cache.put(request, networkResponse.clone()).catch(() => {});
        return networkResponse;
      }).catch(() => undefined);
      return cachedResponse || networkFetch;
    })
  );
}

function cacheFirst(request) {
  return caches.open(CACHE_NAME).then(cache =>
    cache.match(request).then(cachedResponse => {
      if (cachedResponse) return cachedResponse;
      return fetch(request).then(networkResponse => {
        cache.put(request, networkResponse.clone()).catch(() => {});
        return networkResponse;
      });
    })
  );
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const networkResponse = await fetch(request, { cache: 'no-store' });
        const cache = await caches.open(CACHE_NAME);
        cache.put(OFFLINE_URL, networkResponse.clone()).catch(() => {});
        return networkResponse;
      } catch (err) {
        const cached = await caches.match(OFFLINE_URL);
        if (cached) {
          return cached;
        }
        // Return a proper offline page
        return new Response(`
          <!DOCTYPE html>
          <html><head><title>Offline</title></head>
          <body><h1>Trenutno nimate internetne povezave</h1>
          <p>Poskusite znova, ko bo povezava vzpostavljena.</p></body></html>
        `, { 
          status: 200,
          headers: { 'Content-Type': 'text/html; charset=utf-8' } 
        });
      }
    })());
    return;
  }

  if (['style', 'script', 'worker'].includes(request.destination)) {
    // Always try network first to avoid stale scripts/styles that can blank the page
    event.respondWith(fetch(request).then(r => {
      caches.open(CACHE_NAME).then(c => c.put(request, r.clone())).catch(() => {});
      return r;
    }).catch(() => staleWhileRevalidate(request)));
    return;
  }

  if (request.destination === 'image') {
    event.respondWith(cacheFirst(request));
    return;
  }

  event.respondWith(fetch(request).catch(() => caches.match(request)));
});