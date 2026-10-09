"""
Rate limiting por IP con ventana deslizante (en memoria).

Protege la cuota de GEE/Open-Meteo. En despliegues multi-instancia debería
migrarse a Redis, pero para un VPS de instancia única es suficiente.
"""
import time
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

# Rutas exentas: monitoreo, documentación y métricas no deben quedarse sin cuota
RUTAS_EXENTAS = {"/api/health", "/health", "/metrics", "/docs", "/redoc", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limita las peticiones por minuto y por IP de cliente."""

    def __init__(self, app, limite_por_minuto: int | None = None) -> None:
        super().__init__(app)
        self.limite = limite_por_minuto or settings.rate_limit_per_minute
        self._historial: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _ip_cliente(self, request: Request) -> str:
        # Detrás de Caddy/Nginx la IP real llega en X-Forwarded-For
        reenviada = request.headers.get("x-forwarded-for")
        if reenviada:
            return reenviada.split(",")[0].strip()
        return request.client.host if request.client else "desconocida"

    async def dispatch(self, request: Request, call_next):
        if request.url.path in RUTAS_EXENTAS:
            return await call_next(request)

        ahora = time.monotonic()
        ip = self._ip_cliente(request)

        with self._lock:
            historial = self._historial[ip]
            while historial and ahora - historial[0] > 60.0:
                historial.popleft()
            if len(historial) >= self.limite:
                reintento = int(60 - (ahora - historial[0])) + 1
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit",
                        "message": (
                            f"Demasiadas peticiones. Límite: {self.limite}/min. "
                            f"Intenta de nuevo en {reintento} s."
                        ),
                    },
                    headers={"Retry-After": str(reintento)},
                )
            historial.append(ahora)

        return await call_next(request)
