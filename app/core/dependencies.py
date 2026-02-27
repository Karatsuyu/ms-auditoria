# =============================================================================
# ms-auditoria | core/dependencies.py
# =============================================================================
# Dependencias inyectables de FastAPI (Dependency Injection).
# - Sesión ASYNC de base de datos
# - Unit of Work
# - Validación de token/sesión con ms-autenticación
# =============================================================================

from typing import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.database.unit_of_work import UnitOfWork
from app.services.auth_service import validate_session


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
    authorization: str = Header(..., description="Bearer <token>"),
):
    """
    Dependencia que valida el token de sesión contra ms-autenticación.
    Retorna los datos del usuario si el token es válido.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de autorización inválido. Use: Bearer <token>",
        )

    token = authorization.removeprefix("Bearer ").strip()

    user_data = await validate_session(token)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o sesión expirada",
        )

    return user_data
