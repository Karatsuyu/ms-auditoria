# =============================================================================
# ms-auditoria | core/middleware.py
# =============================================================================
# Middleware personalizado para:
# - Inyectar/propagar X-Request-ID en cada request (trazabilidad)
# - Medir duración de cada request
# - Logging estructurado de cada petición
# =============================================================================

import uuid
import time

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

from app.utils.logger import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware que garantiza que cada request tenga un X-Request-ID único.
    Si el cliente envía uno, se propaga; si no, se genera automáticamente.
    También mide la duración del request en milisegundos.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # ── Obtener o generar Request-ID ──────────────────────────────────
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Inyectar en el state del request para uso posterior
        request.state.request_id = request_id

        # ── Medir tiempo de respuesta ─────────────────────────────────────
        start_time = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # ── Headers de respuesta ──────────────────────────────────────────
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = str(duration_ms)

        # ── Log estructurado ──────────────────────────────────────────────
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response
