# =============================================================================
# ms-auditoria | tests/conftest.py
# =============================================================================
# Configuración de pytest: fixtures globales para testing ASYNC.
# Usa SQLite + aiosqlite en memoria para tests rápidos sin PostgreSQL.
# =============================================================================

import os

# Establecer variables de entorno ANTES de importar la app
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["AES_SECRET_KEY"] = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
os.environ["MS_AUTENTICACION_URL"] = "http://localhost:8001/api/v1/auth"
os.environ["MS_ROLES_URL"] = "http://localhost:8002/api/v1/roles"
os.environ["APP_ENV"] = "testing"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.core.dependencies import get_db


# ── Base de datos SQLite ASYNC para tests ──────────────────────────────────────

SQLALCHEMY_TEST_ASYNC_URL = "sqlite+aiosqlite:///./test.db"
SQLALCHEMY_TEST_SYNC_URL = "sqlite:///./test.db"

# Engine sync solo para create_all / drop_all (DDL no es async en SQLite)
_sync_test_engine = create_engine(
    SQLALCHEMY_TEST_SYNC_URL,
    connect_args={"check_same_thread": False},
)

# Engine async para las sesiones de test
_async_test_engine = create_async_engine(
    SQLALCHEMY_TEST_ASYNC_URL,
    connect_args={"check_same_thread": False},
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=_async_test_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="function")
def db_session():
    """Crea tablas limpias para cada test (DDL sync, sesión async inyectada)."""
    from app.models import AuditLog, MicroserviceToken  # noqa: F401

    Base.metadata.create_all(bind=_sync_test_engine)
    yield  # el override usa TestAsyncSessionLocal directamente
    Base.metadata.drop_all(bind=_sync_test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Cliente HTTP de prueba con BD async inyectada."""
    from app.main import app

    async def _override_get_db():
        async with TestAsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
