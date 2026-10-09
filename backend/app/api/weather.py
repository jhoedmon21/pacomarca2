"""
Clima actual (Open-Meteo) con caché corto para no golpear la API externa.
"""
import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_weather
from app.cache import get_cache
from app.config import settings
from app.models import WeatherResponse
from app.services.weather import WeatherService, WeatherServiceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/weather", tags=["clima"])

# El clima cambia rápido: máx. 10 min de caché aunque el TTL general sea mayor
_TTL_CLIMA = min(settings.cache_ttl_seconds, 600)


@router.get("", response_model=WeatherResponse, summary="Clima actual en el punto")
async def weather(
    lat: float = Query(ge=-90, le=90, description="Latitud en grados decimales"),
    lon: float = Query(ge=-180, le=180, description="Longitud en grados decimales"),
    servicio: WeatherService = Depends(get_weather),
) -> WeatherResponse:
    """Temperatura, humedad relativa y lluvia actuales (Open-Meteo, sin API key)."""
    clave = f"weather:{math.floor(lat * 100) / 100}:{math.floor(lon * 100) / 100}"
    cache = get_cache()

    en_cache = cache.get(clave)
    if en_cache is not None:
        return WeatherResponse(**en_cache)

    try:
        datos = await servicio.get_current_weather(lat, lon)
    except WeatherServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    respuesta = WeatherResponse(
        temperature_2m=datos["temperature_2m"],
        relative_humidity_2m=datos["relative_humidity_2m"],
        rain=datos["rain"],
    )
    cache.set(clave, respuesta.model_dump(), ttl=_TTL_CLIMA)
    return respuesta
