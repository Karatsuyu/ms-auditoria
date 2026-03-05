# =============================================================================
# ms-auditoria | repositories/audit_repository.py
# =============================================================================
# Capa de acceso a datos ASYNC (Repository Pattern).
# Todas las consultas SQL a la tabla aud_eventos_log están aquí.
# Usa SQLAlchemy 2.0 async con select() en vez de query().
# =============================================================================

from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, delete

from app.models.audit_log import AuditLog


class AuditRepository:
    """Repositorio async para operaciones CRUD sobre aud_eventos_log."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── CREATE ─────────────────────────────────────────────────────────────

    async def save(self, audit_log: AuditLog) -> AuditLog:
        """Persiste un nuevo registro de auditoría."""
        self.session.add(audit_log)
        await self.session.flush()
        await self.session.refresh(audit_log)
        return audit_log

    async def save_batch(self, audit_logs: List[AuditLog]) -> List[AuditLog]:
        """Persiste múltiples registros en la transacción actual."""
        self.session.add_all(audit_logs)
        await self.session.flush()
        for log in audit_logs:
            await self.session.refresh(log)
        return audit_logs

    # ── READ ───────────────────────────────────────────────────────────────

    async def find_by_request_id(
        self,
        request_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[AuditLog], int]:
        """
        Busca registros por request_id, paginados y ordenados ASC por fecha.
        Para reconstruir la traza cronológica distribuida.
        """
        condition = AuditLog.request_id == request_id

        count_stmt = select(func.count(AuditLog.id)).where(condition)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        data_stmt = (
            select(AuditLog)
            .where(condition)
            .order_by(asc(AuditLog.fecha_hora))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        data_result = await self.session.execute(data_stmt)
        results = list(data_result.scalars().all())

        return results, total

    async def find_filtered(
        self,
        page: int = 1,
        page_size: int = 20,
        service_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[List[AuditLog], int]:
        """
        Busca registros con filtros opcionales y paginación.
        Al menos un filtro debe proporcionarse (validado en la capa de servicio).
        """
        conditions = []
        if service_name:
            conditions.append(AuditLog.microservicio == service_name)
        if date_from:
            conditions.append(AuditLog.fecha_hora >= date_from)
        if date_to:
            conditions.append(AuditLog.fecha_hora <= date_to)

        count_stmt = select(func.count(AuditLog.id)).where(*conditions)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        data_stmt = (
            select(AuditLog)
            .where(*conditions)
            .order_by(desc(AuditLog.fecha_hora))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        data_result = await self.session.execute(data_stmt)
        results = list(data_result.scalars().all())

        return results, total

    async def find_rotation_history(
        self,
        page: int = 1,
        page_size: int = 20,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[List[AuditLog], int]:
        """
        Busca registros de auto-auditoría de rotaciones ejecutadas.
        Filtra por microservicio='ms-auditoria' y funcionalidad='ejecutar_rotacion'.
        """
        conditions = [
            AuditLog.microservicio == "ms-auditoria",
            AuditLog.funcionalidad == "ejecutar_rotacion",
        ]
        if date_from:
            conditions.append(AuditLog.fecha_hora >= date_from)
        if date_to:
            conditions.append(AuditLog.fecha_hora <= date_to)

        count_stmt = select(func.count(AuditLog.id)).where(*conditions)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        data_stmt = (
            select(AuditLog)
            .where(*conditions)
            .order_by(desc(AuditLog.fecha_hora))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        data_result = await self.session.execute(data_stmt)
        results = list(data_result.scalars().all())

        return results, total

    # ── DELETE ─────────────────────────────────────────────────────────────

    async def delete_before(self, cutoff_date: datetime) -> int:
        """
        Elimina registros con fecha_hora anterior a cutoff_date.
        Retorna la cantidad de registros eliminados.
        """
        stmt = delete(AuditLog).where(AuditLog.fecha_hora < cutoff_date)
        result = await self.session.execute(stmt)
        return result.rowcount

    # ── COUNT ──────────────────────────────────────────────────────────────

    async def count_total(self) -> int:
        """Retorna el total de registros de auditoría."""
        stmt = select(func.count(AuditLog.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0
