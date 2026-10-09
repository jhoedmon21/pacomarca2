"""
Genera plantillas de URL de tiles XYZ de GEE (getMapId) para MapLibre/Leaflet.
"""
import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_gee
from app.cache import get_cache
from app.models import LayerType, TileResponse
from app.services.gee import GEEError, GEEService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tiles", tags=["mapa"])


@router.get(
    "/{layer}",
    response_model=TileResponse,
    summary="URL de tiles de una capa para el mapa",
)
def tiles(
    layer: LayerType,
    lat: float = Query(ge=-90, le=90, description="Latitud del centro del área"),
    lon: float = Query(ge=-180, le=180, description="Longitud del centro del área"),
    gee: GEEService = Depends(get_gee),
) -> TileResponse:
    """
    Devuelve la plantilla `https://.../{z}/{x}/{y}?token=...` para usar como
    fuente raster en el mapa, junto con min/max/paleta para la leyenda.
    """
    clave = f"tiles:{layer.value}:{math.floor(lat * 100) / 100}:{math.floor(lon * 100) / 100}"
    cache = get_cache()
    en_cache = cache.get(clave)
    if en_cache is not None:
        return TileResponse(**en_cache)

    try:
        resultado = gee.get_tile_url(lat, lon, layer.value)
    except GEEError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    respuesta = TileResponse(**resultado)
    cache.set(clave, respuesta.model_dump())
    return respuesta
