"""
Validación cruzada de escalas: NDVI MODIS (250 m) vs Sentinel-2 (10 m).
Ayuda a interpretar la serie: si ambas fuentes coinciden, la lectura MODIS
del área es confiable pese a la gruesa resolución.
"""
import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_gee
from app.cache import get_cache
from app.models import CrosscheckResponse
from app.services.gee import GEEError, GEEService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/crosscheck", tags=["validación"])


@router.get(
    "",
    response_model=CrosscheckResponse,
    summary="Compara el NDVI de MODIS (250 m) con Sentinel-2 (10 m) en el punto",
)
def crosscheck(
    lat: float = Query(ge=-90, le=90, description="Latitud en grados decimales"),
    lon: float = Query(ge=-180, le=180, description="Longitud en grados decimales"),
    gee: GEEService = Depends(get_gee),
) -> CrosscheckResponse:
    """NDVI MODIS (media de 48 días) frente al de la última escena Sentinel-2."""
    clave = f"crosscheck:{math.floor(lat * 100) / 100}:{math.floor(lon * 100) / 100}"
    cache = get_cache()
    en_cache = cache.get(clave)
    if en_cache is not None:
        return CrosscheckResponse(**en_cache)

    try:
        resultado = gee.crosscheck_modis_s2(lat, lon)
    except GEEError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    cache.set(clave, resultado)
    return CrosscheckResponse(**resultado)
