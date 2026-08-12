const CACHE_VERSION = 'techshop-v1';
const PRECACHE = [
  '/',
  '/static/manifest.json'
];

// Installation : pré-cache des pages essentielles
self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function (cache) {
      return cache.addAll(PRECACHE);
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

// Activation : purge des anciens caches
self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (key) {
          return key !== CACHE_VERSION;
        }).map(function (key) {
          return caches.delete(key);
        })
      );
    }).then(function () {
      return self.clients.claim();
    })
  );
});

// Stratégie : réseau d'abord, cache en secours (hors-ligne)
self.addEventListener('fetch', function (event) {
  const request = event.request;

  // On n'intercepte pas les requêtes POST ni les APIs
  if (request.method !== 'GET') return;

  // Ignorer les URL non http(s) (ex: chrome-extension, CDN)
  const url = new URL(request.url);
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return;

  event.respondWith(
    fetch(request)
      .then(function (response) {
        // On ne cache que les réponses valides et identiques (pas /admin/)
        if (response && response.status === 200 && response.type === 'basic') {
          const copy = response.clone();
          caches.open(CACHE_VERSION).then(function (cache) {
            cache.put(request, copy);
          });
        }
        return response;
      })
      .catch(function () {
        return caches.match(request).then(function (cached) {
          return cached || caches.match('/');
        });
      })
  );
});