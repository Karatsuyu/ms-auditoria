# =============================================================================
# ms-auditoria | utils/pagination.py
# =============================================================================
# Utilidades de paginación reutilizables.
# =============================================================================

import math
from typing import Optional

from fastapi import Query

from app.core.config import settings


class PaginationParams:
    """Parámetros de paginación extraídos del query string."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Número de página"),
        page_size: int = Query(
            default=None,
            ge=1,
            le=100,
            description="Registros por página",
        ),
    ) -> None:
        self.page = page
        self.page_size = page_size or settings.DEFAULT_PAGE_SIZE

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @staticmethod
    def total_pages(total: int, page_size: int) -> int:
        return math.ceil(total / page_size) if total > 0 else 0
