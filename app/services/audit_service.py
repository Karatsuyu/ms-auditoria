# =============================================================================
# ms-auditoria | services/audit_service.py
# =============================================================================
# Servicio principal de lógica de negocio para auditoría (ASYNC).
# Orquesta la creación, consulta y gestión de logs de auditoría.
# =============================================================================

import math
import uuid
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.schemas.audit_schema import AuditLogCreate, AuditLogResponse, AuditLogFilter
from app.schemas.response_schema import PaginatedResponse, DataResponse
from app.repositories.audit_repository import AuditRepository
from app.core.config import settings
from app.utils.logger import logger


class AuditService:
    """Servicio async de lógica de negocio para auditoría."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AuditRepository(db)

    # ── Crear log de auditoría ─────────────────────────────────────────────

    async def create_log(self, data: AuditLogCreate) -> AuditLogResponse:
        """
        Crea un nuevo registro de auditoría.
        Mapea del schema de entrada al modelo ORM.
        """
        audit_log = AuditLog(
            request_id=data.request_id or str(uuid.uuid4()),
            servicio=data.nombre_microservicio,
            endpoint=data.endpoint,
            metodo=data.metodo_http,
            codigo_respuesta=data.codigo_respuesta,
            duracion_ms=data.duracion_ms,
            usuario_id=data.usuario_id,
            detalle=data.detalle,
            ip_origen=data.ip_origen,
            timestamp_evento=data.timestamp,
        )

        saved = await self.repo.save(audit_log)
        await self.db.commit()

        logger.info(
            "audit_log_created",
            extra={
                "audit_id": str(saved.id),
                "servicio": saved.servicio,
                "endpoint": saved.endpoint,
            },
        )

        return AuditLogResponse.model_validate(saved)

    # ── Crear logs en batch ────────────────────────────────────────────────

    async def create_logs_batch(self, logs: List[AuditLogCreate]) -> List[AuditLogResponse]:
        """Crea múltiples registros de auditoría en una sola transacción."""
        audit_logs = [
            AuditLog(
                request_id=data.request_id or str(uuid.uuid4()),
                servicio=data.nombre_microservicio,
                endpoint=data.endpoint,
                metodo=data.metodo_http,
                codigo_respuesta=data.codigo_respuesta,
                duracion_ms=data.duracion_ms,
                usuario_id=data.usuario_id,
                detalle=data.detalle,
                ip_origen=data.ip_origen,
                timestamp_evento=data.timestamp,
            )
            for data in logs
        ]

        saved_logs = await self.repo.save_batch(audit_logs)
        await self.db.commit()

        logger.info("audit_batch_created", extra={"count": len(saved_logs)})

        return [AuditLogResponse.model_validate(log) for log in saved_logs]

    # ── Obtener log por ID ─────────────────────────────────────────────────

    async def get_by_id(self, audit_id: UUID) -> Optional[AuditLogResponse]:
        """Obtiene un registro de auditoría por su ID."""
        log = await self.repo.find_by_id(audit_id)
        if not log:
            return None
        return AuditLogResponse.model_validate(log)

    # ── Listar logs con filtros y paginación ───────────────────────────────

    async def get_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[AuditLogFilter] = None,
    ) -> PaginatedResponse[AuditLogResponse]:
        """Obtiene registros paginados con filtros opcionales."""
        # Validar paginación
        page_size = min(page_size, settings.MAX_PAGE_SIZE)
        page = max(page, 1)

        # Extraer filtros
        kwargs = {}
        if filters:
            if filters.servicio:
                kwargs["servicio"] = filters.servicio
            if filters.metodo_http:
                kwargs["metodo"] = filters.metodo_http
            if filters.codigo_respuesta:
                kwargs["codigo_respuesta"] = filters.codigo_respuesta
            if filters.usuario_id:
                kwargs["usuario_id"] = filters.usuario_id
            if filters.fecha_inicio:
                kwargs["fecha_inicio"] = filters.fecha_inicio
            if filters.fecha_fin:
                kwargs["fecha_fin"] = filters.fecha_fin
            if filters.request_id:
                kwargs["request_id"] = filters.request_id
            if hasattr(filters, "search_text") and filters.search_text:
                kwargs["search_text"] = filters.search_text

        results, total = await self.repo.find_all(
            page=page,
            page_size=page_size,
            **kwargs,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return PaginatedResponse(
            data=[AuditLogResponse.model_validate(r) for r in results],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # ── Buscar por Request-ID ──────────────────────────────────────────────

    async def get_by_request_id(self, request_id: str) -> List[AuditLogResponse]:
        """Obtiene todos los registros asociados a un X-Request-ID."""
        logs = await self.repo.find_by_request_id(request_id)
        return [AuditLogResponse.model_validate(log) for log in logs]

    # ── Buscar por usuario ─────────────────────────────────────────────────

    async def get_by_usuario(
        self,
        usuario_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[AuditLogResponse]:
        """Obtiene registros de un usuario específico paginados."""
        page_size = min(page_size, settings.MAX_PAGE_SIZE)

        results, total = await self.repo.find_by_usuario(
            usuario_id=usuario_id,
            page=page,
            page_size=page_size,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return PaginatedResponse(
            data=[AuditLogResponse.model_validate(r) for r in results],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # ── Purgar logs antiguos ───────────────────────────────────────────────

    async def purge_old_logs(self, before_date: datetime) -> int:
        """Elimina registros anteriores a una fecha."""
        count = await self.repo.delete_before(before_date)
        await self.db.commit()
        logger.warning("audit_logs_purged", extra={"deleted_count": count, "before": str(before_date)})
        return count
