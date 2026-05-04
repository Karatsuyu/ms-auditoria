# =============================================================================
# ms-auditoria | services/self_audit_service.py
# =============================================================================
# Servicio de auto-auditoría (AUD-RF-005).
# Registra las operaciones propias de ms-auditoria como logs de auditoría,
# ejecutando la persistencia en background (asyncio.create_task) para no
# bloquear la respuesta al cliente.
#
# IMPORTANTE: NO genera auto-auditoría para:
#   - Health check (AUD-RF-017) — evitar ruido
#   - La propia operación de auto-auditoría — evitar bucle infinito
# =============================================================================

import asyncio
from datetime import datetime, timezone

from app.database.session import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.utils.logger import logger


async def _persist_self_audit(
    request_id: str,
    funcionalidad: str,
    metodo: str,
    codigo_respuesta: int,
    duracion_ms: int,
    usuario_id: str | None = None,
    detalle: str | None = None,
) -> None:
    """
    Persiste un registro de auto-auditoría en su propia sesión de BD.
    Diseñado para ejecutarse como tarea asíncrona en background.
    Los errores se registran en el logger pero NO propagan excepciones.
    """
    try:
        async with AsyncSessionLocal() as session:
            log = AuditLog(
                request_id=request_id,
                fecha_hora=datetime.now(timezone.utc),
                microservicio="ms-auditoria",
                funcionalidad=funcionalidad,
                metodo=metodo,
                codigo_respuesta=codigo_respuesta,
                duracion_ms=duracion_ms,
                usuario_id=usuario_id,
                detalle=detalle,
            )
            session.add(log)
            await session.commit()
    except Exception as e:
        logger.error(
            "self_audit_error",
            extra={
                "funcionalidad": funcionalidad,
                "error": str(e),
            },
        )


def fire_self_audit(
    request_id: str,
    funcionalidad: str,
    metodo: str,
    codigo_respuesta: int,
    duracion_ms: int,
    usuario_id: str | None = None,
    detalle: str | None = None,
) -> None:
    """
    Despacha la persistencia de auto-auditoría en background.
    Usa asyncio.create_task — no bloquea la respuesta al cliente.
    Seguro de llamar desde cualquier coroutine activa.
    """
    try:
        asyncio.create_task(
            _persist_self_audit(
                request_id=request_id,
                funcionalidad=funcionalidad,
                metodo=metodo,
                codigo_respuesta=codigo_respuesta,
                duracion_ms=duracion_ms,
                usuario_id=usuario_id,
                detalle=detalle,
            )
        )
    except RuntimeError:
        # No hay event loop activo (eg. en tests sin async context)
        logger.warning("self_audit_no_event_loop")
