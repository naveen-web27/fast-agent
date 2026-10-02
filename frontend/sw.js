const CACHE_NAME = 'rightconnect-shell-v3';
const SHELL = ['/pages/marketplace.html', '/pages/auth.html', '/pages/plans.html', '/manifest.webmanifest', '/assets/rightconnect-mark.svg', '/assets/workspace.js'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET' || new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});