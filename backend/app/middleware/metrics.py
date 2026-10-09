"""
Métricas en formato Prometheus SIN dependencias externas:
contador global de peticiones, desglose por ruta/estado y suma de latencia.

Scrapeable en GET /metrics. El desglose usa rutas normalizadas (prefijo de
endpoint, sin query ni ids) para evitar cardinalidad infinita.
"""
import re
import threading
import time

from starlette.middleware.base import BaseHTTPMiddleware

# Prefijos de ruta que se agregan por endpoint (no por URL exacta)
_PREFIJO = re.compile(
    r"^/(api/)?(tiles/[\w-]+|tiles|timeseries|stats|weather|classification|crosscheck|health)"
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Acumula contadores de peticiones y latencia por ruta normalizada."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._lock = threading.Lock()
        self._peticiones: dict[tuple[str, str, str], int] = {}
        self._latencia_ms: dict[str, float] = {}
        # Registro global para que la ruta /metrics lea el snapshot
        global _instancia
        _instancia = self

    @staticmethod
    def _normalizar(path: str) -> str:
        """Convierte /api/tiles/ndvi?... -> /api/tiles/... para agregar métricas."""
        coincidencia = _PREFIJO.match(path)
        if coincidencia:
            return f"/{coincidencia.group(0).strip('/')}"
        if path == "/":
            return "/"
        return "<otra>"

    async def dispatch(self, request, call_next):
        inicio = time.perf_counter()
        respuesta = await call_next(request)
        duracion_ms = (time.perf_counter() - inicio) * 1000
        ruta = self._normalizar(request.url.path)
        with self._lock:
            clave = (ruta, request.method, str(respuesta.status_code))
            self._peticiones[clave] = self._peticiones.get(clave, 0) + 1
            self._latencia_ms[ruta] = self._latencia_ms.get(ruta, 0.0) + duracion_ms
        return respuesta

    def snapshot(self) -> str:
        """Devuelve las métricas en formato de exposición de Prometheus."""
        with self._lock:
            peticiones = dict(self._peticiones)
            latencias = dict(self._latencia_ms)

        lineas = ["# TYPE pacomarca_http_requests_total counter"]
        lineas.append(f"pacomarca_http_requests_total {sum(peticiones.values())}")
        for (ruta, metodo, estado), conteo in sorted(peticiones.items()):
            etiquetas = f'ruta="{ruta}",metodo="{metodo}",estado="{estado}"'
            lineas.append(f"pacomarca_http_requests_por_ruta{{{etiquetas}}} {conteo}")
        lineas.append("# TYPE pacomarca_http_latency_ms_sum gauge")
        for ruta, total_ms in sorted(latencias.items()):
            lineas.append(f'pacomarca_http_latency_ms_sum{{ruta="{ruta}"}} {total_ms:.1f}')
        return "\n".join(lineas) + "\n"


_instancia: MetricsMiddleware | None = None


def get_instancia() -> MetricsMiddleware | None:
    """Instancia registrada del middleware (None si aún no arrancó)."""
    return _instancia
