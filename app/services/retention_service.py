# =============================================================================
# ms-auditoria | services/retention_service.py
# =============================================================================
# Servicio de retención automática (TTL) de logs de auditoría.
# Ejecuta una tarea periódica en background que purga registros
# más antiguos que RETENTION_DAYS.
# Usa asyncio nativo — sin dependencias externas (APScheduler, Celery, etc).
# =============================================================================

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.utils.logger import logger


class RetentionService:
    """Servicio de purga automática de logs con TTL configurable."""

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Inicia el scheduler de retención en background."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info(
            "retention_scheduler_started",
            extra={
                "retention_days": settings.RETENTION_DAYS,
                "cron_hour_utc": settings.RETENTION_CRON_HOUR,
            },
        )

    async def stop(self) -> None:
        """Detiene el scheduler de retención."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("retention_scheduler_stopped")

    async def _scheduler_loop(self) -> None:
        """
        Loop principal: calcula cuánto falta para la próxima hora programada,
        duerme, ejecuta la purga y repite.
        """
        while self._running:
            try:
                # Calcular segundos hasta la próxima ejecución
                seconds_until = self._seconds_until_next_run()
                logger.info(
                    "retention_next_run",
                    extra={"seconds_until": seconds_until},
                )

                await asyncio.sleep(seconds_until)

                if self._running:
                    await self.purge_old_logs()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "retention_scheduler_error",
                    extra={"error": str(e)},
                    exc_info=True,
                )
                # Esperar 1 hora antes de reintentar en caso de error
                await asyncio.sleep(3600)

    def _seconds_until_next_run(self) -> float:
        """Calcula los segundos hasta la próxima ejecución programada."""
        now = datetime.now(timezone.utc)
        target = now.replace(
            hour=settings.RETENTION_CRON_HOUR,
            minute=0,
            second=0,
            microsecond=0,
        )
        # Si ya pasó la hora hoy, programar para mañana
        if target <= now:
            target += timedelta(days=1)
        return (target - now).total_seconds()

    async def purge_old_logs(self) -> int:
        """
        Ejecuta la purga de logs más antiguos que RETENTION_DAYS.
        Usa su propia sesión de BD (independiente de requests HTTP).
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=settings.RETENTION_DAYS)

        async with AsyncSessionLocal() as session:
            stmt = delete(AuditLog).where(AuditLog.timestamp_evento < cutoff_date)
            result = await session.execute(stmt)
            deleted_count = result.rowcount
            await session.commit()

        logger.info(
            "retention_purge_completed",
            extra={
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": settings.RETENTION_DAYS,
            },
        )
        return deleted_count


# Singleton para usar en lifespan
retention_service = RetentionService()
