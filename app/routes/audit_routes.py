# =============================================================================
# ms-auditoria | routes/audit_routes.py
# =============================================================================
# Rutas HTTP ASYNC del microservicio de auditoría.
# 12 endpoints definidos según AUD-especificacion-api-rest.md:
#
#  Eventos de log:
#   1. POST   /api/v1/logs                          — Recibir log individual
#   2. POST   /api/v1/logs/batch                    — Recibir lote de logs
#   3. GET    /api/v1/logs/trace/{request_id}       — Traza por request_id
#   4. GET    /api/v1/logs                          — Filtrar registros
#
#  Configuración de retención:
#   5. GET    /api/v1/retention-config               — Consultar config
#   6. PATCH  /api/v1/retention-config               — Actualizar config
#   7. POST   /api/v1/retention-config/rotate        — Rotación manual
#   8. GET    /api/v1/retention-config/rotation-history — Historial
#
#  Estadísticas:
#   9. GET    /api/v1/stats                          — Generales
#  10. GET    /api/v1/stats/{service_name}           — Por servicio
#
#  Sistema:
#  11. GET    /api/v1/health                         — Health check
#  12. GET    /                                      — Raíz (info)
# =============================================================================

import time
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.dependencies import get_db, require_permission
from app.core.auth import verify_app_token
from app.schemas.audit_schema import (
    LogCreate,
    LogBatchRequest,
    LogRecord,
    TraceData,
    FilteredLogsData,
    LogReceivedData,
    BatchReceivedData,
    RotationHistoryRecord,
    RotationHistoryData,
)
from app.schemas.retention_schema import (
    RetentionConfigData,
    RetentionUpdateRequest,
    RetentionConfigUpdatedData,
    RotationResultData,
)
from app.schemas.statistics_schema import (
    StatsRecord,
    GeneralStatsData,
    ServiceStatsData,
)
from app.schemas.response_schema import APIResponse, HealthResponse
from app.services.audit_service import AuditService
from app.services.retention_service import RetentionService
from app.services.statistics_service import StatisticsService
from app.services.self_audit_service import fire_self_audit

# ── Routers ────────────────────────────────────────────────────────────────────

log_router = APIRouter(prefix="/api/v1/logs", tags=["Eventos de Log"])
retention_router = APIRouter(prefix="/api/v1/retention-config", tags=["Configuración de Retención"])
stats_router = APIRouter(prefix="/api/v1/stats", tags=["Estadísticas"])
system_router = APIRouter(prefix="/api/v1", tags=["Sistema"])


# =============================================================================
# HELPER: Obtener request_id del state
# =============================================================================

def _rid(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


# =============================================================================
# 1. POST /api/v1/logs — Recibir log individual (202 Accepted)
# =============================================================================

@log_router.post(
    "",
    response_model=APIResponse[LogReceivedData],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Recibir registro de log individual",
    description="Recibe un log de cualquier microservicio. 202 inmediato, persistencia en background.",
)
async def receive_log(
    data: LogCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _token=Depends(verify_app_token),
):
    start = time.perf_counter()
    request_id = _rid(request)

    service = AuditService(db)
    service.enqueue_log(data)

    duration = round((time.perf_counter() - start) * 1000)

    # Auto-auditoría (AUD-RF-005)
    fire_self_audit(
        request_id=request_id,
        funcionalidad="recibir_log",
        metodo="POST",
        codigo_respuesta=202,
        duracion_ms=duration,
        detalle=f"Log recibido de {data.service_name}.",
    )

    return APIResponse(
        request_id=request_id,
        success=True,
        data=LogReceivedData(
            received=True,
            log_request_id=data.request_id or "",
        ),
        message="Registro de log recibido y en proceso de almacenamiento.",
    )


# =============================================================================
# 2. POST /api/v1/logs/batch — Recibir lote de logs (202 Accepted)
# =============================================================================

@log_router.post(
    "/batch",
    response_model=APIResponse[BatchReceivedData],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Recibir registros de log en lote",
    description="Recibe múltiples logs. Valida individualmente, persiste válidos en background.",
)
async def receive_log_batch(
    body: LogBatchRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _token=Depends(verify_app_token),
):
    start = time.perf_counter()
    request_id = _rid(request)

    valid_logs = []
    rejected = []

    for idx, log in enumerate(body.logs):
        # Validaciones adicionales sobre campos
        errors = []
        if log.method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
            errors.append(f"method '{log.method}' no es un método HTTP válido.")
        if errors:
            rejected.append({"index": idx, "reason": "; ".join(errors)})
        else:
            valid_logs.append(log)

    service = AuditService(db)
    service.enqueue_batch(valid_logs)

    duration = round((time.perf_counter() - start) * 1000)
    total = len(body.logs)

    # Auto-auditoría
    fire_self_audit(
        request_id=request_id,
        funcionalidad="recibir_logs_batch",
        metodo="POST",
        codigo_respuesta=202,
        duracion_ms=duration,
        detalle=f"Lote recibido: {len(valid_logs)} aceptados, {len(rejected)} rechazados.",
    )

    return APIResponse(
        request_id=request_id,
        success=True,
        data=BatchReceivedData(
            received_count=total,
            accepted_count=len(valid_logs),
            rejected_count=len(rejected),
            rejected_indices=rejected,
        ),
        message=f"Lote de logs recibido. {len(valid_logs)} registros aceptados para almacenamiento.",
    )


# =============================================================================
# 3. GET /api/v1/logs/trace/{request_id} — Consultar traza completa
# =============================================================================

@log_router.get(
    "/trace/{trace_request_id}",
    response_model=APIResponse[TraceData],
    summary="Consultar traza completa por Request ID",
    description="Retorna todos los logs de un request_id ordenados cronológicamente.",
)
async def get_trace(
    trace_request_id: str,
    request: Request,
    page: int = Query(..., ge=1, description="Página (obligatorio)"),
    page_size: int = Query(..., ge=1, le=100, description="Registros por página (obligatorio)"),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_permission("AUD_CONSULTAR_LOGS")),
):
    start = time.perf_counter()
    request_id = _rid(request)

    service = AuditService(db)
    records, total = await service.get_trace(
        request_id=trace_request_id,
        page=page,
        page_size=page_size,
    )

    duration = round((time.perf_counter() - start) * 1000)

    fire_self_audit(
        request_id=request_id,
        funcionalidad="consultar_traza",
        metodo="GET",
        codigo_respuesta=200,
        duracion_ms=duration,
        usuario_id=_user.get("user_id") or _user.get("data", {}).get("user_id"),
        detalle=f"Traza consultada para request_id={trace_request_id}. {total} registros.",
    )

    return APIResponse(
        request_id=request_id,
        success=True,
        data=TraceData(
            trace_request_id=trace_request_id,
            total_records=total,
            page=page,
            page_size=page_size,
            records=[LogRecord.model_validate(r) for r in records],
        ),
        message="Traza recuperada exitosamente.",
    )


# =============================================================================
# 4. GET /api/v1/logs — Filtrar registros de log
# =============================================================================

@log_router.get(
    "",
    response_model=APIResponse[FilteredLogsData],
    summary="Filtrar registros de log",
    description="Retorna logs filtrados. Al menos un filtro obligatorio.",
)
async def filter_logs(
    request: Request,
    page: int = Query(..., ge=1, description="Página (obligatorio)"),
    page_size: int = Query(..., ge=1, le=100, description="Registros por página (obligatorio)"),
    service_name: Optional[str] = Query(default=None, description="Microservicio origen"),
    date_from: Optional[datetime] = Query(default=None, description="Fecha inicio (ISO 8601)"),
    date_to: Optional[datetime] = Query(default=None, description="Fecha fin (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_permission("AUD_CONSULTAR_LOGS")),
):
    start = time.perf_counter()
    request_id = _rid(request)

    # Validar que al menos un filtro esté presente
    if not service_name and not date_from and not date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionarse al menos un criterio de filtro: service_name, date_from o date_to.",
        )

    # Validar coherencia de fechas
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from no puede ser posterior a date_to.",
        )

    service = AuditService(db)
    records, total = await service.get_filtered_logs(
        page=page,
        page_size=page_size,
        service_name=service_name,
        date_from=date_from,
        date_to=date_to,
    )

    duration = round((time.perf_counter() - start) * 1000)

    fire_self_audit(
        request_id=request_id,
        funcionalidad="filtrar_logs",
        metodo="GET",
        codigo_respuesta=200,
        duracion_ms=duration,
        usuario_id=_user.get("user_id") or _user.get("data", {}).get("user_id"),
        detalle=f"Filtro aplicado: service_name={service_name}, {total} resultados.",
    )

    filters_applied = {}
    if service_name:
        filters_applied["service_name"] = service_name
    if date_from:
        filters_applied["date_from"] = date_from.isoformat()
    if date_to:
        filters_applied["date_to"] = date_to.isoformat()

    return APIResponse(
        request_id=request_id,
        success=True,
        data=FilteredLogsData(
            filters_applied=filters_applied,
            total_records=total,
            page=page,
            page_size=page_size,
            records=[LogRecord.model_validate(r) for r in records],
        ),
        message="Registros de log recuperados exitosamente.",
    )


# =============================================================================
# 5. GET /api/v1/retention-config — Consultar configuración de retención
# =============================================================================

@retention_router.get(
    "",
    response_model=APIResponse[RetentionConfigData],
    summary="Consultar configuración vigente de retención",
)
async def get_retention_config(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_permission("AUD_ADMINISTRAR_RETENCION")),
):
    start = time.perf_counter()
    request_id = _rid(request)

    service = RetentionService(db)
    data = await service.get_config()

    duration = round((time.perf_counter() - start) * 1000)

    fire_self_audit(
        request_id=request_id,
        funcionalidad="consultar_retencion",
        metodo="GET",
        codigo_respuesta=200,
        duracion_ms=duration,
        usuario_id=_user.get("user_id") or _user.get("data", {}).get("user_id"),
    )

    return APIResponse(
        request_id=request_id,
        success=True,
        data=RetentionConfigData(**data),
        message="Configuración de retención recuperada exitosamente.",
    )


# =============================================================================
# 6. PATCH /api/v1/retention-config — Actualizar configuración
# =============================================================================

@retention_router.patch(
    "",
    response_model=APIResponse[RetentionConfigUpdatedData],
    summary="Actualizar cantidad de días de retención",
)
async def update_retention_config(
    body: RetentionUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_permission("AUD_ADMINISTRAR_RETENCION")),
):
    start = time.perf_counter()
    request_id = _rid(request)

    service = RetentionService(db)
    data = await service.update_config(body.retention_days)

    duration = round((time.perf_counter() - start) * 1000)

    fire_self_audit(
        request_id=request_id,
        funcionalidad="actualizar_retencion",
        metodo="PATCH",
        codigo_respuesta=200,
        duracion_ms=duration,
        usuario_id=_user.get("user_id") or _user.get("data", {}).get("user_id"),
        detalle=f"Días de retención actualizados a {body.retention_days}.",
    )

    return APIResponse(
        request_id=request_id,
        success=True,
        data=RetentionConfigUpdatedData(**data),
        message="Configuración de retención actualizada exitosamente.",
    )


# =============================================================================
# 7. POST /api/v1/retention-config/rotate — Rotación manual
# =============================================================================

@retention_router.post(
    "/rotate",
    response_model=APIResponse[RotationResultData],
    summary="Ejecutar rotación manual de registros",
)
async def manual_rotation(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_permission("AUD_ROTAR_REGISTROS")),
):
    start = time.perf_counter()
    request_id = _rid(request)

    service = RetentionService(db)
    result = await service.rotate()

    duration = round((time.perf_counter() - start) * 1000)

    user_id = _user.get("user_id") or _user.get("data", {}).get("user_id")

    fire_self_audit(
        request_id=request_id,
        funcionalidad="ejecutar_rotacion",
        metodo="POST",
        codigo_respuesta=200,
        duracion_ms=duration,
        usuario_id=user_id,
        detalle=f"Rotación manual ejecutada por {user_id}. {result['deleted_count']} registros eliminados.",
    )

    deleted = result["deleted_count"]
    msg = (
        f"Rotación ejecutada exitosamente. {deleted} registros eliminados."
        if deleted > 0
        else "Rotación ejecutada. No se encontraron registros anteriores a la fecha de corte."
    )

    return APIResponse(
        request_id=request_id,
        success=True,
        data=RotationResultData(**result),
        message=msg,
    )


# =============================================================================
# 8. GET /api/v1/retention-config/rotation-history — Historial de rotaciones
# =============================================================================

@retention_router.get(
    "/rotation-history",
    response_model=APIResponse[RotationHistoryData],
    summary="Consultar historial de rotaciones ejecutadas",
)
async def get_rotation_history(
    request: Request,
    page: int = Query(..., ge=1, description="Página (obligatorio)"),
    page_size: int = Query(..., ge=1, le=100, description="Registros por página (obligatorio)"),
    date_from: Optional[datetime] = Query(default=None, description="Fecha inicio (ISO 8601)"),
    date_to: Optional[datetime] = Query(default=None, description="Fecha fin (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_permission("AUD_ADMINISTRAR_RETENCION")),
):
    start = time.perf_counter()
    request_id = _rid(request)

    service = AuditService(db)
    records, total = await service.get_rotation_history(
        page=page,
        page_size=page_size,
        date_from=date_from,
        date_to=date_to,
    )

    duration = round((time.perf_counter() - start) * 1000)

    fire_self_audit(
        request_id=request_id,
        funcionalidad="consultar_historial_rotaciones",
        metodo="GET",
        codigo_respuesta=200,
        duracion_ms=duration,
        usuario_id=_user.get("user_id") or _user.get("data", {}).get("user_id"),
    )

    return APIResponse(
        request_id=request_id,
        success=True,
        data=RotationHistoryData(
            total_records=total,
            page=page,
            page_size=page_size,
            records=[RotationHistoryRecord.model_validate(r) for r in records],
        ),
        message="Historial de rotaciones recuperado exitosamente.",
    )


# =============================================================================
# 9. GET /api/v1/stats — Estadísticas generales
# =============================================================================

@stats_router.get(
    "",
    response_model=APIResponse[GeneralStatsData],
    summary="Consultar estadísticas generales de todos los servicios",
)
async def get_general_stats(
    request: Request,
    period: str = Query(..., description="Periodo: diario | semanal | mensual"),
    page: int = Query(..., ge=1),
    page_size: int = Query(..., ge=1, le=100),
    target_date: Optional[date] = Query(default=None, alias="date", description="Fecha del periodo (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_permission("AUD_CONSULTAR_ESTADISTICAS")),
):
    start = time.perf_counter()
    request_id = _rid(request)

    # Validar period
    if period not in ("diario", "semanal", "mensual"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El valor del parámetro period no es válido.",
        )

    service = StatisticsService(db)
    records, total = await service.get_general_stats(
        period=period,
        target_date=target_date,
        page=page,
        page_size=page_size,
    )

    duration = round((time.perf_counter() - start) * 1000)

    fire_self_audit(
        request_id=request_id,
        funcionalidad="consultar_estadisticas_generales",
        metodo="GET",
        codigo_respuesta=200,
        duracion_ms=duration,
        usuario_id=_user.get("user_id") or _user.get("data", {}).get("user_id"),
    )

    return APIResponse(
        request_id=request_id,
        success=True,
        data=GeneralStatsData(
            period=period,
            date=str(target_date) if target_date else None,
            total_records=total,
            page=page,
            page_size=page_size,
            records=[StatsRecord.model_validate(r) for r in records],
        ),
        message="Estadísticas generales recuperadas exitosamente.",
    )


# =============================================================================
# 10. GET /api/v1/stats/{service_name} — Estadísticas por servicio
# =============================================================================

@stats_router.get(
    "/{service_name}",
    response_model=APIResponse[ServiceStatsData],
    summary="Consultar estadísticas de un servicio específico",
)
async def get_service_stats(
    service_name: str,
    request: Request,
    period: str = Query(..., description="Periodo: diario | semanal | mensual"),
    page: int = Query(..., ge=1),
    page_size: int = Query(..., ge=1, le=100),
    target_date: Optional[date] = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_permission("AUD_CONSULTAR_ESTADISTICAS")),
):
    start = time.perf_counter()
    request_id = _rid(request)

    if not service_name or not service_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro service_name es obligatorio y no puede estar vacío.",
        )

    if period not in ("diario", "semanal", "mensual"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El valor del parámetro period no es válido.",
        )

    service = StatisticsService(db)
    records, total = await service.get_service_stats(
        service_name=service_name,
        period=period,
        target_date=target_date,
        page=page,
        page_size=page_size,
    )

    duration = round((time.perf_counter() - start) * 1000)

    fire_self_audit(
        request_id=request_id,
        funcionalidad="consultar_estadisticas_servicio",
        metodo="GET",
        codigo_respuesta=200,
        duracion_ms=duration,
        usuario_id=_user.get("user_id") or _user.get("data", {}).get("user_id"),
    )

    return APIResponse(
        request_id=request_id,
        success=True,
        data=ServiceStatsData(
            service_name=service_name,
            period=period,
            total_records=total,
            page=page,
            page_size=page_size,
            records=[StatsRecord.model_validate(r) for r in records],
        ),
        message=f"Estadísticas del servicio {service_name} recuperadas exitosamente.",
    )


# =============================================================================
# 11. GET /api/v1/health — Health check (sin autenticación, sin auto-auditoría)
# =============================================================================

@system_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Estado de salud del servicio",
    description="No requiere autenticación. Verifica conectividad con BD.",
)
async def health_check(db: AsyncSession = Depends(get_db)):
    ts = datetime.now(timezone.utc)
    try:
        start = time.perf_counter()
        await db.execute(text("SELECT 1"))
        latency = round((time.perf_counter() - start) * 1000)
        return HealthResponse(
            status="healthy",
            components={
                "database": {
                    "status": "healthy",
                    "latency_ms": latency,
                },
            },
            timestamp=ts,
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            components={
                "database": {
                    "status": "unhealthy",
                    "error": str(e),
                },
            },
            timestamp=ts,
        )
