# =============================================================================
# ms-auditoria | services/auth_service.py
# =============================================================================
# Servicio de comunicación con ms-autenticación y ms-roles-permisos.
# Valida tokens de sesión de usuarios y verifica permisos.
# =============================================================================

from typing import Optional

import httpx

from app.core.config import settings
from app.utils.logger import logger


async def validate_session(token: str) -> Optional[dict]:
    """
    Valida un token de sesión contra ms-autenticación.
    Retorna los datos del usuario si es válido, None si no.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.MS_AUTENTICACION_URL}/validate",
                json={"token": token},
                headers={"Content-Type": "application/json"},
            )

        if response.status_code == 200:
            data = response.json()
            logger.info(
                "session_validated",
                extra={"user_id": data.get("user_id")},
            )
            return data

        logger.warning(
            "session_validation_failed",
            extra={"status_code": response.status_code},
        )
        return None

    except httpx.RequestError as exc:
        logger.error(
            "auth_service_unavailable",
            extra={"error": str(exc)},
        )
        return None


async def check_permission(token: str, permiso: str) -> bool:
    """
    Verifica si el usuario tiene un permiso específico consultando ms-roles-permisos.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.MS_ROLES_URL}/check-permission",
                json={"token": token, "permiso": permiso},
                headers={"Content-Type": "application/json"},
            )

        return response.status_code == 200 and response.json().get("authorized", False)

    except httpx.RequestError as exc:
        logger.error(
            "roles_service_unavailable",
            extra={"error": str(exc)},
        )
        return False
