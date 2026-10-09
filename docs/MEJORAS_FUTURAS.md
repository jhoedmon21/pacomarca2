# Mejoras futuras priorizadas — Pacomarca Scientific Suite

> Estado al 2026-10-08: varias mejoras P1-P3 ya están **aplicadas** (marcadas
> ✅). Las pendientes mantienen su prioridad original.

Criterios de prioridad: valor agronómico para Pacomarca ÷ esfuerzo, y riesgo
técnico mitigado. P = prioridad (P1 ahora, P2 después, P3 cuando haya uso real).

## P1 — Calidad de datos y confianza

1. **Calibrar el modelo de biomasa con campo** (2-3 muestreos de temporada):
   cortes de biomasa georreferenciados → ajuste lineal/potencia NDVI→Kg/Ha con
   scikit-learn, guardando R² y fechas de calibración. Convierte el modelo
   heurístico en un modelo con respaldo experimental. *Esfuerzo: bajo-medio.*
   **Requiere muestreo de campo: pendiente hasta disponer de datos.**
2. **Clasificador supervisado opcional**: reemplazar umbrales fijos por
   RandomForest entrenado con las mismas muestras de campo (la interfaz
   `ClassificationService` ya está lista para el cambio sin tocar la API).
   **Depende de (1).**
3. ✅ **Validación cruzada de MODIS con Sentinel-2**: implementada como
   `GET /api/crosscheck` y mostrada bajo el gráfico de la serie
   ("Concordancia MODIS vs Sentinel-2", Δ entre ambas escalas).
4. ✅ **Descarga del ROI como GeoJSON**: botón sobre el mapa descarga el
   círculo de 2 km como `.geojson` (listo para QGIS/ArcGIS). La exportación
   CSV de la serie ya existía.

## P2 — Operación y monitoreo

5. ✅ **Observabilidad (base)**: `GET /metrics` en formato Prometheus sin
   dependencias externas (contador de peticiones por ruta/estado y latencia).
   *Pendiente opcional: panel de grafado (Grafana/Uptime-Kuma) y Sentry.*
6. ✅ **Alertas proactivas**: job `deploy/jobs/alerta_diaria.py` + servicio
   compose con perfil `jobs`; cron del VPS lo ejecuta a diario y envía correo
   (SMTP configurable en `.env`) si la anomalía de biomasa < −15 %.
7. **Autenticación opcional** (JWT u OAuth de Google) si el dashboard va a
   circular fuera del equipo técnico; hoy solo hay GET públicos de telemetría.
8. **Backup del `.env` y de la configuración de Caddy** en el runbook del VPS
   (restore probado una vez al año).

## P3 — Producto y ciencia

9. **Multi-punto / parcelas**: guardar puntos con nombre ("potrero norte") y
   comparar su serie lado a lado; requiere una base de datos (SQLite/Postgres)
   y endpoints CRUD con autenticación.
10. **Pronóstico de oferta forrajera**: combinar serie NDVI + clima (Open-Meteo
    forecast) para proyección a 15-30 días de Kg MS/Ha, con bandas de
    incertidumbre.
11. ✅ **Índices complementarios**: capas **SAVI** (corrección de suelo en
    cobertura baja, relevante en el altiplano) y **NDWI** (agua/humedad,
    útil para bofedales) disponibles en el mapa y el selector de capas.
12. ✅ **Histórico MODIS completo (2000-hoy)**: el slider y la API aceptan
    ahora hasta **26 años**; verificado con datos reales: 597 puntos desde
    2000-10-15 para el punto por defecto.
13. ✅ **PWA instalable**: `manifest.webmanifest`, iconos 192/512, service
    worker (network-first para HTML, SWR para assets, `/api/` siempre red) y
    registro solo en producción. El sidebar llega al riel plegado y la app se
    instala en el móvil para uso en campo con poca conexión.
14. **i18n completo runu simi (quechua)** para operadores de campo, si se
    justifica (la arquitectura de diccionarios ya lo soporta).

## Deuda técnica conocida (pequeña, documentada)

- `rate_limit` en memoria: con >1 instancia de backend conviene moverlo a Redis.
- `getMapId` de GEE expira (~horas): el caché de tiles usa TTL 30 min; si se
  detectan tiles muertos tras inactividad larga, reducir TTL o refrescar en 404.
- El clasificador de umbrales está calibrado para pastizales de Puno; si se
  usa el software en otra región, recalibrar (constantes en
  `ClassificationService`).
