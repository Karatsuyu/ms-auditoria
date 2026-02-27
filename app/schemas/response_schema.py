# =============================================================================
# ms-auditoria | schemas/response_schema.py
# =============================================================================
# Schemas genéricos de respuesta para estandarizar todas las respuestas API.
# =============================================================================

from typing import Generic, TypeVar, Optional, List

from pydantic import BaseModel, Field

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Respuesta simple con mensaje."""
    success: bool
    message: str


class DataResponse(BaseModel, Generic[T]):
    """Respuesta con datos genérica."""
    success: bool = True
    message: str = "OK"
    data: T


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica."""
    success: bool = True
    message: str = "OK"
    data: List[T]
    total: int = Field(description="Total de registros")
    page: int = Field(description="Página actual")
    page_size: int = Field(description="Registros por página")
    total_pages: int = Field(description="Total de páginas")


class ErrorResponse(BaseModel):
    """Respuesta de error estandarizada."""
    success: bool = False
    error: str
    detail: Optional[str] = None


class StatsResponse(BaseModel):
    """Respuesta con estadísticas de auditoría."""
    success: bool = True
    data: dict
