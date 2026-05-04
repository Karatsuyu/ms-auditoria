# =============================================================================
# ms-auditoria | tests/test_integration_postgres.py
# =============================================================================
# Tests de integración contra PostgreSQL REAL.
# Se ejecutan SOLO cuando la variable TEST_POSTGRES_URL existe.
#
# Para ejecutar:
#   $env:TEST_POSTGRES_URL="postgresql+asyncpg://postgres:Ame@127.0.0.1:5432/ms_auditoria_test"
#   pytest tests/test_integration_postgres.py -v
# =============================================================================

import os
from datetime import datetime, timezone, timedelta

import pytest

# Skip TODOS los tests si no hay URL de PostgreSQL
pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_POSTGRES_URL"),
    reason="TEST_POSTGRES_URL not set — skipping PostgreSQL integration tests",
)

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import text

from app.database.base import Base
from app.models.audit_log import AuditLog
from app.models.retention_config import RetentionConfig
from app.models.service_statistics import ServiceStatistics
from app.models.microservice_token import MicroserviceToken  # noqa: F401
from app.models.repositories.audit_repository import AuditRepository
from app.models.repositories.retention_repository import RetentionRepository
from app.models.repositories.statistics_repository import StatisticsRepository
from app.models.services.audit_service import AuditService
from app.models.services.retention_service import RetentionService
from app.models.services.statistics_service import StatisticsService
from app.views.audit_schema import LogCreate


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def pg_engine():
    """Crea engine async contra PostgreSQL de test."""
    url = os.environ["TEST_POSTGRES_URL"]
    engine = create_async_engine(url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def pg_session(pg_engine):
    """Sesión async con rollback por test."""
    SessionLocal = async_sessionmaker(
        bind=pg_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with SessionLocal() as session:
        yield session
        # Limpiar datos
        await session.execute(text("DELETE FROM aud_eventos_log"))
        await session.execute(text("DELETE FROM aud_configuracion_retencion"))
        await session.execute(text("DELETE FROM aud_estadisticas_servicio"))
        await session.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_log(
    service_name: str = "ms-matriculas",
    functionality: str = "consultar_matriculas",
    method: str = "POST",
    response_code: int = 200,
    duration_ms: int = 150,
    request_id: str = "TEST-1709302000-abc123",
    user_id: str = "usr-0001-uuid-admin",
    detail: str = "Test operation",
) -> AuditLog:
    return AuditLog(
        request_id=request_id,
        fecha_hora=datetime.now(timezone.utc),
        microservicio=service_name,
        funcionalidad=functionality,
        metodo=method,
        codigo_respuesta=response_code,
        duracion_ms=duration_ms,
        usuario_id=user_id,
        detalle=detail,
    )


# ── Repository Tests ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestAuditRepositoryPostgres:
    """Tests de AuditRepository contra PostgreSQL real."""

    async def test_save_and_find_by_request_id(self, pg_session):
        repo = AuditRepository(pg_session)
        log = _make_log(request_id="TRACE-PG-001")
        pg_session.add(log)
        await pg_session.commit()

        results, total = await repo.find_by_request_id("TRACE-PG-001")
        assert total == 1
        assert results[0].microservicio == "ms-matriculas"

    async def test_find_filtered_by_service(self, pg_session):
        repo = AuditRepository(pg_session)
        for svc in ["ms-reservas", "ms-reservas", "ms-matriculas"]:
            pg_session.add(_make_log(service_name=svc))
        await pg_session.commit()

        results, total = await repo.find_filtered(service_name="ms-reservas")
        assert total == 2

    async def test_delete_before(self, pg_session):
        repo = AuditRepository(pg_session)
        old_log = _make_log()
        old_log.fecha_hora = datetime.now(timezone.utc) - timedelta(days=100)
        pg_session.add(old_log)

        new_log = _make_log()
        new_log.fecha_hora = datetime.now(timezone.utc)
        pg_session.add(new_log)
        await pg_session.commit()

        cutoff = datetime.now(timezone.utc) - timedelta(days=50)
        deleted = await repo.delete_before(cutoff)
        await pg_session.commit()
        assert deleted >= 1


@pytest.mark.asyncio
class TestRetentionRepositoryPostgres:
    """Tests de RetentionRepository contra PostgreSQL real."""

    async def test_get_active_config(self, pg_session):
        config = RetentionConfig(
            dias_retencion=30,
            estado="activo",
        )
        pg_session.add(config)
        await pg_session.commit()

        repo = RetentionRepository(pg_session)
        active = await repo.get_active()
        assert active is not None
        assert active.dias_retencion == 30


@pytest.mark.asyncio
class TestStatisticsRepositoryPostgres:
    """Tests de StatisticsRepository contra PostgreSQL real."""

    async def test_find_by_period(self, pg_session):
        from datetime import date as date_type

        stat = ServiceStatistics(
            microservicio="ms-test",
            periodo="diario",
            fecha=date_type(2026, 2, 15),
            total_peticiones=100,
            total_errores=5,
            tiempo_promedio_ms=50.0,
            funcionalidad_top="test_op",
            fecha_calculo=datetime.now(timezone.utc),
        )
        pg_session.add(stat)
        await pg_session.commit()

        repo = StatisticsRepository(pg_session)
        results, total = await repo.find_by_period("diario")
        assert total >= 1


# ── Service Tests ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestRetentionServicePostgres:
    """Tests de RetentionService contra PostgreSQL real."""

    async def test_rotate_deletes_old_records(self, pg_session):
        # Insert config
        config = RetentionConfig(dias_retencion=30, estado="activo")
        pg_session.add(config)

        # Insert old log (40 days ago)
        old_log = _make_log()
        old_log.fecha_hora = datetime.now(timezone.utc) - timedelta(days=40)
        pg_session.add(old_log)

        # Insert recent log (1 day ago)
        new_log = _make_log()
        new_log.fecha_hora = datetime.now(timezone.utc) - timedelta(days=1)
        pg_session.add(new_log)
        await pg_session.commit()

        service = RetentionService(pg_session)
        result = await service.rotate()
        assert result["deleted_count"] >= 1
        assert result["retention_days_applied"] == 30


@pytest.mark.asyncio
class TestCheckConstraints:
    """Verifica que las CHECK constraints de PostgreSQL funcionan."""

    async def test_invalid_method_rejected(self, pg_session):
        """Método HTTP inválido debe ser rechazado por CHECK constraint."""
        log = _make_log(method="INVALID")
        pg_session.add(log)
        with pytest.raises(Exception):
            await pg_session.commit()
        await pg_session.rollback()

    async def test_invalid_response_code_rejected(self, pg_session):
        """Código de respuesta fuera de rango 100-599."""
        log = _make_log(response_code=999)
        pg_session.add(log)
        with pytest.raises(Exception):
            await pg_session.commit()
        await pg_session.rollback()

    async def test_negative_duration_rejected(self, pg_session):
        """Duración negativa rechazada por CHECK constraint."""
        log = _make_log(duration_ms=-1)
        pg_session.add(log)
        with pytest.raises(Exception):
            await pg_session.commit()
        await pg_session.rollback()
