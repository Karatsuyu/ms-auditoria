# =============================================================================
# ms-auditoria | schemas/retention_schema.py
# =============================================================================
# Schemas para los endpoints de configuración de retención.
# =============================================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RetentionConfigData(BaseModel):
    """Datos de respuesta para GET /api/v1/retention-config."""
    retention_days: int
    status: str
    last_rotation_date: Optional[datetime] = None
    last_rotation_deleted_count: int = 0


class RetentionUpdateRequest(BaseModel):
    """Request body para PATCH /api/v1/retention-config."""
    retention_days: int = Field(
        ...,
        gt=0,
        description="Cantidad de días de retención (entero positivo > 0)",
    )


class RetentionConfigUpdatedData(RetentionConfigData):
    """Datos de respuesta para PATCH (incluye updated_at)."""
    updated_at: datetime


class RotationResultData(BaseModel):
    """Datos de respuesta para POST /api/v1/retention-config/rotate."""
    rotation_date: datetime
    deleted_count: int
    cutoff_date: datetime
    retention_days_applied: int
