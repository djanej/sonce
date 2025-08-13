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
    try {
      const cache = await caches.open(CACHE_NAME);
      // Cache URLs individually to handle failures gracefully
      await Promise.all(
        urlsToCache.map(async url => {
          try {
            await cache.add(url);
          } catch (error) {
            // Individual URL caching failure won't break entire SW installation
            // This handles cross-origin or opaque responses gracefully
          }
        })
      );
      await self.skipWaiting();
    } catch (error) {
      // Installation continues even if caching fails
    }
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    try {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames.map(name => name !== CACHE_NAME ? caches.delete(name) : undefined)
      );
      await self.clients.claim();
    } catch (error) {
      // Activation continues even if old cache cleanup fails
    }
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
        // Only cache successful responses
        if (networkResponse && networkResponse.status === 200) {
          cache.put(request, networkResponse.clone()).catch(() => {});
        }
        return networkResponse;
      }).catch(() => undefined);
      return cachedResponse || networkFetch;
    })
  ).catch(() => fetch(request));
}

function cacheFirst(request) {
  return caches.open(CACHE_NAME).then(cache =>
    cache.match(request).then(cachedResponse => {
      if (cachedResponse) return cachedResponse;
      return fetch(request).then(networkResponse => {
        // Only cache successful responses
        if (networkResponse && networkResponse.status === 200) {
          cache.put(request, networkResponse.clone()).catch(() => {});
        }
        return networkResponse;
      });
    })
  ).catch(() => fetch(request));
}

self.addEventListener('fetch', event => {
  const request = event.request;
  
  // Only handle GET requests
  if (request.method !== 'GET') return;

  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const networkResponse = await fetch(request, { cache: 'no-store' });
        // Only cache successful responses
        if (networkResponse && networkResponse.status === 200) {
          const cache = await caches.open(CACHE_NAME);
          cache.put(OFFLINE_URL, networkResponse.clone()).catch(() => {});
        }
        return networkResponse;
      } catch (err) {
        // Try to return cached offline page
        const cached = await caches.match(OFFLINE_URL);
        return cached || new Response(
          '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Offline</title></head><body><h1>You are offline</h1><p>Please check your internet connection and try again.</p></body></html>',
          { headers: { 'Content-Type': 'text/html; charset=UTF-8' } }
        );
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