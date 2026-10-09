"""
Serie temporal de índices satelitales (MODIS/061/MOD13Q1, 250 m, 16 días).

Formatos: JSON (por defecto) o CSV con ?format=csv.
"""
import csv
import io
import logging
import math
import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.api.deps import get_gee
from app.cache import get_cache
from app.config import settings
from app.models import IndexType, TimeseriesPoint, TimeseriesResponse
from app.services.gee import GEEError, GEEService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/timeseries", tags=["series temporales"])

UNIDADES = {
    IndexType.NDVI: "índice (adimensional)",
    IndexType.EVI: "índice (adimensional)",
    IndexType.BIOMASS: "Kg/Ha",
}
FUENTE = "MODIS/061/MOD13Q1 (250 m, compuesto 16 días)"


def _clave_cache(lat: float, lon: float, years: int, index: IndexType) -> str:
    """Clave de caché con coordenadas redondeadas (evita explotar el espacio de claves)."""
    return f"ts:{math.floor(lat * 1000) / 1000}:{math.floor(lon * 1000) / 1000}:{years}:{index.value}"


def _obtener_serie(
    gee: GEEService, lat: float, lon: float, years: int, index: IndexType
) -> List[dict]:
    """Consulta con caché; devuelve la lista de puntos cruda."""
    clave = _clave_cache(lat, lon, years, index)
    cache = get_cache()
    en_cache = cache.get(clave)
    if en_cache is not None:
        return en_cache

    puntos = gee.get_timeseries(lat, lon, years, index.value)
    cache.set(clave, puntos)
    return puntos


def _respuesta(lat: float, lon: float, years: int, index: IndexType, puntos: List[dict]) -> TimeseriesResponse:
    return TimeseriesResponse(
        lat=lat,
        lon=lon,
        years=years,
        index=index,
        data=[TimeseriesPoint(**p) for p in puntos],
        unit=UNIDADES[index],
        source=FUENTE,
    )


def _csv(lat: float, lon: float, years: int, index: IndexType, puntos: List[dict]) -> Response:
    """Serializa la serie a CSV para descarga directa."""
    buffer = io.StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(["fecha", "valor", "biomasa_kg_ha"])
    for p in puntos:
        escritor.writerow([p["date"], p["value"], p.get("biomass", "")])
    contenido = buffer.getvalue()

    # Nombre de archivo seguro (sin puntos ni signos problemáticos)
    nombre = re.sub(r"[^0-9a-zA-Z_\-]", "", f"pacomarca_{index.value}_{lat}_{lon}_{years}a")
    return Response(
        content=contenido,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre}.csv"'},
    )


@router.get("", response_model=TimeseriesResponse, summary="Serie temporal del índice")
def timeseries(
    lat: float = Query(ge=-90, le=90, description="Latitud en grados decimales"),
    lon: float = Query(ge=-180, le=180, description="Longitud en grados decimales"),
    years: int = Query(default=20, ge=1, le=26, description="Años hacia atrás (MODIS 061 cubre desde 2000)"),
    index: IndexType = Query(default=IndexType.NDVI, description="Índice a consultar"),
    format: str = Query(default="json", pattern="^(json|csv)$", description="Formato de salida"),
    gee: GEEService = Depends(get_gee),
):
    """
    Serie histórica del índice (ndvi | evi | biomasa) con promedio zonal sobre
    un buffer de 2000 m alrededor del punto. Incluye biomasa estimada cuando
    el índice base es NDVI (modelo heurístico NDVI x 2800, configurable).
    """
    try:
        puntos = _obtener_serie(gee, lat, lon, years, index)
    except GEEError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if format == "csv":
        return _csv(lat, lon, years, index, puntos)
    return _respuesta(lat, lon, years, index, puntos)
