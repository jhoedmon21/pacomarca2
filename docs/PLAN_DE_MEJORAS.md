# Plan de Mejoras - Pacomarca Scientific Suite

## Estado Actual (Octubre 2026)

### ✅ Lo que ya existe
| Criterio | Estado | Implementación |
|---------|--------|----------------|
| Modelo de biomasa heurístico (NDVI × 2800) | ✅ | Línea 124 de `app.py` |
| Clasificación por umbrales NDVI (0.2/0.45) | ✅ | Líneas 203-212 de `app.py` |
| Serie temporal MODIS (23 años) | ✅ | Líneas 103-126 de `app.py` |
| Alertas de anomalía (>±15%) | ✅ | Líneas 313-322 de `app.py` |
| Clima en tiempo real (Open-Meteo) | ✅ | Líneas 96-100 de `app.py` |
| Exportación CSV (serie temporal) | ⚠️ | No implementado en UI |
| API REST para datos | ✅ | Backend `/api/timeseries`, `/api/weather`, etc. |

### ⚠️ Problemas conocidos
1. **Deprecación MODIS/006**: Usar `MODIS/061/MOD13Q1` (advertencia en consola)
2. **Rate limit en memoria**: Con >1 instancia de backend conviene Redis
3. **Credenciales GEE**: Funciona localmente, pero requiere `secrets.toml` para Streamlit Cloud

---

## P1 — Calidad de Datos y Confianza (Prioridad Alta)

### P1.1 — Calibración del modelo de biomasa con campo
**Esfuerzo**: Bajo-medio
**Impacto**: Alto

**Qué hacer**:
1. Crear función de calibración que acepte muestreos de campo (NDVI + Kg/Ha)
2. Entrenar modelo lineal/potencia con scikit-learn
3. Guardar coeficientes y R² en un archivo `.json` local
4. Reemplazar `biomasa = df['v'] * 2800` por `biomasa = df['v'] * coeficiente_calibrado`

**Archivos a crear**:
- `calibrate_biomass.py`: Script de calibración
- `config/biomass_model.json`: Coeficientes del modelo
- Actualizar `app.py` para cargar el modelo

---

### P1.2 — Clasificador supervisado (RandomForest)
**Esfuerzo**: Bajo
**Impacto**: Medio

**Qué hacer**:
1. Usar las muestras de campo del P1.1
2. Entrenar RandomForest con scikit-learn (ya está instalado)
3. Crear endpoint `/api/classification` que use el modelo entrenado
4. Actualizar frontend para mostrar % de suelo/pasto alto/bajo

**Archivos a crear/modificar**:
- `backend/app/services/classification.py`: Nueva clase RandomForestClassifier
- `backend/app/main.py`: Nuevo endpoint `/api/classification`
- `frontend/src/hooks/useClassification.ts`: Hook para consumir el endpoint

---

### P1.3 — Validación cruzada MODIS vs Sentinel-2
**Esfuerzo**: Medio
**Impacto**: Alto

**Qué hacer**:
1. Crear endpoint `/api/crosscheck` que devuelva NDVI MODIS (250m) vs S2 (10m)
2. Mostrar discrepancia en la UI (gráfico de dispersión o tabla)
3. Documentar la escala del análisis

**Archivos a crear/modificar**:
- `backend/app/services/crosscheck.py`: Lógica de validación
- `backend/app/main.py`: Nuevo endpoint `/api/crosscheck`
- `frontend/src/hooks/useCrosscheck.ts`: Hook para consumir el endpoint
- `frontend/src/pages/Crosscheck.tsx`: Página de validación

---

### P1.4 — Exportación de ROI como GeoJSON/Shapefile
**Esfuerzo**: Bajo
**Impacto**: Medio

**Qué hacer**:
1. Agregar botón "Exportar ROI" en la UI
2. Generar GeoJSON de la región de interés (ROI)
3. Opción para descargar como `.shp` (usar pyshp)

**Archivos a crear/modificar**:
- `app.py`: Agregar función `export_roi_geojson(lat, lon, buffer)`
- UI: Botón "📥 Exportar ROI" en el sidebar

---

## P2 — Operación y Monitoreo (Prioridad Media)

### P2.1 — Observabilidad (Sentry + Uptime-Kuma)
**Esfuerzo**: Medio
**Impacto**: Alto

**Qué hacer**:
1. Configurar Sentry para frontend (Streamlit)
2. Configurar Sentry para backend (FastAPI)
3. Crear panel `/metrics` con métricas Prometheus
4. Opcional: Uptime-Kuma para monitoreo visual

**Archivos a crear/modificar**:
- `backend/requirements.txt`: Añadir `sentry-sdk`
- `backend/app/main.py`: Integrar Sentry
- `frontend/src/main.tsx`: Integrar Sentry
- `backend/app/middleware/metrics.py`: Métricas Prometheus

---

### P2.2 — Alertas proactivas (cron job)
**Esfuerzo**: Medio
**Impacto**: Alto

**Qué hacer**:
1. Crear script `deploy/jobs/alerta_diaria.py`
2. Programar cron en VPS (07:00 UTC)
3. Enviar email/WhatsApp si anomalía >15%
4. Usar SMTP (configuración en `.env`)

**Archivos a crear/modificar**:
- `deploy/jobs/alerta_diaria.py`: Script de alerta
- `.env`: Variables SMTP y umbral
- `deploy/update.sh`: Agregar línea al cron

---

### P2.3 — Autenticación opcional (JWT/OAuth)
**Esfuerzo**: Alto
**Impacto**: Medio (solo si circula fuera del equipo técnico)

**Qué hacer**:
1. Elegir autenticador (Auth0, Firebase, o JWT propio)
2. Crear endpoints protegidos con JWT
3. Actualizar frontend para requerir login

**Archivos a crear/modificar**:
- `backend/app/middleware/auth.py`: Middleware JWT
- `backend/app/main.py`: Endpoints protegidos
- `frontend/src/services/api.ts`: Interceptores JWT

---

### P2.4 — Backup del .env y configuración Caddy
**Esfuerzo**: Bajo
**Impacto**: Alto (redundancia)

**Qué hacer**:
1. Crear script de backup (`deploy/jobs/backup.sh`)
2. Programar backup diario
3. Guardar en disco seguro (S3 o NAS local)

**Archivos a crear/modificar**:
- `deploy/jobs/backup.sh`: Script de backup
- `deploy/update.sh`: Agregar línea al cron
- `docs/RUNBOOK.md`: Documentación de restore

---

## P3 — Producto y Ciencia (Prioridad Baja)

### P3.1 — Multi-punto / parcelas
**Esfuerzo**: Alto
**Impacto**: Medio

**Qué hacer**:
1. Crear base de datos (SQLite/Postgres)
2. Crear endpoints CRUD para puntos
3. Actualizar UI para gestionar múltiples puntos

**Archivos a crear/modificar**:
- `backend/app/models.py`: Modelo de puntos
- `backend/app/database.py`: Conexión a base de datos
- `backend/app/main.py`: Endpoints CRUD
- `frontend/src/pages/Points.tsx`: Página de gestión de puntos

---

### P3.2 — Pronóstico de oferta forrajera
**Esfuerzo**: Alto
**Impacto**: Alto

**Qué hacer**:
1. Usar Open-Meteo forecast (15-30 días)
2. Combinar con serie NDVI actual
3. Proyectar Kg MS/Ha con incertidumbre
4. Mostrar en UI (gráfico de proyección)

**Archivos a crear/modificar**:
- `backend/app/services/forecast.py`: Lógica de pronóstico
- `backend/app/main.py`: Nuevo endpoint `/api/forecast`
- `frontend/src/hooks/useForecast.ts`: Hook para consumir el endpoint
- `frontend/src/pages/Forecast.tsx`: Página de pronóstico

---

### P3.3 — Índices complementarios (NDWI, SAVI, NDVI S2)
**Esfuerzo**: Medio
**Impacto**: Medio

**Qué hacer**:
1. Implementar cálculo de NDWI (agua)
2. Implementar SAVI (corrección de suelo)
3. Usar Sentinel-2 para NDVI a 10m (serie reciente)
4. Agregar opciones en la UI

**Archivos a crear/modificar**:
- `app.py`: Agregar funciones de cálculo de índices
- UI: Agregar opción en el radio button de capas

---

### P3.4 — Histórico MODIS completo (2000-hoy)
**Esfuerzo**: Bajo
**Impacto**: Medio

**Qué hacer**:
1. Cambiar colección de MODIS de `MODIS/006/MOD13Q1` a `MODIS/061/MOD13Q1`
2. Verificar que el slider ya llega a 23 años
3. Documentar el cambio

**Archivos a crear/modificar**:
- `app.py`: Línea 108 (cambiar colección)
- `docs/NOTAS_MODIS.md`: Documentación del cambio

---

### P3.5 — PWA (App móvil instalable)
**Esfuerzo**: Medio
**Impacto**: Medio

**Qué hacer**:
1. Asegurar que `frontend/dist` ya sea un PWA (manifest + service worker)
2. Agregar `manifest.webmanifest` al backend (servir estáticos)
3. Probar en móvil

**Archivos a crear/modificar**:
- `backend/app/main.py`: Servir `dist/manifest.webmanifest`
- `frontend/src/pwa.ts`: Configurar service worker
- `frontend/public/manifest.webmanifest`: Manifest actualizado

---

### P3.6 — i18n completo runu simi (quechua)
**Esfuerzo**: Alto
**Impacto**: Bajo (solo si se justifica)

**Qué hacer**:
1. Crear diccionario de traducciones (es/en/runu)
2. Actualizar frontend para usar i18n
3. Traducir UI completa

**Archivos a crear/modificar**:
- `frontend/src/i18n/translations.ts`: Diccionario de traducciones
- `frontend/src/i18n/index.tsx`: Provider i18n
- Actualizar todos los componentes para usar `useTranslation`

---

## Deuda Técnica Conocida

| Deuda | Prioridad | Solución |
|-------|-----------|----------|
| Rate limit en memoria | P2 | Mover a Redis |
| getMapId de GEE expira (~horas) | P3 | Reducir TTL o refrescar en 404 |
| Clasificador calibrado para Puno | P3 | Documentar y crear guía de recálculo |

---

## Cronograma Propuesto

### Fase 1 (2-3 semanas) — P1
1. **Semana 1**:
   - P1.1: Calibración de biomasa con campo
   - P1.4: Exportación de ROI

2. **Semana 2**:
   - P1.2: Clasificador RandomForest
   - P1.3: Validación cruzada MODIS vs S2

### Fase 2 (2-3 semanas) — P2
1. **Semana 1**:
   - P2.1: Observabilidad (Sentry)
   - P2.4: Backup

2. **Semana 2**:
   - P2.2: Alertas proactivas
   - P2.3: Autenticación (opcional)

### Fase 3 (3-4 semanas) — P3
1. **Semana 1**:
   - P3.4: Histórico MODIS completo
   - P3.5: PWA

2. **Semana 2-3**:
   - P3.2: Pronóstico de oferta forrajera
   - P3.3: Índices complementarios

3. **Semana 4** (opcional):
   - P3.6: i18n runu simi

---

## Próximos Pasos Inmediatos

1. **Resolver deprecación MODIS** (P3.4 - Bajo esfuerzo, Alto impacto)
2. **Crear script de calibración de biomasa** (P1.1)
3. **Agregar exportación de ROI** (P1.4 - Bajo esfuerzo, Medio impacto)
4. **Configurar Sentry** (P2.1 - Medio esfuerzo, Alto impacto)

¿Qué te gustaría empezar con?
