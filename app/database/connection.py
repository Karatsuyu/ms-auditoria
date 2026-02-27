# =============================================================================
# ms-auditoria | database/connection.py
# =============================================================================
# Motor ASYNC de conexión a PostgreSQL con pool de conexiones optimizado.
# Usa SQLAlchemy 2.0 AsyncEngine para non-blocking I/O.
#
# También mantiene un engine SYNC para Alembic y operaciones que lo requieran.
# Detecta SQLite para deshabilitar opciones de pool no soportadas.
# =============================================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# ── Engine ASYNC (uso principal de la aplicación) ──────────────────────────────
if _is_sqlite:
    # SQLite: no soporta pool_size/max_overflow; usar StaticPool para async
    async_engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=settings.APP_DEBUG,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    async_engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
        echo=settings.APP_DEBUG,
    )

# ── Engine SYNC (solo para Alembic y create_all en development) ────────────────
if _is_sqlite:
    sync_engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.APP_DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    sync_engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        echo=settings.APP_DEBUG,
    )
