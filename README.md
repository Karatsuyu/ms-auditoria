# 🔍 ms-auditoria — Microservicio de Auditoría

> **Microservicio #19** del ERP Universitario  
> Materia: Desarrollo de Software 3  
> Tecnología: FastAPI + SQLAlchemy 2.0 Async + PostgreSQL 17

---

## 📋 Descripción

`ms-auditoria` es el microservicio central de logging y auditoría del sistema ERP Universitario. Recibe, almacena y permite consultar eventos generados por los **18 microservicios** del ecosistema.

### Funcionalidades principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/audit/health` | GET | Health check del servicio |
| `/api/v1/audit/log` | POST | Registrar un evento de auditoría |
| `/api/v1/audit/log/batch` | POST | Registrar múltiples eventos (batch) |
| `/api/v1/audit/logs` | GET | Listar logs con filtros y paginación |
| `/api/v1/audit/log/{id}` | GET | Obtener log por UUID |
| `/api/v1/audit/trace/{request_id}` | GET | Trazabilidad por X-Request-ID |
| `/api/v1/audit/user/{usuario_id}` | GET | Historial de un usuario |
| `/api/v1/audit/stats` | GET | Estadísticas generales |
| `/api/v1/audit/purge` | DELETE | Purgar logs antiguos |

---

## 🏗️ Arquitectura

```
ms-auditoria/
├── app/
│   ├── core/               # Configuración, middleware, auth, rate limiter
│   │   ├── config.py       # Pydantic Settings (multi-entorno)
│   │   ├── middleware.py    # X-Request-ID + response time
│   │   ├── rate_limiter.py  # Rate limiting por IP (sliding window)
│   │   ├── auth.py          # Autenticación inter-servicio (API Keys)
│   │   ├── security.py      # AES-256-GCM cifrado
│   │   ├── dependencies.py  # FastAPI Dependency Injection
│   │   └── exception_handlers.py  # Manejadores globales de errores
│   ├── database/            # Capa de acceso a datos
│   │   ├── base.py          # SQLAlchemy DeclarativeBase
│   │   ├── connection.py    # Async + Sync engines
│   │   ├── session.py       # AsyncSessionLocal factory
│   │   └── unit_of_work.py  # Patrón Unit of Work
│   ├── models/              # Modelos ORM
│   │   ├── audit_log.py     # Tabla audit_logs (GUID cross-DB)
│   │   └── microservice_token.py  # Tabla microservice_tokens
│   ├── repositories/        # Repository Pattern (async)
│   │   └── audit_repository.py
│   ├── schemas/             # Pydantic v2 schemas
│   │   ├── audit_schema.py  # Create, Response, Filter
│   │   └── response_schema.py  # Respuestas genéricas
│   ├── services/            # Lógica de negocio
│   │   ├── audit_service.py
│   │   ├── statistics_service.py
│   │   ├── auth_service.py  # Comunicación con ms-autenticación
│   │   └── retention_service.py  # TTL / purga automática
│   ├── routes/
│   │   └── audit_routes.py  # 9 endpoints RESTful
│   └── utils/
│       ├── logger.py        # JSON structured logging
│       └── pagination.py    # PaginationParams helper
├── alembic/                 # Migraciones de BD
├── tests/                   # 38+ unit tests + integration tests
├── .github/workflows/       # CI/CD pipeline
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # PostgreSQL + App
└── requirements.txt
```

### Patrones implementados

- **Repository Pattern** — Abstracción de acceso a datos
- **Unit of Work** — Transacciones atómicas con rollback automático
- **Dependency Injection** — FastAPI `Depends()` para sesiones y auth
- **CQRS-like** — Separación de comandos (POST) y queries (GET)
- **Middleware Chain** — Request-ID → Rate Limit → CORS
- **Strategy Pattern** — GUID TypeDecorator (PostgreSQL UUID nativo / SQLite CHAR)

---

## 🚀 Instalación y Ejecución

### Requisitos previos

- Python 3.10+
- PostgreSQL 16+ (local o Docker)

### Instalación local

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd ms-auditoria

# 2. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.development .env
# Editar .env con tus credenciales de PostgreSQL

# 5. Crear base de datos
# En psql o pgAdmin: CREATE DATABASE ms_auditoria;

# 6. Ejecutar migraciones
alembic upgrade head

# 7. Iniciar el servidor
uvicorn app.main:app --reload --port 8019
```

### Con Docker

```bash
# Iniciar PostgreSQL + App
docker-compose up -d

# La app estará en http://localhost:8019
# Swagger UI en http://localhost:8019/docs
```

---

## 📖 Documentación de la API

Con el servidor corriendo, acceder a:

- **Swagger UI**: [http://localhost:8019/docs](http://localhost:8019/docs)
- **ReDoc**: [http://localhost:8019/redoc](http://localhost:8019/redoc)

### Ejemplo: Registrar un evento

```bash
curl -X POST http://localhost:8019/api/v1/audit/log \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-02-27T10:30:00Z",
    "nombre_microservicio": "ms-matriculas",
    "endpoint": "/api/v1/matricula/inscribir",
    "metodo_http": "POST",
    "codigo_respuesta": 201,
    "duracion_ms": 142,
    "usuario_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "detalle": "{\"carrera\": \"Ing. Sistemas\"}",
    "ip_origen": "192.168.1.50",
    "request_id": "req-001"
  }'
```

### Ejemplo: Consultar con filtros

```bash
# Logs del servicio ms-pagos, método POST, página 1
curl "http://localhost:8019/api/v1/audit/logs?servicio=ms-pagos&metodo_http=POST&page=1&page_size=10"

# Trazabilidad por request-id
curl "http://localhost:8019/api/v1/audit/trace/req-001"

# Estadísticas generales
curl "http://localhost:8019/api/v1/audit/stats"
```

---

## 🔐 Seguridad

| Feature | Descripción |
|---------|-------------|
| **API Key Auth** | Endpoints de escritura (POST, DELETE) requieren header `X-API-Key` en producción |
| **AES-256-GCM** | Cifrado de datos sensibles en campo `detalle` |
| **Rate Limiting** | Máximo 100 req/min por IP (configurable) |
| **CORS** | Orígenes específicos por entorno |
| **X-Request-ID** | Trazabilidad end-to-end entre microservicios |
| **Non-root Docker** | Container ejecuta como usuario `appuser` |

---

## 🧪 Tests

### Unit tests (SQLite en memoria)

```bash
# Ejecutar todos los unit tests
pytest tests/ --ignore=tests/test_integration_postgres.py -v

# Con cobertura
pytest tests/ --ignore=tests/test_integration_postgres.py --cov=app --cov-report=term-missing
```

### Integration tests (PostgreSQL real)

```bash
# Requiere PostgreSQL corriendo con BD de test
TEST_POSTGRES_URL=postgresql+asyncpg://postgres:Ame@127.0.0.1:5432/ms_auditoria_test \
  pytest tests/test_integration_postgres.py -v
```

### Resumen de tests

| Archivo | Tests | Tipo |
|---------|-------|------|
| `test_audit_routes.py` | 15 | Integración (endpoints) |
| `test_edge_cases.py` | 13 | Edge cases y validación |
| `test_security.py` | 5 | Cifrado AES |
| `test_statistics.py` | 4 | Estadísticas |
| `test_integration_postgres.py` | 12 | PostgreSQL real |
| **Total** | **49** | |

---

## ⚙️ Configuración por Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+psycopg2://...` | URL de conexión a PostgreSQL |
| `AES_SECRET_KEY` | — | Clave AES-256 (64 hex chars) |
| `APP_ENV` | `development` | Entorno: development/testing/production |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Orígenes CORS permitidos |
| `RATE_LIMIT_REQUESTS` | `100` | Max requests por ventana |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Ventana de rate limiting |
| `RETENTION_DAYS` | `90` | Días de retención de logs |
| `RETENTION_CRON_HOUR` | `3` | Hora UTC de purga automática |
| `DB_POOL_SIZE` | `10` | Conexiones en pool |
| `DB_MAX_OVERFLOW` | `20` | Conexiones extra |
| `LOG_LEVEL` | `INFO` | Nivel de logging |

Archivos de entorno disponibles: `.env.development`, `.env.testing`, `.env.production`

---

## 🐳 Docker

```bash
# Build
docker build -t ms-auditoria .

# Run con PostgreSQL via docker-compose
docker-compose up -d

# Verificar health
curl http://localhost:8019/api/v1/audit/health
```

---

## 🔄 CI/CD

Pipeline de GitHub Actions (`.github/workflows/ci.yml`):

1. **Lint** — Verifica syntax e imports
2. **Unit Tests** — 38 tests contra SQLite
3. **Integration Tests** — 12 tests contra PostgreSQL 16 (service container)
4. **Docker Build** — Solo en merge a `main`

---

## 📊 Índices de Base de Datos

| Índice | Columnas | Tipo |
|--------|----------|------|
| PK `id` | `id` | UUID (nativo PostgreSQL) |
| `ix_audit_logs_request_id` | `request_id` | B-tree |
| `ix_audit_logs_servicio` | `servicio` | B-tree |
| `ix_audit_logs_codigo_respuesta` | `codigo_respuesta` | B-tree |
| `ix_audit_logs_usuario_id` | `usuario_id` | B-tree |
| `ix_audit_servicio_timestamp` | `servicio, timestamp_evento` | B-tree compuesto |
| `ix_audit_usuario_timestamp` | `usuario_id, timestamp_evento` | B-tree compuesto |
| `ix_audit_codigo_servicio` | `codigo_respuesta, servicio` | B-tree compuesto |
| `ix_audit_detalle_fulltext` | `detalle` | **GIN** (full-text search) |

---

## 🛠️ Stack Tecnológico

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| FastAPI | 0.115.6 | Framework web async |
| SQLAlchemy | 2.0.36 | ORM async (AsyncSession) |
| PostgreSQL | 17 | Base de datos principal |
| asyncpg | 0.30.0 | Driver async PostgreSQL |
| Pydantic | 2.10.3 | Validación de datos |
| Alembic | 1.14.0 | Migraciones de BD |
| Uvicorn | 0.34.0 | ASGI server |
| pytest | 8.3.4 | Testing framework |
| Docker | Multi-stage | Containerización |

---

## 🔗 Guía de Integración con los Otros 18 Microservicios

Esta sección es para tus compañeros. Explica **cómo conectar su microservicio** con `ms-auditoria` para que cada acción relevante quede registrada en el log centralizado.

### Paso 1 — Configurar la URL de ms-auditoria

En el archivo `.env` de cada microservicio, agregar:

```env
MS_AUDITORIA_URL=http://localhost:8019/api/v1/audit
```

> En producción, cambiar `localhost` por el hostname del contenedor o servicio (ej: `http://ms-auditoria:8019`).

### Paso 2 — Obtener un API Key (producción)

En producción, los endpoints de escritura (`POST /log`, `POST /log/batch`, `DELETE /purge`) requieren autenticación por API Key. En desarrollo, el API Key es **opcional** (se puede omitir).

Cada microservicio debe tener un registro en la tabla `microservice_tokens`:

```sql
INSERT INTO microservice_tokens (nombre_microservicio, token_hash, activo)
VALUES (
    'ms-matriculas',
    -- SHA-256 del token que usará tu microservicio
    encode(sha256('MI_TOKEN_SECRETO_AQUI'::bytea), 'hex'),
    true
);
```

Luego enviar el header en cada request:

```
X-API-Key: MI_TOKEN_SECRETO_AQUI
```

> ⚠️ En **desarrollo/testing** se puede omitir el header `X-API-Key` (el servicio permite acceso sin él).

### Paso 3 — Enviar eventos de auditoría

#### Opción A: Llamada HTTP directa (recomendada)

Ejemplo en **Python (httpx/requests)**:

```python
import httpx
from datetime import datetime, timezone

AUDITORIA_URL = "http://localhost:8019/api/v1/audit/log"
API_KEY = "MI_TOKEN_SECRETO_AQUI"  # Omitir en desarrollo

async def registrar_auditoria(
    endpoint: str,
    metodo: str,
    codigo: int,
    duracion_ms: int,
    usuario_id: str = None,
    detalle: str = None,
    request_id: str = None,
    ip_origen: str = None,
):
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nombre_microservicio": "ms-matriculas",  # ← Cambiar por tu microservicio
        "endpoint": endpoint,
        "metodo_http": metodo,
        "codigo_respuesta": codigo,
        "duracion_ms": duracion_ms,
        "usuario_id": usuario_id,
        "detalle": detalle,
        "ip_origen": ip_origen,
        "request_id": request_id,
    }
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY

    async with httpx.AsyncClient() as client:
        try:
            await client.post(AUDITORIA_URL, json=payload, headers=headers, timeout=5.0)
        except Exception:
            pass  # No fallar si auditoría no está disponible
```

Ejemplo en **Java (Spring Boot)**:

```java
RestTemplate restTemplate = new RestTemplate();
HttpHeaders headers = new HttpHeaders();
headers.setContentType(MediaType.APPLICATION_JSON);
headers.set("X-API-Key", "MI_TOKEN_SECRETO_AQUI"); // Omitir en dev

Map<String, Object> body = new HashMap<>();
body.put("timestamp", Instant.now().toString());
body.put("nombre_microservicio", "ms-pagos");  // ← Tu microservicio
body.put("endpoint", "/api/v1/pagos/procesar");
body.put("metodo_http", "POST");
body.put("codigo_respuesta", 201);
body.put("duracion_ms", 230);
body.put("usuario_id", "a1b2c3d4-e5f6-7890-abcd-ef1234567890");
body.put("request_id", request.getHeader("X-Request-ID"));

HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
restTemplate.postForEntity(
    "http://localhost:8019/api/v1/audit/log",
    request,
    String.class
);
```

Ejemplo en **Node.js (axios)**:

```javascript
const axios = require('axios');

async function registrarAuditoria(endpoint, metodo, codigo, duracionMs, usuarioId, detalle) {
    try {
        await axios.post('http://localhost:8019/api/v1/audit/log', {
            timestamp: new Date().toISOString(),
            nombre_microservicio: 'ms-notificaciones',  // ← Tu microservicio
            endpoint: endpoint,
            metodo_http: metodo,
            codigo_respuesta: codigo,
            duracion_ms: duracionMs,
            usuario_id: usuarioId,
            detalle: detalle,
            request_id: req.headers['x-request-id'] || null,
            ip_origen: req.ip
        }, {
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': 'MI_TOKEN_SECRETO_AQUI'  // Omitir en dev
            },
            timeout: 5000
        });
    } catch (error) {
        // No fallar si auditoría no responde
        console.warn('No se pudo registrar auditoría:', error.message);
    }
}
```

#### Opción B: Envío en lote (batch) — para alta carga

Si tu microservicio genera muchos eventos, puedes acumularlos y enviarlos en batch:

```bash
POST http://localhost:8019/api/v1/audit/log/batch
Content-Type: application/json
X-API-Key: MI_TOKEN_SECRETO_AQUI

[
    {
        "timestamp": "2026-02-27T10:30:00Z",
        "nombre_microservicio": "ms-matriculas",
        "endpoint": "/api/v1/matricula/inscribir",
        "metodo_http": "POST",
        "codigo_respuesta": 201,
        "duracion_ms": 142,
        "usuario_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    },
    {
        "timestamp": "2026-02-27T10:30:05Z",
        "nombre_microservicio": "ms-matriculas",
        "endpoint": "/api/v1/matricula/consultar",
        "metodo_http": "GET",
        "codigo_respuesta": 200,
        "duracion_ms": 35,
        "usuario_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901"
    }
]
```

### Paso 4 — Campos del payload

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|:-----------:|-------------|
| `timestamp` | `datetime ISO 8601` | ✅ | Momento exacto del evento en tu microservicio |
| `nombre_microservicio` | `string (1-50)` | ✅ | Nombre de tu microservicio (ej: `ms-matriculas`) |
| `endpoint` | `string (1-200)` | ✅ | Ruta del endpoint invocado (ej: `/api/v1/matricula/inscribir`) |
| `metodo_http` | `string (1-10)` | ✅ | Método HTTP: `GET`, `POST`, `PUT`, `DELETE`, `PATCH` |
| `codigo_respuesta` | `int (100-599)` | ✅ | Código HTTP de respuesta (ej: `200`, `201`, `404`, `500`) |
| `duracion_ms` | `int (≥ 0)` | ✅ | Duración del request en milisegundos |
| `usuario_id` | `UUID string` | ❌ | UUID del usuario autenticado (null si anónimo) |
| `detalle` | `string (≤ 5000)` | ❌ | JSON string con datos adicionales del evento |
| `ip_origen` | `string (≤ 45)` | ❌ | IP del cliente (soporta IPv4 e IPv6) |
| `request_id` | `string (≤ 50)` | ❌ | ID único para trazabilidad entre servicios |

### Paso 5 — Consultar logs de tu microservicio

Cada compañero puede consultar los logs de su propio microservicio:

```bash
# Ver logs de ms-matriculas, solo POST, código 500 (errores)
GET http://localhost:8019/api/v1/audit/logs?servicio=ms-matriculas&metodo_http=POST&codigo_respuesta=500

# Trazabilidad de un request que pasó por varios microservicios
GET http://localhost:8019/api/v1/audit/trace/{request_id}

# Historial de un usuario específico
GET http://localhost:8019/api/v1/audit/user/{usuario_id}

# Búsqueda full-text en detalle (solo PostgreSQL)
GET http://localhost:8019/api/v1/audit/logs?search_text=inscripción

# Estadísticas generales (todos los microservicios)
GET http://localhost:8019/api/v1/audit/stats
```

### Paso 6 — Trazabilidad con X-Request-ID

Para rastrear un request que pasa por múltiples microservicios:

```
┌──────────────┐   X-Request-ID: abc-123   ┌──────────────┐
│  ms-gateway  │ ─────────────────────────► │ ms-matriculas│
└──────────────┘                            └──────┬───────┘
                                                   │ POST /audit/log
                                                   │ request_id: "abc-123"
                                                   ▼
                   X-Request-ID: abc-123   ┌──────────────┐
                 ◄──────────────────────── │  ms-pagos    │
                                           └──────┬───────┘
                                                   │ POST /audit/log
                                                   │ request_id: "abc-123"
                                                   ▼
                                           ┌──────────────┐
                                           │ ms-auditoria │ ← Almacena ambos
                                           │   (este ms)  │    con el mismo
                                           └──────────────┘    request_id
```

Después se puede ver toda la traza:

```bash
GET http://localhost:8019/api/v1/audit/trace/abc-123
# Retorna los 2 registros de ms-matriculas y ms-pagos
```

### Paso 7 — Buenas prácticas

1. **No bloquear tu servicio** — Usa `try/catch` o fire-and-forget. Si auditoría no responde, tu microservicio no debe fallar.
2. **Enviar `request_id`** — Propagar el header `X-Request-ID` entre servicios para trazabilidad.
3. **Medir duración real** — Calcular `duracion_ms` con timestamp antes y después de tu lógica.
4. **Usar batch para alta carga** — Si tu servicio genera >50 eventos/segundo, acumular y enviar en lote cada 5-10 segundos.
5. **Incluir detalle útil** — Poner en `detalle` información de negocio relevante como JSON string.
6. **Nombre del microservicio consistente** — Usar siempre el mismo `nombre_microservicio` (ej: `ms-matriculas`, no `matriculas` ni `MS-MATRICULAS`).

### Mapa de los 19 microservicios

| # | Microservicio | Ejemplo de `nombre_microservicio` |
|---|---------------|----------------------------------|
| 1 | Autenticación | `ms-autenticacion` |
| 2 | Roles y Permisos | `ms-roles` |
| 3 | Gestión de Usuarios | `ms-usuarios` |
| 4 | Gestión Académica | `ms-academica` |
| 5 | Matrículas | `ms-matriculas` |
| 6 | Calificaciones | `ms-calificaciones` |
| 7 | Horarios | `ms-horarios` |
| 8 | Asistencia | `ms-asistencia` |
| 9 | Pagos | `ms-pagos` |
| 10 | Becas | `ms-becas` |
| 11 | Biblioteca | `ms-biblioteca` |
| 12 | Laboratorios | `ms-laboratorios` |
| 13 | Comunicaciones | `ms-comunicaciones` |
| 14 | Reportes | `ms-reportes` |
| 15 | Notificaciones | `ms-notificaciones` |
| 16 | Configuración | `ms-configuracion` |
| 17 | Backup | `ms-backup` |
| 18 | Documentos | `ms-documentos` |
| **19** | **Auditoría (este)** | **`ms-auditoria`** |

> ⚠️ **Importante**: Coordinar con todos los compañeros para que usen exactamente los nombres de la tabla. Las estadísticas y filtros dependen de que el campo `nombre_microservicio` sea consistente.

### Respuesta esperada

Al enviar un evento exitosamente, recibirás:

```json
{
    "success": true,
    "data": {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "request_id": "req-001",
        "servicio": "ms-matriculas",
        "endpoint": "/api/v1/matricula/inscribir",
        "metodo": "POST",
        "codigo_respuesta": 201,
        "duracion_ms": 142,
        "usuario_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "detalle": "{\"carrera\": \"Ing. Sistemas\"}",
        "ip_origen": "192.168.1.50",
        "timestamp_evento": "2026-02-27T10:30:00Z",
        "created_at": "2026-02-27T10:30:01.123Z"
    }
}
```

Si hay error de validación (422):

```json
{
    "success": false,
    "errors": [
        {
            "field": "codigo_respuesta",
            "message": "Input should be greater than or equal to 100",
            "type": "greater_than_equal"
        }
    ]
}
```

---

## 👥 Equipo

Proyecto final — **Desarrollo de Software 3**  
ERP Universitario — Microservicio #19: Auditoría y Logging
