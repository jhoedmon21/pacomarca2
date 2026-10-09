"""
Base de datos asíncrona (SQLAlchemy 2.0 + aiosqlite/asyncpg).

Motor y sesión singleton por proceso; `init_db()` crea el esquema al arrancar
(create_all es suficiente aquí: el esquema nace con la app y evoluciona poco;
cuando crezca, migrar a Alembic sin cambiar esta interfaz).
"""
import logging
from pathlib import Path
from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from app.config import settings

logger = logging.getLogger(__name__)

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """Crea (una sola vez) el motor según DATABASE_URL."""
    global _engine, _session_factory
    if _engine is None:
        # SQLite necesita su directorio creado y evita el bloqueo de WAL
        # multi-conn en Windows/contenedor.
        if settings.database_url.startswith("sqlite"):
            ruta = settings.database_url.split("///")[-1]
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False}
            if settings.database_url.startswith("sqlite")
            else {},
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
        dialecto = _engine.dialect.name
        logger.info("Base de datos: %s", "SQLite local" if dialecto == "sqlite" else dialecto)
    return _engine


async def get_db() -> AsyncIterator[AsyncSession]:
    """Dependencia de FastAPI: una sesión por petición, cerrada al salir."""
    get_engine()
    assert _session_factory is not None  # narrows para mypy
    async with _session_factory() as session:
        yield session


async def init_db() -> None:
    """Crea el esquema y siembra el punto por defecto si no hay ninguno."""
    from sqlalchemy import select

    from app.db.models import PuntoControl

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: PuntoControl.metadata.create_all(sync_conn)
        )

    assert _session_factory is not None
    async with _session_factory() as session:
        existentes = await session.scalar(select(PuntoControl.id).limit(1))
        if existentes is None:
            session.add(
                PuntoControl(
                    nombre="Fundo Pacomarca",
                    lat=settings.default_lat,
                    lon=settings.default_lon,
                    buffer_m=settings.roi_buffer_m,
                    notas="Punto de control principal (sembrado al instalar).",
                )
            )
            await session.commit()
            logger.info("Base de datos sembrada con el punto por defecto")


async def ping_db() -> bool:
    """Comprobación rápida para /api/health."""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001 - healthcheck: nunca debe propagar
        logger.warning("Healthcheck de base de datos falló: %s", exc)
        return False


def reset_engine() -> None:
    """Solo para tests: fuerza a recrear el motor con la configuración actual."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
