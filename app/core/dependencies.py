# =============================================================================
# ms-auditoria | core/dependencies.py
# =============================================================================
# Dependencias inyectables de FastAPI (Dependency Injection).
# - Sesión ASYNC de base de datos
# - Unit of Work
# - Validación de sesión + permisos con ms-autenticación y ms-roles
# =============================================================================

from typing import AsyncGenerator, Callable

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.database.unit_of_work import UnitOfWork
from app.services.auth_service import (
    validate_session,
    check_permission,
    ExternalServiceUnavailable,
)
from app.core.config import settings


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provee una AsyncSession de base de datos por request.
    Se cierra automáticamente al finalizar.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def get_uow() -> AsyncGenerator[UnitOfWork, None]:
    """
    Provee un Unit of Work por request.
    Gestiona transacciones atómicas con rollback automático en error.
    """
    async with UnitOfWork() as uow:
        yield uow


async def get_current_user(
    request: Request,
    authorization: str = Header(..., description="Bearer <session_token>"),
) -> dict:
    """
    Dependencia que valida el token de sesión contra ms-autenticación.
    Retorna los datos del usuario si el token es válido.
    Propaga el request_id al servicio de autenticación.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada.",
        )

    token = authorization.removeprefix("Bearer ").strip()
    request_id = getattr(request.state, "request_id", "")

    # En desarrollo/testing, retornar mock sin llamar al servicio externo
    if settings.APP_ENV in ("development", "testing"):
        return {
            "valid": True,
            "user_id": "dev-user-mock",
            "expires_at": None,
            "_session_token": token,
        }

    try:
        user_data = await validate_session(token, request_id=request_id)
    except ExternalServiceUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.detail,
        )
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada.",
        )

    # Guardar el token en user_data para uso posterior en check_permission
    user_data["_session_token"] = token
    return user_data


def require_permission(permission_code: str) -> Callable:
    """
    Factory que crea una dependencia que verifica un permiso específico.
    Uso: Depends(require_permission("AUD_CONSULTAR_LOGS"))
    """
    async def _check(
        request: Request,
        user: dict = Depends(get_current_user),
    ) -> dict:
        # En desarrollo/testing, skip permission check si no hay servicios externos
        if settings.APP_ENV in ("development", "testing"):
            return user

        request_id = getattr(request.state, "request_id", "")
        user_id = user.get("user_id") or user.get("data", {}).get("user_id")

        try:
            has_perm = await check_permission(
                user_id=user_id,
                functionality_code=permission_code,
                request_id=request_id,
            )
        except ExternalServiceUnavailable as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=exc.detail,
            )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permiso denegado para esta operación.",
            )
        return user

    return _check
