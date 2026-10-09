# Frontend Pacomarca Scientific Suite - imagen multi-stage
# Etapa 1: build de Vite (TypeScript + empaquetado)
# Etapa 2: nginx mínimo sirviendo los estáticos
FROM node:22-slim AS builder

WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
# VITE_API_URL vacío => el navegador llama a /api del mismo origen
# (Caddy lo enruta al backend en producción).
RUN npm run build

FROM nginx:1.27-alpine

# Configuración: SPA fallback (todas las rutas a index.html) y caché de assets
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /build/dist /usr/share/nginx/html

# nginx:alpine ya corre como usuario sin root (nginx usuario + master root
# solo para puertos 80; aquí quedamos tras el proxy Caddy en la red interna)
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1/ || exit 1
