# =============================================================================
# ms-auditoria | tests/test_integration_postgres.py
# =============================================================================
# Tests de integración contra PostgreSQL REAL.
# Estos tests se ejecutan SOLO cuando la variable TEST_POSTGRES_URL existe.
# Usa una base de datos separada (ms_auditoria_test) para no afectar dev.
#
# Para ejecutar:
#   TEST_POSTGRES_URL=postgresql+asyncpg://postgres:Ame@127.0.0.1:5432/ms_auditoria_test \
#   pytest tests/test_integration_postgres.py -v
# =============================================================================

import os
import uuid
from datetime import datetime, timezone

import pytest

# Skip TODOS los tests si no hay URL de PostgreSQL definida
pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_POSTGRES_URL"),
    reason="TEST_POSTGRES_URL not set — skipping PostgreSQL integration tests",
)

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

from app.database.base import Base
from app.models.audit_log import AuditLog
from app.models.microservice_token import MicroserviceToken  # noqa: F401
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.services.statistics_service import StatisticsService
from app.schemas.audit_schema import AuditLogCreate


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="module")
async def pg_engine():
    """Crea engine async contra PostgreSQL de test."""
    url = os.environ["TEST_POSTGRES_URL"]
    engine = create_async_engine(url, echo=False)

    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Limpiar tablas al finalizar
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def pg_session(pg_engine):
    """Provee una sesión async contra PostgreSQL con rollback por test."""
    SessionLocal = async_sessionmaker(
        bind=pg_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with SessionLocal() as session:
        yield session
        # Limpiar datos del test
        await session.execute(text("DELETE FROM audit_logs"))
        await session.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_log(
    servicio: str = "ms-matriculas",
    endpoint: str = "/api/v1/test",
    metodo: str = "POST",
    codigo: int = 200,
    duracion: int = 100,
) -> AuditLogCreate:
    return AuditLogCreate(
        timestamp=datetime.now(timezone.utc),
        nombre_microservicio=servicio,
        endpoint=endpoint,
        metodo_http=metodo,
        codigo_respuesta=codigo,
        duracion_ms=duracion,
        usuario_id=uuid.uuid4(),
        ip_origen="10.0.0.1",
        request_id=str(uuid.uuid4()),
    )


# ── Tests de Repository (acceso directo a PostgreSQL) ─────────────────────────

class TestPostgresRepository:
    """Tests del repositorio contra PostgreSQL real."""

    @pytest.mark.asyncio
    async def test_save_and_find_by_id(self, pg_session):
        repo = AuditRepository(pg_session)
        log = AuditLog(
            request_id="pg-req-001",
            servicio="ms-matriculas",
            endpoint="/api/v1/test",
            metodo="POST",
            codigo_respuesta=201,
            duracion_ms=150,
            timestamp_evento=datetime.now(timezone.utc),
        )
        saved = await repo.save(log)
        await pg_session.commit()

        found = await repo.find_by_id(saved.id)
        assert found is not None
        assert found.servicio == "ms-matriculas"
        assert found.codigo_respuesta == 201

    @pytest.mark.asyncio
    async def test_save_batch_postgresql(self, pg_session):
        repo = AuditRepository(pg_session)
        logs = [
            AuditLog(
                request_id=f"pg-batch-{i}",
                servicio="ms-pagos",
                endpoint="/api/v1/pagos",
                metodo="POST",
                codigo_respuesta=201,
                duracion_ms=50 + i,
                timestamp_evento=datetime.now(timezone.utc),
            )
            for i in range(10)
        ]
        saved = await repo.save_batch(logs)
        await pg_session.commit()
        assert len(saved) == 10

    @pytest.mark.asyncio
    async def test_find_all_with_filters(self, pg_session):
        repo = AuditRepository(pg_session)
        for svc in ["ms-pagos", "ms-pagos", "ms-matriculas"]:
            log = AuditLog(
                request_id=str(uuid.uuid4()),
                servicio=svc,
                endpoint="/api/v1/test",
                metodo="GET",
                codigo_respuesta=200,
                duracion_ms=50,
                timestamp_evento=datetime.now(timezone.utc),
            )
            await repo.save(log)
        await pg_session.commit()

        results, total = await repo.find_all(servicio="ms-pagos")
        assert total == 2
        assert all(r.servicio == "ms-pagos" for r in results)

    @pytest.mark.asyncio
    async def test_count_by_servicio(self, pg_session):
        repo = AuditRepository(pg_session)
        for svc in ["ms-a", "ms-a", "ms-b"]:
            log = AuditLog(
                request_id=str(uuid.uuid4()),
                servicio=svc,
                endpoint="/test",
                metodo="GET",
                codigo_respuesta=200,
                duracion_ms=10,
                timestamp_evento=datetime.now(timezone.utc),
            )
            await repo.save(log)
        await pg_session.commit()

        counts = await repo.count_by_servicio()
        assert len(counts) >= 2

    @pytest.mark.asyncio
    async def test_fulltext_search_detalle(self, pg_session):
        """Verifica que la búsqueda full-text GIN funciona en PostgreSQL."""
        repo = AuditRepository(pg_session)
        log = AuditLog(
            request_id="pg-ft-001",
            servicio="ms-matriculas",
            endpoint="/api/v1/inscribir",
            metodo="POST",
            codigo_respuesta=201,
            duracion_ms=100,
            detalle='{"carrera": "Ingeniería de Sistemas", "semestre": "2026-I"}',
            timestamp_evento=datetime.now(timezone.utc),
        )
        await repo.save(log)
        await pg_session.commit()

        # Búsqueda full-text debe encontrar por "Ingeniería"
        results, total = await repo.find_all(search_text="Ingeniería")
        assert total >= 1

    @pytest.mark.asyncio
    async def test_delete_before(self, pg_session):
        repo = AuditRepository(pg_session)
        old_log = AuditLog(
            request_id="pg-old-001",
            servicio="ms-test",
            endpoint="/old",
            metodo="GET",
            codigo_respuesta=200,
            duracion_ms=10,
            timestamp_evento=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        new_log = AuditLog(
            request_id="pg-new-001",
            servicio="ms-test",
            endpoint="/new",
            metodo="GET",
            codigo_respuesta=200,
            duracion_ms=10,
            timestamp_evento=datetime.now(timezone.utc),
        )
        await repo.save(old_log)
        await repo.save(new_log)
        await pg_session.commit()

        deleted = await repo.delete_before(datetime(2023, 1, 1, tzinfo=timezone.utc))
        await pg_session.commit()
        assert deleted == 1

        total = await repo.count_total()
        assert total == 1


# ── Tests de Service (lógica de negocio contra PostgreSQL) ────────────────────

class TestPostgresService:
    """Tests del servicio contra PostgreSQL real."""

    @pytest.mark.asyncio
    async def test_create_log_service(self, pg_session):
        service = AuditService(pg_session)
        data = _make_log(servicio="ms-calificaciones")
        result = await service.create_log(data)
        assert result.servicio == "ms-calificaciones"
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_create_batch_service(self, pg_session):
        service = AuditService(pg_session)
        logs = [_make_log(servicio=f"ms-svc-{i}") for i in range(5)]
        results = await service.create_logs_batch(logs)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_get_logs_paginated(self, pg_session):
        service = AuditService(pg_session)
        for i in range(15):
            await service.create_log(_make_log())

        result = await service.get_logs(page=1, page_size=10)
        assert result.total == 15
        assert len(result.data) == 10
        assert result.total_pages == 2

    @pytest.mark.asyncio
    async def test_statistics_service(self, pg_session):
        service = AuditService(pg_session)
        for _ in range(3):
            await service.create_log(_make_log(servicio="ms-pagos", codigo=200))
        for _ in range(2):
            await service.create_log(_make_log(servicio="ms-pagos", codigo=500))

        stats_service = StatisticsService(pg_session)
        stats = await stats_service.get_general_stats()
        assert stats["total_registros"] == 5
        assert len(stats["logs_por_servicio"]) >= 1
        assert len(stats["tasa_errores_por_servicio"]) >= 1


# ── Tests de UUID nativo PostgreSQL ───────────────────────────────────────────

class TestPostgresUUID:
    """Verifica que el tipo GUID usa UUID nativo de PostgreSQL."""

    @pytest.mark.asyncio
    async def test_uuid_is_native_postgres(self, pg_session):
        """El id debe almacenarse como UUID nativo, no CHAR(36)."""
        result = await pg_session.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'audit_logs' AND column_name = 'id'"
            )
        )
        data_type = result.scalar()
        assert data_type == "uuid", f"Expected 'uuid' but got '{data_type}'"

    @pytest.mark.asyncio
    async def test_usuario_id_is_native_uuid(self, pg_session):
        result = await pg_session.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'audit_logs' AND column_name = 'usuario_id'"
            )
        )
        data_type = result.scalar()
        assert data_type == "uuid"
