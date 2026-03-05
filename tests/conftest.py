# =============================================================================
# ms-auditoria | tests/conftest.py
# =============================================================================
# Configuración de pytest: fixtures globales para testing ASYNC.
# Usa SQLite + aiosqlite en memoria para tests rápidos sin PostgreSQL.
#
# NOTE: SQLite no soporta CheckConstraint, TIMESTAMP(timezone=True), ni
# partial indexes, pero es suficiente para tests unitarios de lógica.
# =============================================================================

import os

# Establecer variables de entorno ANTES de importar la app
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["AES_SECRET_KEY"] = (
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
)
os.environ["MS_AUTENTICACION_URL"] = "http://localhost:8001/api/v1"
os.environ["MS_ROLES_URL"] = "http://localhost:8002/api/v1"
os.environ["APP_ENV"] = "testing"
os.environ["AUD_APP_TOKEN"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from app.database.base import Base
from app.core.dependencies import get_db


# ── Base de datos SQLite ASYNC para tests ──────────────────────────────────────

SQLALCHEMY_TEST_ASYNC_URL = "sqlite+aiosqlite:///./test.db"
SQLALCHEMY_TEST_SYNC_URL = "sqlite:///./test.db"

# Engine sync para DDL (create_all / drop_all)
_sync_test_engine = create_engine(
    SQLALCHEMY_TEST_SYNC_URL,
    connect_args={"check_same_thread": False},
)

# Engine async para sesiones de test
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
    # Importar TODOS los modelos para que Base.metadata los conozca
    from app.models import (  # noqa: F401
        AuditLog,
        MicroserviceToken,
        RetentionConfig,
        ServiceStatistics,
    )

    Base.metadata.create_all(bind=_sync_test_engine)
    yield
    Base.metadata.drop_all(bind=_sync_test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Cliente HTTP de prueba con BD async inyectada.
    APP_ENV=testing por lo que:
      - verify_app_token permite requests sin X-App-Token
      - get_current_user retorna mock user (skip ms-autenticacion)
      - require_permission retorna user sin check (skip ms-roles)
    """
    from app.main import app

    async def _override_get_db():
        async with TestAsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict:
    """Headers para endpoints que requieren sesión de usuario."""
    return {"Authorization": "Bearer test-session-token"}


@pytest.fixture
def app_token_headers() -> dict:
    """Headers para endpoints que requieren token de aplicación."""
    return {"X-App-Token": "dev-test-token"}


@pytest.fixture
def sample_log() -> dict:
    """Payload de ejemplo para POST /api/v1/logs."""
    from datetime import datetime, timezone

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": "RES-1709302000-xyz789",
        "service_name": "ms-reservas",
        "functionality": "crear_reserva",
        "method": "POST",
        "response_code": 201,
        "duration_ms": 312,
        "user_id": "usr-0002-uuid-docente",
        "detail": "Reserva creada para espacio A-101.",
    }


@pytest.fixture
def sample_batch_logs() -> dict:
    """Payload de ejemplo para POST /api/v1/logs/batch."""
    from datetime import datetime, timezone

    return {
        "logs": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": f"MAT-1709302000-00{i}",
                "service_name": "ms-matriculas",
                "functionality": "consultar_matriculas",
                "method": "GET",
                "response_code": 200,
                "duration_ms": 95 + i * 10,
                "user_id": "usr-0001-uuid-admin",
                "detail": f"Consulta de matrículas, operación {i}.",
            }
            for i in range(1, 4)
        ]
    }
