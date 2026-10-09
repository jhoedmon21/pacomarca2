"""
Agregador de routers de la API bajo el prefijo /api.
"""
from fastapi import APIRouter

from .alertas import router as alertas_router
from .classification import router as classification_router
from .crosscheck import router as crosscheck_router
from .health import router as health_router
from .puntos import router as puntos_router
from .stats import router as stats_router
from .timeseries import router as timeseries_router
from .tiles import router as tiles_router
from .weather import router as weather_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(weather_router)
api_router.include_router(timeseries_router)
api_router.include_router(tiles_router)
api_router.include_router(classification_router)
api_router.include_router(crosscheck_router)
api_router.include_router(stats_router)
api_router.include_router(puntos_router)
api_router.include_router(alertas_router)
