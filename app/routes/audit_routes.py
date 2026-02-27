# =============================================================================
# ms-auditoria | routes/audit_routes.py
# =============================================================================
# Rutas HTTP ASYNC del microservicio de auditoría.
# Implementa todos los endpoints RESTful para:
#   - Registrar logs de auditoría (POST)
#   - Consultar logs con filtros y paginación (GET)
#   - Obtener estadísticas (GET)
#   - Buscar por request-id y usuario (GET)
#   - Purgar logs antiguos (DELETE)
# =============================================================================

from datetime import datetime
from typing import Optional, List, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.auth import verify_api_key
from app.schemas.audit_schema import AuditLogCreate, AuditLogResponse, AuditLogFilter
from app.schemas.response_schema import (
    DataResponse,
    PaginatedResponse,
    MessageResponse,
    StatsResponse,
)
from app.services.audit_service import AuditService
from app.services.statistics_service import StatisticsService

router = APIRouter(prefix="/api/v1/audit", tags=["Auditoría"])


# ── Health Check ───────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=MessageResponse,
    summary="Health Check",
    description="Verifica que el microservicio está activo.",
)
async def health_check():
    return MessageResponse(success=True, message="ms-auditoria is running")


# ── POST: Registrar log de auditoría ──────────────────────────────────────────

@router.post(
    "/log",
    response_model=DataResponse[AuditLogResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar evento de auditoría",
    description="Recibe un evento de auditoría de cualquier microservicio y lo persiste.",
)
async def create_audit_log(
    data: AuditLogCreate,
    db: AsyncSession = Depends(get_db),
    _api_key=Depends(verify_api_key),
):
    """
    Endpoint principal para que los 18 microservicios envíen sus logs.
    Requiere API Key válida (X-API-Key header) en producción.
    """
    service = AuditService(db)
    result = await service.create_log(data)
    return DataResponse(
        success=True,
        message="Evento de auditoría registrado exitosamente",
        data=result,
    )


# ── POST: Registrar logs en batch ─────────────────────────────────────────────

@router.post(
    "/log/batch",
    response_model=DataResponse[List[AuditLogResponse]],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar múltiples eventos de auditoría",
    description="Recibe y persiste múltiples eventos en una sola transacción.",
)
async def create_audit_logs_batch(
    logs: List[AuditLogCreate],
    db: AsyncSession = Depends(get_db),
    _api_key=Depends(verify_api_key),
):
    """Endpoint para envío masivo de logs (mejora rendimiento)."""
    if len(logs) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo 1000 registros por batch",
        )

    service = AuditService(db)
    results = await service.create_logs_batch(logs)
    return DataResponse(
        success=True,
        message=f"{len(results)} eventos registrados exitosamente",
        data=results,
    )


# ── GET: Listar logs con filtros ──────────────────────────────────────────────

@router.get(
    "/logs",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="Listar logs de auditoría",
    description="Consulta logs con filtros opcionales y paginación.",
)
async def get_audit_logs(
    page: int = Query(default=1, ge=1, description="Página"),
    page_size: int = Query(default=20, ge=1, le=100, description="Registros por página"),
    servicio: Optional[str] = Query(default=None, description="Filtrar por microservicio"),
    metodo_http: Optional[str] = Query(default=None, description="Filtrar por método HTTP"),
    codigo_respuesta: Optional[int] = Query(default=None, description="Filtrar por código HTTP"),
    usuario_id: Optional[UUID] = Query(default=None, description="Filtrar por usuario"),
    fecha_inicio: Optional[datetime] = Query(default=None, description="Fecha inicio (ISO 8601)"),
    fecha_fin: Optional[datetime] = Query(default=None, description="Fecha fin (ISO 8601)"),
    request_id: Optional[str] = Query(default=None, description="Filtrar por X-Request-ID"),
    search_text: Optional[str] = Query(default=None, description="Búsqueda full-text en detalle"),
    db: AsyncSession = Depends(get_db),
):
    """Consulta principal con todos los filtros disponibles."""
    filters = AuditLogFilter(
        servicio=servicio,
        metodo_http=metodo_http,
        codigo_respuesta=codigo_respuesta,
        usuario_id=usuario_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        request_id=request_id,
        search_text=search_text,
    )
    service = AuditService(db)
    return await service.get_logs(page=page, page_size=page_size, filters=filters)


# ── GET: Obtener log por ID ───────────────────────────────────────────────────

@router.get(
    "/log/{audit_id}",
    response_model=DataResponse[AuditLogResponse],
    summary="Obtener log por ID",
    description="Obtiene un registro de auditoría específico por su UUID.",
)
async def get_audit_log_by_id(
    audit_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = AuditService(db)
    result = await service.get_by_id(audit_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro de auditoría {audit_id} no encontrado",
        )
    return DataResponse(data=result)


# ── GET: Buscar por Request-ID (trazabilidad) ─────────────────────────────────

@router.get(
    "/trace/{request_id}",
    response_model=DataResponse[List[AuditLogResponse]],
    summary="Trazar request por X-Request-ID",
    description="Obtiene todos los eventos asociados a un mismo Request-ID.",
)
async def trace_request(
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Permite rastrear una petición a través de múltiples microservicios."""
    service = AuditService(db)
    results = await service.get_by_request_id(request_id)
    return DataResponse(
        message=f"{len(results)} eventos encontrados para request {request_id}",
        data=results,
    )


# ── GET: Logs por usuario ─────────────────────────────────────────────────────

@router.get(
    "/user/{usuario_id}",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="Logs de un usuario",
    description="Obtiene el historial de acciones de un usuario específico. Acepta UUID.",
)
async def get_user_audit_logs(
    usuario_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # Validar que sea un UUID válido
    try:
        parsed_id = UUID(usuario_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{usuario_id}' no es un UUID válido. Formato esperado: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        )

    service = AuditService(db)
    return await service.get_by_usuario(
        usuario_id=parsed_id,
        page=page,
        page_size=page_size,
    )


# ── GET: Estadísticas ─────────────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Estadísticas de auditoría",
    description="Retorna estadísticas generales: logs por servicio, errores, duración promedio.",
)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
):
    service = StatisticsService(db)
    stats = await service.get_general_stats()
    return StatsResponse(data=stats)


# ── DELETE: Purgar logs antiguos ───────────────────────────────────────────────

@router.delete(
    "/purge",
    response_model=MessageResponse,
    summary="Purgar logs antiguos",
    description="Elimina registros de auditoría anteriores a una fecha dada.",
)
async def purge_logs(
    before_date: datetime = Query(..., description="Eliminar registros anteriores a esta fecha"),
    db: AsyncSession = Depends(get_db),
    _api_key=Depends(verify_api_key),
):
    """Solo microservicios autorizados pueden purgar logs (requiere API Key)."""
    service = AuditService(db)
    deleted = await service.purge_old_logs(before_date)
    return MessageResponse(
        success=True,
        message=f"{deleted} registros eliminados anteriores a {before_date.isoformat()}",
    )
