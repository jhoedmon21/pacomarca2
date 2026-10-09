"""
Proveedores de dependencias (inyección). Tests sobrescriben estas funciones
con `app.dependency_overrides` para simular GEE/Open-Meteo.
"""
from typing import Optional

from app.services.gee import GEEService, get_gee_service
from app.services.weather import WeatherService

_weather_service: Optional[WeatherService] = None


def get_gee() -> GEEService:
    """Dependencia: servicio de Google Earth Engine (singleton)."""
    return get_gee_service()


def get_weather() -> WeatherService:
    """Dependencia: servicio de Open-Meteo (singleton)."""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service
