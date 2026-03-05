# =============================================================================
# ms-auditoria | schemas/audit_schema.py
# =============================================================================
# Schemas de Pydantic para validación de entrada/salida de la API.
# Nombres de campos en inglés para la API (mapeados al modelo ORM en español).
# =============================================================================

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


# ── Schema de creación individual (POST /api/v1/logs) ─────────────────────────

class LogCreate(BaseModel):
    """Schema para recibir un evento de log desde cualquier microservicio."""

    timestamp: datetime = Field(
        ...,
        description="Momento exacto del evento en el microservicio origen (ISO 8601)",
        examples=["2026-03-02T14:05:12Z"],
    )
    request_id: Optional[str] = Field(
        default=None,
        max_length=36,
        description="Request ID de la operación original en el ms emisor",
        examples=["RES-1709302000-xyz789"],
    )
    service_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Nombre del microservicio que genera el evento",
        examples=["ms-reservas"],
    )
    functionality: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre de la funcionalidad o endpoint ejecutado",
        examples=["crear_reserva"],
    )
    method: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Método HTTP utilizado",
        examples=["POST"],
    )
    response_code: int = Field(
        ...,
        ge=100,
        le=599,
        description="Código de respuesta HTTP",
        examples=[201],
    )
    duration_ms: int = Field(
        ...,
        ge=0,
        description="Duración de la operación en milisegundos",
        examples=[312],
    )
    user_id: Optional[str] = Field(
        default=None,
        max_length=36,
        description="ID del usuario (null para operaciones de sistema)",
    )
    detail: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Descripción libre del contexto o resultado",
    )


# ── Schema de creación batch (POST /api/v1/logs/batch) ────────────────────────

class LogBatchRequest(BaseModel):
    """Schema para envío de múltiples logs en lote."""
    logs: List[LogCreate] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Arreglo de registros de log (1-1000)",
    )


# ── Schema de registro en respuesta de consulta ───────────────────────────────

class LogRecord(BaseModel):
    """Schema de un registro de log en respuestas de consulta."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime = Field(alias="fecha_hora")
    service_name: str = Field(alias="microservicio")
    functionality: str = Field(alias="funcionalidad")
    method: str = Field(alias="metodo")
    response_code: int = Field(alias="codigo_respuesta")
    duration_ms: int = Field(alias="duracion_ms")
    user_id: Optional[str] = Field(default=None, alias="usuario_id")
    detail: Optional[str] = Field(default=None, alias="detalle")


# ── Schema para datos de respuesta de traza ───────────────────────────────────

class TraceData(BaseModel):
    """Datos del endpoint GET /api/v1/logs/trace/{request_id}."""
    trace_request_id: str
    total_records: int
    page: int
    page_size: int
    records: List[LogRecord]


# ── Schema para datos de respuesta de filtrado de logs ────────────────────────

class FilteredLogsData(BaseModel):
    """Datos del endpoint GET /api/v1/logs."""
    filters_applied: dict
    total_records: int
    page: int
    page_size: int
    records: List[LogRecord]


# ── Schema de respuesta para POST individual ──────────────────────────────────

class LogReceivedData(BaseModel):
    """Datos de respuesta 202 para POST /api/v1/logs."""
    received: bool = True
    log_request_id: str


# ── Schema de respuesta para POST batch ───────────────────────────────────────

class BatchReceivedData(BaseModel):
    """Datos de respuesta 202 para POST /api/v1/logs/batch."""
    received_count: int
    accepted_count: int
    rejected_count: int
    rejected_indices: List[dict] = []


# ── Schema de respuesta para historial de rotaciones ──────────────────────────

class RotationHistoryRecord(BaseModel):
    """Un registro del historial de rotaciones."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    timestamp: datetime = Field(alias="fecha_hora")
    trigger: str = Field(default="manual")
    functionality: str = Field(alias="funcionalidad")
    method: str = Field(alias="metodo")
    response_code: int = Field(alias="codigo_respuesta")
    duration_ms: int = Field(alias="duracion_ms")
    detail: Optional[str] = Field(default=None, alias="detalle")


class RotationHistoryData(BaseModel):
    """Datos del endpoint GET /api/v1/retention-config/rotation-history."""
    total_records: int
    page: int
    page_size: int
    records: List[RotationHistoryRecord]
