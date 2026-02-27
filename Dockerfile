# =============================================================================
# ms-auditoria | Dockerfile
# =============================================================================
# Imagen Docker profesional multi-stage para producción.
# Stage 1: build  → instala dependencias en un layer separado
# Stage 2: runtime → imagen mínima con solo lo necesario
# =============================================================================

# ── Stage 1: Build ─────────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Instalar dependencias del sistema para compilar psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ───────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

LABEL maintainer="equipo-erp-universitario" \
      service="ms-auditoria" \
      version="1.0.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

WORKDIR /app

# Solo las libs de runtime necesarias (no gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias pre-compiladas desde el stage builder
COPY --from=builder /install /usr/local

# Copiar código fuente y Alembic
COPY alembic/ alembic/
COPY alembic.ini .
COPY app/ app/
COPY .env.production .env

# Crear usuario no-root por seguridad
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

# Puerto del microservicio
EXPOSE 8019

# Health check integrado
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8019/api/v1/audit/health || exit 1

# Comando de ejecución: Alembic upgrade + Uvicorn
CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8019 --workers 4 --loop uvloop --http httptools"]
