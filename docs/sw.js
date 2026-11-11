/* Network first, so every change you push shows up on the next open; the saved copy is only used offline. */
var C = 'bg-v2';
self.addEventListener('install', function (e) { self.skipWaiting(); });
self.addEventListener('activate', function (e) { e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', function (e) {
  var r = e.request;
  if (r.method !== 'GET' || new URL(r.url).origin !== location.origin) return;
  e.respondWith(fetch(r, { cache: 'no-cache' }).then(function (res) {
    var copy = res.clone(); caches.open(C).then(function (c) { c.put(r, copy); }); return res;
  }).catch(function () { return caches.match(r); }));
});
