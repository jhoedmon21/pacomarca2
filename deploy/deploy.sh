#!/usr/bin/env bash
# ============================================================
# Despliegue inicial en un VPS (Ubuntu) con Docker.
# Uso:  ./deploy/deploy.sh   (desde la raíz del proyecto, con .env ya creado)
# ============================================================
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
    echo "ERROR: falta .env. Copia .env.example a .env y completa los valores." >&2
    exit 1
fi

echo "==> 1/4 Cargando configuración de .env"
set -a; source .env; set +a

echo "==> 2/4 Construyendo imágenes"
docker compose build

echo "==> 3/4 Levantando servicios"
docker compose up -d

echo "==> 4/4 Esperando healthchecks (máx. 90 s)..."
for i in $(seq 1 30); do
    estado=$(docker inspect --format='{{.State.Health.Status}}' "$(docker compose ps -q backend)" 2>/dev/null || echo "starting")
    if [[ "$estado" == "healthy" ]]; then
        echo "✔ Backend saludable"
        break
    fi
    if [[ "$i" == "30" ]]; then
        echo "✘ El backend no pasó el healthcheck en 90 s. Revisa: docker compose logs backend" >&2
        exit 1
    fi
    sleep 3
done

echo ""
echo "Despliegue completado. Verificación rápida:"
docker compose ps
echo ""
echo "Prueba: curl -s http://localhost/api/health"
