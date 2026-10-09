"""
Servicio de Google Earth Engine.

Autenticación con cuenta de servicio (sin OAuth manual) y consultas:
series temporales (MODIS 061), tiles (getMapId), clasificación y estadísticas.

Nota: todas las llamadas `.getInfo()` son bloqueantes; los endpoints que usan
este servicio se declaran `def` (síncronos) para que FastAPI los ejecute en
su threadpool sin bloquear el event loop.
"""
import json
import logging
import os
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import ee
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# Colecciones satelitales
MODIS_COLLECTION = "MODIS/061/MOD13Q1"          # 006 retirada -> 061 vigente
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
S1_COLLECTION = "COPERNICUS/S1_GRD"
MODIS_SCALE_M = 250                              # resolución nativa MOD13Q1
MODIS_SCALE_FACTOR = 10000.0                     # NDVI/EVI de MODIS vienen x10000


class GEEError(RuntimeError):
    """Error de consulta a Google Earth Engine (mensaje apto para el usuario)."""


class GEEService:
    """Servicio para interactuar con Google Earth Engine."""

    def __init__(self) -> None:
        self._initialized = False
        self.init_error: Optional[str] = None
        self._lock = threading.Lock()
        self._initialize()

    # ------------------------------------------------------------------
    # Autenticación
    # ------------------------------------------------------------------
    def _resolve_key_data(self) -> Optional[str]:
        """Devuelve el JSON de la clave: valor directo, o lee la ruta indicada."""
        raw = settings.gee_private_key_json.strip()
        if not raw:
            return None
        if os.path.exists(raw):  # ruta a un secret montado
            with open(raw, "r", encoding="utf-8") as f:
                return f.read()
        return raw  # contenido JSON embebido

    def _initialize(self) -> None:
        """Inicializa EE con cuenta de servicio. Si falla, la app arranca
        en modo degradado (los endpoints devuelven 503 con mensaje claro)."""
        with self._lock:
            if self._initialized:
                return
            try:
                key_data = self._resolve_key_data()
                if settings.gee_service_account_email and key_data:
                    credentials = ee.ServiceAccountCredentials(
                        settings.gee_service_account_email, key_data=key_data
                    )
                    ee.Initialize(credentials, project=settings.gee_project)
                else:
                    # Fallback: credenciales persistentes locales (ee.Authenticate)
                    ee.Initialize(project=settings.gee_project)
                self._initialized = True
                self.init_error = None
                logger.info("GEE inicializado (proyecto: %s)", settings.gee_project)
            except Exception as exc:  # noqa: BLE001 - reportamos cualquier fallo de arranque
                self.init_error = str(exc)
                logger.error("Error al inicializar GEE: %s", exc)

    @property
    def ready(self) -> bool:
        return self._initialized

    def ensure_ready(self) -> None:
        """Lanza GEEError si la conexión no está disponible."""
        if not self._initialized:
            raise GEEError(
                "Google Earth Engine no está autenticado. "
                "Verifica GEE_SERVICE_ACCOUNT_EMAIL y GEE_PRIVATE_KEY_JSON."
            )

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    def _roi(self, lat: float, lon: float) -> ee.Geometry:
        """Área de análisis: círculo del radio configurado alrededor del punto."""
        return ee.Geometry.Point([lon, lat]).buffer(settings.roi_buffer_m)

    def _collection_size(self, collection: ee.ImageCollection) -> int:
        return int(collection.size().getInfo())

    def _latest_s2(self, roi: ee.Geometry, dias: int = 60) -> Optional[ee.Image]:
        """Imagen Sentinel-2 menos nublada de los últimos `dias` días."""
        coll = (
            ee.ImageCollection(S2_COLLECTION)
            .filterBounds(roi)
            .filterDate(
                (datetime.utcnow() - timedelta(days=dias)).strftime("%Y-%m-%d"),
                datetime.utcnow().strftime("%Y-%m-%d"),
            )
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 80))
            .sort("CLOUDY_PIXEL_PERCENTAGE")
        )
        if self._collection_size(coll) == 0:
            return None
        return ee.Image(coll.first())

    def _latest_s1(self, roi: ee.Geometry, dias: int = 30) -> Optional[ee.Image]:
        """Imagen Sentinel-1 (radar) más reciente de los últimos `dias` días."""
        coll = (
            ee.ImageCollection(S1_COLLECTION)
            .filterBounds(roi)
            .filterDate(
                (datetime.utcnow() - timedelta(days=dias)).strftime("%Y-%m-%d"),
                datetime.utcnow().strftime("%Y-%m-%d"),
            )
            .sort("system:time_start", False)
        )
        if self._collection_size(coll) == 0:
            return None
        return ee.Image(coll.first())

    # ------------------------------------------------------------------
    # Series temporales (MODIS 061)
    # ------------------------------------------------------------------
    def get_timeseries(self, lat: float, lon: float, years: int, index: str = "ndvi") -> List[Dict[str, Any]]:
        """
        Serie temporal del índice solicitado con promedio zonal sobre el ROI.

        Args:
            lat/lon: centro del área de análisis.
            years: años hacia atrás (1..23).
            index: 'ndvi' | 'evi' | 'biomasa' (biomasa = NDVI * coeficiente).

        Returns:
            Lista de {date, value, biomass} ordenada por fecha.
        """
        self.ensure_ready()
        if index not in ("ndvi", "evi", "biomasa"):
            raise GEEError(f"Índice no soportado: {index}")

        banda = "NDVI" if index in ("ndvi", "biomasa") else "EVI"
        roi = self._roi(lat, lon)
        fin = datetime.utcnow()
        inicio = fin - timedelta(days=365 * years)

        coleccion = (
            ee.ImageCollection(MODIS_COLLECTION)
            .filterDate(inicio.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d"))
            .filterBounds(roi)
            .select(banda)
        )

        def _extraer(img: ee.Image) -> ee.Feature:
            valor = img.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=roi, scale=MODIS_SCALE_M, maxPixels=1e9
            ).get(banda)
            return ee.Feature(
                None, {"fecha": img.date().format("YYYY-MM-dd"), "valor": valor}
            )

        try:
            info = ee.FeatureCollection(coleccion.map(_extraer)).getInfo()
        except Exception as exc:  # noqa: BLE001
            logger.error("Fallo consulta de serie temporal en GEE: %s", exc)
            raise GEEError("No se pudo obtener la serie temporal desde GEE.") from exc

        puntos: List[Dict[str, Any]] = []
        for feature in info.get("features", []):
            props = feature.get("properties", {})
            if props.get("valor") is None:
                continue  # escenas sin cobertura del ROI
            valor = float(props["valor"]) / MODIS_SCALE_FACTOR
            punto: Dict[str, Any] = {"date": props["fecha"], "value": round(valor, 5)}
            if banda == "NDVI":
                # Modelo heurístico documentado en BiomassService
                punto["biomass"] = round(valor * settings.biomass_coefficient, 2)
            puntos.append(punto)

        puntos.sort(key=lambda p: p["date"])
        logger.info("Serie temporal: %d puntos para (%.4f, %.4f) índice=%s", len(puntos), lat, lon, index)
        return puntos

    # ------------------------------------------------------------------
    # Clasificación de hábitats
    # ------------------------------------------------------------------
    def get_classification(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Porcentaje de cobertura por clase dentro del ROI (Sentinel-2, 10 m):
        0=Suelo desnudo, 1=Pasto bajo, 2=Pasto alto (umbrales NDVI configurables).
        """
        self.ensure_ready()
        roi = self._roi(lat, lon)
        s2 = self._latest_s2(roi)
        if s2 is None:
            raise GEEError("No hay imágenes Sentinel-2 recientes para esta zona.")

        ndvi = s2.normalizedDifference(["B8", "B4"])
        clasificacion = (
            ee.Image(0).where(ndvi.gte(0.2), 1).where(ndvi.gte(0.45), 2).rename("clase")
        )

        try:
            histograma = (
                clasificacion.reduceRegion(
                    reducer=ee.Reducer.frequencyHistogram(),
                    geometry=roi,
                    scale=10,
                    maxPixels=1e9,
                ).get("clase")
                .getInfo()
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Fallo de clasificación en GEE: %s", exc)
            raise GEEError("No se pudo clasificar el área desde GEE.") from exc

        total = float(sum(histograma.values())) if histograma else 0.0
        porcentajes: Dict[str, float] = {}
        for clase in ("0", "1", "2"):
            conteo = float(histograma.get(clase, 0.0)) if histograma else 0.0
            porcentajes[clase] = round(conteo / total * 100, 2) if total > 0 else 0.0

        return {
            "classification_map": porcentajes,
            "legend": {
                "0": {"label": "Suelo desnudo", "color": "#d73027"},
                "1": {"label": "Pasto bajo", "color": "#fee08b"},
                "2": {"label": "Pasto alto", "color": "#1a9850"},
            },
            "unit": "% del área",
        }

    # ------------------------------------------------------------------
    # Tiles para el mapa (getMapId)
    # ------------------------------------------------------------------
    def get_tile_url(self, lat: float, lon: float, layer: str) -> Dict[str, Any]:
        """
        Genera la plantilla de URL de tiles XYZ de GEE para la capa pedida,
        lista para usarla como fuente raster en MapLibre/Leaflet:
        https://.../{z}/{x}/{y}?token=...
        """
        self.ensure_ready()
        roi = self._roi(lat, lon)

        s2 = self._latest_s2(roi)
        s2_disponible = s2 is not None

        if layer in ("biomasa", "clasificacion", "ndvi", "evi", "savi", "ndwi") and not s2_disponible:
            raise GEEError("No hay imágenes Sentinel-2 recientes para esta zona.")

        if layer == "biomasa" and s2 is not None:
            ndvi = s2.normalizedDifference(["B8", "B4"])
            imagen = ndvi.multiply(settings.biomass_coefficient).rename("Biomasa")
            vis = {"min": 0, "max": 2500,
                   "palette": ["#ffffe5", "#f7fcb9", "#addd8e", "#41ab5d", "#005a32"]}
            nombre, unidad = "Biomasa (Kg/Ha)", "Kg/Ha"

        elif layer == "clasificacion" and s2 is not None:
            ndvi = s2.normalizedDifference(["B8", "B4"])
            imagen = ee.Image(0).where(ndvi.gte(0.2), 1).where(ndvi.gte(0.45), 2)
            vis = {"min": 0, "max": 2, "palette": ["#d73027", "#fee08b", "#1a9850"]}
            nombre, unidad = "Clasificación de hábitat", "ID clase"

        elif layer == "ndvi" and s2 is not None:
            imagen = s2.normalizedDifference(["B8", "B4"])
            vis = {"min": 0, "max": 0.8,
                   "palette": ["#d73027", "#fdae61", "#d9ef8b", "#1a9850"]}
            nombre, unidad = "NDVI (vigor)", "índice"

        elif layer == "evi" and s2 is not None:
            # Bandas en reflectancia (0-1): S2_SR entrega DN x10000 y las
            # correcciones del EVI (término +1) solo aplican a esa escala.
            nir = s2.select("B8").divide(10000.0)
            red = s2.select("B4").divide(10000.0)
            blue = s2.select("B2").divide(10000.0)
            imagen = s2.expression(
                "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
                {"NIR": nir, "RED": red, "BLUE": blue},
            )
            vis = {"min": 0, "max": 1, "palette": ["#ffffff", "#008000"]}
            nombre, unidad = "EVI (alta densidad)", "índice"

        elif layer == "savi" and s2 is not None:
            # SAVI: ajusta el efecto del brillo del suelo en coberturas bajas
            # (L = 0.5, valor estándar recomendado por Huete 1988).
            # Bandas en reflectancia (0-1) para que la corrección L aplique.
            nir = s2.select("B8").divide(10000.0)
            red = s2.select("B4").divide(10000.0)
            imagen = s2.expression(
                "1.5 * ((NIR - RED) / (NIR + RED + 0.5))",
                {"NIR": nir, "RED": red},
            )
            vis = {"min": 0, "max": 0.6,
                   "palette": ["#d73027", "#fdae61", "#d9ef8b", "#1a9850"]}
            nombre, unidad = "SAVI (suelo / cobertura baja)", "índice"

        elif layer == "ndwi" and s2 is not None:
            # NDWI (McFeeters): positivo = superficie húmeda/agua; útil para
            # humedales y bofedales del altiplano. Verde=NIR(B8), Azul=B3.
            imagen = s2.normalizedDifference(["B3", "B8"])
            vis = {"min": -0.5, "max": 0.5,
                   "palette": ["#d73027", "#ffffbf", "#1a9850"]}
            nombre, unidad = "NDWI (agua / humedad)", "índice"

        elif layer == "radar_s1":
            s1 = self._latest_s1(roi)
            if s1 is None:
                raise GEEError("No hay imágenes Sentinel-1 recientes para esta zona.")
            imagen = s1.select("VV")
            vis = {"min": -25, "max": 5, "palette": []}
            nombre, unidad = "Radar Sentinel-1 (estructura)", "dB"

        else:
            raise GEEError(f"Capa no soportada: {layer}")

        try:
            map_id = imagen.clip(roi).getMapId(vis)
        except Exception as exc:  # noqa: BLE001
            logger.error("Fallo getMapId para capa %s: %s", layer, exc)
            raise GEEError(f"No se pudo generar el mapa de la capa '{layer}'.") from exc

        # tile_fetcher.url_format ya incluye {z}/{x}/{y} y el token
        tile_fetcher = map_id.get("tile_fetcher")
        if tile_fetcher is not None and getattr(tile_fetcher, "url_format", None):
            url = tile_fetcher.url_format
        else:
            token = map_id.get("token", "")
            url = (
                f"https://earthengine.googleapis.com/map/{map_id['mapid']}"
                f"/{{z}}/{{x}}/{{y}}?token={token}"
            )

        return {
            "url": url,
            "layer_name": nombre,
            "min_val": float(vis["min"]),
            "max_val": float(vis["max"]),
            "palette": vis.get("palette", []),
            "unit": unidad,
        }

    # ------------------------------------------------------------------
    # Estadísticas resumen
    # ------------------------------------------------------------------
    def get_stats(self, lat: float, lon: float, years: int, layer: str = "biomasa") -> Dict[str, Any]:
        """
        Métricas resumen de la serie de la capa pedida:
        media, máx, mín, desviación, tendencia (unidades/año) y anomalía
        del último valor vs. el promedio histórico.
        """
        self.ensure_ready()

        if layer == "clasificacion":
            resultado = self.get_classification(lat, lon)
            valores = list(resultado["classification_map"].values())
            return {
                "mean": round(sum(valores) / len(valores), 2),
                "max": round(max(valores), 2),
                "min": round(min(valores), 2),
                "std": 0.0,
                "trend": 0.0,
                "anomaly_percent": 0.0,
                "unit": resultado["unit"],
                "data_count": 3,
            }

        if layer == "radar_s1":
            roi = self._roi(lat, lon)
            s1 = self._latest_s1(roi)
            if s1 is None:
                raise GEEError("No hay imágenes Sentinel-1 recientes para esta zona.")
            media_vv = float(
                s1.select("VV")
                .reduceRegion(ee.Reducer.mean(), roi, 10, maxPixels=1e9)
                .get("VV")
                .getInfo()
            )
            return {"mean": round(media_vv, 2), "max": round(media_vv, 2),
                    "min": round(media_vv, 2), "std": 0.0, "trend": 0.0,
                    "anomaly_percent": 0.0, "unit": "dB", "data_count": 1}

        if layer in ("savi", "ndwi"):
            # Snapshot actual (Sentinel-2): MODIS no tiene bandas SAVI/NDWI,
            # así que no existe serie histórica; se reporta media/min/max de
            # la última escena (tendencia y anomalía no aplican).
            roi = self._roi(lat, lon)
            s2 = self._latest_s2(roi)
            if s2 is None:
                raise GEEError("No hay imágenes Sentinel-2 recientes para esta zona.")
            if layer == "savi":
                # Bandas en reflectancia (0-1) para que la corrección L=0.5 aplique
                nir = s2.select("B8").divide(10000.0)
                red = s2.select("B4").divide(10000.0)
                indice = s2.expression(
                    "1.5 * ((NIR - RED) / (NIR + RED + 0.5))",
                    {"NIR": nir, "RED": red},
                ).rename("valor")
            else:
                # NDWI (McFeeters): (Verde - NIR) / (Verde + NIR)
                indice = s2.normalizedDifference(["B3", "B8"]).rename("valor")
            try:
                estadisticas = indice.reduceRegion(
                    reducer=ee.Reducer.mean().combine(
                        ee.Reducer.minMax(), sharedInputs=True
                    ),
                    geometry=roi,
                    scale=10,
                    maxPixels=1e9,
                ).getInfo()
            except Exception as exc:  # noqa: BLE001
                logger.error("Fallo de snapshot %s en GEE: %s", layer, exc)
                raise GEEError("No se pudo calcular el índice para el área.") from exc
            # Con un reducer combinado sobre una banda renombrada, las claves
            # llegan prefijadas: valor_mean / valor_min / valor_max.
            return {
                "mean": round(float(estadisticas.get("valor_mean") or 0.0), 3),
                "max": round(float(estadisticas.get("valor_max") or 0.0), 3),
                "min": round(float(estadisticas.get("valor_min") or 0.0), 3),
                "std": 0.0,
                "trend": 0.0,
                "anomaly_percent": 0.0,
                "unit": "índice",
                "data_count": 1,
            }

        # Capas con serie temporal (ndvi | evi | biomasa)
        index = "biomasa" if layer == "biomasa" else layer
        puntos = self.get_timeseries(lat, lon, years, index)

        clave = "biomass" if layer == "biomasa" else "value"
        valores = [p[clave] for p in puntos if p.get(clave) is not None]
        if not valores:
            raise GEEError("No hay datos disponibles para calcular estadísticas.")

        media = float(np.mean(valores))
        ultimo = valores[-1]
        anomalia = ((ultimo - media) / media * 100.0) if media != 0 else 0.0

        # Tendencia: regresión lineal en años decimales -> unidades por año
        tendencia = 0.0
        if len(valores) >= 2:
            fechas = [datetime.strptime(p["date"], "%Y-%m-%d") for p in puntos]
            base = fechas[0]
            x_anios = np.array([(f - base).days / 365.25 for f in fechas])
            if x_anios[-1] > x_anios[0]:
                pendiente = float(np.polyfit(x_anios, valores, 1)[0])
                tendencia = pendiente

        unidad = "Kg/Ha" if layer == "biomasa" else "índice"
        return {
            "mean": round(media, 2),
            "max": round(float(np.max(valores)), 2),
            "min": round(float(np.min(valores)), 2),
            "std": round(float(np.std(valores)), 2),
            "trend": round(tendencia, 2),
            "anomaly_percent": round(anomalia, 2),
            "unit": unidad,
            "data_count": len(valores),
        }

    # ------------------------------------------------------------------
    # Validación cruzada MODIS vs Sentinel-2
    # ------------------------------------------------------------------
    def crosscheck_modis_s2(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Comparación puntual de NDVI en dos escalas, para que el usuario
        valore la limitación de 250 m de MODIS en un área tan pequeña:

          - MODIS/061: media de los últimos 48 días (3 compuestos) a 250 m.
          - Sentinel-2: última escena menos nublada, NDVI a 10 m.

        Returns: {modis_ndvi, s2_ndvi, diferencia, nota}
        """
        self.ensure_ready()
        roi = self._roi(lat, lon)
        s2 = self._latest_s2(roi)
        if s2 is None:
            raise GEEError("No hay imágenes Sentinel-2 recientes para esta zona.")

        ndvi_modis = (
            ee.ImageCollection(MODIS_COLLECTION)
            .filterDate(
                (datetime.utcnow() - timedelta(days=48)).strftime("%Y-%m-%d"),
                datetime.utcnow().strftime("%Y-%m-%d"),
            )
            .filterBounds(roi)
            .select("NDVI")
            .mean()
            .rename("ndvi_modis")
        )
        ndvi_s2 = s2.normalizedDifference(["B8", "B4"]).rename("ndvi_s2")

        # Cada índice a su escala nativa (250 m / 10 m)
        try:
            resultado = ee.Dictionary(
                {
                    "modis": ndvi_modis.reduceRegion(
                        ee.Reducer.mean(), roi, MODIS_SCALE_M, maxPixels=1e9
                    ).get("ndvi_modis"),
                    "s2": ndvi_s2.reduceRegion(
                        ee.Reducer.mean(), roi, 10, maxPixels=1e9
                    ).get("ndvi_s2"),
                }
            ).getInfo()
        except Exception as exc:  # noqa: BLE001
            logger.error("Fallo de validación cruzada en GEE: %s", exc)
            raise GEEError("No se pudo comparar MODIS con Sentinel-2.") from exc

        modis_val = float(resultado.get("modis") or 0) / MODIS_SCALE_FACTOR
        s2_val = float(resultado.get("s2") or 0)
        return {
            "modis_ndvi": round(modis_val, 4),
            "s2_ndvi": round(s2_val, 4),
            "diferencia": round(s2_val - modis_val, 4),
            "nota": (
                "MODIS 250 m (media 48 días) vs Sentinel-2 10 m "
                "(última escena menos nublada)"
            ),
        }


# Instancia perezosa (singleton) del servicio
_gee_service: Optional[GEEService] = None
_gee_lock = threading.Lock()


def get_gee_service() -> GEEService:
    """Devuelve el singleton de GEEService, creándolo en la primera llamada."""
    global _gee_service
    if _gee_service is None:
        with _gee_lock:
            if _gee_service is None:
                _gee_service = GEEService()
    return _gee_service
