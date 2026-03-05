# =============================================================================
# ms-auditoria | services/audit_service.py
# =============================================================================
# Servicio principal de lógica de negocio para auditoría (ASYNC).
# Orquesta la recepción, almacenamiento en background y consulta de logs.
# =============================================================================

import asyncio
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.schemas.audit_schema import LogCreate
from app.repositories.audit_repository import AuditRepository
from app.utils.logger import logger


class AuditService:
    """Servicio async de lógica de negocio para auditoría."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AuditRepository(db)

    # ── Background: persistir un log ───────────────────────────────────────

    @staticmethod
    async def _persist_log_background(data: LogCreate) -> None:
        """
        Persiste un log en background con su propia sesión de BD.
        Los errores se loguean pero NO propagan (el 202 ya fue enviado).
        """
        try:
            async with AsyncSessionLocal() as session:
                log = AuditLog(
                    request_id=data.request_id or "",
                    fecha_hora=data.timestamp,
                    microservicio=data.service_name,
                    funcionalidad=data.functionality,
                    metodo=data.method,
                    codigo_respuesta=data.response_code,
                    duracion_ms=data.duration_ms,
                    usuario_id=data.user_id,
                    detalle=data.detail,
                )
                session.add(log)
                await session.commit()
        except Exception as e:
            logger.error(
                "log_persist_error",
                extra={"error": str(e), "service_name": data.service_name},
            )

    @staticmethod
    async def _persist_batch_background(logs: List[LogCreate]) -> None:
        """Persiste múltiples logs en background."""
        try:
            async with AsyncSessionLocal() as session:
                orm_logs = [
                    AuditLog(
                        request_id=data.request_id or "",
                        fecha_hora=data.timestamp,
                        microservicio=data.service_name,
                        funcionalidad=data.functionality,
                        metodo=data.method,
                        codigo_respuesta=data.response_code,
                        duracion_ms=data.duration_ms,
                        usuario_id=data.user_id,
                        detalle=data.detail,
                    )
                    for data in logs
                ]
                session.add_all(orm_logs)
                await session.commit()
                logger.info("batch_persisted", extra={"count": len(orm_logs)})
        except Exception as e:
            logger.error(
                "batch_persist_error",
                extra={"error": str(e), "count": len(logs)},
            )

    def enqueue_log(self, data: LogCreate) -> None:
        """Despacha la persistencia de un log como tarea asíncrona."""
        try:
            asyncio.create_task(self._persist_log_background(data))
        except RuntimeError:
            logger.warning("enqueue_log_no_event_loop")

    def enqueue_batch(self, valid_logs: List[LogCreate]) -> None:
        """Despacha la persistencia de un batch como tarea asíncrona."""
        if not valid_logs:
            return
        try:
            asyncio.create_task(self._persist_batch_background(valid_logs))
        except RuntimeError:
            logger.warning("enqueue_batch_no_event_loop")

    # ── Consulta: traza por request_id ─────────────────────────────────────

    async def get_trace(
        self,
        request_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[AuditLog], int]:
        """Busca registros por request_id (traza distribuida)."""
        return await self.repo.find_by_request_id(
            request_id=request_id,
            page=page,
            page_size=page_size,
        )

    # ── Consulta: filtrar logs ─────────────────────────────────────────────

    async def get_filtered_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        service_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[List[AuditLog], int]:
        """Busca registros con filtros y paginación."""
        return await self.repo.find_filtered(
            page=page,
            page_size=page_size,
            service_name=service_name,
            date_from=date_from,
            date_to=date_to,
        )

    # ── Consulta: historial de rotaciones ──────────────────────────────────

    async def get_rotation_history(
        self,
        page: int = 1,
        page_size: int = 20,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[List[AuditLog], int]:
        """Busca registros de auto-auditoría de rotaciones."""
        return await self.repo.find_rotation_history(
            page=page,
            page_size=page_size,
            date_from=date_from,
            date_to=date_to,
        )
