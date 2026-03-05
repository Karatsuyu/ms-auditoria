# =============================================================================
# ms-auditoria | core/auth.py
# =============================================================================
# Autenticación inter-servicio basada en tokens de aplicación.
# Cada microservicio del ERP tiene un token registrado en la tabla
# microservice_tokens. Este módulo valida ese token recibido en el header
# X-App-Token para los endpoints de ingesta (POST /logs, POST /logs/batch).
#
# Los endpoints de consulta (GET) usan Bearer token + sesión de usuario
# validada por ms-autenticación y ms-roles (gestionado en dependencies.py).
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


def hash_token(token: str) -> str:
    """Genera el hash SHA-256 de un token para comparar con la BD."""
    return hashlib.sha256(token.encode()).hexdigest()


async def verify_app_token(
    x_app_token: Optional[str] = Header(None, alias="X-App-Token"),
    db: AsyncSession = Depends(get_db),
) -> Optional[MicroserviceToken]:
    """
    Dependencia que valida el X-App-Token del microservicio emisor.
    Si APP_ENV == 'development' y no hay token, permite el paso (modo dev).
    En producción, el X-App-Token es OBLIGATORIO.
    """
    # En desarrollo/testing, si no se envía token, permitir acceso
    if not x_app_token:
        if settings.APP_ENV in ("development", "testing"):
            logger.debug("app_token_skipped_dev_mode")
            return None
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de aplicación inválido o no proporcionado.",
        )

    # Buscar token en la BD
    token_hash = hash_token(x_app_token)
    stmt = select(MicroserviceToken).where(
        MicroserviceToken.token_hash == token_hash,
        MicroserviceToken.activo == True,  # noqa: E712
    )
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()

    if not token_record:
        logger.warning(
            "invalid_app_token",
            extra={"token_prefix": x_app_token[:8] + "..." if len(x_app_token) > 8 else "***"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de aplicación inválido o no proporcionado.",
        )

    logger.info(
        "app_token_validated",
        extra={"microservicio": token_record.nombre_microservicio},
    )
    return token_record
