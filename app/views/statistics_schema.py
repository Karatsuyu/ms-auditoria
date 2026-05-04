# =============================================================================
# ms-auditoria | schemas/statistics_schema.py
# =============================================================================
# Schemas para los endpoints de estadísticas.
# =============================================================================

import datetime as dt
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class StatsRecord(BaseModel):
    """Un registro de estadísticas en las respuestas."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    service_name: str = Field(alias="microservicio")
    period: str = Field(alias="periodo")
    date: dt.date = Field(alias="fecha")
    total_requests: int = Field(alias="total_peticiones")
    total_errors: int = Field(alias="total_errores")
    avg_response_time_ms: float = Field(alias="tiempo_promedio_ms")
    most_used_functionality: Optional[str] = Field(default=None, alias="funcionalidad_top")
    calculation_date: dt.datetime = Field(alias="fecha_calculo")


class GeneralStatsData(BaseModel):
    """Datos del endpoint GET /api/v1/stats."""
    period: str
    date: Optional[str] = None
    total_records: int
    page: int
    page_size: int
    records: List[StatsRecord]


class ServiceStatsData(BaseModel):
    """Datos del endpoint GET /api/v1/stats/{service_name}."""
    service_name: str
    period: str
    total_records: int
    page: int
    page_size: int
    records: List[StatsRecord]
