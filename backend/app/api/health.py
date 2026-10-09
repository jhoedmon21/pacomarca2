"""
Endpoint de verificación de salud (usado por Docker y el monitor del VPS).
"""
import logging
import time

from fastapi import APIRouter, Depends

from app.api.deps import get_gee
from app.config import settings
from app.models import HealthResponse
from app.services.gee import GEEService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["salud"])

# Caché del resultado del ping a GEE (un ping real en cada /health sería muy costoso)
_ultimo_estado: dict = {"ok": None, "ts": 0.0}
_PING_TTL = 30.0


def _ping_gee(gee: GEEService) -> str:
    ahora = time.monotonic()
    if _ultimo_estado["ok"] is not None and ahora - _ultimo_estado["ts"] < _PING_TTL:
        return _ultimo_estado["ok"]
    try:
        gee.ensure_ready()
        estado = "conectado"
    except Exception:  # noqa: BLE001 - el health check nunca debe lanzar
        estado = "sin conexión"
    _ultimo_estado.update(ok=estado, ts=ahora)
    return estado


@router.get("/health", response_model=HealthResponse, summary="Estado del servicio")
async def health(gee: GEEService = Depends(get_gee)) -> HealthResponse:
    """Estado general: versión, entorno, caché, base de datos y conexión con GEE."""
    from app.cache import get_cache
    from app.db import ping_db

    try:
        get_cache()
        estado_cache = "operativo"
    except Exception:  # noqa: BLE001
        estado_cache = "degradado"

    estado_db = "operativo" if await ping_db() else "sin conexión"

    estado_gee = _ping_gee(gee)
    estado_general = (
        "ok"
        if (estado_cache == "operativo" and estado_gee == "conectado" and estado_db == "operativo")
        else "degradado"
    )

    return HealthResponse(
        status=estado_general,
        version=settings.app_version,
        environment=settings.app_env,
        cache_status=estado_cache,
        database_status=estado_db,
        gee_status=estado_gee,
    )
