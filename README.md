# Pacomarca Scientific Suite

Plataforma web de monitoreo de pastizales y forraje para el fundo Pacomarca
(altiplano de Puno, Perú) mediante teledetección: series temporales MODIS,
capas Sentinel-1/2, clasificación de hábitats, clima en tiempo real y modelo
heurístico de biomasa.

Sustituye a la aplicación Streamlit original (conservada en `legacy/` solo como
referencia) con una arquitectura API + SPA lista para producción.

---

## Arquitectura

```
                    ┌──────────────────────────┐
   Usuario ────────►│  Caddy (HTTPS automático) │ :80/:443
                    └──────────┬───────────────┘
                    /api/*     │     resto (SPA)
              ┌────────────────┴────────────────┐
              ▼                                 ▼
   ┌─────────────────────┐          ┌─────────────────────┐
   │  FastAPI (uvicorn)  │          │  nginx (estáticos   │
   │  GEE · Open-Meteo   │          │  de React + Vite)   │
   └───────┬──────┬──────┘          └─────────────────────┘
     get/set│     │ SQLAlchemy async
            ▼     ▼
   ┌───────┐  ┌─────────────────────────┐
   │ Redis │  │ Base de datos           │
   │ caché │  │ SQLite (local/volumen)  │
   └───────┘  │ o Postgres (Neon,       │
              │ Supabase... gratis)     │
              └─────────────────────────┘
              ┌───────────────────────────┐
              │ Externos: Google Earth    │
              │ Engine · Open-Meteo · Esri│
              └───────────────────────────┘
```

**Backend** — Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 async
(aiosqlite/asyncpg), earthengine-api, httpx, numpy. Caché Redis (fallback en
memoria), rate limiting, logs JSON, cabeceras de seguridad, cuenta de servicio
GEE.

**Base de datos** — persistencia de *puntos de control guardados* (parcelas
con nombre, coordenadas y notas) y del *historial de alertas* que registra el
job diario. Por defecto SQLite (archivo en volumen Docker, cero
configuración); para despliegues multi-instancia basta apuntar `DATABASE_URL`
a un **Postgres gratuito** (Neon, Supabase, Railway, Aiven — ver
`.env.example`). El esquema se crea y siembra solo al arrancar.

**Frontend** — React 18 + TypeScript + Vite, Tailwind CSS, TanStack Query,
Zustand (estado persistente), MapLibre GL (mapa), Recharts (gráficos),
tema claro/oscuro con tokens CSS, i18n es/en, accesible (WCAG 2.1 AA).

| Endpoint | Descripción |
|---|---|
| `GET /api/health` | Estado general, caché, **base de datos** y conexión GEE |
| `GET /api/weather?lat=&lon=` | Clima actual (Open-Meteo) |
| `GET /api/timeseries?lat=&lon=&years=1..26&index=ndvi\|evi\|biomasa[&format=csv]` | Serie temporal MODIS/061 (histórico completo desde 2000) |
| `GET /api/tiles/{layer}?lat=&lon=` | Tiles XYZ de GEE: `biomasa`, `clasificacion`, `radar_s1`, `ndvi`, `evi`, `savi`, `ndwi` |
| `GET /api/classification?lat=&lon=` | % de suelo/pasto bajo/pasto alto |
| `GET /api/crosscheck?lat=&lon=` | Validación cruzada NDVI MODIS (250 m) vs Sentinel-2 (10 m) |
| `GET /api/stats?lat=&lon=&years=&layer=` | Media, máx., mín., tendencia y anomalía |
| `GET/POST /api/puntos` · `PATCH/DELETE /api/puntos/{id}` | **CRUD de puntos de control (base de datos)** |
| `GET/POST /api/alertas` | **Historial de alertas persistido (base de datos)** |
| `GET /metrics` | Métricas Prometheus (peticiones y latencia) |

Documentación interactiva: `/docs` (Swagger) y `/redoc`.

## Servicios gratuitos utilizados

| Servicio | Uso | Límite del plan gratuito |
|---|---|---|
| Google Earth Engine | Datos satelitales (MODIS, Sentinel) | Investigación/usos no comerciales |
| Open-Meteo | Clima actual | Sin API key, uso razonable |
| **Neon** / **Supabase** / **Railway** / **Aiven** | Postgres gestionado (opcional a SQLite) | 0.5 GB / 500 MB / crédito mensual / 1 GB aprox |
| Esri World Imagery | Basemap del mapa | Uso en apps con atribución |
| Caddy + Let's Encrypt | HTTPS automático | Ilimitado |

La base de datos **funciona sin ninguno de estos Postgres**: SQLite local es el
valor por defecto y no requiere cuenta ni tarjeta.

## Modelo de biomasa (importante)

`biomasa_kg_ha = NDVI × 2800` es un modelo **simple y heurístico**:

* Relación lineal que se satura con coberturas altas.
* Coeficiente único (configurable con `BIOMASS_COEFFICIENT`), sin separación
  por especie ni estado fenológico; NDVI MODIS mezcla pixeles de 250 m.
* Útil para **tendencias y alertas**, no como medida parcelaria exacta.
* Para decisiones de carga animal, validar con muestreo de campo.

La clasificación de hábitats es por umbrales de NDVI (0.20 / 0.45) sobre
Sentinel-2, calibrada para pastizales altoandinos.

## Desarrollo local

Requisitos: Python 3.12+, Node 22+, (opcional) Redis.

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000/docs
pytest                                 # 46 tests (incluye CRUD y persistencia)

# Frontend (otra terminal)
cd frontend
npm install
npm run dev                            # http://localhost:5173 (proxy /api -> :8000)
```

Sin credenciales GEE el backend arranca en **modo degradado**: los endpoints
de datos devuelven 503 con mensaje claro y `/api/health` reporta `"degradado"`.
La base de datos SQLite se crea sola en `backend/data/pacomarca.db` al primer
arranque y el punto "Fundo Pacomarca" queda sembrado.

## Despliegue en VPS Ubuntu (paso a paso)

### 1. Servidor base

```bash
ssh root@TU_IP
adduser pacomarca && usermod -aG sudo pacomarca
rsync --archive --chown=pacomarca:pacomarca ~/.ssh /home/pacomarca
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw enable
```

### 2. Docker + compose

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker pacomarca
exit   # reconectar
```

### 3. Código y configuración

```bash
git clone TU_REPOSITORIO pacomarca && cd pacomarca
cp .env.example .env
nano .env    # completar: SITE_ADDRESS, GEE_SERVICE_ACCOUNT_EMAIL, GEE_PRIVATE_KEY_JSON, ALLOWED_ORIGINS
chmod 600 .env
```

`GEE_PRIVATE_KEY_JSON` acepta dos formatos:
* El **contenido JSON completo** de la clave de la cuenta de servicio
  (pégalo en una línea), o
* una **ruta a un archivo** montado en el contenedor, p. ej.
  `/run/secrets/gee.json` (cópialo con `sudo install -m 640 gee.json /etc/pacomarca/`).

### 4. Dominio

En tu proveedor DNS, crea un registro `A` que apunte `pacomarca.tudominio.com`
a la IP del VPS. Espera la propagación: `dig +short pacomarca.tudominio.com`.

### 5. Desplegar

```bash
./deploy/deploy.sh
```

Caddy emite y renueva el certificado TLS **automáticamente** al detectar el
dominio en `SITE_ADDRESS`.

### 6. Checklist post-despliegue

```bash
docker compose ps                        # los 4 servicios Up/healthy
curl -s http://localhost/api/health      # {"status":"ok",...,"gee_status":"conectado"}
curl -sI https://pacomarca.tudominio.com | head -1   # HTTP/2 200
```

- [ ] `/api/health` responde `"ok"` (si dice `"degradado"`, revisa `docker compose logs backend`)
- [ ] HTTPS activo con candado válido (Caddy, Let's Encrypt)
- [ ] El mapa carga la capa activa y el clic mueve el punto
- [ ] Clima visible en la cabecera
- [ ] Serie temporal y exportación CSV/PNG funcionan
- [ ] `docker compose logs backend | grep ERROR` vacío
- [ ] Reinicio del VPS levanta todo solo: `sudo reboot` y repetir los checks

### Actualizar

```bash
./deploy/update.sh
```

### Alerta diaria por email (opcional)

Configura `SMTP_*` y `ALERTA_EMAIL_DESTINO` en `.env` y programa el job en el
cron del VPS (por ejemplo a las 07:00):

```bash
crontab -e
# 0 7 * * * cd /srv/pacomarca && docker compose --profile jobs run --rm alerta >> /var/log/pacomarca-alerta.log 2>&1
```

Envía un correo cuando la anomalía de biomasa del punto por defecto cae por
debajo de `ALERTA_UMBRAL_PORCENTAJE` (−15 % por defecto). Cada alerta queda
**registrada en la base de datos** (`/api/alertas`) y se muestra en el
historial del dashboard, aunque no haya correo configurado.

## Alternativa: Railway / Render

1. Crea **dos servicios** desde el repositorio:
   * **Backend**: root `backend/`, puerto `$PORT` con comando
     `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
   * **Frontend**: root `frontend/`, comando `npm run build`, directorio
     público `dist` (en Railway añade un servicio estático; en Render usa
     "Static Site").
2. Configura las variables del `.env.example` en el panel (sin `SITE_ADDRESS`
   ni Caddy: la plataforma termina TLS).
3. Redis: usa el add-on de la plataforma y pon su URL en `REDIS_URL`
   (opcional; sin Redis el caché funciona en memoria).
4. Apunta `VITE_API_URL` del frontend a la URL pública del backend, o usa un
   rewrite de `/api/*` si la plataforma lo soporta.

## Seguridad

* Ninguna clave en el código: todo por entorno (`.env`, fuera del repo).
* CORS restringido a `ALLOWED_ORIGINS`; rate limiting 100 req/min/IP
  (configurable); cabeceras OWASP; contenedores sin privilegios; Redis sin
  persistencia ni exposición externa.
* Consultas públicas en GET; la escritura (puntos y alertas) queda limitada a
  los orígenes de `ALLOWED_ORIGINS` y no admite datos personales: solo nombres
  de parcelas y coordenadas. No hay cuentas de usuario ni contraseñas.
* Si expones la API más allá de tu organización, añade autenticación (p. ej.
  API key u OAuth) delante de los endpoints de escritura.

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `gee_status: sin conexión` | Cuenta de servicio mal formada | Verifica email + JSON; prueba `earthengine authenticate --private_key_file` |
| Capa no carga en el mapa | Sin imágenes S2/S1 recientes (nubes/orbita) | Prueba otra capa o espera; es normal en época de lluvias |
| 429 en la API | Rate limit superado | Espera el `Retry-After` indicado o sube `RATE_LIMIT_PER_MINUTE` |
| Certificado no llega | DNS no propagado o puerto 80 bloqueado | `dig`, `ufw status`; Caddy reintenta solo |
| Mapa en blanco tras deploy | Tiles bloqueados por CSP | Verifica que usas el `Caddyfile` incluido |

## Licencia y créditos

Jhon Monroy — Experto en Informática.
Fuentes: Google Earth Engine (MODIS/061/MOD13Q1, Sentinel-1/2), Open-Meteo,
Esri World Imagery.
