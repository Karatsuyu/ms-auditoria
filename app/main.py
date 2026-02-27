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
from app.routes.audit_routes import router as audit_router
from app.database.base import Base
from app.database.connection import sync_engine, async_engine
from app.services.retention_service import retention_service
from app.utils.logger import logger

# Importar modelos para que SQLAlchemy los registre
from app.models import AuditLog, MicroserviceToken  # noqa: F401


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

    # Iniciar scheduler de retención automática (TTL)
    await retention_service.start()

    yield

    # Shutdown — detener scheduler y cerrar pool async
    await retention_service.stop()
    await async_engine.dispose()
    logger.info("ms-auditoria shutting down")


# ── Instancia FastAPI ─────────────────────────────────────────────────────────

app = FastAPI(
    title="ms-auditoria",
    description=(
        "Microservicio #19 del ERP Universitario.\n\n"
        "Responsable de registrar, almacenar y consultar eventos de auditoría "
        "generados por los 18 microservicios del sistema.\n\n"
        "**Funcionalidades principales:**\n"
        "- Registro de eventos de auditoría (POST)\n"
        "- Registro en batch para alto volumen (POST)\n"
        "- Consulta con filtros avanzados y paginación (GET)\n"
        "- Trazabilidad por X-Request-ID (GET)\n"
        "- Historial de acciones por usuario (GET)\n"
        "- Estadísticas y métricas (GET)\n"
        "- Purga de logs antiguos (DELETE)\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────

# CORS — configurado por entorno (orígenes específicos)
_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if settings.APP_ENV == "development":
    # En desarrollo, permitir todos los orígenes para facilitar testing
    _origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True if _origins != ["*"] else False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-ms", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# Rate Limiting — protección contra abuso de requests
app.add_middleware(RateLimitMiddleware)

# Request-ID para trazabilidad entre microservicios
app.add_middleware(RequestIDMiddleware)

# ── Exception Handlers ─────────────────────────────────────────────────────────

register_exception_handlers(app)

# ── Rutas ──────────────────────────────────────────────────────────────────────

app.include_router(audit_router)


# ── Root Endpoint ──────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información del microservicio."""
    return {
        "microservicio": "ms-auditoria",
        "version": "1.0.0",
        "descripcion": "Microservicio de Auditoría y Logging del ERP Universitario",
        "docs": "/docs",
        "health": "/api/v1/audit/health",
    }
