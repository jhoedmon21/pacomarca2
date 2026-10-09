#!/usr/bin/env bash
# ============================================================
# Actualización de la aplicación (git pull + rebuild sin pérdida de datos).
# Uso:  ./deploy/update.sh
# ============================================================
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> 1/3 Trayendo la última versión del código"
git pull --ff-only

echo "==> 2/3 Reconstruyendo y reiniciando servicios"
docker compose up -d --build

echo "==> 3/3 Purgando imágenes antiguas"
docker image prune -f

echo ""
echo "Actualización completada:"
docker compose ps
echo ""
echo "Prueba: curl -s http://localhost/api/health"
