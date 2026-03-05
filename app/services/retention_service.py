# =============================================================================
# ms-auditoria | services/retention_service.py
# =============================================================================
# Servicio de retención de logs.
# - Consulta/actualiza configuración desde aud_configuracion_retencion.
# - Ejecuta rotación manual (DELETE registros antiguos + actualiza config).
# - Ejecuta rotación automática en background (scheduler).
# =============================================================================

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.models.retention_config import RetentionConfig
from app.repositories.retention_repository import RetentionRepository
from app.repositories.audit_repository import AuditRepository
from app.core.config import settings
from app.utils.logger import logger


class RetentionService:
    """Servicio de retención de logs (consulta, actualización, rotación)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = RetentionRepository(db)
        self.audit_repo = AuditRepository(db)

    async def get_config(self) -> dict:
        """
        Retorna la configuración activa de retención.
        Si no existe, retorna valores por defecto (30 días).
        """
        config = await self.repo.get_active()
        if not config:
            return {
                "retention_days": 30,
                "status": "activo",
                "last_rotation_date": None,
                "last_rotation_deleted_count": 0,
            }
        return {
            "retention_days": config.dias_retencion,
            "status": config.estado,
            "last_rotation_date": config.ultima_rotacion,
            "last_rotation_deleted_count": config.registros_eliminados_ultima or 0,
        }

    async def update_config(self, retention_days: int) -> dict:
        """Actualiza los días de retención en la configuración activa."""
        config = await self.repo.get_active()
        if not config:
            # Crear configuración si no existe
            config = RetentionConfig(
                dias_retencion=retention_days,
                estado="activo",
            )
            self.db.add(config)
        else:
            config.dias_retencion = retention_days

        await self.db.commit()
        await self.db.refresh(config)

        return {
            "retention_days": config.dias_retencion,
            "status": config.estado,
            "last_rotation_date": config.ultima_rotacion,
            "last_rotation_deleted_count": config.registros_eliminados_ultima or 0,
            "updated_at": config.updated_at,
        }

    async def rotate(self) -> dict:
        """
        Ejecuta rotación manual: elimina logs más antiguos que dias_retencion.
        Actualiza la configuración con fecha y conteo de la rotación.
        """
        config = await self.repo.get_active()
        retention_days = config.dias_retencion if config else 30

        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=retention_days)

        # DELETE registros antiguos
        deleted_count = await self.audit_repo.delete_before(cutoff_date)

        # Actualizar configuración
        if config:
            config.ultima_rotacion = now
            config.registros_eliminados_ultima = deleted_count

        await self.db.commit()

        logger.info(
            "rotation_executed",
            extra={
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": retention_days,
            },
        )

        return {
            "rotation_date": now,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date,
            "retention_days_applied": retention_days,
        }


# =============================================================================
# Scheduler de rotación automática (singleton)
# =============================================================================

class RetentionScheduler:
    """Scheduler que ejecuta la rotación automática periódicamente."""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Inicia el scheduler en background."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(
            "retention_scheduler_started",
            extra={
                "retention_cron_hour_utc": settings.RETENTION_CRON_HOUR,
            },
        )

    async def stop(self) -> None:
        """Detiene el scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("retention_scheduler_stopped")

    async def _loop(self) -> None:
        """Loop principal del scheduler."""
        while self._running:
            try:
                seconds_until = self._seconds_until_next_run()
                logger.info("retention_next_run", extra={"seconds_until": seconds_until})
                await asyncio.sleep(seconds_until)
                if self._running:
                    await self._execute_rotation()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("retention_scheduler_error", extra={"error": str(e)}, exc_info=True)
                await asyncio.sleep(3600)

    def _seconds_until_next_run(self) -> float:
        """Calcula segundos hasta la próxima ejecución programada."""
        now = datetime.now(timezone.utc)
        target = now.replace(
            hour=settings.RETENTION_CRON_HOUR,
            minute=0,
            second=0,
            microsecond=0,
        )
        if target <= now:
            target += timedelta(days=1)
        return (target - now).total_seconds()

    async def _execute_rotation(self) -> None:
        """Ejecuta la rotación usando su propia sesión de BD."""
        async with AsyncSessionLocal() as session:
            service = RetentionService(session)
            result = await service.rotate()
            # Auto-auditoría de la rotación automática
            from app.services.self_audit_service import fire_self_audit
            from app.core.middleware import generate_request_id
            fire_self_audit(
                request_id=generate_request_id(),
                funcionalidad="ejecutar_rotacion",
                metodo="POST",
                codigo_respuesta=200,
                duracion_ms=0,
                detalle=f"Rotación automática ejecutada. {result['deleted_count']} registros eliminados.",
            )


retention_scheduler = RetentionScheduler()
