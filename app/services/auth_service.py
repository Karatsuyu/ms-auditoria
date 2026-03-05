# =============================================================================
# ms-auditoria | services/auth_service.py
# =============================================================================
# Servicio de comunicación con ms-autenticación y ms-roles-permisos.
#
# Contratos según AUD-diseno-integracion.md §3:
#   - Validar sesión: GET {MS_AUTENTICACION_URL}/sessions/validate
#     Headers: Authorization: Bearer {session_token}
#              X-App-Token: {AUD_APP_TOKEN cifrado}
#              X-Request-ID: {request_id}
#     Timeout: 3 s
#
#   - Verificar permiso: GET {MS_ROLES_URL}/permissions/check
#     Query params: user_id, functionality_code
#     Headers: X-App-Token: {AUD_APP_TOKEN cifrado}
#              X-Request-ID: {request_id}
#     Timeout: 3 s
# =============================================================================

from typing import Optional

import httpx

from app.core.config import settings
from app.utils.logger import logger

# Timeout según especificación: 3 segundos
_TIMEOUT = httpx.Timeout(3.0, connect=3.0)


class ExternalServiceUnavailable(Exception):
    """Raised when ms-autenticacion or ms-roles is unreachable/times out."""
    def __init__(self, service_name: str, detail: str):
        self.service_name = service_name
        self.detail = detail
        super().__init__(detail)


async def validate_session(
    token: str,
    request_id: str = "",
) -> Optional[dict]:
    """
    Valida un token de sesión contra ms-autenticación.
    GET /api/v1/sessions/validate
    Retorna los datos del usuario si es válido, None si no.
    """
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Request-ID": request_id,
            "Content-Type": "application/json",
        }
        # Si tenemos AUD_APP_TOKEN configurado, incluirlo
        app_token = getattr(settings, "AUD_APP_TOKEN", None)
        if app_token:
            headers["X-App-Token"] = app_token

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{settings.MS_AUTENTICACION_URL}/sessions/validate",
                headers=headers,
            )

        if response.status_code == 200:
            body = response.json()
            # El contrato retorna: {success, data: {valid, user_id, expires_at}, ...}
            data = body.get("data", body)
            user_id = data.get("user_id")
            logger.info(
                "session_validated",
                extra={"user_id": user_id, "request_id": request_id},
            )
            return data

        logger.warning(
            "session_validation_failed",
            extra={
                "status_code": response.status_code,
                "request_id": request_id,
            },
        )
        return None

    except httpx.TimeoutException:
        logger.error(
            "auth_service_timeout",
            extra={"request_id": request_id, "timeout_seconds": 3},
        )
        raise ExternalServiceUnavailable(
            service_name="ms-autenticacion",
            detail="Servicio de autenticación no disponible.",
        )
    except httpx.RequestError as exc:
        logger.error(
            "auth_service_unavailable",
            extra={"error": str(exc), "request_id": request_id},
        )
        raise ExternalServiceUnavailable(
            service_name="ms-autenticacion",
            detail="Servicio de autenticación no disponible.",
        )


async def check_permission(
    user_id: str,
    functionality_code: str,
    request_id: str = "",
) -> bool:
    """
    Verifica si el usuario tiene un permiso específico consultando ms-roles.
    GET /api/v1/permissions/check?user_id={user_id}&functionality_code={code}
    """
    try:
        headers = {
            "X-Request-ID": request_id,
            "Content-Type": "application/json",
        }
        app_token = getattr(settings, "AUD_APP_TOKEN", None)
        if app_token:
            headers["X-App-Token"] = app_token

        params = {
            "user_id": user_id,
            "functionality_code": functionality_code,
        }

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{settings.MS_ROLES_URL}/permissions/check",
                headers=headers,
                params=params,
            )

        if response.status_code == 200:
            body = response.json()
            data = body.get("data", body)
            authorized = data.get("authorized", False)
            logger.info(
                "permission_checked",
                extra={
                    "user_id": user_id,
                    "functionality_code": functionality_code,
                    "authorized": authorized,
                    "request_id": request_id,
                },
            )
            return authorized

        logger.warning(
            "permission_denied",
            extra={
                "user_id": user_id,
                "functionality_code": functionality_code,
                "status_code": response.status_code,
                "request_id": request_id,
            },
        )
        return False

    except httpx.TimeoutException:
        logger.error(
            "roles_service_timeout",
            extra={"request_id": request_id, "timeout_seconds": 3},
        )
        raise ExternalServiceUnavailable(
            service_name="ms-roles",
            detail="Servicio de roles no disponible.",
        )
    except httpx.RequestError as exc:
        logger.error(
            "roles_service_unavailable",
            extra={"error": str(exc), "request_id": request_id},
        )
        raise ExternalServiceUnavailable(
            service_name="ms-roles",
            detail="Servicio de roles no disponible.",
        )
