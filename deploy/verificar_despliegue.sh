#!/usr/bin/env bash
# ============================================================
# Verifica la cadena completa de despliegue:
#   backend (Railway/Render) -> CORS -> frontend (Vercel)
#
# Uso:
#   ./deploy/verificar_despliegue.sh https://mi-backend.up.railway.app
#   ./deploy/verificar_despliegue.sh https://mi-backend.up.railway.app https://pacomarca2.vercel.app
# ============================================================
set -uo pipefail

BACKEND="${1:?Uso: $0 <url-backend> [url-frontend]}"
FRONTEND="${2:-https://pacomarca2.vercel.app}"
BACKEND="${BACKEND%/}"
FRONTEND="${FRONTEND%/}"

ok=0
fallo=0
pasa() { printf '  \033[32mOK\033[0m   %s\n' "$1"; ok=$((ok + 1)); }
falla() { printf '  \033[31mFALLA\033[0m %s\n' "$1"; fallo=$((fallo + 1)); }

echo "Backend : $BACKEND"
echo "Frontend: $FRONTEND"
echo

# ---------- 1. Salud ----------
echo "1) /api/health"
salud=$(curl -s -m 90 "$BACKEND/api/health" || echo "")
if [ -z "$salud" ]; then
  falla "el backend no responde (¿servicio caído o URL incorrecta?)"
elif ! printf '%s' "$salud" | grep -q '"gee_status"'; then
  # Respuesta del edge del hosting (404 "Application not found", HTML, etc.)
  falla "esa URL no es la API: $salud"
  echo "         -> el servicio no existe o cambió de dominio; revisa el panel de Railway/Render"
else
  echo "   $salud"
  case "$salud" in
    *'"status":"ok"'*) pasa "estado general ok" ;;
    *) falla "estado degradado: revisa gee_status y database_status arriba" ;;
  esac
  case "$salud" in
    *'"gee_status":"conectado"'*) pasa "GEE conectado" ;;
    *) falla "GEE sin conexión: GEE_SERVICE_ACCOUNT_EMAIL / GEE_PRIVATE_KEY_JSON / GEE_PROJECT" ;;
  esac
  case "$salud" in
    *'"database_status":"operativo"'*) pasa "base de datos operativa" ;;
    *) falla "base de datos caída: revisa DATABASE_URL (o el volumen SQLite)" ;;
  esac
fi
echo

# ---------- 2. Endpoint de datos real ----------
echo "2) /api/tiles/ndvi"
tiles=$(curl -s -m 120 -w '\n%{http_code}' "$BACKEND/api/tiles/ndvi?lat=-14.85&lon=-70.92" || echo "000")
codigo=$(printf '%s' "$tiles" | tail -n1)
cuerpo=$(printf '%s' "$tiles" | sed '$d')
case "$codigo" in
  200) pasa "tiles generados" ;;
  503) falla "503: GEE no autenticado -> $cuerpo" ;;
  502 | 504) falla "timeout del proxy ($codigo): GEE tarda demasiado en arrancar" ;;
  *) falla "HTTP $codigo -> $cuerpo" ;;
esac
echo

# ---------- 3. CORS ----------
echo "3) CORS desde el dominio del frontend"
cabeceras=$(curl -s -m 30 -D - -o /dev/null -X OPTIONS \
  -H "Origin: $FRONTEND" \
  -H "Access-Control-Request-Method: GET" \
  "$BACKEND/api/health" || echo "")
if printf '%s' "$cabeceras" | grep -qi "access-control-allow-origin"; then
  pasa "el preflight devuelve Access-Control-Allow-Origin"
else
  falla "sin cabecera CORS: añade $FRONTEND a ALLOWED_ORIGINS en el backend"
fi
echo

# ---------- 4. Frontend ----------
echo "4) Frontend en Vercel"
inicio=$(curl -s -m 30 "$FRONTEND" || echo "")
if printf '%s' "$inicio" | grep -q '<div id="root"'; then
  pasa "el frontend responde"
else
  falla "el frontend no devuelve la app (revisa el deploy en Vercel)"
fi
api_local=$(curl -s -m 30 "$FRONTEND/api/health" || echo "")
case "$api_local" in
  *'"gee_status"'*) echo "  INFO el frontend también proxya /api (no necesita VITE_API_URL)" ;;
  *) echo "  INFO /api en Vercel devuelve HTML: es normal, el frontend llama a VITE_API_URL directamente" ;;
esac
echo

# ---------- Resumen ----------
echo "--------------------------------------------"
echo "Correctos: $ok   Fallos: $fallo"
if [ "$fallo" -eq 0 ]; then
  echo "Despliegue coherente: la app debería mostrar datos."
  exit 0
fi
echo "Revisa los puntos marcados como FALLA."
exit 1
