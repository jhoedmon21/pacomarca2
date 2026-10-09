"""
Cabeceras de seguridad para todas las respuestas de la API.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Añade cabeceras de endurecimiento recomendadas (OWASP)."""

    async def dispatch(self, request, call_next) -> Response:
        respuesta = await call_next(request)
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["X-Frame-Options"] = "DENY"
        respuesta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        respuesta.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
        # API pura: sin contenido propio que ejecutar
        respuesta.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return respuesta
