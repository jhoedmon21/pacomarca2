"""
Punto de entrada de la API (FastAPI).

Arranque en desarrollo:
    uvicorn app.main:app --reload --port 8000
Documentación interactiva: http://localhost:8000/docs
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response

from app.api import api_router
from app.config import settings
from app.middleware import (
    MetricsMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    setup_logging,
)
from app.models import ErrorResponse, ValidationErrorResponse
from app.services.gee import GEEError, get_gee_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Arranque/parada: logging, base de datos, caché y conexión a GEE en modo tolerante."""
    setup_logging("DEBUG" if settings.app_debug else "INFO")

    try:
        from app.db import init_db

        await init_db()
        logger.info("Base de datos lista (%s)", settings.database_url.split("///")[0])
    except Exception as exc:  # noqa: BLE001
        # Sin base de datos la app arranca degradada (health lo reporta), pero
        # los endpoints de persistencia devolverán 500 hasta que se resuelva.
        logger.error("No se pudo inicializar la base de datos: %s", exc)

    gee = get_gee_service()
    if gee.ready:
        logger.info("Arranque completo: GEE conectado al proyecto %s", settings.gee_project)
    else:
        # No frenamos el arranque: /api/health reportará 'degradado' y los
        # endpoints de datos devolverán 503 con un mensaje claro.
        logger.error("Arranque DEGRADADO: GEE no autenticado (%s)", gee.init_error)
    yield
    logger.info("Cierre de la aplicación")


def create_app() -> FastAPI:
    """Fábrica de la aplicación (facilita los tests con dependencias simuladas)."""
    app = FastAPI(
        title="Pacomarca Scientific Suite API",
        description=(
            "API de monitoreo de pastizales y forraje para el fundo Pacomarca "
            "(altiplano de Puno, Perú) mediante teledetección: series MODIS, "
            "Sentinel-1/2, clima en tiempo real y modelo heurístico de biomasa."
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middleware (el último añadido es el más externo):
    # CORS debe quedar por fuera para que también los errores lleven sus cabeceras,
    # y métricas es lo más externo para contar TODAS las peticiones.
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        """Endpoint de scrape de Prometheus (texto plano)."""
        from app.middleware.metrics import get_instancia

        mw = get_instancia()
        contenido = mw.snapshot() if mw is not None else ""
        return Response(
            content=contenido,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    @app.get("/", include_in_schema=False)
    def raiz() -> dict:
        """Redirección informativa hacia la documentación."""
        return {"aplicacion": "Pacomarca Scientific Suite API", "docs": "/docs", "salud": "/api/health"}

    @app.exception_handler(RequestValidationError)
    async def manejar_validacion(request: Request, exc: RequestValidationError):
        """Convierte los 422 por defecto en mensajes en español, campo por campo."""
        detalles = []
        for error in exc.errors():
            campo = ".".join(str(p) for p in error.get("loc", []) if p not in ("query", "path", "body"))
            mensajes = {
                "greater_than_equal": "debe ser mayor o igual a",
                "less_than_equal": "debe ser menor o igual a",
                "enum": "no es un valor permitido",
                "missing": "es obligatorio",
                "string_pattern_mismatch": "tiene un formato no permitido",
            }
            tipo = error.get("type", "")
            texto = mensajes.get(tipo, tipo)
            detalles.append(
                {
                    "field": campo or "desconocido",
                    "message": f"El valor de '{campo}' {texto} (recibido: {error.get('input', '')}).",
                }
            )
        return JSONResponse(
            status_code=422,
            content=ValidationErrorResponse(
                error="Error de validación",
                message="Uno o más parámetros son inválidos.",
                details=detalles,
            ).model_dump(),
        )

    @app.exception_handler(GEEError)
    async def manejar_gee(request: Request, exc: GEEError):
        """Errores de Earth Engine -> 503 con mensaje accionable."""
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(error="servicio_no_disponible", message=str(exc)).model_dump(),
        )

    @app.exception_handler(Exception)
    async def manejar_errores_no_previstos(request: Request, exc: Exception):
        """Última barrera: nunca devolver HTML ni trazar stack al cliente."""
        logger.exception("Error no previsto en %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="error_interno",
                message="Ocurrió un error inesperado. El equipo fue notificado vía logs.",
            ).model_dump(),
        )

    return app


# Instancia para uvicorn (app.main:app)
app = create_app()
