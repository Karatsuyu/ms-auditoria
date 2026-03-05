# =============================================================================
# ms-auditoria | repositories/statistics_repository.py
# =============================================================================
# Capa de acceso a datos para la tabla aud_estadisticas_servicio.
# =============================================================================

from typing import Optional, List
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.service_statistics import ServiceStatistics


class StatisticsRepository:
    """Repositorio async para aud_estadisticas_servicio."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_period(
        self,
        period: str,
        target_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[ServiceStatistics], int]:
        """
        Busca estadísticas por periodo y opcionalmente por fecha.
        Retorna (resultados, total).
        """
        conditions = [ServiceStatistics.periodo == period]
        if target_date:
            conditions.append(ServiceStatistics.fecha == target_date)

        count_stmt = select(func.count(ServiceStatistics.id)).where(*conditions)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        data_stmt = (
            select(ServiceStatistics)
            .where(*conditions)
            .order_by(desc(ServiceStatistics.fecha))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        data_result = await self.session.execute(data_stmt)
        results = list(data_result.scalars().all())

        return results, total

    async def find_by_service_and_period(
        self,
        service_name: str,
        period: str,
        target_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[ServiceStatistics], int]:
        """
        Busca estadísticas de un servicio específico por periodo.
        """
        conditions = [
            ServiceStatistics.microservicio == service_name,
            ServiceStatistics.periodo == period,
        ]
        if target_date:
            conditions.append(ServiceStatistics.fecha == target_date)

        count_stmt = select(func.count(ServiceStatistics.id)).where(*conditions)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        data_stmt = (
            select(ServiceStatistics)
            .where(*conditions)
            .order_by(desc(ServiceStatistics.fecha))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        data_result = await self.session.execute(data_stmt)
        results = list(data_result.scalars().all())

        return results, total

    async def upsert(self, stats: ServiceStatistics) -> ServiceStatistics:
        """Inserta o actualiza un registro de estadísticas."""
        self.session.add(stats)
        await self.session.flush()
        await self.session.refresh(stats)
        return stats
