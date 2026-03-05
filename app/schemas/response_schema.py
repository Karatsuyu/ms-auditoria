# =============================================================================
# ms-auditoria | schemas/response_schema.py
# =============================================================================
# Schemas genéricos de respuesta para estandarizar todas las respuestas API.
# Todas las respuestas incluyen request_id, success, data, message y timestamp.
# =============================================================================

from datetime import datetime, timezone
from typing import Generic, TypeVar, Optional, Any

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Formato de respuesta estándar del microservicio.
    Todos los endpoints (excepto /health) retornan este formato.
    """
    request_id: str = Field(description="Request ID de la operación")
    success: bool = True
    data: Optional[T] = None
    message: str = "OK"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthResponse(BaseModel):
    """Respuesta del endpoint de health check."""
    status: str
    service: str = "ms-auditoria"
    version: str = "1.0.0"
    components: dict = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
