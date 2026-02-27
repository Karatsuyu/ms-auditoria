# =============================================================================
# ms-auditoria | core/exception_handlers.py
# =============================================================================
# Manejadores globales de excepciones para estandarizar respuestas de error.
# Captura errores 500, validación, y HTTPException de forma uniforme.
# =============================================================================

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.logger import logger


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
                "success": False,
                "error": _status_phrase(exc.status_code),
                "detail": str(exc.detail),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Maneja errores de validación de Pydantic (422)."""
        errors = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            })

        logger.warning(
            "validation_error",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_count": len(errors),
            },
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Error de validación",
                "detail": errors,
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
                "success": False,
                "error": "Error interno del servidor",
                "detail": "Ha ocurrido un error inesperado. Contacte al administrador."
                if not _is_debug()
                else str(exc),
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
