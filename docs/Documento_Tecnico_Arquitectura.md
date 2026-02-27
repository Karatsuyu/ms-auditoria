# Documento Técnico de Arquitectura — ms-auditoria

## Microservicio #19: Auditoría y Logging del ERP Universitario

**Materia:** Desarrollo de Software 3  
**Tecnología:** FastAPI + SQLAlchemy 2.0 Async + PostgreSQL 16  
**Versión:** 1.0.0  
**Fecha:** Febrero 2026  
**Repositorio:** https://github.com/Karatsuyu/ms-auditoria

---

## Tabla de Contenidos

1. [Información General](#1-información-general)
2. [Descripción General del Sistema](#2-descripción-general-del-sistema)
3. [Arquitectura de Alto Nivel](#3-arquitectura-de-alto-nivel)
4. [Arquitectura Interna Detallada](#4-arquitectura-interna-detallada)
5. [Modelo de Datos](#5-modelo-de-datos)
6. [Seguridad](#6-seguridad)
7. [Concurrencia y Rendimiento](#7-concurrencia-y-rendimiento)
8. [Testing y CI/CD](#8-testing-y-cicd)
9. [DevOps y Despliegue](#9-devops-y-despliegue)
10. [Justificaciones Técnicas](#10-justificaciones-técnicas)

---

## 1. Información General

| Campo | Valor |
|-------|-------|
| **Nombre** | ms-auditoria |
| **Número** | Microservicio #19 |
| **Puerto** | 8019 |
| **Framework** | FastAPI 0.115.6 |
| **ORM** | SQLAlchemy 2.0.36 (100% async) |
| **Base de datos** | PostgreSQL 16 |
| **Driver async** | asyncpg 0.30.0 |
| **Validación** | Pydantic 2.10.3 + pydantic-settings 2.7.0 |
| **Migraciones** | Alembic 1.14.0 |
| **Servidor ASGI** | Uvicorn 0.34.0 |
| **Python** | 3.10 |
| **Lenguaje** | 100% Python, 100% async/await |

---

## 2. Descripción General del Sistema

### 2.1 Propósito

`ms-auditoria` es el microservicio centralizado de auditoría y logging del ERP Universitario. Es responsable de **registrar, almacenar, consultar y analizar** todos los eventos generados por los 18 microservicios restantes del sistema.

### 2.2 Responsabilidades

- **Recepción de eventos**: Recibe logs de auditoría vía HTTP REST desde cualquier microservicio autorizado.
- **Persistencia**: Almacena los eventos en PostgreSQL con modelo optimizado para consultas de alto volumen.
- **Consulta**: Proporciona endpoints con filtros avanzados, paginación y búsqueda full-text.
- **Trazabilidad**: Permite rastrear una petición a través de múltiples microservicios usando `X-Request-ID`.
- **Estadísticas**: Genera métricas (logs por servicio, tasa de errores, duración promedio).
- **Retención automática (TTL)**: Purga automática de logs antiguos configurable.
- **Seguridad**: Autenticación inter-servicio con API Keys, cifrado AES-256-GCM disponible para datos sensibles, rate limiting por IP.

### 2.3 Posición en el ERP

```
┌──────────────────────────────────────────────────────────────┐
│                     ERP UNIVERSITARIO                        │
│                                                              │
│  ms-autenticación ──┐                                        │
│  ms-roles ──────────┤                                        │
│  ms-usuarios ───────┤                                        │
│  ms-académica ──────┤     POST /api/v1/audit/log             │
│  ms-matrículas ─────┤────────────────────────►┌────────────┐ │
│  ms-calificaciones ─┤                         │ms-auditoria│ │
│  ms-horarios ───────┤  (X-API-Key + JSON)     │   :8019    │ │
│  ms-pagos ──────────┤                         │            │ │
│  ms-becas ──────────┤                         │ PostgreSQL │ │
│  ms-biblioteca ─────┤                         │   :5432    │ │
│  ... (18 total) ────┘                         └────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Arquitectura de Alto Nivel

### 3.1 Estilo Arquitectónico

El microservicio implementa una **arquitectura en capas (Clean Architecture)** con 4 capas bien definidas:

```
┌─────────────────────────────────────┐
│         ROUTES (Presentación)       │  ← audit_routes.py
│   FastAPI Router + Endpoints        │
├─────────────────────────────────────┤
│        SERVICES (Negocio)           │  ← audit_service.py, statistics_service.py
│   Lógica de negocio + orquestación  │
├─────────────────────────────────────┤
│      REPOSITORIES (Datos)           │  ← audit_repository.py
│   Consultas SQL async (select/func) │
├─────────────────────────────────────┤
│         MODELS (Dominio)            │  ← audit_log.py, microservice_token.py
│   ORM SQLAlchemy + Schemas Pydantic │
└─────────────────────────────────────┘
```

### 3.2 Patrones de Diseño Implementados

| Patrón | Implementación | Archivo(s) |
|--------|----------------|------------|
| **Repository Pattern** | `AuditRepository` abstrae todas las consultas SQL | `repositories/audit_repository.py` |
| **Unit of Work** | `UnitOfWork` disponible como infraestructura para transacciones atómicas complejas; los endpoints actuales usan `AsyncSession` directa con `commit()` por simplicidad | `database/unit_of_work.py` |
| **Dependency Injection** | FastAPI `Depends()` para sesiones de BD y autenticación | `core/dependencies.py` |
| **CQRS-like** | Separación de comandos (POST/DELETE) y queries (GET) | `routes/audit_routes.py` |
| **Middleware Chain** | Cadena de middlewares para cross-cutting concerns | `core/middleware.py`, `core/rate_limiter.py` |
| **Strategy Pattern** | `GUID` TypeDecorator adapta UUID entre PostgreSQL (nativo) y SQLite (CHAR) | `models/audit_log.py` |
| **Singleton** | Instancias únicas de `retention_service`, `aes_cipher`, `logger`, `settings` | Varios módulos |

### 3.3 Estructura del Proyecto

```
ms-auditoria/
├── app/
│   ├── core/                          # Configuración y cross-cutting concerns
│   │   ├── config.py                  # Pydantic Settings (multi-entorno)
│   │   ├── middleware.py              # X-Request-ID + response time
│   │   ├── rate_limiter.py            # Rate limiting por IP (sliding window)
│   │   ├── auth.py                    # Autenticación inter-servicio (API Keys)
│   │   ├── security.py               # AES-256-GCM cifrado
│   │   ├── dependencies.py           # FastAPI Dependency Injection
│   │   └── exception_handlers.py     # Manejadores globales de errores
│   ├── database/                      # Capa de acceso a datos
│   │   ├── base.py                    # SQLAlchemy DeclarativeBase
│   │   ├── connection.py              # AsyncEngine + SyncEngine
│   │   ├── session.py                 # AsyncSessionLocal factory
│   │   └── unit_of_work.py           # Patrón Unit of Work
│   ├── models/                        # Modelos ORM
│   │   ├── audit_log.py              # Tabla audit_logs (GUID cross-DB)
│   │   └── microservice_token.py     # Tabla microservice_tokens
│   ├── repositories/                  # Repository Pattern (async)
│   │   └── audit_repository.py
│   ├── schemas/                       # Pydantic v2 schemas
│   │   ├── audit_schema.py           # Create, Response, Filter
│   │   └── response_schema.py        # Respuestas genéricas estandarizadas
│   ├── services/                      # Lógica de negocio
│   │   ├── audit_service.py          # Servicio principal de auditoría
│   │   ├── statistics_service.py     # Estadísticas y métricas
│   │   ├── auth_service.py           # Comunicación con ms-autenticación
│   │   └── retention_service.py      # TTL / purga automática
│   ├── routes/
│   │   └── audit_routes.py           # 9 endpoints RESTful
│   ├── utils/
│   │   └── logger.py                 # JSON structured logging
│   └── main.py                        # Punto de entrada FastAPI
├── alembic/                           # Migraciones de BD
│   └── versions/
│       ├── fae4016df4b8_initial.py   # Schema inicial
│       └── b2a3c4d5e6f7_gin_index.py # Índice GIN full-text
├── tests/                             # 38 unit + 12 integration tests
├── .github/workflows/ci.yml          # CI/CD pipeline (4 jobs)
├── Dockerfile                         # Multi-stage build
├── docker-compose.yml                 # PostgreSQL 16 + App
└── requirements.txt
```

---

## 4. Arquitectura Interna Detallada

### 4.1 Flujo de una Petición (POST /api/v1/audit/log)

```
Cliente (ms-matriculas)
    │
    │  POST /api/v1/audit/log
    │  Headers: X-API-Key: <token>, X-Request-ID: <uuid>
    │  Body: { timestamp, nombre_microservicio, endpoint, ... }
    │
    ▼
┌─────────────────────────────────────┐
│  1. RequestIDMiddleware             │  Inyecta/propaga X-Request-ID
│     (core/middleware.py)            │  Mide tiempo con perf_counter
├─────────────────────────────────────┤
│  2. RateLimitMiddleware             │  Sliding window por IP
│     (core/rate_limiter.py)          │  429 si excede límite
├─────────────────────────────────────┤
│  3. CORSMiddleware                  │  Valida origen permitido
│     (Starlette built-in)            │
├─────────────────────────────────────┤
│  4. ExceptionHandlers               │  Captura errores globales
│     (core/exception_handlers.py)    │  HTTPException, Validation, 500
├─────────────────────────────────────┤
│  5. Route: create_audit_log()       │  Endpoint FastAPI
│     (routes/audit_routes.py)        │
│     - Depends(get_db) → AsyncSession│
│     - Depends(verify_api_key) → auth│
├─────────────────────────────────────┤
│  6. AuditService.create_log()       │  Lógica de negocio
│     (services/audit_service.py)     │  Mapea schema → ORM model
│     - detalle se persiste como texto│
├─────────────────────────────────────┤
│  7. AuditRepository.save()          │  Persistencia async
│     (repositories/audit_repository) │  session.add → flush → refresh
│     - await db.commit()             │
├─────────────────────────────────────┤
│  8. PostgreSQL 16                   │  INSERT en audit_logs
│     (asyncpg driver)                │  8 índices optimizados
└─────────────────────────────────────┘
    │
    ▼
Response 201 Created
Headers: X-Request-ID, X-Response-Time-ms, X-RateLimit-*
Body: { success: true, data: { id, servicio, ... } }
```

### 4.2 Endpoints Implementados (9 totales)

| # | Método | Ruta | Función | Auth | Descripción |
|---|--------|------|---------|------|-------------|
| 1 | GET | `/api/v1/audit/health` | `health_check` | No | Health check del servicio |
| 2 | POST | `/api/v1/audit/log` | `create_audit_log` | API Key | Registrar evento de auditoría |
| 3 | POST | `/api/v1/audit/log/batch` | `create_audit_logs_batch` | API Key | Registro masivo (máx 1000) |
| 4 | GET | `/api/v1/audit/logs` | `get_audit_logs` | No | Listar con filtros + paginación |
| 5 | GET | `/api/v1/audit/log/{audit_id}` | `get_audit_log_by_id` | No | Obtener log por UUID |
| 6 | GET | `/api/v1/audit/trace/{request_id}` | `trace_request` | No | Trazabilidad por X-Request-ID |
| 7 | GET | `/api/v1/audit/user/{usuario_id}` | `get_user_audit_logs` | No | Historial de un usuario |
| 8 | GET | `/api/v1/audit/stats` | `get_statistics` | No | Estadísticas generales |
| 9 | DELETE | `/api/v1/audit/purge` | `purge_logs` | API Key | Purgar logs antiguos |

Adicionalmente, existe un endpoint raíz `GET /` definido en `main.py` con información del microservicio.

### 4.3 Ejemplo del Endpoint Principal

```python
# routes/audit_routes.py — POST /api/v1/audit/log

@router.post(
    "/log",
    response_model=DataResponse[AuditLogResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar evento de auditoría",
)
async def create_audit_log(
    data: AuditLogCreate,
    db: AsyncSession = Depends(get_db),
    _api_key=Depends(verify_api_key),
):
    service = AuditService(db)
    result = await service.create_log(data)
    return DataResponse(
        success=True,
        message="Evento de auditoría registrado exitosamente",
        data=result,
    )
```

**Dependencias inyectadas:**
- `get_db`: Provee una `AsyncSession` por request, se cierra automáticamente al finalizar.
- `verify_api_key`: Valida el header `X-API-Key` contra la tabla `microservice_tokens` usando SHA-256. En `development`/`testing` permite acceso sin key.

### 4.4 Capa de Servicio — Mapeo Schema → ORM

```python
# services/audit_service.py

async def create_log(self, data: AuditLogCreate) -> AuditLogResponse:
    audit_log = AuditLog(
        request_id=data.request_id or str(uuid.uuid4()),
        servicio=data.nombre_microservicio,
        endpoint=data.endpoint,
        metodo=data.metodo_http,
        codigo_respuesta=data.codigo_respuesta,
        duracion_ms=data.duracion_ms,
        usuario_id=data.usuario_id,
        detalle=data.detalle,
        ip_origen=data.ip_origen,
        timestamp_evento=data.timestamp,
    )
    saved = await self.repo.save(audit_log)
    await self.db.commit()
    return AuditLogResponse.model_validate(saved)
```

**Nota sobre el campo `detalle`:** Se persiste como texto plano para permitir la búsqueda full-text con el índice GIN de PostgreSQL. El módulo `core/security.py` provee la clase `AESCipher` con cifrado AES-256-GCM disponible como utilidad si se requiere cifrar datos especialmente sensibles en el futuro, pero no se aplica automáticamente en el flujo de creación.

### 4.5 Cadena de Middleware

Los middlewares se registran en `main.py` en este orden:

```python
# main.py
app.add_middleware(CORSMiddleware, ...)       # Línea 94
app.add_middleware(RateLimitMiddleware)        # Línea 102
app.add_middleware(RequestIDMiddleware)        # Línea 105
```

Starlette ejecuta los middlewares en **orden inverso** al registro (LIFO). Por lo tanto, el orden de ejecución real para una petición entrante es:

```
Request entrante
    → RequestIDMiddleware  (inyecta X-Request-ID, mide tiempo)
    → RateLimitMiddleware  (sliding window por IP, 429 si excede)
    → CORSMiddleware       (valida origen, agrega headers CORS)
    → Endpoint
    → (respuesta sube por la misma cadena en orden inverso)
```

### 4.6 Exception Handlers Globales

Registrados en `core/exception_handlers.py` mediante `register_exception_handlers(app)`:

| Handler | Captura | Respuesta |
|---------|---------|-----------|
| `http_exception_handler` | `StarletteHTTPException` (4xx, 5xx conocidos) | JSON estandarizado con `success: false` |
| `validation_exception_handler` | `RequestValidationError` (Pydantic) | 422 con lista de errores por campo |
| `unhandled_exception_handler` | `Exception` genérica | 500 con detalle oculto en producción, visible en debug |

Formato de respuesta de error estandarizado:

```json
{
  "success": false,
  "error": "Descripción del tipo de error",
  "detail": "Detalle específico del error"
}
```

### 4.7 Servicio de Estadísticas

`StatisticsService` (en `services/statistics_service.py`) genera métricas consultando el repositorio:

| Métrica | Método del repositorio | Descripción |
|---------|----------------------|-------------|
| Total de registros | `count_total()` | COUNT total de audit_logs |
| Logs por servicio | `count_by_servicio()` | GROUP BY servicio, ORDER BY total DESC |
| Logs por código HTTP | `count_by_codigo_respuesta()` | GROUP BY codigo_respuesta |
| Duración promedio | `average_duration_by_servicio()` | AVG(duracion_ms) por servicio |
| Tasa de errores | `error_rate_by_servicio()` | % de códigos ≥400 por servicio |

### 4.8 Servicio de Retención Automática (TTL)

`RetentionService` (en `services/retention_service.py`) implementa purga automática:

- **Scheduler**: Loop con `asyncio.create_task()` — sin dependencias externas (no usa APScheduler ni Celery).
- **Ejecución**: Calcula segundos hasta `RETENTION_CRON_HOUR` (default: 03:00 UTC), duerme con `asyncio.sleep()`, ejecuta purga.
- **Purga**: `DELETE FROM audit_logs WHERE timestamp_evento < (now - RETENTION_DAYS)`.
- **Sesión propia**: Usa `AsyncSessionLocal()` independiente de los requests HTTP.
- **Lifecycle**: Se inicia en `lifespan` startup, se detiene en shutdown con `task.cancel()`.
- **Resiliencia**: En caso de error, espera 1 hora antes de reintentar.

---

## 5. Modelo de Datos

### 5.1 Diagrama Entidad-Relación

```
┌─────────────────────────────────────────────────┐
│                  audit_logs                      │
├─────────────────────────────────────────────────┤
│ PK  id                UUID          NOT NULL     │
│     request_id        VARCHAR(50)   NOT NULL     │
│     servicio          VARCHAR(50)   NOT NULL     │
│     endpoint          VARCHAR(200)  NOT NULL     │
│     metodo            VARCHAR(10)   NOT NULL     │
│     codigo_respuesta  INTEGER       NULLABLE     │
│     duracion_ms       INTEGER       NULLABLE     │
│     usuario_id        UUID          NULLABLE     │
│     detalle           TEXT          NULLABLE     │
│     ip_origen         VARCHAR(45)   NULLABLE     │
│     timestamp_evento  TIMESTAMP(tz) NOT NULL     │
│     created_at        TIMESTAMP(tz) NOT NULL     │
├─────────────────────────────────────────────────┤
│ Índices: 8 (4 simples + 3 compuestos + 1 GIN)  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              microservice_tokens                 │
├─────────────────────────────────────────────────┤
│ PK  id                    UUID          NOT NULL │
│ UQ  nombre_microservicio  VARCHAR(50)   NOT NULL │
│     token_hash            VARCHAR(256)  NOT NULL │
│     activo                BOOLEAN       NOT NULL │
│     created_at            TIMESTAMP(tz) NOT NULL │
│     updated_at            TIMESTAMP(tz) NOT NULL │
└─────────────────────────────────────────────────┘
```

### 5.2 Tabla `audit_logs` — Detalle de Columnas

| Columna | Tipo SQL | Tipo ORM | Nullable | Default | Comentario |
|---------|----------|----------|----------|---------|------------|
| `id` | UUID (PG) / CHAR(36) (SQLite) | `GUID()` custom | NOT NULL | `uuid.uuid4()` | Identificador único del registro |
| `request_id` | VARCHAR(50) | `String(50)` | NOT NULL | — | ID de trazabilidad (X-Request-ID) |
| `servicio` | VARCHAR(50) | `String(50)` | NOT NULL | — | Nombre del microservicio emisor |
| `endpoint` | VARCHAR(200) | `String(200)` | NOT NULL | — | Ruta del endpoint invocado |
| `metodo` | VARCHAR(10) | `String(10)` | NOT NULL | — | Método HTTP (GET, POST, PUT, DELETE, PATCH) |
| `codigo_respuesta` | INTEGER | `Integer` | NULLABLE | — | Código de respuesta HTTP |
| `duracion_ms` | INTEGER | `Integer` | NULLABLE | — | Duración del request en milisegundos |
| `usuario_id` | UUID / CHAR(36) | `GUID()` | NULLABLE | `None` | UUID del usuario (null si anónimo) |
| `detalle` | TEXT | `Text` | NULLABLE | `None` | Detalle adicional (JSON stringificado) |
| `ip_origen` | VARCHAR(45) | `String(45)` | NULLABLE | `None` | Dirección IP de origen (soporta IPv6) |
| `timestamp_evento` | TIMESTAMP WITH TZ | `TIMESTAMP(timezone=True)` | NOT NULL | — | Momento del evento en el microservicio origen |
| `created_at` | TIMESTAMP WITH TZ | `TIMESTAMP(timezone=True)` | NOT NULL | `datetime.now(UTC)` | Momento de registro en ms-auditoria |

**Nota sobre GUID:** El tipo `GUID` es un `TypeDecorator` custom que usa UUID nativo en PostgreSQL y CHAR(36) en SQLite, permitiendo que los unit tests funcionen con SQLite sin cambiar el modelo.

### 5.3 Tabla `microservice_tokens` — Detalle de Columnas

| Columna | Tipo SQL | Tipo ORM | Nullable | Default | Comentario |
|---------|----------|----------|----------|---------|------------|
| `id` | UUID / CHAR(36) | `GUID()` | NOT NULL | `uuid.uuid4()` | Identificador único del token |
| `nombre_microservicio` | VARCHAR(50) UNIQUE | `String(50)` | NOT NULL | — | Nombre del microservicio (ej: ms-matricula) |
| `token_hash` | VARCHAR(256) | `String(256)` | NOT NULL | — | Hash SHA-256 del API Key |
| `activo` | BOOLEAN | `Boolean` | NOT NULL | `True` | Si el microservicio está autorizado |
| `created_at` | TIMESTAMP WITH TZ | `TIMESTAMP(timezone=True)` | NOT NULL | `datetime.now(UTC)` | Fecha de creación |
| `updated_at` | TIMESTAMP WITH TZ | `TIMESTAMP(timezone=True)` | NOT NULL | `datetime.now(UTC)` | Última actualización (con `onupdate`) |

### 5.4 Índices (8 totales)

#### Índices simples (4):

| Nombre | Columna | Propósito |
|--------|---------|-----------|
| `ix_audit_logs_request_id` | `request_id` | Búsqueda rápida por X-Request-ID (trazabilidad) |
| `ix_audit_logs_servicio` | `servicio` | Filtro por microservicio emisor |
| `ix_audit_logs_codigo_respuesta` | `codigo_respuesta` | Filtro por código HTTP |
| `ix_audit_logs_usuario_id` | `usuario_id` | Filtro por usuario |

#### Índices compuestos (3):

| Nombre | Columnas | Propósito |
|--------|----------|-----------|
| `ix_audit_servicio_timestamp` | `servicio`, `timestamp_evento` | Consultas de logs por servicio en rango de tiempo |
| `ix_audit_usuario_timestamp` | `usuario_id`, `timestamp_evento` | Historial de usuario en rango de tiempo |
| `ix_audit_codigo_servicio` | `codigo_respuesta`, `servicio` | Estadísticas de errores por servicio |

#### Índice GIN (1):

| Nombre | Expresión | Propósito |
|--------|-----------|-----------|
| `ix_audit_detalle_fulltext` | `GIN(to_tsvector('spanish', COALESCE(detalle, '')))` | Búsqueda full-text en español sobre el campo detalle |

**Nota:** El índice GIN se crea en la migración Alembic `b2a3c4d5e6f7` usando `op.execute()` con SQL raw porque es un índice funcional de PostgreSQL no soportado directamente por el autogenerate de Alembic.

### 5.5 Migraciones Alembic

| Revisión | ID | Descripción |
|----------|----|-------------|
| 1 | `fae4016df4b8` | Schema inicial: tablas `audit_logs` y `microservice_tokens` con todos los índices simples y compuestos |
| 2 | `b2a3c4d5e6f7` | Índice GIN full-text en campo `detalle` para búsqueda en español |

### 5.6 Schemas Pydantic

#### AuditLogCreate (entrada — POST)

| Campo | Tipo | Obligatorio | Validación | Mapea a columna ORM |
|-------|------|:-----------:|------------|---------------------|
| `timestamp` | `datetime` | ✅ | ISO 8601 | `timestamp_evento` |
| `nombre_microservicio` | `str` | ✅ | 1-50 chars | `servicio` |
| `endpoint` | `str` | ✅ | 1-200 chars | `endpoint` |
| `metodo_http` | `str` | ✅ | 1-10 chars | `metodo` |
| `codigo_respuesta` | `int` | ✅ | 100-599 | `codigo_respuesta` |
| `duracion_ms` | `int` | ✅ | ≥0 | `duracion_ms` |
| `usuario_id` | `UUID?` | ❌ | UUID válido | `usuario_id` |
| `detalle` | `str?` | ❌ | máx 5000 chars | `detalle` |
| `ip_origen` | `str?` | ❌ | máx 45 chars | `ip_origen` |
| `request_id` | `str?` | ❌ | máx 50 chars | `request_id` (auto-genera UUID si null) |

**Nota:** Los nombres de los campos del schema difieren de los nombres de las columnas ORM. El mapeo se realiza explícitamente en `AuditService.create_log()`.

#### AuditLogResponse (salida — GET)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | `UUID` | ID del registro |
| `request_id` | `str` | X-Request-ID |
| `servicio` | `str` | Microservicio emisor |
| `endpoint` | `str` | Ruta invocada |
| `metodo` | `str` | Método HTTP |
| `codigo_respuesta` | `int` | Código HTTP |
| `duracion_ms` | `int` | Duración en ms |
| `usuario_id` | `UUID?` | UUID del usuario |
| `detalle` | `str?` | Detalle del evento |
| `ip_origen` | `str?` | IP de origen |
| `timestamp_evento` | `datetime` | Momento del evento |
| `created_at` | `datetime` | Momento de registro |

Usa `ConfigDict(from_attributes=True)` para mapear directamente desde el modelo ORM.

#### AuditLogFilter (consulta — GET /logs)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `servicio` | `str?` | Filtrar por microservicio |
| `metodo_http` | `str?` | Filtrar por método HTTP |
| `codigo_respuesta` | `int?` | Filtrar por código HTTP |
| `usuario_id` | `UUID?` | Filtrar por usuario |
| `fecha_inicio` | `datetime?` | Fecha inicio del rango |
| `fecha_fin` | `datetime?` | Fecha fin del rango |
| `request_id` | `str?` | Filtrar por X-Request-ID |
| `search_text` | `str?` | Búsqueda full-text en detalle (máx 200 chars) |

---

## 6. Seguridad

### 6.1 Autenticación Inter-Servicio (API Keys)

**Archivo:** `core/auth.py`

| Aspecto | Detalle |
|---------|---------|
| **Mecanismo** | API Key enviada en header `X-API-Key` |
| **Hash** | SHA-256 (`hashlib.sha256`) del API Key |
| **Almacenamiento** | Tabla `microservice_tokens` — solo se guarda el hash, nunca el key en texto plano |
| **Validación** | Se busca un token activo (`activo=True`) cuyo `token_hash` coincida con el SHA-256 del key recibido |
| **Modo desarrollo** | Si `APP_ENV` es `development` o `testing` y no se envía key, se permite el acceso |
| **Modo producción** | API Key **obligatorio** — retorna 401 si falta o es inválido |
| **Endpoints protegidos** | POST `/log`, POST `/log/batch`, DELETE `/purge` (usan `Depends(verify_api_key)`) |
| **Endpoints públicos** | GET (health, logs, trace, user, stats) — no requieren API Key |

**Flujo de validación:**

```
X-API-Key header → SHA-256 hash → SELECT FROM microservice_tokens
                                   WHERE token_hash = hash AND activo = True
                                   → 200 OK / 401 Unauthorized
```

### 6.2 Cifrado AES-256-GCM (Disponible)

**Archivo:** `core/security.py`

El módulo provee la clase `AESCipher` como utilidad de cifrado:

| Aspecto | Detalle |
|---------|---------|
| **Algoritmo** | AES-256-GCM (cifrado autenticado) |
| **Librería** | `cryptography.hazmat.primitives.ciphers.aead.AESGCM` |
| **Clave** | `AES_SECRET_KEY` — 64 caracteres hexadecimales (256 bits) |
| **Nonce** | 12 bytes random (`os.urandom(12)`) |
| **Formato** | `Base64(nonce[12] + ciphertext)` |
| **Instancia** | Singleton `aes_cipher` disponible para importar |
| **Uso actual** | Disponible como utilidad; no se aplica automáticamente en el flujo de creación de logs. El campo `detalle` se persiste como texto plano para permitir búsqueda full-text con el índice GIN |

### 6.3 CORS (Cross-Origin Resource Sharing)

**Configuración en `main.py`:**

| Aspecto | Detalle |
|---------|---------|
| **Orígenes** | Configurados vía `CORS_ORIGINS` (default: `http://localhost:3000,http://localhost:8080`) |
| **Desarrollo** | `allow_origins=["*"]` y `allow_credentials=False` |
| **Producción** | Orígenes específicos con `allow_credentials=True` |
| **Métodos** | `GET, POST, PUT, DELETE, PATCH, OPTIONS` |
| **Headers expuestos** | `X-Request-ID`, `X-Response-Time-ms`, `X-RateLimit-Limit`, `X-RateLimit-Remaining` |

### 6.4 Rate Limiting

**Archivo:** `core/rate_limiter.py`

| Aspecto | Detalle |
|---------|---------|
| **Algoritmo** | Sliding window por IP |
| **Almacenamiento** | En memoria (diccionario `IP → [timestamps]`) |
| **Límite default** | 100 requests / 60 segundos (configurable vía `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`) |
| **IP real** | Soporta `X-Forwarded-For` para proxies |
| **Excluidos** | `/api/v1/audit/health`, `/docs`, `/redoc`, `/openapi.json`, `/` |
| **Respuesta 429** | JSON con `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining` |
| **Headers** | Cada respuesta incluye `X-RateLimit-Limit` y `X-RateLimit-Remaining` |

### 6.5 X-Request-ID (Trazabilidad)

**Archivo:** `core/middleware.py`

- Si el cliente envía `X-Request-ID`, se propaga.
- Si no lo envía, se genera automáticamente con `uuid.uuid4()`.
- Se inyecta en `request.state.request_id` para uso dentro del request.
- Se retorna en los headers `X-Request-ID` y `X-Response-Time-ms`.

### 6.6 Docker — Ejecución No-Root

El `Dockerfile` crea un usuario `appuser` en grupo `appgroup` y ejecuta la aplicación como usuario no-root:

```dockerfile
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser
```

---

## 7. Concurrencia y Rendimiento

### 7.1 Motor Async

| Componente | Implementación |
|------------|----------------|
| **AsyncEngine** | `create_async_engine()` de SQLAlchemy 2.0 |
| **Driver** | `asyncpg` — driver PostgreSQL nativo async |
| **Session Factory** | `async_sessionmaker(bind=async_engine, class_=AsyncSession)` |
| **Opciones de sesión** | `autoflush=False`, `autocommit=False`, `expire_on_commit=False` |

### 7.2 Pool de Conexiones

**Archivo:** `database/connection.py`

| Parámetro | Default | Variable de entorno | Descripción |
|-----------|---------|--------------------|-----------  |
| `pool_size` | 10 | `DB_POOL_SIZE` | Conexiones activas en el pool |
| `max_overflow` | 20 | `DB_MAX_OVERFLOW` | Conexiones extra permitidas bajo alta carga |
| `pool_recycle` | 3600 | `DB_POOL_RECYCLE` | Reciclar conexiones cada N segundos |
| `pool_pre_ping` | `True` | — | Verificar conexión antes de usarla |

**Nota:** Para SQLite (usado en tests), se usa `StaticPool` y `check_same_thread=False` en vez del pool estándar.

### 7.3 Compatibilidad PostgreSQL / SQLite

El sistema detecta automáticamente el tipo de base de datos:

```python
# database/connection.py
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    async_engine = create_async_engine(..., poolclass=StaticPool)
else:
    async_engine = create_async_engine(..., pool_size=..., max_overflow=...)
```

Esto permite que los **unit tests** usen SQLite en memoria y la **aplicación real** use PostgreSQL con pool de conexiones optimizado.

### 7.4 Conversión Automática de URL

**Archivo:** `core/config.py` — `computed_field`

```python
@computed_field
@property
def ASYNC_DATABASE_URL(self) -> str:
    # postgresql+psycopg2://... → postgresql+asyncpg://...
    # sqlite:///...             → sqlite+aiosqlite:///...
```

Solo se configura `DATABASE_URL` (sync). La URL async se genera automáticamente reemplazando el driver.

### 7.5 Uvicorn en Producción

**Dockerfile CMD:**

```
uvicorn app.main:app --host 0.0.0.0 --port 8019 --workers 4 --loop uvloop --http httptools
```

| Opción | Valor | Propósito |
|--------|-------|-----------|
| `--workers` | 4 | Procesos worker para paralelismo real |
| `--loop` | `uvloop` | Event loop optimizado (más rápido que asyncio default) |
| `--http` | `httptools` | Parser HTTP en C (más rápido que h11) |

### 7.6 Resource Limits (Docker Compose)

```yaml
deploy:
  resources:
    limits:
      cpus: "1.0"
      memory: 512M
```

---

## 8. Testing y CI/CD

### 8.1 Estrategia de Testing

| Tipo | Base de datos | Archivos | Tests |
|------|---------------|----------|-------|
| Unit tests | SQLite en memoria | `test_audit_routes.py`, `test_edge_cases.py`, `test_security.py`, `test_statistics.py` | 37 |
| Integration tests | PostgreSQL 16 real | `test_integration_postgres.py` | 12 |
| **Total** | | | **49** |

### 8.2 Unit Tests (SQLite)

- Se ejecutan con `DATABASE_URL=sqlite:///./test.db` y `APP_ENV=testing`.
- Usan el tipo `GUID` que se adapta automáticamente a CHAR(36) para SQLite.
- No requieren PostgreSQL instalado.

### 8.3 Integration Tests (PostgreSQL)

- Requieren un servidor PostgreSQL 16 real corriendo.
- Se configuran con `TEST_POSTGRES_URL=postgresql+asyncpg://...`.
- Ejecutan las migraciones Alembic antes de los tests.
- Validan funcionalidad real incluyendo el índice GIN full-text.

### 8.4 Pipeline CI/CD — GitHub Actions

**Archivo:** `.github/workflows/ci.yml`

4 jobs configurados:

```
┌─────────┐     ┌──────────────┐     ┌───────────────────┐     ┌──────────────┐
│  lint   │────►│  test-unit   │────►│ test-integration  │────►│   docker     │
│         │     │  (SQLite)    │     │  (PostgreSQL 16)  │     │  (build)     │
└─────────┘     └──────────────┘     └───────────────────┘     └──────────────┘
```

| Job | Descripción | Depende de |
|-----|-------------|------------|
| `lint` | Verifica sintaxis Python y que los imports funcionen | — |
| `test-unit` | Ejecuta unit tests con SQLite | `lint` |
| `test-integration` | Ejecuta integration tests con PostgreSQL 16 (service container) | `lint` |
| `docker` | Construye imagen Docker multi-stage | `test-unit` + `test-integration` |

**Nota:** El job `docker` solo se ejecuta en push a `main` (no en PRs ni en develop).

El servicio PostgreSQL en CI se configura como:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ci_test_password
      POSTGRES_DB: ms_auditoria_test
```

---

## 9. DevOps y Despliegue

### 9.1 Dockerfile — Multi-Stage Build

**Archivo:** `Dockerfile`

| Stage | Base | Propósito |
|-------|------|-----------|
| `builder` | `python:3.10-slim` | Instala `gcc`, `libpq-dev`, compila dependencias |
| `runtime` | `python:3.10-slim` | Solo `libpq5` + `curl` + código + deps precompiladas |

**Beneficios:**
- Imagen final más pequeña (sin compiladores).
- Layer de dependencias cacheado (solo se reconstruye si cambia `requirements.txt`).
- Usuario no-root (`appuser`) por seguridad.

**Healthcheck integrado:**

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8019/api/v1/audit/health || exit 1
```

**CMD de ejecución:**

```dockerfile
CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8019 --workers 4 --loop uvloop --http httptools"]
```

Ejecuta las migraciones Alembic **antes** de iniciar el servidor.

### 9.2 Docker Compose

**Archivo:** `docker-compose.yml`

| Servicio | Imagen | Puerto | Descripción |
|----------|--------|--------|-------------|
| `db` | `postgres:16-alpine` | 5432 | Base de datos PostgreSQL con healthcheck |
| `app` | Build local | 8019 | Microservicio ms-auditoria |

**Características:**
- `depends_on: db: condition: service_healthy` — la app espera a que PostgreSQL esté listo.
- `restart: unless-stopped` — reinicio automático del contenedor.
- Red `erp-net` (bridge) para comunicación con otros microservicios del ERP.
- Volumen `pgdata` para persistencia de datos entre reinicios.

### 9.3 Variables de Entorno (Producción)

| Variable | Valor en Docker Compose | Descripción |
|----------|------------------------|-------------|
| `DATABASE_URL` | `postgresql+psycopg2://postgres:Ame@db:5432/ms_auditoria` | Conexión a PostgreSQL vía nombre de servicio `db` |
| `AES_SECRET_KEY` | (64 hex chars) | Clave AES-256 |
| `APP_ENV` | `production` | Entorno de ejecución |
| `APP_DEBUG` | `false` | Sin modo debug |
| `LOG_LEVEL` | `INFO` | Nivel de logging |
| `DB_POOL_SIZE` | `20` | Pool de conexiones |
| `DB_MAX_OVERFLOW` | `40` | Overflow del pool |
| `DB_POOL_RECYCLE` | `3600` | Reciclaje de conexiones |
| `MS_AUTENTICACION_URL` | `http://ms-autenticacion:8001/api/v1/auth` | URL de ms-autenticación (red interna) |
| `MS_ROLES_URL` | `http://ms-roles-permisos:8002/api/v1/roles` | URL de ms-roles (red interna) |

### 9.4 Lifecycle de la Aplicación

Gestionado con `asynccontextmanager` en `main.py`:

**Startup:**
1. Log de inicio con entorno actual.
2. Si `APP_ENV == "development"`: crear tablas con `Base.metadata.create_all()` (sync engine).
3. Iniciar scheduler de retención automática (`retention_service.start()`).

**Shutdown:**
1. Detener scheduler de retención (`retention_service.stop()`).
2. Cerrar pool async (`async_engine.dispose()`).
3. Log de cierre.

---

## 10. Justificaciones Técnicas

### 10.1 ¿Por qué FastAPI?

| Razón | Detalle |
|-------|---------|
| **Async nativo** | Soporte completo de `async/await` sin workarounds |
| **Rendimiento** | Uno de los frameworks Python más rápidos (basado en Starlette + Uvicorn) |
| **Documentación automática** | Swagger UI (`/docs`) y ReDoc (`/redoc`) generados automáticamente |
| **Validación integrada** | Pydantic v2 para validación de entrada/salida con tipos Python |
| **Dependency Injection** | Sistema nativo de DI con `Depends()` |
| **Estándar OpenAPI** | Compatible con herramientas de generación de clientes |

### 10.2 ¿Por qué SQLAlchemy 2.0 Async?

| Razón | Detalle |
|-------|---------|
| **Non-blocking I/O** | Las consultas no bloquean el event loop |
| **Pool de conexiones** | Gestión automática con `pool_pre_ping`, `pool_recycle` |
| **ORM maduro** | Modelo de datos expresivo con relaciones, tipos custom, etc. |
| **Compatibilidad** | Funciona con PostgreSQL (asyncpg) y SQLite (aiosqlite) |
| **Select 2.0** | Sintaxis `select(Model).where(...)` más explícita que `query()` |

### 10.3 ¿Por qué PostgreSQL 16?

| Razón | Detalle |
|-------|---------|
| **GIN index** | Índice invertido para búsqueda full-text en español |
| **UUID nativo** | Tipo UUID sin overhead de conversión |
| **JSONB** | Soporte nativo si se necesita en el futuro |
| **Rendimiento** | Mejoras significativas en query planner y vacuuming |
| **Ecosystem** | Driver async `asyncpg` con rendimiento superior |

### 10.4 ¿Por qué Pydantic v2?

| Razón | Detalle |
|-------|---------|
| **Rendimiento** | Core en Rust — hasta 50x más rápido que v1 |
| **`model_validate`** | Mapeo directo desde ORM con `from_attributes=True` |
| **`computed_field`** | Campos calculados (ej: `ASYNC_DATABASE_URL`) |
| **`ConfigDict`** | Configuración más limpia que `class Config` |
| **Integración FastAPI** | Validación automática de request/response |

### 10.5 ¿Por qué Repository Pattern?

| Razón | Detalle |
|-------|---------|
| **Testabilidad** | Se puede mockear el repositorio en tests |
| **Separación** | Las consultas SQL están aisladas de la lógica de negocio |
| **Mantenibilidad** | Un solo lugar para modificar consultas |
| **Extensibilidad** | Agregar filtros o consultas sin tocar el servicio |

### 10.6 ¿Por qué Unit of Work como infraestructura disponible?

El patrón UoW está implementado en `database/unit_of_work.py` y disponible vía `get_uow()` en `dependencies.py`. Los endpoints actuales usan `AsyncSession` directa con `commit()` porque cada operación es una sola transacción simple. El UoW queda disponible como infraestructura para futuros casos que requieran múltiples operaciones atómicas en una sola transacción.

### 10.7 ¿Por qué asyncio nativo para retención (no APScheduler/Celery)?

| Razón | Detalle |
|-------|---------|
| **Cero dependencias** | No agrega librerías externas al proyecto |
| **Simplicidad** | Un `asyncio.create_task()` + `asyncio.sleep()` es suficiente |
| **Integración** | Se gestiona con el `lifespan` de FastAPI (startup/shutdown) |
| **Caso de uso simple** | Solo una tarea diaria — no necesita un scheduler completo |

### 10.8 ¿Por qué JSON Structured Logging?

**Archivo:** `utils/logger.py`

| Razón | Detalle |
|-------|---------|
| **Machine-readable** | Parseable automáticamente por ELK, Grafana, Loki |
| **Campos estándar** | `timestamp`, `level`, `service`, `message`, `module`, `function`, `line` |
| **Extensible** | Campos extra opcionales bajo la key `"extra"` (ej: `request_id`, `duration_ms`) |
| **UTC** | Timestamps en UTC ISO 8601 para consistencia entre servidores |

Ejemplo de log:

```json
{
  "timestamp": "2026-02-27T10:30:00.000000+00:00",
  "level": "INFO",
  "service": "ms-auditoria",
  "message": "audit_log_created",
  "module": "audit_service",
  "function": "create_log",
  "line": 45,
  "extra": {
    "audit_id": "a1b2c3d4-...",
    "servicio": "ms-matriculas",
    "endpoint": "/api/v1/matricula/inscribir"
  }
}
```

### 10.9 ¿Por qué el campo `detalle` NO se cifra automáticamente?

El módulo `AESCipher` está disponible en `core/security.py`, pero el campo `detalle` se persiste como texto plano por diseño:

1. **Full-text search**: El índice GIN con `to_tsvector('spanish', ...)` requiere texto plano para funcionar. Si se cifra, la búsqueda full-text deja de ser posible.
2. **Consultas por contenido**: El endpoint `GET /logs?search_text=...` necesita buscar dentro del detalle.
3. **Naturaleza de los datos**: Los logs de auditoría típicamente contienen metadata operativa (endpoint, parámetros), no datos personales sensibles como contraseñas.
4. **Disponibilidad**: Si un caso de uso futuro requiere cifrar detalle específico, el microservicio emisor puede cifrar el campo antes de enviarlo usando la misma librería, y el receptor puede almacenarlo ya cifrado.

---

## Apéndice: Configuración Completa

### Variables de Entorno

| Variable | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `DATABASE_URL` | str | `postgresql+psycopg2://...` | URL de conexión sync a PostgreSQL |
| `AES_SECRET_KEY` | str | (requerida) | Clave AES-256 en hexadecimal (64 chars) |
| `API_KEY_HEADER` | str | `X-API-Key` | Nombre del header para autenticación |
| `CORS_ORIGINS` | str | `http://localhost:3000,...` | Orígenes CORS (separados por coma) |
| `RATE_LIMIT_REQUESTS` | int | `100` | Máximo de requests por ventana |
| `RATE_LIMIT_WINDOW_SECONDS` | int | `60` | Ventana en segundos |
| `RETENTION_DAYS` | int | `90` | Días de retención de logs |
| `RETENTION_CRON_HOUR` | int | `3` | Hora UTC de purga automática |
| `MS_AUTENTICACION_URL` | str | `http://localhost:8001/api/v1/auth` | URL de ms-autenticación |
| `MS_ROLES_URL` | str | `http://localhost:8002/api/v1/roles` | URL de ms-roles-permisos |
| `DB_POOL_SIZE` | int | `10` | Conexiones activas en pool |
| `DB_MAX_OVERFLOW` | int | `20` | Conexiones extra bajo carga |
| `DB_POOL_RECYCLE` | int | `3600` | Reciclaje de conexiones (seg) |
| `APP_HOST` | str | `0.0.0.0` | Host del servidor |
| `APP_PORT` | int | `8019` | Puerto del servidor |
| `APP_ENV` | str | `development` | Entorno de ejecución |
| `APP_DEBUG` | bool | `False` | Modo debug |
| `LOG_LEVEL` | str | `INFO` | Nivel de logging |
| `DEFAULT_PAGE_SIZE` | int | `20` | Tamaño de página default |
| `MAX_PAGE_SIZE` | int | `100` | Tamaño de página máximo |
