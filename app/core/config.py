# =============================================================================
# ms-auditoria | core/config.py
# =============================================================================
# Configuración centralizada del microservicio con soporte multi-entorno.
# Lee variables de entorno desde .env y las expone como un objeto tipado.
# Genera automáticamente la ASYNC_DATABASE_URL a partir de DATABASE_URL.
# =============================================================================

from pydantic_settings import BaseSettings
from pydantic import Field, computed_field


class Settings(BaseSettings):
    """Configuración global del microservicio ms-auditoria."""

    # ── Base de datos ──────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/ms_auditoria",
        description="URL de conexión SYNC a PostgreSQL (psycopg2)",
    )

    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """
        Genera la URL async automáticamente.
        postgresql://... → postgresql+asyncpg://...
        sqlite:///...    → sqlite+aiosqlite:///...
        """
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql+psycopg2://"):
            return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        if url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return url

    # ── Pool de conexiones ─────────────────────────────────────────────────
    DB_POOL_SIZE: int = Field(default=10, description="Conexiones activas en el pool")
    DB_MAX_OVERFLOW: int = Field(default=20, description="Conexiones extra bajo alta carga")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Reciclar conexiones cada N segundos")

    # ── Seguridad ──────────────────────────────────────────────────────────
    AES_SECRET_KEY: str = Field(
        description="Clave AES-256 en hexadecimal (64 caracteres)",
    )
    API_KEY_HEADER: str = Field(
        default="X-App-Token",
        description="Nombre del header para autenticación inter-servicio",
    )
    AUD_APP_TOKEN: str = Field(
        default="",
        description="Token de identidad de ms-auditoria para llamadas salientes a ms-autenticacion y ms-roles",
    )

    # ── CORS ───────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Orígenes permitidos separados por coma",
    )

    # ── Rate Limiting ──────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        description="Máximo de requests por ventana de tiempo",
    )
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=60,
        description="Ventana de tiempo en segundos para rate limiting",
    )

    # ── Retención automática (TTL) ─────────────────────────────────────────
    RETENTION_DAYS: int = Field(
        default=90,
        description="Días de retención de logs antes de purga automática",
    )
    RETENTION_CRON_HOUR: int = Field(
        default=3,
        description="Hora UTC en que se ejecuta la purga automática (0-23)",
    )

    # ── URLs de microservicios externos ────────────────────────────────────
    MS_AUTENTICACION_URL: str = Field(
        default="http://localhost:8001/api/v1",
        description="URL base del ms-autenticación (sin trailing slash)",
    )
    MS_ROLES_URL: str = Field(
        default="http://localhost:8002/api/v1",
        description="URL base del ms-roles-permisos (sin trailing slash)",
    )

    # ── Servidor ───────────────────────────────────────────────────────────
    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8019)
    APP_ENV: str = Field(default="development")
    APP_DEBUG: bool = Field(default=False)

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = Field(default="INFO")

    # ── Paginación ─────────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = Field(default=20)
    MAX_PAGE_SIZE: int = Field(default=100)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
