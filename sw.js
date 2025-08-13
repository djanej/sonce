// Service Worker for Sindikat Sonce Koper website
const CACHE_NAME = 'sonce-cache-v2';
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
        const networkResponse = await fetch(request);
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, networkResponse.clone()).catch(() => {});
        return networkResponse;
      } catch (err) {
        const cached = await caches.match(OFFLINE_URL);
        return cached || new Response('Offline', { headers: { 'Content-Type': 'text/plain' } });
      }
    })());
    return;
  }

  if (['style', 'script', 'worker'].includes(request.destination)) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  if (request.destination === 'image') {
    event.respondWith(cacheFirst(request));
    return;
  }

  event.respondWith(fetch(request).catch(() => caches.match(request)));
});