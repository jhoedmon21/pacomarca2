/*
 * Service worker de Pacomarca (PWA básica para uso en campo).
 * Estrategia conservadora para evitar datos satelitales viejos:
 *   - Navegación (HTML): network-first, con fallback al caché si no hay red.
 *   - Assets estáticos (js/css/imagenes): stale-while-revalidate.
 *   - /api/: SIEMPRE red directa (nunca se cachea).
 * Bump de versión: cambiar CACHE para invalidar el caché viejo.
 */
const CACHE = 'pacomarca-v1'
const PRECACHE = ['/']

self.addEventListener('install', (evento) => {
  evento.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((claves) =>
        Promise.all(claves.filter((clave) => clave !== CACHE).map((clave) => caches.delete(clave))),
      )
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (evento) => {
  const url = new URL(evento.request.url)

  // Solo GET del mismo origen; la API nunca se intercepta
  if (evento.request.method !== 'GET' || url.origin !== location.origin) return
  if (url.pathname.startsWith('/api/')) return

  // HTML: red primero (deploy nuevo visible al instante), caché sin conexión
  if (evento.request.mode === 'navigate') {
    evento.respondWith(
      fetch(evento.request).catch(() => caches.match('/').then((r) => r || Response.error())),
    )
    return
  }

  // Resto de estáticos: stale-while-revalidate
  evento.respondWith(
    caches.match(evento.request).then((enCache) => {
      const desdeRed = fetch(evento.request).then((respuesta) => {
        if (respuesta.ok) {
          const clon = respuesta.clone()
          caches.open(CACHE).then((cache) => cache.put(evento.request, clon))
        }
        return respuesta
      })
      return enCache || desdeRed
    }),
  )
})
