import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// En desarrollo, /api se delega al backend local (puerto 8000 por defecto;
// cámbialo con VITE_API_PROXY si ese puerto está ocupado), así el frontend
// no necesita CORS ni URLs absolutas.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY ?? 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        // Separar las librerías pesadas mejora la carga inicial y el caché
        manualChunks: {
          mapa: ['maplibre-gl'],
          graficos: ['recharts'],
        },
      },
    },
  },
})
