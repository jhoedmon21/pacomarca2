"""
Estadísticas resumen: media, máx., mín., desviación, tendencia y anomalía.
"""
import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_gee
from app.cache import get_cache
from app.models import LayerType, StatsResponse
from app.services.gee import GEEError, GEEService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stats", tags=["estadísticas"])


@router.get("", response_model=StatsResponse, summary="Métricas resumen de la capa")
def stats(
    lat: float = Query(ge=-90, le=90, description="Latitud en grados decimales"),
    lon: float = Query(ge=-180, le=180, description="Longitud en grados decimales"),
    years: int = Query(default=20, ge=1, le=26, description="Años de historia a considerar (MODIS 061 cubre desde 2000)"),
    layer: LayerType = Query(default=LayerType.BIOMASS, description="Capa/variable a resumir"),
    gee: GEEService = Depends(get_gee),
) -> StatsResponse:
    """
    Métricas de la serie de la capa elegida: media, máximo, mínimo, desviación
    estándar, tendencia (unidades por año) y anomalía del último valor frente
    al promedio histórico (%).
    """
    clave = f"stats:{math.floor(lat * 100) / 100}:{math.floor(lon * 100) / 100}:{years}:{layer.value}"
    cache = get_cache()
    en_cache = cache.get(clave)
    if en_cache is not None:
        return StatsResponse(lat=lat, lon=lon, years=years, layer=layer, **en_cache)

    try:
        resultado = gee.get_stats(lat, lon, years, layer.value)
    except GEEError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    cache.set(clave, resultado)
    return StatsResponse(lat=lat, lon=lon, years=years, layer=layer, **resultado)
