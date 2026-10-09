"""
Servicio de clima en tiempo real (Open-Meteo).

Sin API key. Usa httpx asíncrono con timeout y reintentos con backoff.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WeatherServiceError(RuntimeError):
    """Error al consultar Open-Meteo (mensaje apto para el usuario)."""


class WeatherService:
    """Cliente asíncrono de la API de Open-Meteo."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        reintentos: int = 2,
    ) -> None:
        self._base_url = (base_url or settings.openmeteo_base_url).rstrip("/")
        self._timeout = timeout
        self._reintentos = reintentos

    async def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Clima actual para las coordenadas dadas.

        Returns:
            {temperature_2m, relative_humidity_2m, rain, windspeed_10m, timestamp}
        Raises:
            WeatherServiceError: si Open-Meteo no responde tras los reintentos.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,rain,wind_speed_10m",
            "timezone": "auto",
        }

        ultimo_error: Optional[Exception] = None
        for intento in range(self._reintentos + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as cliente:
                    respuesta = await cliente.get(self._base_url, params=params)
                    respuesta.raise_for_status()
                    datos = respuesta.json()

                actual = datos.get("current", {})
                if not actual:
                    raise WeatherServiceError("Open-Meteo no devolvió datos actuales.")

                return {
                    "temperature_2m": actual.get("temperature_2m"),
                    "relative_humidity_2m": actual.get("relative_humidity_2m"),
                    "rain": actual.get("rain"),
                    "wind_speed_10m": actual.get("wind_speed_10m"),
                    "timestamp": actual.get("time"),
                }

            except (httpx.HTTPError, ValueError) as exc:
                ultimo_error = exc
                if intento < self._reintentos:
                    espera = 0.5 * (2 ** intento)  # backoff exponencial: 0.5s, 1s, ...
                    logger.warning(
                        "Open-Meteo falló (intento %d/%d): %s. Reintentando en %.1fs",
                        intento + 1, self._reintentos + 1, exc, espera,
                    )
                    await asyncio.sleep(espera)

        logger.error("Open-Meteo no disponible tras %d intentos: %s", self._reintentos + 1, ultimo_error)
        raise WeatherServiceError(
            "El servicio de clima no está disponible en este momento. Intenta de nuevo en unos minutos."
        )
