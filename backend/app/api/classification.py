"""
Clasificación (IA) de hábitats dentro del área de análisis (Sentinel-2, 10 m).
"""
import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_gee
from app.cache import get_cache
from app.models import ClassificationResponse
from app.services.gee import GEEError, GEEService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/classification", tags=["clasificación"])


@router.get(
    "",
    response_model=ClassificationResponse,
    summary="Porcentaje de cobertura por clase de hábitat",
)
def classification(
    lat: float = Query(ge=-90, le=90, description="Latitud en grados decimales"),
    lon: float = Query(ge=-180, le=180, description="Longitud en grados decimales"),
    gee: GEEService = Depends(get_gee),
) -> ClassificationResponse:
    """
    Clasificación por umbrales de NDVI sobre la imagen Sentinel-2 menos nublada
    de los últimos 60 días: 0=Suelo desnudo, 1=Pasto bajo, 2=Pasto alto.
    """
    clave = f"clasif:{math.floor(lat * 100) / 100}:{math.floor(lon * 100) / 100}"
    cache = get_cache()
    en_cache = cache.get(clave)
    if en_cache is not None:
        return ClassificationResponse(lat=lat, lon=lon, **en_cache)

    try:
        resultado = gee.get_classification(lat, lon)
    except GEEError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    cache.set(clave, resultado)
    return ClassificationResponse(lat=lat, lon=lon, **resultado)
