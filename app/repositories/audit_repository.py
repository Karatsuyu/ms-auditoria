# =============================================================================
# ms-auditoria | repositories/audit_repository.py
# =============================================================================
# Capa de acceso a datos ASYNC (Repository Pattern).
# Todas las consultas SQL a la tabla audit_logs están aquí.
# Usa SQLAlchemy 2.0 async con select() en vez de query().
# =============================================================================

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete, case, Integer, text

from app.models.audit_log import AuditLog


class AuditRepository:
    """Repositorio async para operaciones CRUD sobre audit_logs."""

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

    async def find_by_id(self, audit_id: UUID) -> Optional[AuditLog]:
        """Busca un registro por su ID."""
        stmt = select(AuditLog).where(AuditLog.id == audit_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(
        self,
        page: int = 1,
        page_size: int = 20,
        servicio: Optional[str] = None,
        metodo: Optional[str] = None,
        codigo_respuesta: Optional[int] = None,
        usuario_id: Optional[UUID] = None,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        request_id: Optional[str] = None,
        search_text: Optional[str] = None,
    ) -> tuple[List[AuditLog], int]:
        """
        Busca registros con filtros opcionales y paginación.
        Retorna (lista_resultados, total_registros).
        Soporta búsqueda full-text en el campo detalle (PostgreSQL GIN).
        """
        # Construir filtros dinámicos
        conditions = []
        if servicio:
            conditions.append(AuditLog.servicio == servicio)
        if metodo:
            conditions.append(AuditLog.metodo == metodo)
        if codigo_respuesta:
            conditions.append(AuditLog.codigo_respuesta == codigo_respuesta)
        if usuario_id:
            conditions.append(AuditLog.usuario_id == usuario_id)
        if fecha_inicio:
            conditions.append(AuditLog.timestamp_evento >= fecha_inicio)
        if fecha_fin:
            conditions.append(AuditLog.timestamp_evento <= fecha_fin)
        if request_id:
            conditions.append(AuditLog.request_id == request_id)
        if search_text:
            # Full-text search con to_tsvector (PostgreSQL)
            # Fallback a LIKE para SQLite en tests
            conditions.append(
                text("to_tsvector('spanish', COALESCE(detalle, '')) @@ plainto_tsquery('spanish', :q)").bindparams(q=search_text)
            )

        # Contar total
        count_stmt = select(func.count(AuditLog.id)).where(*conditions)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Obtener resultados paginados
        data_stmt = (
            select(AuditLog)
            .where(*conditions)
            .order_by(desc(AuditLog.timestamp_evento))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        data_result = await self.session.execute(data_stmt)
        results = list(data_result.scalars().all())

        return results, total

    async def find_by_request_id(self, request_id: str) -> List[AuditLog]:
        """Busca todos los registros asociados a un X-Request-ID."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.request_id == request_id)
            .order_by(desc(AuditLog.timestamp_evento))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_usuario(
        self,
        usuario_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[AuditLog], int]:
        """Busca registros de un usuario específico con paginación."""
        condition = AuditLog.usuario_id == usuario_id

        count_stmt = select(func.count(AuditLog.id)).where(condition)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        data_stmt = (
            select(AuditLog)
            .where(condition)
            .order_by(desc(AuditLog.timestamp_evento))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        data_result = await self.session.execute(data_stmt)
        results = list(data_result.scalars().all())

        return results, total

    # ── STATISTICS ─────────────────────────────────────────────────────────

    async def count_by_servicio(self) -> List[tuple]:
        """Cuenta registros agrupados por microservicio."""
        stmt = (
            select(
                AuditLog.servicio,
                func.count(AuditLog.id).label("total"),
            )
            .group_by(AuditLog.servicio)
            .order_by(desc("total"))
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def count_by_codigo_respuesta(self) -> List[tuple]:
        """Cuenta registros agrupados por código de respuesta."""
        stmt = (
            select(
                AuditLog.codigo_respuesta,
                func.count(AuditLog.id).label("total"),
            )
            .group_by(AuditLog.codigo_respuesta)
            .order_by(desc("total"))
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def average_duration_by_servicio(self) -> List[tuple]:
        """Calcula el promedio de duración por microservicio."""
        stmt = (
            select(
                AuditLog.servicio,
                func.avg(AuditLog.duracion_ms).label("avg_duration_ms"),
                func.count(AuditLog.id).label("total_requests"),
            )
            .group_by(AuditLog.servicio)
            .order_by(desc("avg_duration_ms"))
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def error_rate_by_servicio(self) -> List[tuple]:
        """Calcula la tasa de errores (4xx + 5xx) por microservicio."""
        stmt = (
            select(
                AuditLog.servicio,
                func.count(AuditLog.id).label("total"),
                func.sum(
                    case(
                        (AuditLog.codigo_respuesta >= 400, 1),
                        else_=0,
                    )
                ).label("errors"),
            )
            .group_by(AuditLog.servicio)
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def count_total(self) -> int:
        """Retorna el total de registros de auditoría."""
        stmt = select(func.count(AuditLog.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    # ── DELETE ─────────────────────────────────────────────────────────────

    async def delete_before(self, before_date: datetime) -> int:
        """
        Elimina registros anteriores a una fecha (purga).
        Retorna la cantidad de registros eliminados.
        """
        stmt = (
            delete(AuditLog)
            .where(AuditLog.timestamp_evento < before_date)
        )
        result = await self.session.execute(stmt)
        return result.rowcount
