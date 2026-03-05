# =============================================================================
# ms-auditoria | core/middleware.py
# =============================================================================
# Middleware personalizado para:
# - Inyectar/propagar X-Request-ID en cada request (trazabilidad)
#   Formato propio: AUD-{timestamp_unix_ms}-{6char_random}
# - Medir duración de cada request
# - Logging estructurado de cada petición
# =============================================================================

import re
import time
import string
import random

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

from app.utils.logger import logger

# Regex para validar formato de Request ID recibido
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9\-]{1,36}$")


def generate_request_id() -> str:
    """
    Genera un Request ID con formato AUD-{timestamp_unix_ms}-{6char}.
    Máximo 36 caracteres según especificación.
    """
    ts = int(time.time() * 1000)
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"AUD-{ts}-{suffix}"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware que garantiza que cada request tenga un X-Request-ID.
    Si el cliente envía uno, se reutiliza (AUD-RF-003); si no, se genera
    con formato AUD-{timestamp_unix_ms}-{6char}.
    También mide la duración del request en milisegundos.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # ── Obtener o generar Request-ID ──────────────────────────────────
        incoming_rid = request.headers.get("X-Request-ID")
        if incoming_rid and _REQUEST_ID_RE.match(incoming_rid):
            request_id = incoming_rid
        else:
            if incoming_rid:
                logger.warning(
                    "invalid_request_id_format",
                    extra={"received": incoming_rid[:50]},
                )
            request_id = generate_request_id()

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
