# =============================================================================
# ms-auditoria | core/auth.py
# =============================================================================
# Autenticación inter-servicio basada en API Keys.
# Cada microservicio del ERP tiene un token registrado en la tabla
# microservice_tokens. Este módulo valida ese token en cada request de
# escritura (POST, DELETE) para garantizar que solo servicios autorizados
# puedan registrar o purgar logs de auditoría.
#
# Los endpoints de lectura (GET) no requieren API Key para permitir
# consultas desde dashboards y herramientas de monitoreo.
# =============================================================================

import hashlib
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.microservice_token import MicroserviceToken
from app.utils.logger import logger


def hash_api_key(api_key: str) -> str:
    """Genera el hash SHA-256 de una API key para comparar con la BD."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def verify_api_key(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Optional[MicroserviceToken]:
    """
    Dependencia que valida el API Key del microservicio emisor.
    Si APP_ENV == 'development' y no hay key, permite el paso (modo dev).
    En producción, el API Key es OBLIGATORIO.
    """
    # En desarrollo/testing, si no se envía API key, permitir acceso
    if not api_key:
        if settings.APP_ENV in ("development", "testing"):
            logger.debug("api_key_skipped_dev_mode")
            return None
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key requerida. Envíe el header X-API-Key.",
        )

    # Buscar token en la BD
    key_hash = hash_api_key(api_key)
    stmt = select(MicroserviceToken).where(
        MicroserviceToken.token_hash == key_hash,
        MicroserviceToken.activo == True,  # noqa: E712
    )
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()

    if not token_record:
        logger.warning(
            "invalid_api_key",
            extra={"key_prefix": api_key[:8] + "..." if len(api_key) > 8 else "***"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o microservicio desactivado.",
        )

    logger.info(
        "api_key_validated",
        extra={"microservicio": token_record.nombre_microservicio},
    )
    return token_record
