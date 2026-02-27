# =============================================================================
# ms-auditoria | database/session.py
# =============================================================================
# Fábrica de sesiones ASYNC de base de datos.
# Cada request obtiene su propia AsyncSession vía Dependency Injection.
# =============================================================================

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.database.connection import async_engine

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
