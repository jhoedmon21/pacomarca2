"""
Caché con TTL: Redis si está configurado y disponible, o en memoria como fallback.

Interfaz mínima: get / set / get_or_set. Los valores deben ser serializables a JSON.
"""
import json
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


class MemoryCache:
    """Caché en memoria con expiración por entrada (para desarrollo o single-node)."""

    def __init__(self) -> None:
        self._datos: Dict[str, Tuple[float, Any]] = {}  # clave -> (expira_en, valor)
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entrada = self._datos.get(key)
            if entrada is None:
                return None
            expira, valor = entrada
            if time.monotonic() > expira:
                del self._datos[key]
                return None
            return valor

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl_efectivo = ttl if ttl is not None else settings.cache_ttl_seconds
        with self._lock:
            self._datos[key] = (time.monotonic() + ttl_efectivo, value)

    def clear(self) -> None:
        with self._lock:
            self._datos.clear()


class RedisCache:
    """Caché distribuido en Redis. Los valores se serializan como JSON."""

    def __init__(self, url: str) -> None:
        import redis  # importación perezosa: solo si se usa Redis

        self._cliente = redis.Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        crudo = self._cliente.get(key)
        if crudo is None:
            return None
        return json.loads(crudo)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl_efectivo = ttl if ttl is not None else settings.cache_ttl_seconds
        self._cliente.set(key, json.dumps(value), ex=ttl_efectivo)

    def clear(self) -> None:
        self._cliente.flushdb()


def get_cache() -> MemoryCache | RedisCache:
    """
    Devuelve el caché singleton.
    Intenta Redis si REDIS_URL está definido; si no responde, usa memoria
    y deja constancia en el log (la app nunca debe caer por el caché).
    """
    global _cache
    if _cache is None:
        with _cache_lock:
            if _cache is None:
                if settings.redis_url:
                    try:
                        candidato = RedisCache(settings.redis_url)
                        candidato._cliente.ping()  # noqa: SLF001 - verificación de conexión
                        _cache = candidato
                        logger.info("Caché: Redis (%s)", settings.redis_url)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Redis no disponible (%s); usando caché en memoria.", exc)
                        _cache = MemoryCache()
                else:
                    logger.info("Caché: memoria (REDIS_URL no definido)")
                    _cache = MemoryCache()
    return _cache


_cache: MemoryCache | RedisCache | None = None
_cache_lock = threading.Lock()
