"""
Logging estructurado (JSON) y registro de cada petición HTTP.
"""
import json
import logging
import sys
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class JsonFormatter(logging.Formatter):
    """Formateador JSON: un log por línea, listo para Docker/loki/journald."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "nivel": record.levelname,
            "logger": record.name,
            "mensaje": record.getMessage(),
        }
        if record.exc_info:
            payload["excepcion"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(nivel: str = "INFO") -> None:
    """Configura el logging raíz con formato JSON y salida a stdout."""
    manejador = logging.StreamHandler(sys.stdout)
    manejador.setFormatter(JsonFormatter())
    raiz = logging.getLogger()
    raiz.handlers = [manejador]
    raiz.setLevel(nivel.upper())
    # Reducir ruido de librerías de terceros
    for ruidoso in ("uvicorn.access", "httpx", "httpcore", "urllib3"):
        logging.getLogger(ruidoso).setLevel(logging.WARNING)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Registra método, ruta, estado y duración de cada petición."""

    async def dispatch(self, request: Request, call_next):
        inicio = time.perf_counter()
        respuesta = await call_next(request)
        duracion_ms = (time.perf_counter() - inicio) * 1000
        logging.getLogger("pacomarca.http").info(
            "%s %s -> %d (%.1f ms)",
            request.method,
            request.url.path,
            respuesta.status_code,
            duracion_ms,
        )
        return respuesta
