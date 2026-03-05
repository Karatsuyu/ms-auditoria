# =============================================================================
# ms-auditoria | core/exception_handlers.py
# =============================================================================
# Manejadores globales de excepciones para estandarizar respuestas de error.
# Todas las respuestas incluyen request_id, success, data, message, timestamp.
# =============================================================================

from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.logger import logger


def _get_request_id(request: Request) -> str:
    """Obtiene el request_id del state del request (inyectado por middleware)."""
    return getattr(request.state, "request_id", "unknown")


def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos los exception handlers en la app FastAPI."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Maneja HTTPException (4xx, 5xx conocidas)."""
        logger.warning(
            "http_exception",
            extra={
                "status_code": exc.status_code,
                "detail": str(exc.detail),
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "request_id": _get_request_id(request),
                "success": False,
                "data": None,
                "message": str(exc.detail),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Maneja errores de validación de Pydantic (422)."""
        invalid_fields = []
        detail_parts = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            invalid_fields.append(field)
            detail_parts.append(f"{field}: {error['msg']}")

        logger.warning(
            "validation_error",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_count": len(invalid_fields),
            },
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "request_id": _get_request_id(request),
                "success": False,
                "data": {
                    "invalid_fields": invalid_fields,
                    "detail": "; ".join(detail_parts),
                },
                "message": "El cuerpo del log no cumple el formato requerido.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Maneja cualquier excepción no capturada (500)."""
        logger.error(
            "unhandled_exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "request_id": _get_request_id(request),
                "success": False,
                "data": None,
                "message": "Error interno del servidor. Contacte al administrador."
                if not _is_debug()
                else str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


def _status_phrase(code: int) -> str:
    """Retorna frase descriptiva para códigos HTTP comunes."""
    phrases = {
        400: "Bad Request",
        401: "No autorizado",
        403: "Acceso prohibido",
        404: "Recurso no encontrado",
        405: "Método no permitido",
        409: "Conflicto",
        422: "Error de validación",
        429: "Demasiadas solicitudes",
        500: "Error interno del servidor",
        502: "Bad Gateway",
        503: "Servicio no disponible",
    }
    return phrases.get(code, f"Error HTTP {code}")


def _is_debug() -> bool:
    """Verifica si estamos en modo debug."""
    try:
        from app.core.config import settings
        return settings.APP_DEBUG
    except Exception:
        return False
