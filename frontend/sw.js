const CACHE_NAME = 'rightconnect-shell-v7';
const SHELL = ['/', '/pages/marketplace.html', '/pages/auth.html', '/pages/plans.html', '/manifest.webmanifest', '/assets/rightconnect-mark.svg', '/assets/icon-192.png', '/assets/workspace.js', '/assets/mobile-install.js', '/assets/showcases.js', '/assets/app-tour.js'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key.startsWith('rightconnect-shell-') && key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET' || new URL(event.request.url).origin !== self.location.origin) return;
  if (new URL(event.request.url).pathname.startsWith('/downloads/')) return;
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});