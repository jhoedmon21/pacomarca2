// Registro del service worker: solo en producción para no interferir
// con el HMR de Vite en desarrollo. Un fallo de registro nunca rompe la app.
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      /* PWA es un extra opcional */
    })
  })
}
