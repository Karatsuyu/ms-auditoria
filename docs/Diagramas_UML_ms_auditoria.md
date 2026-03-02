# Diagramas UML — ms-auditoria

## Microservicio #19: Auditoría y Logging del ERP Universitario

**Materia:** Desarrollo de Software 3  
**Fecha:** Marzo 2026  
**Repositorio:** https://github.com/Karatsuyu/ms-auditoria

---

## Tabla de Contenidos

1. [Diagrama de Casos de Uso](#1-diagrama-de-casos-de-uso)
2. [Diagrama de Clases UML](#2-diagrama-de-clases-uml)
3. [Diagramas de Secuencia UML](#3-diagramas-de-secuencia-uml)
4. [Diagrama de Componentes Interno](#4-diagrama-de-componentes-interno)
5. [Diagrama Entidad-Relación (ER)](#5-diagrama-entidad-relación-er)

---

## 1. Diagrama de Casos de Uso

### 1.1 Actores del Sistema

| Actor | Tipo | Descripción |
|-------|------|-------------|
| **Microservicio Externo** | Sistema externo | Cualquiera de los 18 microservicios del ERP (ms-matriculas, ms-pagos, etc.) que envían eventos de auditoría |
| **Administrador del Sistema** | Usuario humano | Persona que consulta logs, revisa estadísticas, gestiona tokens y ejecuta purgas manuales |
| **Scheduler (RetentionService)** | Sistema interno | Proceso automático en background que purga logs antiguos según la política TTL |
| **ms-autenticación** | Sistema externo | Microservicio que valida tokens de sesión de usuarios |
| **ms-roles-permisos** | Sistema externo | Microservicio que verifica permisos de usuarios |

### 1.2 Diagrama de Casos de Uso

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ms-auditoria (Sistema)                             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    GESTIÓN DE LOGS                                   │    │
│  │                                                                     │    │
│  │   ┌──────────────────────┐     ┌──────────────────────┐            │    │
│  │   │  CU-01: Registrar    │     │  CU-02: Registrar    │            │    │
│  │   │  Log de Auditoría    │     │  Logs en Batch       │            │    │
│  │   └──────────┬───────────┘     └──────────┬───────────┘            │    │
│  │              │ «include»                  │ «include»              │    │
│  │              ▼                             ▼                        │    │
│  │   ┌──────────────────────────────────────────────┐                 │    │
│  │   │  CU-03: Validar API Key del Microservicio    │                 │    │
│  │   └──────────────────────────────────────────────┘                 │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    CONSULTA DE LOGS                                  │    │
│  │                                                                     │    │
│  │   ┌──────────────────────┐     ┌──────────────────────┐            │    │
│  │   │  CU-04: Consultar    │     │  CU-05: Filtrar      │            │    │
│  │   │  Logs con Paginación │     │  Logs Avanzado       │            │    │
│  │   └──────────────────────┘     └──────────────────────┘            │    │
│  │                                                                     │    │
│  │   ┌──────────────────────┐     ┌──────────────────────┐            │    │
│  │   │  CU-06: Obtener Log  │     │  CU-07: Trazar       │            │    │
│  │   │  por ID              │     │  Request (X-Req-ID)  │            │    │
│  │   └──────────────────────┘     └──────────────────────┘            │    │
│  │                                                                     │    │
│  │   ┌──────────────────────┐     ┌──────────────────────┐            │    │
│  │   │  CU-08: Consultar    │     │  CU-09: Buscar       │            │    │
│  │   │  Logs por Usuario    │     │  Full-Text en Detalle │            │    │
│  │   └──────────────────────┘     └──────────────────────┘            │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    ESTADÍSTICAS Y MÉTRICAS                          │    │
│  │                                                                     │    │
│  │   ┌──────────────────────────────────────────┐                     │    │
│  │   │  CU-10: Obtener Estadísticas Generales   │                     │    │
│  │   │  (logs/servicio, errores, duración avg)   │                     │    │
│  │   └──────────────────────────────────────────┘                     │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    ADMINISTRACIÓN                                    │    │
│  │                                                                     │    │
│  │   ┌──────────────────────┐     ┌──────────────────────┐            │    │
│  │   │  CU-11: Purgar Logs  │     │  CU-12: Purga        │            │    │
│  │   │  Antiguos (Manual)   │     │  Automática (TTL)    │            │    │
│  │   └──────────┬───────────┘     └──────────────────────┘            │    │
│  │              │ «include»                                            │    │
│  │              ▼                                                      │    │
│  │   ┌──────────────────────────────────────────────┐                 │    │
│  │   │  CU-03: Validar API Key del Microservicio    │                 │    │
│  │   └──────────────────────────────────────────────┘                 │    │
│  │                                                                     │    │
│  │   ┌──────────────────────┐     ┌──────────────────────┐            │    │
│  │   │  CU-13: Verificar    │     │  CU-14: Health       │            │    │
│  │   │  Estado del Servicio │     │  Check               │            │    │
│  │   └──────────────────────┘     └──────────────────────┘            │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

ACTORES Y SUS RELACIONES:

  ┌───────────────┐                              ┌───────────────────┐
  │ Microservicio │───────► CU-01, CU-02         │  Administrador    │
  │   Externo     │                              │  del Sistema      │
  └───────────────┘                              └───────────────────┘
         │                                              │
         ├───► CU-03 (vía «include»)                    ├───► CU-04, CU-05
         │                                              ├───► CU-06, CU-07
         │                                              ├───► CU-08, CU-09
         │                                              ├───► CU-10
         │                                              ├───► CU-11
         │                                              └───► CU-13, CU-14
         │
  ┌───────────────┐
  │  Scheduler    │───────► CU-12 (Purga Automática TTL)
  │ (Retention)   │
  └───────────────┘
```

### 1.3 Descripción de Casos de Uso

| ID | Caso de Uso | Actor(es) | Endpoint | Precondiciones | Postcondiciones |
|----|-------------|-----------|----------|----------------|-----------------|
| CU-01 | Registrar Log de Auditoría | Microservicio Externo | `POST /api/v1/audit/log` | API Key válido (producción) | Log persistido en BD, respuesta 201 |
| CU-02 | Registrar Logs en Batch | Microservicio Externo | `POST /api/v1/audit/log/batch` | API Key válido, máx 1000 logs | Logs persistidos atómicamente |
| CU-03 | Validar API Key | Sistema (interno) | — | Header X-API-Key presente | Token verificado con SHA-256 contra BD |
| CU-04 | Consultar Logs con Paginación | Administrador | `GET /api/v1/audit/logs` | Ninguna | Lista paginada de logs |
| CU-05 | Filtrar Logs Avanzado | Administrador | `GET /api/v1/audit/logs?filtros` | Ninguna | Logs filtrados por servicio, método, código, fecha, usuario |
| CU-06 | Obtener Log por ID | Administrador | `GET /api/v1/audit/log/{id}` | UUID válido | Log específico o 404 |
| CU-07 | Trazar Request | Administrador | `GET /api/v1/audit/trace/{request_id}` | X-Request-ID existente | Todos los logs asociados al request |
| CU-08 | Consultar Logs por Usuario | Administrador | `GET /api/v1/audit/user/{usuario_id}` | UUID de usuario válido | Historial del usuario paginado |
| CU-09 | Buscar Full-Text en Detalle | Administrador | `GET /api/v1/audit/logs?search_text=...` | Índice GIN activo | Resultados de búsqueda en español |
| CU-10 | Obtener Estadísticas | Administrador | `GET /api/v1/audit/stats` | Ninguna | Métricas por servicio, errores, duración |
| CU-11 | Purgar Logs Antiguos (Manual) | Administrador | `DELETE /api/v1/audit/purge` | API Key válido, fecha límite | Logs anteriores a la fecha eliminados |
| CU-12 | Purga Automática (TTL) | Scheduler | — (interno) | Servicio en ejecución | Logs > RETENTION_DAYS eliminados diariamente |
| CU-13 | Verificar Estado del Servicio | Administrador | `GET /api/v1/audit/health` | Ninguna | Respuesta "is running" |
| CU-14 | Health Check | Administrador | `GET /` | Ninguna | Info del microservicio |

---

## 2. Diagrama de Clases UML

### 2.1 Diagrama Completo

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CAPA DE PRESENTACIÓN                               │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────┐              │
│  │                    «controller» audit_routes                   │              │
│  │                    (APIRouter: /api/v1/audit)                  │              │
│  ├───────────────────────────────────────────────────────────────┤              │
│  │ + router: APIRouter                                           │              │
│  ├───────────────────────────────────────────────────────────────┤              │
│  │ + health_check() : MessageResponse                            │              │
│  │ + create_audit_log(data, db, _api_key) : DataResponse         │              │
│  │ + create_audit_logs_batch(logs, db, _api_key) : DataResponse  │              │
│  │ + get_audit_logs(page, page_size, filtros, db) : Paginated    │              │
│  │ + get_audit_log_by_id(audit_id, db) : DataResponse            │              │
│  │ + trace_request(request_id, db) : DataResponse                │              │
│  │ + get_user_audit_logs(usuario_id, page, db) : Paginated       │              │
│  │ + get_statistics(db) : StatsResponse                          │              │
│  │ + purge_logs(before_date, db, _api_key) : MessageResponse     │              │
│  └───────────────────────────────┬───────────────────────────────┘              │
│                                  │ usa                                           │
└──────────────────────────────────┼──────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CAPA DE NEGOCIO                                    │
│                                                                                 │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐     │
│  │      «service» AuditService     │   │  «service» StatisticsService    │     │
│  ├─────────────────────────────────┤   ├─────────────────────────────────┤     │
│  │ - db: AsyncSession              │   │ - repo: AuditRepository         │     │
│  │ - repo: AuditRepository         │   ├─────────────────────────────────┤     │
│  ├─────────────────────────────────┤   │ + __init__(db: AsyncSession)    │     │
│  │ + __init__(db: AsyncSession)    │   │ + get_general_stats() : dict    │     │
│  │ + create_log(data) : Response   │   └─────────────────────────────────┘     │
│  │ + create_logs_batch(logs) : []  │                                            │
│  │ + get_by_id(id) : Response?     │   ┌─────────────────────────────────┐     │
│  │ + get_logs(page, filters) : Pg  │   │  «service» RetentionService     │     │
│  │ + get_by_request_id(rid) : []   │   ├─────────────────────────────────┤     │
│  │ + get_by_usuario(uid, pg) : Pg  │   │ - _task: asyncio.Task | None    │     │
│  │ + purge_old_logs(date) : int    │   │ - _running: bool                │     │
│  └───────────────┬─────────────────┘   ├─────────────────────────────────┤     │
│                  │ usa                  │ + start() : None                │     │
│                  ▼                      │ + stop() : None                 │     │
│  ┌─────────────────────────────────┐   │ + purge_old_logs() : int        │     │
│  │ «service» AuthService           │   │ - _scheduler_loop() : None      │     │
│  ├─────────────────────────────────┤   │ - _seconds_until_next() : float │     │
│  │ + validate_session(token): dict?│   └─────────────────────────────────┘     │
│  │ + check_permission(token): bool │                                            │
│  └─────────────────────────────────┘                                            │
│                                                                                 │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CAPA DE DATOS                                      │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────┐              │
│  │              «repository» AuditRepository                     │              │
│  ├───────────────────────────────────────────────────────────────┤              │
│  │ - session: AsyncSession                                       │              │
│  ├───────────────────────────────────────────────────────────────┤              │
│  │ + __init__(session: AsyncSession)                             │              │
│  │ + save(audit_log: AuditLog) : AuditLog                        │              │
│  │ + save_batch(logs: List[AuditLog]) : List[AuditLog]           │              │
│  │ + find_by_id(id: UUID) : AuditLog?                            │              │
│  │ + find_all(page, size, **filtros) : (List, int)               │              │
│  │ + find_by_request_id(rid: str) : List[AuditLog]               │              │
│  │ + find_by_usuario(uid, page, size) : (List, int)              │              │
│  │ + count_total() : int                                         │              │
│  │ + count_by_servicio() : List[tuple]                           │              │
│  │ + count_by_codigo_respuesta() : List[tuple]                   │              │
│  │ + average_duration_by_servicio() : List[tuple]                │              │
│  │ + error_rate_by_servicio() : List[tuple]                      │              │
│  │ + delete_before(date: datetime) : int                         │              │
│  └───────────────────────────────────────────────────────────────┘              │
│                                                                                 │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CAPA DE DOMINIO (Modelos + Schemas)                │
│                                                                                 │
│  ┌────────────────────────────────┐   ┌────────────────────────────────┐        │
│  │    «entity» AuditLog           │   │  «entity» MicroserviceToken    │        │
│  │    (tabla: audit_logs)         │   │  (tabla: microservice_tokens)  │        │
│  ├────────────────────────────────┤   ├────────────────────────────────┤        │
│  │ + id: UUID [PK]               │   │ + id: UUID [PK]               │        │
│  │ + request_id: String(50)      │   │ + nombre_microservicio: Str(50)│        │
│  │ + servicio: String(50)        │   │ + token_hash: String(256)     │        │
│  │ + endpoint: String(200)       │   │ + activo: Boolean             │        │
│  │ + metodo: String(10)          │   │ + created_at: Timestamp(tz)   │        │
│  │ + codigo_respuesta: Integer   │   │ + updated_at: Timestamp(tz)   │        │
│  │ + duracion_ms: Integer        │   └────────────────────────────────┘        │
│  │ + usuario_id: UUID?           │                                              │
│  │ + detalle: Text?              │                                              │
│  │ + ip_origen: String(45)?      │                                              │
│  │ + timestamp_evento: Timestamp │                                              │
│  │ + created_at: Timestamp       │                                              │
│  └────────────────────────────────┘                                              │
│                                                                                 │
│  ┌────────────────────────────────┐   ┌────────────────────────────────┐        │
│  │  «schema» AuditLogCreate       │   │  «schema» AuditLogResponse     │        │
│  ├────────────────────────────────┤   ├────────────────────────────────┤        │
│  │ + timestamp: datetime          │   │ + id: UUID                    │        │
│  │ + nombre_microservicio: str    │   │ + request_id: str             │        │
│  │ + endpoint: str                │   │ + servicio: str               │        │
│  │ + metodo_http: str             │   │ + endpoint: str               │        │
│  │ + codigo_respuesta: int        │   │ + metodo: str                 │        │
│  │ + duracion_ms: int             │   │ + codigo_respuesta: int       │        │
│  │ + usuario_id: UUID?            │   │ + duracion_ms: int            │        │
│  │ + detalle: str?                │   │ + usuario_id: UUID?           │        │
│  │ + ip_origen: str?              │   │ + detalle: str?               │        │
│  │ + request_id: str?             │   │ + ip_origen: str?             │        │
│  └────────────────────────────────┘   │ + timestamp_evento: datetime  │        │
│                                        │ + created_at: datetime        │        │
│  ┌────────────────────────────────┐   └────────────────────────────────┘        │
│  │  «schema» AuditLogFilter       │                                              │
│  ├────────────────────────────────┤   ┌────────────────────────────────┐        │
│  │ + servicio: str?               │   │  «schema» Respuestas Genéricas │        │
│  │ + metodo_http: str?            │   ├────────────────────────────────┤        │
│  │ + codigo_respuesta: int?       │   │ MessageResponse {success, msg} │        │
│  │ + usuario_id: UUID?            │   │ DataResponse<T> {success, data}│        │
│  │ + fecha_inicio: datetime?      │   │ PaginatedResponse<T>          │        │
│  │ + fecha_fin: datetime?         │   │   {data, total, page, pages}  │        │
│  │ + request_id: str?             │   │ ErrorResponse {error, detail} │        │
│  │ + search_text: str?            │   │ StatsResponse {data: dict}    │        │
│  └────────────────────────────────┘   └────────────────────────────────┘        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Relaciones entre Clases

```
┌──────────────┐         ┌──────────────────┐         ┌──────────────────┐
│ audit_routes │ ──usa──►│  AuditService    │ ──usa──►│ AuditRepository  │
│ (Controller) │         │  (Service)       │         │ (Repository)     │
└──────┬───────┘         └────────┬─────────┘         └────────┬─────────┘
       │                          │                             │
       │ ──usa──► StatisticsService ──usa──► AuditRepository    │
       │                                                        │
       │ ──depends──► verify_api_key() ──consulta──►            │
       │              (core/auth.py)        MicroserviceToken   │
       │                                                        │
       │ ──depends──► get_db()                                  │
       │              (core/dependencies.py)                    │
       │                                                        │
       │                          │ opera sobre                 │
       │                          ▼                             │
       │                 ┌──────────────────┐                   │
       │                 │    AuditLog      │◄──────────────────┘
       │                 │    (Model)       │
       │                 └──────────────────┘
       │
       │ ──valida con──►  AuditLogCreate (schema entrada)
       │ ──responde con──► AuditLogResponse (schema salida)
       │ ──filtra con──►  AuditLogFilter (schema filtros)

RetentionService ──────► AsyncSessionLocal ──────► AuditLog (DELETE directo)
                         (sesión propia)
```

### 2.3 Tabla de Relaciones

| Clase Origen | Relación | Clase Destino | Cardinalidad | Descripción |
|---|---|---|---|---|
| `audit_routes` | usa | `AuditService` | 1 → 1 | Cada endpoint crea una instancia de servicio |
| `audit_routes` | usa | `StatisticsService` | 1 → 1 | Endpoint /stats usa servicio de estadísticas |
| `audit_routes` | depends | `verify_api_key()` | 1 → 1 | POST y DELETE requieren validación |
| `audit_routes` | depends | `get_db()` | 1 → 1 | Inyección de AsyncSession por request |
| `AuditService` | usa | `AuditRepository` | 1 → 1 | Composición: servicio contiene repositorio |
| `StatisticsService` | usa | `AuditRepository` | 1 → 1 | Composición: servicio contiene repositorio |
| `AuditRepository` | opera sobre | `AuditLog` | 1 → * | CRUD sobre la entidad |
| `verify_api_key` | consulta | `MicroserviceToken` | 1 → 0..1 | Busca token activo por hash |
| `RetentionService` | elimina | `AuditLog` | 1 → * | DELETE WHERE timestamp < cutoff |
| `AuditLogCreate` | mapea a | `AuditLog` | 1 → 1 | Schema → Modelo ORM |
| `AuditLog` | mapea a | `AuditLogResponse` | 1 → 1 | Modelo ORM → Schema (model_validate) |

---

## 3. Diagramas de Secuencia UML

### 3.1 Secuencia: Crear Log de Auditoría (POST /api/v1/audit/log)

```
┌──────────────┐  ┌───────────────┐  ┌────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────┐
│Microservicio │  │RequestID      │  │RateLimit   │  │audit_routes  │  │verify_api_key│  │AuditService│  │AuditRepo │
│  Externo     │  │Middleware     │  │Middleware  │  │(Controller)  │  │(core/auth)   │  │(Service)   │  │(Repo)    │
└──────┬───────┘  └──────┬────────┘  └─────┬──────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘  └────┬─────┘
       │                 │                  │                │                 │                │              │
       │  POST /log      │                  │                │                 │                │              │
       │  X-API-Key: xxx │                  │                │                 │                │              │
       │  Body: {...}    │                  │                │                 │                │              │
       │────────────────►│                  │                │                 │                │              │
       │                 │                  │                │                 │                │              │
       │                 │ Inyecta/propaga  │                │                 │                │              │
       │                 │ X-Request-ID     │                │                 │                │              │
       │                 │ Inicia timer     │                │                 │                │              │
       │                 │─────────────────►│                │                 │                │              │
       │                 │                  │                │                 │                │              │
       │                 │                  │ Verifica IP    │                 │                │              │
       │                 │                  │ sliding window │                 │                │              │
       │                 │                  │                │                 │                │              │
       │                 │                  │  [OK: bajo     │                 │                │              │
       │                 │                  │   límite]      │                 │                │              │
       │                 │                  │───────────────►│                 │                │              │
       │                 │                  │                │                 │                │              │
       │                 │                  │                │  Depends(       │                │              │
       │                 │                  │                │  verify_api_key)│                │              │
       │                 │                  │                │────────────────►│                │              │
       │                 │                  │                │                 │                │              │
       │                 │                  │                │                 │ SHA-256(key)   │              │
       │                 │                  │                │                 │──────┐         │              │
       │                 │                  │                │                 │      │         │              │
       │                 │                  │                │                 │◄─────┘         │              │
       │                 │                  │                │                 │                │              │
       │                 │                  │                │                 │ SELECT FROM    │              │
       │                 │                  │                │                 │ microservice_  │              │
       │                 │                  │                │                 │ tokens WHERE   │              │
       │                 │                  │                │                 │ hash = ? AND   │              │
       │                 │                  │                │                 │ activo = true  │              │
       │                 │                  │                │                 │──────────────────────────────►│
       │                 │                  │                │                 │                │              │
       │                 │                  │                │                 │◄─ token_record ───────────────│
       │                 │                  │                │                 │                │              │
       │                 │                  │                │  [API Key OK]   │                │              │
       │                 │                  │                │◄────────────────│                │              │
       │                 │                  │                │                 │                │              │
       │                 │                  │                │  Pydantic valida                 │              │
       │                 │                  │                │  AuditLogCreate                  │              │
       │                 │                  │                │──────┐                           │              │
       │                 │                  │                │      │                           │              │
       │                 │                  │                │◄─────┘                           │              │
       │                 │                  │                │                                  │              │
       │                 │                  │                │  service.create_log(data)        │              │
       │                 │                  │                │─────────────────────────────────►│              │
       │                 │                  │                │                                  │              │
       │                 │                  │                │                  Mapea schema    │              │
       │                 │                  │                │                  → AuditLog ORM  │              │
       │                 │                  │                │                                  │              │
       │                 │                  │                │                  repo.save(log)  │              │
       │                 │                  │                │                  │───────────────────────────►│
       │                 │                  │                │                  │               │  session.add│
       │                 │                  │                │                  │               │  flush()    │
       │                 │                  │                │                  │               │  refresh()  │
       │                 │                  │                │                  │◄──────────────────────────│
       │                 │                  │                │                  │               │             │
       │                 │                  │                │                  │ db.commit()   │             │
       │                 │                  │                │                  │──────┐        │             │
       │                 │                  │                │                  │      │        │             │
       │                 │                  │                │                  │◄─────┘        │             │
       │                 │                  │                │                  │               │             │
       │                 │                  │                │  AuditLogResponse                │             │
       │                 │                  │                │  (model_validate)                │             │
       │                 │                  │                │◄─────────────────────────────────│             │
       │                 │                  │                │                                  │             │
       │                 │                  │  201 Created   │                                  │             │
       │                 │                  │  + RateLimit   │                                  │             │
       │                 │                  │  headers       │                                  │             │
       │                 │                  │◄───────────────│                                  │             │
       │                 │                  │                │                                  │             │
       │                 │  + X-Request-ID  │                │                                  │             │
       │                 │  + X-Response-   │                │                                  │             │
       │                 │    Time-ms       │                │                                  │             │
       │                 │◄─────────────────│                │                                  │             │
       │                 │                  │                │                                  │             │
       │  201 Created    │                  │                │                                  │             │
       │  {success:true, │                  │                │                                  │             │
       │   data:{...}}   │                  │                │                                  │             │
       │◄────────────────│                  │                │                                  │             │
       │                 │                  │                │                                  │             │
```

### 3.2 Secuencia: Consultar Logs con Filtros (GET /api/v1/audit/logs)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│Administrador │     │audit_routes  │     │AuditService  │     │AuditRepo     │     │PostgreSQL│
│              │     │(Controller)  │     │(Service)     │     │(Repository)  │     │          │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └────┬─────┘
       │                    │                    │                    │                   │
       │ GET /logs?servicio │                    │                    │                   │
       │ =ms-matriculas    │                    │                    │                   │
       │ &page=1           │                    │                    │                   │
       │ &page_size=20     │                    │                    │                   │
       │───────────────────►│                    │                    │                   │
       │                    │                    │                    │                   │
       │                    │ Construye          │                    │                   │
       │                    │ AuditLogFilter     │                    │                   │
       │                    │──────┐             │                    │                   │
       │                    │      │             │                    │                   │
       │                    │◄─────┘             │                    │                   │
       │                    │                    │                    │                   │
       │                    │ service.get_logs() │                    │                   │
       │                    │───────────────────►│                    │                   │
       │                    │                    │                    │                   │
       │                    │                    │ repo.find_all()    │                   │
       │                    │                    │ (page, filters)    │                   │
       │                    │                    │───────────────────►│                   │
       │                    │                    │                    │                   │
       │                    │                    │                    │ SELECT count(id)  │
       │                    │                    │                    │ WHERE servicio=?  │
       │                    │                    │                    │──────────────────►│
       │                    │                    │                    │                   │
       │                    │                    │                    │◄── total: 150 ────│
       │                    │                    │                    │                   │
       │                    │                    │                    │ SELECT * FROM     │
       │                    │                    │                    │ audit_logs WHERE  │
       │                    │                    │                    │ servicio=?        │
       │                    │                    │                    │ ORDER BY timestamp│
       │                    │                    │                    │ OFFSET 0 LIMIT 20 │
       │                    │                    │                    │──────────────────►│
       │                    │                    │                    │                   │
       │                    │                    │                    │◄── [20 rows] ─────│
       │                    │                    │                    │                   │
       │                    │                    │◄── (results, 150) ─│                   │
       │                    │                    │                    │                   │
       │                    │                    │ model_validate()   │                   │
       │                    │                    │ por cada resultado │                   │
       │                    │                    │──────┐             │                   │
       │                    │                    │      │             │                   │
       │                    │                    │◄─────┘             │                   │
       │                    │                    │                    │                   │
       │                    │  PaginatedResponse │                    │                   │
       │                    │  {data, total:150, │                    │                   │
       │                    │   page:1, pages:8} │                    │                   │
       │                    │◄───────────────────│                    │                   │
       │                    │                    │                    │                   │
       │  200 OK            │                    │                    │                   │
       │  {success:true,    │                    │                    │                   │
       │   data:[...],      │                    │                    │                   │
       │   total:150,       │                    │                    │                   │
       │   total_pages:8}   │                    │                    │                   │
       │◄───────────────────│                    │                    │                   │
       │                    │                    │                    │                   │
```

### 3.3 Secuencia: Scheduler de Retención Automática (TTL)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│ FastAPI      │     │Retention     │     │AsyncSession   │     │PostgreSQL│
│ Lifespan     │     │Service       │     │Local          │     │          │
└──────┬───────┘     └──────┬───────┘     └──────┬────────┘     └────┬─────┘
       │                    │                    │                    │
       │  ══ STARTUP ══     │                    │                    │
       │                    │                    │                    │
       │  start()           │                    │                    │
       │───────────────────►│                    │                    │
       │                    │                    │                    │
       │                    │ _running = True    │                    │
       │                    │ asyncio.create_    │                    │
       │                    │ task(scheduler)    │                    │
       │                    │──────┐             │                    │
       │                    │      │             │                    │
       │                    │◄─────┘             │                    │
       │                    │                    │                    │
       │  ◄── return ───────│                    │                    │
       │                    │                    │                    │
       │   ══ SCHEDULER LOOP (background) ══    │                    │
       │                    │                    │                    │
       │                    │ _seconds_until_    │                    │
       │                    │ next_run()         │                    │
       │                    │ (ej: 28800 seg     │                    │
       │                    │  hasta 03:00 UTC)  │                    │
       │                    │──────┐             │                    │
       │                    │      │             │                    │
       │                    │◄─────┘             │                    │
       │                    │                    │                    │
       │                    │ asyncio.sleep(     │                    │
       │                    │   28800)           │                    │
       │                    │──────┐             │                    │
       │                    │      │ zzz...      │                    │
       │                    │      │ (espera     │                    │
       │                    │      │  hasta      │                    │
       │                    │      │  03:00 UTC) │                    │
       │                    │◄─────┘             │                    │
       │                    │                    │                    │
       │                    │ ══ 03:00 UTC ══    │                    │
       │                    │ purge_old_logs()   │                    │
       │                    │                    │                    │
       │                    │ cutoff = now() -   │                    │
       │                    │ timedelta(90 days) │                    │
       │                    │                    │                    │
       │                    │ Abre sesión propia │                    │
       │                    │───────────────────►│                    │
       │                    │                    │                    │
       │                    │                    │ DELETE FROM        │
       │                    │                    │ audit_logs WHERE   │
       │                    │                    │ timestamp_evento   │
       │                    │                    │ < cutoff_date      │
       │                    │                    │───────────────────►│
       │                    │                    │                    │
       │                    │                    │◄── rowcount: 1523 ─│
       │                    │                    │                    │
       │                    │                    │ COMMIT             │
       │                    │                    │───────────────────►│
       │                    │                    │                    │
       │                    │                    │◄── OK ─────────────│
       │                    │                    │                    │
       │                    │◄── 1523 eliminados │                    │
       │                    │                    │                    │
       │                    │ logger.info(       │                    │
       │                    │  "retention_purge_ │                    │
       │                    │   completed",      │                    │
       │                    │  deleted: 1523)    │                    │
       │                    │                    │                    │
       │                    │ (vuelve al loop    │                    │
       │                    │  → sleep hasta     │                    │
       │                    │  mañana 03:00 UTC) │                    │
       │                    │                    │                    │
       │  ══ SHUTDOWN ══    │                    │                    │
       │                    │                    │                    │
       │  stop()            │                    │                    │
       │───────────────────►│                    │                    │
       │                    │                    │                    │
       │                    │ _running = False   │                    │
       │                    │ task.cancel()      │                    │
       │                    │──────┐             │                    │
       │                    │      │             │                    │
       │                    │◄─────┘             │                    │
       │                    │                    │                    │
```

### 3.4 Secuencia: Validación de API Key (Detalle)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│  Request     │     │verify_api_key│     │  AsyncSession │     │PostgreSQL│
│  (Depends)   │     │(core/auth)   │     │  (get_db)    │     │          │
└──────┬───────┘     └──────┬───────┘     └──────┬────────┘     └────┬─────┘
       │                    │                    │                    │
       │ Header: X-API-Key  │                    │                    │
       │───────────────────►│                    │                    │
       │                    │                    │                    │
       │                    │ api_key == None?   │                    │
       │                    │──────┐             │                    │
       │                    │      │             │                    │
       │                    │◄─────┘             │                    │
       │                    │                    │                    │
       │  ALT [No API Key + development/testing] │                    │
       │  ┌─────────────────────────────────────────────────────────┐│
       │  │                 │                    │                    ││
       │  │                 │ return None        │                    ││
       │  │                 │ (acceso permitido) │                    ││
       │  │◄────────────────│                    │                    ││
       │  └─────────────────────────────────────────────────────────┘│
       │                    │                    │                    │
       │  ALT [No API Key + production]          │                    │
       │  ┌─────────────────────────────────────────────────────────┐│
       │  │                 │                    │                    ││
       │  │                 │ raise HTTPException│                    ││
       │  │                 │ (401 Unauthorized) │                    ││
       │  │◄────────────────│                    │                    ││
       │  └─────────────────────────────────────────────────────────┘│
       │                    │                    │                    │
       │  ALT [API Key presente]                 │                    │
       │  ┌─────────────────────────────────────────────────────────┐│
       │  │                 │                    │                    ││
       │  │                 │ hash = SHA-256(key)│                    ││
       │  │                 │──────┐             │                    ││
       │  │                 │      │             │                    ││
       │  │                 │◄─────┘             │                    ││
       │  │                 │                    │                    ││
       │  │                 │ SELECT * FROM      │                    ││
       │  │                 │ microservice_tokens│                    ││
       │  │                 │ WHERE token_hash   │                    ││
       │  │                 │ = hash AND activo  │                    ││
       │  │                 │ = True             │                    ││
       │  │                 │───────────────────►│                    ││
       │  │                 │                    │───────────────────►││
       │  │                 │                    │◄───────────────────││
       │  │                 │◄───────────────────│                    ││
       │  │                 │                    │                    ││
       │  │  [token found]  │ return token_record│                    ││
       │  │◄────────────────│                    │                    ││
       │  │                 │                    │                    ││
       │  │  [not found]    │ raise HTTPException│                    ││
       │  │                 │ (401 Unauthorized) │                    ││
       │  │◄────────────────│                    │                    ││
       │  └─────────────────────────────────────────────────────────┘│
       │                    │                    │                    │
```

### 3.5 Secuencia: Obtener Estadísticas (GET /api/v1/audit/stats)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│Administrador │     │audit_routes  │     │Statistics    │     │AuditRepo     │     │PostgreSQL│
│              │     │(Controller)  │     │Service       │     │(Repository)  │     │          │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └────┬─────┘
       │                    │                    │                    │                   │
       │  GET /stats        │                    │                    │                   │
       │───────────────────►│                    │                    │                   │
       │                    │                    │                    │                   │
       │                    │ get_general_stats()│                    │                   │
       │                    │───────────────────►│                    │                   │
       │                    │                    │                    │                   │
       │                    │                    │ count_total()      │                   │
       │                    │                    │───────────────────►│──── COUNT(*) ────►│
       │                    │                    │◄── total: 5000 ────│◄──────────────────│
       │                    │                    │                    │                   │
       │                    │                    │ count_by_servicio()│                   │
       │                    │                    │───────────────────►│── GROUP BY srv ──►│
       │                    │                    │◄── [{srv, cnt}] ───│◄──────────────────│
       │                    │                    │                    │                   │
       │                    │                    │ count_by_codigo()  │                   │
       │                    │                    │───────────────────►│── GROUP BY cod ──►│
       │                    │                    │◄── [{cod, cnt}] ───│◄──────────────────│
       │                    │                    │                    │                   │
       │                    │                    │ avg_duration()     │                   │
       │                    │                    │───────────────────►│── AVG(dur_ms) ───►│
       │                    │                    │◄── [{srv, avg}] ───│◄──────────────────│
       │                    │                    │                    │                   │
       │                    │                    │ error_rate()       │                   │
       │                    │                    │───────────────────►│── SUM(CASE) ─────►│
       │                    │                    │◄── [{srv, rate}] ──│◄──────────────────│
       │                    │                    │                    │                   │
       │                    │  StatsResponse     │                    │                   │
       │                    │  {total, por_srv,  │                    │                   │
       │                    │   por_cod, avg,    │                    │                   │
       │                    │   errores}         │                    │                   │
       │                    │◄───────────────────│                    │                   │
       │                    │                    │                    │                   │
       │  200 OK            │                    │                    │                   │
       │  {success: true,   │                    │                    │                   │
       │   data: {...}}     │                    │                    │                   │
       │◄───────────────────│                    │                    │                   │
       │                    │                    │                    │                   │
```

---

## 4. Diagrama de Componentes Interno

### 4.1 Diagrama de Componentes (Clean Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              ms-auditoria (:8019)                                   │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                     «component» MIDDLEWARE CHAIN                             │    │
│  │                                                                             │    │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │    │
│  │  │  RequestID       │  │  RateLimit       │  │  CORS            │          │    │
│  │  │  Middleware       │──│  Middleware       │──│  Middleware       │          │    │
│  │  │                  │  │                  │  │  (Starlette)     │          │    │
│  │  │ • X-Request-ID   │  │ • Sliding window │  │ • Orígenes       │          │    │
│  │  │ • Response time  │  │ • 100 req/60s    │  │ • Methods        │          │    │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘          │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────┬───────────────┘    │
│                                                                │                    │
│  ┌─────────────────────────────────────────────────────────────┼───────────────┐    │
│  │                     «component» EXCEPTION HANDLERS          │               │    │
│  │                                                             │               │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │               │    │
│  │  │ HTTP 4xx/5xx │  │ Validation   │  │ Unhandled    │     │               │    │
│  │  │ Handler      │  │ 422 Handler  │  │ 500 Handler  │     │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │               │    │
│  │                                                             │               │    │
│  └─────────────────────────────────────────────────────────────┼───────────────┘    │
│                                                                │                    │
│                                                                ▼                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                     «component» PRESENTACIÓN (Routes)                       │    │
│  │                                                                             │    │
│  │  ┌──────────────────────────────────────────────────────┐                  │    │
│  │  │              audit_routes.py (APIRouter)              │                  │    │
│  │  │              /api/v1/audit/*                          │                  │    │
│  │  │                                                      │                  │    │
│  │  │  POST /log    POST /log/batch   GET /logs            │                  │    │
│  │  │  GET /log/{id}   GET /trace/{rid}                    │                  │    │
│  │  │  GET /user/{uid}   GET /stats   DELETE /purge        │                  │    │
│  │  │  GET /health                                         │                  │    │
│  │  └────────────────────────┬─────────────────────────────┘                  │    │
│  │                           │                                                 │    │
│  │  Dependencias inyectadas: │                                                 │    │
│  │  ┌──────────────┐  ┌─────┴──────────┐                                     │    │
│  │  │ verify_api_  │  │ get_db()       │                                     │    │
│  │  │ key()        │  │ (AsyncSession) │                                     │    │
│  │  │ (core/auth)  │  │ (dependencies) │                                     │    │
│  │  └──────────────┘  └────────────────┘                                     │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────┬───────────────┘    │
│                                                                │                    │
│                                                                ▼                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                     «component» LÓGICA DE NEGOCIO (Services)                │    │
│  │                                                                             │    │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │    │
│  │  │  AuditService    │  │ StatisticsService│  │ RetentionService │          │    │
│  │  │                  │  │                  │  │                  │          │    │
│  │  │ • create_log()   │  │ • get_general_   │  │ • start()        │          │    │
│  │  │ • create_batch() │  │   stats()        │  │ • stop()         │          │    │
│  │  │ • get_logs()     │  │                  │  │ • purge_old_     │          │    │
│  │  │ • get_by_id()    │  │  Usa:            │  │   logs()         │          │    │
│  │  │ • get_by_rid()   │  │  AuditRepository │  │ • _scheduler_    │          │    │
│  │  │ • get_by_user()  │  │                  │  │   loop()         │          │    │
│  │  │ • purge()        │  │                  │  │                  │          │    │
│  │  └────────┬─────────┘  └────────┬─────────┘  └──────────────────┘          │    │
│  │           │                     │                                           │    │
│  │  ┌────────┴─────────┐          │    ┌──────────────────┐                   │    │
│  │  │  AuthService     │          │    │  AESCipher       │                   │    │
│  │  │                  │          │    │  (core/security)  │                   │    │
│  │  │ • validate_      │          │    │ • encrypt()      │                   │    │
│  │  │   session()      │          │    │ • decrypt()      │                   │    │
│  │  │ • check_         │          │    │ (disponible)     │                   │    │
│  │  │   permission()   │          │    └──────────────────┘                   │    │
│  │  └──────────────────┘          │                                           │    │
│  │                                │                                           │    │
│  └────────────────────────────────┼───────────────────────────────────────────┘    │
│                                   │                                                │
│                                   ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                     «component» ACCESO A DATOS (Repository)                 │    │
│  │                                                                             │    │
│  │  ┌──────────────────────────────────────────────────────┐                  │    │
│  │  │              AuditRepository                          │                  │    │
│  │  │                                                      │                  │    │
│  │  │  CRUD:       save(), save_batch(), find_by_id(),     │                  │    │
│  │  │             find_all(), find_by_request_id(),        │                  │    │
│  │  │             find_by_usuario(), delete_before()       │                  │    │
│  │  │                                                      │                  │    │
│  │  │  STATS:      count_total(), count_by_servicio(),     │                  │    │
│  │  │             count_by_codigo_respuesta(),             │                  │    │
│  │  │             average_duration_by_servicio(),          │                  │    │
│  │  │             error_rate_by_servicio()                 │                  │    │
│  │  └────────────────────────┬─────────────────────────────┘                  │    │
│  │                           │                                                 │    │
│  └───────────────────────────┼─────────────────────────────────────────────────┘    │
│                              │                                                      │
│                              ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                     «component» BASE DE DATOS (Database)                    │    │
│  │                                                                             │    │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │    │
│  │  │  connection.py   │  │  session.py      │  │  unit_of_work.py │          │    │
│  │  │                  │  │                  │  │  (disponible)    │          │    │
│  │  │ • async_engine   │  │ • AsyncSession   │  │ • commit()      │          │    │
│  │  │ • sync_engine    │  │   Local          │  │ • rollback()    │          │    │
│  │  │ • pool config    │  │                  │  │                  │          │    │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘          │    │
│  │                                                                             │    │
│  │  ┌──────────────────┐  ┌──────────────────┐                                │    │
│  │  │  base.py         │  │  config.py       │                                │    │
│  │  │  (Declarative    │  │  (Settings +     │                                │    │
│  │  │   Base)          │  │   computed URL)  │                                │    │
│  │  └──────────────────┘  └──────────────────┘                                │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                     «component» DOMINIO (Models + Schemas)                  │    │
│  │                                                                             │    │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │    │
│  │  │  AuditLog        │  │ MicroserviceToken│  │  GUID            │          │    │
│  │  │  (ORM Model)     │  │ (ORM Model)      │  │  (TypeDecorator) │          │    │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘          │    │
│  │                                                                             │    │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │    │
│  │  │ AuditLogCreate   │  │ AuditLogResponse │  │  AuditLogFilter  │          │    │
│  │  │ (Pydantic)       │  │ (Pydantic)       │  │  (Pydantic)      │          │    │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘          │    │
│  │                                                                             │    │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │    │
│  │  │ MessageResponse  │  │ DataResponse<T>  │  │ PaginatedResp<T> │          │    │
│  │  │ ErrorResponse    │  │ StatsResponse    │  │                  │          │    │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘          │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                     «component» UTILIDADES                                  │    │
│  │                                                                             │    │
│  │  ┌──────────────────────────────────────────┐                              │    │
│  │  │  logger.py (JSON Structured Logging)      │                              │    │
│  │  │  • JSONFormatter → stdout                 │                              │    │
│  │  │  • Campos: timestamp, level, service,     │                              │    │
│  │  │    message, module, function, line, extra  │                              │    │
│  │  └──────────────────────────────────────────┘                              │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                              │
                              │  asyncpg (pool_size=10, max_overflow=20)
                              ▼
                   ┌──────────────────────┐
                   │    PostgreSQL 16     │
                   │    (:5432)           │
                   │                      │
                   │  • audit_logs        │
                   │  • microservice_     │
                   │    tokens            │
                   │  • 8 índices         │
                   │  • GIN full-text     │
                   └──────────────────────┘
```

### 4.2 Diagrama Simplificado de Capas MVC

```
                    ┌───────────────────────┐
                    │       REQUEST         │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      MIDDLEWARE       │
                    │  RequestID → RateLimit │
                    │  → CORS               │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │       ROUTER         │
                    │   (audit_routes.py)   │
                    │   9 endpoints         │
                    │   + Depends(auth, db) │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      SERVICE         │
                    │  (audit_service.py)   │
                    │  (statistics_service) │
                    │  (retention_service)  │
                    │                       │
                    │  Lógica de negocio    │
                    │  Mapeo Schema ↔ ORM  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │     REPOSITORY       │
                    │ (audit_repository.py) │
                    │                       │
                    │  SQLAlchemy 2.0 async │
                    │  select() / func()    │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      DATABASE        │
                    │  AsyncSession +       │
                    │  AsyncEngine          │
                    │  (asyncpg driver)     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    PostgreSQL 16      │
                    │    audit_logs         │
                    │    microservice_tokens│
                    └───────────────────────┘
```

---

## 5. Diagrama Entidad-Relación (ER)

### 5.1 Diagrama ER Completo

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                          DIAGRAMA ENTIDAD-RELACIÓN                              │
│                          ms-auditoria — PostgreSQL 16                           │
│                                                                                 │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────┐                     │
│  │                     audit_logs                         │                     │
│  │                     (Tabla principal)                  │                     │
│  ├───────────────────────────────────────────────────────┤                     │
│  │ «PK» id               UUID            NOT NULL        │                     │
│  │───────────────────────────────────────────────────────│                     │
│  │      request_id       VARCHAR(50)     NOT NULL        │ ◄── IX simple      │
│  │      servicio         VARCHAR(50)     NOT NULL        │ ◄── IX simple      │
│  │      endpoint         VARCHAR(200)    NOT NULL        │                     │
│  │      metodo           VARCHAR(10)     NOT NULL        │                     │
│  │      codigo_respuesta INTEGER         NULLABLE        │ ◄── IX simple      │
│  │      duracion_ms      INTEGER         NULLABLE        │                     │
│  │      usuario_id       UUID            NULLABLE        │ ◄── IX simple      │
│  │      detalle          TEXT            NULLABLE        │ ◄── IX GIN (FTS)   │
│  │      ip_origen        VARCHAR(45)     NULLABLE        │                     │
│  │      timestamp_evento TIMESTAMP(tz)   NOT NULL        │                     │
│  │      created_at       TIMESTAMP(tz)   NOT NULL        │                     │
│  ├───────────────────────────────────────────────────────┤                     │
│  │  ÍNDICES COMPUESTOS:                                  │                     │
│  │  • ix_audit_servicio_timestamp  (servicio, timestamp) │                     │
│  │  • ix_audit_usuario_timestamp   (usuario_id, timestamp│)                    │
│  │  • ix_audit_codigo_servicio     (codigo_resp, servicio│)                    │
│  ├───────────────────────────────────────────────────────┤                     │
│  │  ÍNDICE GIN:                                          │                     │
│  │  • ix_audit_detalle_fulltext                          │                     │
│  │    GIN(to_tsvector('spanish', COALESCE(detalle, ''))) │                     │
│  └───────────────────────────────────────────────────────┘                     │
│                                                                                 │
│                                                                                 │
│         (Sin FK directa — relación lógica vía API Key en runtime)              │
│                                                                                 │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────┐                     │
│  │                  microservice_tokens                   │                     │
│  │                  (Tabla de autenticación)              │                     │
│  ├───────────────────────────────────────────────────────┤                     │
│  │ «PK» id                     UUID          NOT NULL    │                     │
│  │───────────────────────────────────────────────────────│                     │
│  │ «UQ» nombre_microservicio   VARCHAR(50)   NOT NULL    │                     │
│  │      token_hash             VARCHAR(256)  NOT NULL    │                     │
│  │      activo                 BOOLEAN       NOT NULL    │                     │
│  │      created_at             TIMESTAMP(tz) NOT NULL    │                     │
│  │      updated_at             TIMESTAMP(tz) NOT NULL    │                     │
│  └───────────────────────────────────────────────────────┘                     │
│                                                                                 │
│                                                                                 │
│  ═══════════════════════════════════════════════════════════                    │
│  RELACIÓN LÓGICA (no FK en BD):                                                │
│                                                                                 │
│  microservice_tokens.nombre_microservicio ──── audit_logs.servicio             │
│                                                                                 │
│  Cardinalidad: 1 microservice_token ────────── 0..* audit_logs                 │
│                                                                                 │
│  Un microservicio registrado puede generar cero o muchos logs.                 │
│  La relación se valida en runtime vía API Key (verify_api_key)                 │
│  y no como Foreign Key en la base de datos, por diseño:                        │
│  - Los logs deben poder existir independientemente de los tokens               │
│  - Facilita la purga masiva sin restricciones de FK                            │
│  - El campo servicio es informativo, no referencial                            │
│  ═══════════════════════════════════════════════════════════                    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Notación ER con Cardinalidades

```
┌───────────────────┐          1 : 0..*          ┌───────────────────┐
│                   │                             │                   │
│ microservice_     │────────────────────────────►│   audit_logs      │
│ tokens            │  "Un microservicio          │                   │
│                   │   registrado genera         │                   │
│ PK: id (UUID)     │   0 o muchos logs"          │ PK: id (UUID)     │
│ UQ: nombre_ms     │                             │    request_id     │
│    token_hash     │   Relación lógica vía       │    servicio       │
│    activo         │   API Key en runtime        │    endpoint       │
│    created_at     │   (NO es FK en BD)          │    metodo         │
│    updated_at     │                             │    codigo_resp    │
│                   │                             │    duracion_ms    │
└───────────────────┘                             │    usuario_id     │
                                                  │    detalle        │
                                                  │    ip_origen      │
                                                  │    timestamp_evt  │
                                                  │    created_at     │
                                                  │                   │
                                                  └───────────────────┘
```

### 5.3 Detalle de Atributos con Tipos y Restricciones

#### Tabla: audit_logs

| # | Atributo | Tipo PostgreSQL | Tipo Python/ORM | PK | FK | UQ | NN | Default | Descripción |
|---|----------|----------------|-----------------|:--:|:--:|:--:|:--:|---------|-------------|
| 1 | id | UUID | GUID() | ✅ | | | ✅ | uuid4() | Identificador único |
| 2 | request_id | VARCHAR(50) | String(50) | | | | ✅ | — | X-Request-ID trazabilidad |
| 3 | servicio | VARCHAR(50) | String(50) | | | | ✅ | — | Microservicio emisor |
| 4 | endpoint | VARCHAR(200) | String(200) | | | | ✅ | — | Ruta invocada |
| 5 | metodo | VARCHAR(10) | String(10) | | | | ✅ | — | HTTP method |
| 6 | codigo_respuesta | INTEGER | Integer | | | | | — | Código HTTP |
| 7 | duracion_ms | INTEGER | Integer | | | | | — | Duración en ms |
| 8 | usuario_id | UUID | GUID() | | | | | None | UUID usuario |
| 9 | detalle | TEXT | Text | | | | | None | Detalle JSON string |
| 10 | ip_origen | VARCHAR(45) | String(45) | | | | | None | IP origen (v4/v6) |
| 11 | timestamp_evento | TIMESTAMP(tz) | TIMESTAMP(tz=True) | | | | ✅ | — | Momento del evento |
| 12 | created_at | TIMESTAMP(tz) | TIMESTAMP(tz=True) | | | | ✅ | now(UTC) | Registro en BD |

#### Tabla: microservice_tokens

| # | Atributo | Tipo PostgreSQL | Tipo Python/ORM | PK | FK | UQ | NN | Default | Descripción |
|---|----------|----------------|-----------------|:--:|:--:|:--:|:--:|---------|-------------|
| 1 | id | UUID | GUID() | ✅ | | | ✅ | uuid4() | Identificador único |
| 2 | nombre_microservicio | VARCHAR(50) | String(50) | | | ✅ | ✅ | — | Nombre del ms |
| 3 | token_hash | VARCHAR(256) | String(256) | | | | ✅ | — | SHA-256 del API Key |
| 4 | activo | BOOLEAN | Boolean | | | | ✅ | True | Autorizado o no |
| 5 | created_at | TIMESTAMP(tz) | TIMESTAMP(tz=True) | | | | ✅ | now(UTC) | Creación |
| 6 | updated_at | TIMESTAMP(tz) | TIMESTAMP(tz=True) | | | | ✅ | now(UTC) | Última actualización |

**Leyenda:** PK = Primary Key, FK = Foreign Key, UQ = Unique, NN = Not Null

### 5.4 Resumen de Índices

| # | Nombre | Tabla | Tipo | Columna(s) | Propósito |
|---|--------|-------|------|------------|-----------|
| 1 | PK (id) | audit_logs | B-Tree (PK) | id | Clave primaria |
| 2 | ix_audit_logs_request_id | audit_logs | B-Tree | request_id | Trazabilidad |
| 3 | ix_audit_logs_servicio | audit_logs | B-Tree | servicio | Filtro por servicio |
| 4 | ix_audit_logs_codigo_respuesta | audit_logs | B-Tree | codigo_respuesta | Filtro por código |
| 5 | ix_audit_logs_usuario_id | audit_logs | B-Tree | usuario_id | Filtro por usuario |
| 6 | ix_audit_servicio_timestamp | audit_logs | B-Tree (compuesto) | servicio, timestamp_evento | Rango temporal por servicio |
| 7 | ix_audit_usuario_timestamp | audit_logs | B-Tree (compuesto) | usuario_id, timestamp_evento | Rango temporal por usuario |
| 8 | ix_audit_codigo_servicio | audit_logs | B-Tree (compuesto) | codigo_respuesta, servicio | Estadísticas de errores |
| 9 | ix_audit_detalle_fulltext | audit_logs | GIN | to_tsvector('spanish', detalle) | Búsqueda full-text español |
| 10 | PK (id) | microservice_tokens | B-Tree (PK) | id | Clave primaria |
| 11 | UQ (nombre) | microservice_tokens | B-Tree (UQ) | nombre_microservicio | Unicidad |
