// Cache vazio mas suficiente para o celular entender como Instalável
const CACHE_NAME = 'thermolac-v1';
const urlsToCache = [
  '/static/css/style.css'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
        return cache.addAll(urlsToCache);
    })
  );
});

self.addEventListener('fetch', event => {
  // Apenas responde com network para estar vivo
});
