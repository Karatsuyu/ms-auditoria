# =============================================================================
# ms-auditoria | schemas/audit_schema.py
# =============================================================================
# Schemas de Pydantic para validación de entrada/salida de la API.
# Separados en Create (entrada), Response (salida) y Filter (consulta).
# =============================================================================

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ── Schema de creación (POST) ─────────────────────────────────────────────────

class AuditLogCreate(BaseModel):
    """Schema para registrar un nuevo evento de auditoría."""

    timestamp: datetime = Field(
        ...,
        description="Momento exacto del evento en el microservicio origen",
        examples=["2026-02-26T10:30:00Z"],
    )
    nombre_microservicio: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Nombre del microservicio que genera el evento",
        examples=["ms-matricula"],
    )
    endpoint: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Ruta del endpoint invocado",
        examples=["/api/v1/matricula/inscribir"],
    )
    metodo_http: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Método HTTP utilizado",
        examples=["POST"],
    )
    codigo_respuesta: int = Field(
        ...,
        ge=100,
        le=599,
        description="Código de respuesta HTTP",
        examples=[200],
    )
    duracion_ms: int = Field(
        ...,
        ge=0,
        description="Duración del request en milisegundos",
        examples=[142],
    )
    usuario_id: Optional[UUID] = Field(
        default=None,
        description="UUID del usuario (null si es anónimo)",
    )
    detalle: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Detalle adicional del evento (JSON string)",
    )
    ip_origen: Optional[str] = Field(
        default=None,
        max_length=45,
        description="Dirección IP de origen",
        examples=["192.168.1.100"],
    )
    request_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="X-Request-ID para trazabilidad",
    )


# ── Schema de respuesta (GET) ─────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    """Schema de respuesta para un registro de auditoría."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: str
    servicio: str
    endpoint: str
    metodo: str
    codigo_respuesta: int
    duracion_ms: int
    usuario_id: Optional[UUID]
    detalle: Optional[str]
    ip_origen: Optional[str]
    timestamp_evento: datetime
    created_at: datetime


# ── Schema de filtros de consulta ──────────────────────────────────────────────

class AuditLogFilter(BaseModel):
    """Schema para filtrar registros de auditoría."""

    servicio: Optional[str] = Field(default=None, max_length=50)
    metodo_http: Optional[str] = Field(default=None, max_length=10)
    codigo_respuesta: Optional[int] = Field(default=None, ge=100, le=599)
    usuario_id: Optional[UUID] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    request_id: Optional[str] = Field(default=None, max_length=50)
    search_text: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Búsqueda full-text en el campo detalle",
    )
