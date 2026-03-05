# =============================================================================
# ms-auditoria | core/rate_limiter.py
# =============================================================================
# Rate limiter en memoria basado en sliding window por IP.
# Protege la API contra abuso de requests.
# Compatible con async FastAPI middleware.
# =============================================================================

import time
from collections import defaultdict
from typing import Dict, List

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.utils.logger import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting basado en sliding window por IP.
    Configurable vía RATE_LIMIT_REQUESTS y RATE_LIMIT_WINDOW_SECONDS.
    Excluye /health y /docs de la limitación.
    """

    # Paths excluidos del rate limiting
    EXCLUDED_PATHS = {"/api/v1/health", "/docs", "/redoc", "/openapi.json", "/"}

    def __init__(self, app, max_requests: int = 0, window_seconds: int = 0):
        super().__init__(app)
        self.max_requests = max_requests or settings.RATE_LIMIT_REQUESTS
        self.window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS
        # Diccionario: IP → lista de timestamps
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Obtiene la IP real del cliente (soporta X-Forwarded-For)."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> tuple[bool, int]:
        """
        Verifica si la IP excedió el límite.
        Retorna (limited: bool, remaining: int).
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Limpiar timestamps viejos (sliding window)
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if ts > window_start
        ]

        current_count = len(self._requests[client_ip])

        if current_count >= self.max_requests:
            return True, 0

        # Registrar el nuevo request
        self._requests[client_ip].append(now)
        return False, self.max_requests - current_count - 1

    async def dispatch(self, request: Request, call_next):
        # Excluir paths del rate limiting
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        is_limited, remaining = self._is_rate_limited(client_ip)

        if is_limited:
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "ip": client_ip,
                    "path": request.url.path,
                    "limit": self.max_requests,
                    "window": self.window_seconds,
                },
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "detail": f"Máximo {self.max_requests} requests por {self.window_seconds}s. Intente más tarde.",
                },
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)

        # Agregar headers de rate limit en cada respuesta
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
