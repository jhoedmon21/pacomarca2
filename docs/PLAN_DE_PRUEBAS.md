# Plan de pruebas — Pacomarca Scientific Suite

## 1. Estrategia

| Nivel | Herramienta | Cobertura actual | Estado |
|---|---|---|---|
| Unitario (backend) | pytest | 26 tests: modelo de biomasa, umbrales de clasificación, caché, errores | ✅ Automatizado |
| Integración (API) | pytest + TestClient con dobles de GEE/Open-Meteo | Todos los endpoints, validación 422 en español, 429, CSV | ✅ Automatizado |
| Contractual | OpenAPI generado por FastAPI | Los tipos del frontend (`types/index.ts`) replican los modelos | ⚠️ Manual |
| E2E (UI) | Navegador (manual o Playwright, ver §4) | Flujo completo usuario | ⚠️ Manual |
| Carga | Locust/k6 (opcional) | No implementado | 🔜 Futuro |

Los tests **nunca** llaman a GEE ni Open-Meteo: `tests/conftest.py` sustituye
los servicios con `FakeGEE`/`FakeWeather` mediante `dependency_overrides`,
así la suite es determinista y gratuita en cuota.

## 2. Ejecución

```bash
cd backend
pytest                 # suite completa (2-3 s)
pytest -k biomasa      # solo modelo de biomasa
pytest -vv             # modo detallado

# Frontend
cd ../frontend
npx tsc --noEmit       # verificación de tipos
npx eslint .           # lint
npm run build          # build de producción (falla si algo rompe)
```

## 3. Casos cubiertos por la suite automatizada

**Modelo de biomasa** (`test_biomass.py`)
- Coeficiente por defecto 2800 y configurable.
- NDVI 0 → biomasa 0; redondeo a 2 decimales; coherencia con `BIOMASS_COEFFICIENT`.

**Clasificación** (`test_classification.py`)
- Umbrales en el límite exacto (0.20 → pasto bajo, 0.45 → pasto alto, inclusivos).
- Histograma vacío → 0 %; conversión conteo→porcentaje; leyenda en español.

**API** (`test_api.py`)
- `/api/health` → 200 con estado de caché y GEE.
- `/api/weather` → datos correctos; **lat=200 → 422 en español** con campo detallado.
- `/api/timeseries` → JSON con biomasa incluida; **CSV** con cabecera y `Content-Disposition`.
- `years=0` y `years=24` → 422 (rango 1–23); índice inexistente → 422.
- `/api/tiles/ndvi` → plantilla con `{z}/{x}/{y}`; capa inexistente → 422.
- `/api/classification` → porcentajes y 3 clases con leyenda.
- `/api/stats` → resumen completo con unidad Kg/Ha.
- **Rate limiting**: 4.ª petición → 429 con `Retry-After`; `/api/health` **exento**.
- Caché: la 2.ª llamada a clima idéntica **no re-invoca** el servicio.

## 4. Pruebas E2E manuales (checklist por versión)

Preparar: backend con credenciales GEE reales + `npm run dev`.

1. **Carga inicial**: mapa satelital centrado en Pacomarca con ROI blanco de 2 km y capa de biomasa visible; KPIs con números (no "--"); clima en cabecera.
2. **Selección de punto**: clic en el mapa → marcador se mueve, ROI se recalcula, KPIs/serie refrescan ( skeletons ), coordenadas del sidebar se actualizan; arrastrar el marcador hace lo mismo.
3. **Entrada manual**: escribir lat/lon inválidas y salir del campo → se revierten al valor previo sin romper nada.
4. **Capas**: recorrer las 5 (biomasa, clasificación, radar, NDVI, EVI) → leyenda cambia, tiles cargan; radar debe funcionar aunque haya nubes.
5. **Slider de años**: mover 5↔23 y soltar → la serie refresca **una sola vez** (no por cada píxel).
6. **Exportación**: CSV (columnas fecha/valor/biomasa, abre bien en Excel con acentos) y PNG del gráfico.
7. **Alertas**: con anomalía < −15 % se muestra degradación; > +15 % favorable; en rango, estable.
8. **Comparador**: elegir dos años → promedios y diferencia % coherentes con la serie.
9. **Temas**: alternar claro/oscuro/sistema; el mapa y los gráficos se ven bien en ambos; preferencia persiste tras recargar.
10. **Idioma**: ES/EN cambia todos los textos visibles sin recargar.
11. **Teclado (a11y)**: Tab alcanza todos los controles con foco visible; pestañas navegan con ←/→; slider con flechas; enlace "Saltar al contenido" presente.
12. **Responsive** (DevTools 375/768/1440 px): sin scroll horizontal; sidebar off-canvas en móvil con fondo cerrable.
13. **Resiliencia**: detener el backend → mensajes de error amigables con botón Reintentar (no pantallas en blanco); reactivar → todo se recupera con el reintento.
14. **Rate limit**: >100 peticiones rápidas → mensaje 429 claro.

## 5. Verificación en producción (post-deploy)

Ver checklist completo en `README.md` §6. Esenciales:

```bash
docker compose ps                      # healthy en los 4 servicios
curl -s https://DOMINIO/api/health     # {"status":"ok","gee_status":"conectado"}
```

Y en el navegador: HTTPS con candado, mapa con capa, clima, exportación.

## 6. Criterios de aceptación (definición de "hecho")

- [x] 26 tests backend en verde; TSC y ESLint sin errores; build de producción OK.
- [x] Equivalencia MODIS 006→061 verificada con datos reales (006 sin datos, 061 con 23 compuestos/año).
- [x] 100 % de funcionalidad del `app.py` original presente (5 capas, clima, serie, alertas, KPIs).
- [x] Validación y errores en español; modo degradado sin pantallas rotas.
- [x] Secrets solo por entorno; `.env.example` sin valores reales; `.gitignore` cubre `.env`, JSON de servicio.
- [x] WCAG 2.1 AA: contraste AA en tokens, teclado completo, aria-roles, foco visible, salt link.
