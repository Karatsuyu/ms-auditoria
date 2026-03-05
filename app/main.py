# =============================================================================
# ms-auditoria | main.py
# =============================================================================
# Punto de entrada de la aplicación FastAPI ASYNC.
# Configura middleware, rutas, eventos de startup/shutdown y documentación.
# =============================================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import RequestIDMiddleware
from app.core.rate_limiter import RateLimitMiddleware
from app.core.exception_handlers import register_exception_handlers
from app.routes.audit_routes import (
    log_router,
    retention_router,
    stats_router,
    system_router,
)
from app.database.base import Base
from app.database.connection import sync_engine, async_engine
from app.services.retention_service import retention_scheduler
from app.services.statistics_service import statistics_scheduler
from app.utils.logger import logger

# Importar modelos para que SQLAlchemy los registre
from app.models import AuditLog, MicroserviceToken, RetentionConfig, ServiceStatistics  # noqa: F401


# ── Lifecycle Events ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de inicio y cierre del microservicio."""
    # Startup
    logger.info("ms-auditoria starting up", extra={"env": settings.APP_ENV})

    # Crear tablas si no existen (solo en desarrollo, usa sync_engine)
    if settings.APP_ENV == "development":
        try:
            Base.metadata.create_all(bind=sync_engine)
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.warning(
                "Could not create tables on startup",
                extra={"error": str(e)},
            )

    # Iniciar schedulers en background
    await retention_scheduler.start()
    await statistics_scheduler.start()

    yield

    # Shutdown — detener schedulers y cerrar pool async
    await retention_scheduler.stop()
    await statistics_scheduler.stop()
    await async_engine.dispose()
    logger.info("ms-auditoria shutting down")


# ── Instancia FastAPI ─────────────────────────────────────────────────────────

app = FastAPI(
    title="ms-auditoria",
    description=(
        "Microservicio #19 del ERP Universitario.\n\n"
        "Responsable de registrar, almacenar y consultar eventos de auditoría "
        "generados por los 18+ microservicios del sistema.\n\n"
        "**Funcionalidades principales:**\n"
        "- Registro de eventos de auditoría individual y batch (POST → 202)\n"
        "- Trazabilidad distribuida por Request ID (GET)\n"
        "- Filtrado de logs por servicio y fechas (GET)\n"
        "- Configuración de retención y rotación (GET/PATCH/POST)\n"
        "- Estadísticas precalculadas por servicio y periodo (GET)\n"
        "- Health check para orquestadores (GET)\n"
        "- Auto-auditoría de todas las operaciones (AUD-RF-005)\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────

# CORS — configurado por entorno
_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if settings.APP_ENV == "development":
    _origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True if _origins != ["*"] else False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-ms", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# Rate Limiting
app.add_middleware(RateLimitMiddleware)

# Request-ID para trazabilidad (formato AUD-{ts}-{random})
app.add_middleware(RequestIDMiddleware)

# ── Exception Handlers ─────────────────────────────────────────────────────────

register_exception_handlers(app)

# ── Rutas ──────────────────────────────────────────────────────────────────────

app.include_router(log_router)
app.include_router(retention_router)
app.include_router(stats_router)
app.include_router(system_router)


# ── Root Endpoint (12. /) ──────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información del microservicio."""
    return {
        "microservicio": "ms-auditoria",
        "version": "1.0.0",
        "descripcion": "Microservicio de Auditoría y Logging del ERP Universitario",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
