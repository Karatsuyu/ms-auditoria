# =============================================================================
# ms-auditoria | services/statistics_service.py
# =============================================================================
# Servicio de estadísticas precalculadas (AUD-RF-014, AUD-RF-015, AUD-RF-016).
# Consulta la tabla aud_estadisticas_servicio en lugar de agregar on-the-fly.
# Incluye scheduler para recalcular estadísticas periódicamente.
# =============================================================================

import asyncio
from typing import Optional, List
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.models.service_statistics import ServiceStatistics
from app.repositories.statistics_repository import StatisticsRepository
from app.utils.logger import logger


class StatisticsService:
    """Servicio de consulta de estadísticas precalculadas."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = StatisticsRepository(db)

    async def get_general_stats(
        self,
        period: str,
        target_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[ServiceStatistics], int]:
        """Obtiene estadísticas generales de todos los servicios."""
        return await self.repo.find_by_period(
            period=period,
            target_date=target_date,
            page=page,
            page_size=page_size,
        )

    async def get_service_stats(
        self,
        service_name: str,
        period: str,
        target_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[ServiceStatistics], int]:
        """Obtiene estadísticas de un servicio específico."""
        return await self.repo.find_by_service_and_period(
            service_name=service_name,
            period=period,
            target_date=target_date,
            page=page,
            page_size=page_size,
        )


# =============================================================================
# Scheduler de cálculo de estadísticas (AUD-RF-014)
# =============================================================================

class StatisticsScheduler:
    """Calcula y persiste estadísticas diarias periódicamente."""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("statistics_scheduler_started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("statistics_scheduler_stopped")

    async def _loop(self) -> None:
        while self._running:
            try:
                # Run at 00:05 UTC daily (after midnight)
                now = datetime.now(timezone.utc)
                target = now.replace(hour=0, minute=5, second=0, microsecond=0)
                if target <= now:
                    target += timedelta(days=1)
                wait_seconds = (target - now).total_seconds()
                logger.info("statistics_next_run", extra={"seconds_until": wait_seconds})
                await asyncio.sleep(wait_seconds)

                if self._running:
                    await self._calculate_daily_stats()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("statistics_scheduler_error", extra={"error": str(e)}, exc_info=True)
                await asyncio.sleep(3600)

    async def _calculate_daily_stats(self) -> None:
        """
        Calcula estadísticas del día anterior por microservicio.
        Inserta/actualiza registros en aud_estadisticas_servicio.
        """
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
        day_start = datetime.combine(yesterday, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        async with AsyncSessionLocal() as session:
            # Obtener microservicios con logs en el día
            services_stmt = (
                select(AuditLog.microservicio)
                .where(AuditLog.fecha_hora >= day_start, AuditLog.fecha_hora < day_end)
                .group_by(AuditLog.microservicio)
            )
            services_result = await session.execute(services_stmt)
            services = [row[0] for row in services_result.all()]

            for svc in services:
                conditions = [
                    AuditLog.microservicio == svc,
                    AuditLog.fecha_hora >= day_start,
                    AuditLog.fecha_hora < day_end,
                ]

                # Calcular métricas
                metrics_stmt = select(
                    func.count(AuditLog.id).label("total"),
                    func.sum(
                        func.cast(AuditLog.codigo_respuesta >= 400, type_=None)
                    ).label("errors"),
                    func.avg(AuditLog.duracion_ms).label("avg_duration"),
                ).where(*conditions)

                metrics = (await session.execute(metrics_stmt)).one()
                total = metrics.total or 0
                errors = metrics.errors or 0
                avg_dur = round(float(metrics.avg_duration or 0), 2)

                # Top funcionalidad
                top_stmt = (
                    select(AuditLog.funcionalidad)
                    .where(*conditions)
                    .group_by(AuditLog.funcionalidad)
                    .order_by(func.count(AuditLog.id).desc())
                    .limit(1)
                )
                top_result = await session.execute(top_stmt)
                top_func = top_result.scalar()

                # Upsert
                now = datetime.now(timezone.utc)
                existing_stmt = select(ServiceStatistics).where(
                    ServiceStatistics.microservicio == svc,
                    ServiceStatistics.periodo == "diario",
                    ServiceStatistics.fecha == yesterday,
                )
                existing = (await session.execute(existing_stmt)).scalar_one_or_none()

                if existing:
                    existing.total_peticiones = total
                    existing.total_errores = errors
                    existing.tiempo_promedio_ms = avg_dur
                    existing.funcionalidad_top = top_func
                    existing.fecha_calculo = now
                else:
                    session.add(ServiceStatistics(
                        microservicio=svc,
                        periodo="diario",
                        fecha=yesterday,
                        total_peticiones=total,
                        total_errores=errors,
                        tiempo_promedio_ms=avg_dur,
                        funcionalidad_top=top_func,
                        fecha_calculo=now,
                    ))

            await session.commit()
            logger.info(
                "daily_stats_calculated",
                extra={"date": str(yesterday), "services_count": len(services)},
            )


statistics_scheduler = StatisticsScheduler()
