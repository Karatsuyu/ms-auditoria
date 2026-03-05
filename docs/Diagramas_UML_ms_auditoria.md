# Diagramas UML — ms-auditoria (Microservicio #19)

> **Versión:** 1.0.0 — Implementación Final  
> **Última actualización:** Junio 2025  
> **Todos los diagramas están en sintaxis Mermaid** (pegables en [Mermaid Live Editor](https://mermaid.live))

---

## Tabla de Contenidos

1. [Diagrama de Casos de Uso](#1-diagrama-de-casos-de-uso)
2. [Diagrama de Clases](#2-diagrama-de-clases)
3. [Diagramas de Secuencia](#3-diagramas-de-secuencia)
4. [Diagrama de Componentes](#4-diagrama-de-componentes)
5. [Diagrama Entidad-Relación (ER)](#5-diagrama-entidad-relación-er)
6. [Diagrama de Despliegue](#6-diagrama-de-despliegue)

---

## 1. Diagrama de Casos de Uso

### 1.1 Actores del Sistema

| Actor | Tipo | Descripción |
|-------|------|-------------|
| **Microservicio Externo** | Sistema | Cualquiera de los 18+ microservicios del ERP. Envía logs con autenticación `X-App-Token` |
| **Administrador** | Persona | Usuario con permisos de auditoría. Usa `Bearer token` + códigos de permiso |
| **Scheduler (Retención)** | Sistema | Tarea de background que ejecuta rotación automática diaria a hora configurable (`RETENTION_CRON_HOUR`) |
| **Scheduler (Estadísticas)** | Sistema | Tarea de background que recalcula estadísticas diarias a las 00:05 UTC |
| **ms-autenticacion** | Sistema | Servicio externo que valida tokens de sesión (`GET /sessions/validate`) |
| **ms-roles-permisos** | Sistema | Servicio externo que verifica permisos (`GET /permissions/check`) |
| **Orquestador (Docker/K8s)** | Sistema | Invoca el health check para verificar disponibilidad |

### 1.2 Casos de Uso

| ID | Caso de Uso | Actor Principal | Endpoint |
|----|-------------|-----------------|----------|
| CU-01 | Recibir log individual | Microservicio Externo | `POST /api/v1/logs` |
| CU-02 | Recibir logs en lote | Microservicio Externo | `POST /api/v1/logs/batch` |
| CU-03 | Consultar traza por Request ID | Administrador | `GET /api/v1/logs/trace/{request_id}` |
| CU-04 | Filtrar registros de log | Administrador | `GET /api/v1/logs` |
| CU-05 | Consultar configuración de retención | Administrador | `GET /api/v1/retention-config` |
| CU-06 | Actualizar días de retención | Administrador | `PATCH /api/v1/retention-config` |
| CU-07 | Ejecutar rotación manual | Administrador | `POST /api/v1/retention-config/rotate` |
| CU-08 | Consultar historial de rotaciones | Administrador | `GET /api/v1/retention-config/rotation-history` |
| CU-09 | Consultar estadísticas generales | Administrador | `GET /api/v1/stats` |
| CU-10 | Consultar estadísticas por servicio | Administrador | `GET /api/v1/stats/{service_name}` |
| CU-11 | Verificar salud del servicio | Orquestador | `GET /api/v1/health` |
| CU-12 | Consultar información del servicio | Cualquiera | `GET /` |

### 1.3 Diagrama Mermaid — Casos de Uso

```mermaid
graph LR
    subgraph Actores Externos
        MS["🖥️ Microservicio Externo<br/>(X-App-Token)"]
        ADM["👤 Administrador<br/>(Bearer + Permiso)"]
        ORC["🐳 Orquestador<br/>(Docker / K8s)"]
        SCHED_RET["⏰ Scheduler Retención"]
        SCHED_STAT["⏰ Scheduler Estadísticas"]
    end

    subgraph ms-auditoria
        CU01["CU-01: Recibir log individual<br/>POST /api/v1/logs → 202"]
        CU02["CU-02: Recibir logs en lote<br/>POST /api/v1/logs/batch → 202"]
        CU03["CU-03: Consultar traza<br/>GET /api/v1/logs/trace/{request_id}"]
        CU04["CU-04: Filtrar registros<br/>GET /api/v1/logs"]
        CU05["CU-05: Consultar config retención<br/>GET /api/v1/retention-config"]
        CU06["CU-06: Actualizar retención<br/>PATCH /api/v1/retention-config"]
        CU07["CU-07: Rotación manual<br/>POST /api/v1/retention-config/rotate"]
        CU08["CU-08: Historial rotaciones<br/>GET /retention-config/rotation-history"]
        CU09["CU-09: Estadísticas generales<br/>GET /api/v1/stats"]
        CU10["CU-10: Estadísticas por servicio<br/>GET /api/v1/stats/{service_name}"]
        CU11["CU-11: Health check<br/>GET /api/v1/health → 200|503"]
        CU12["CU-12: Info del servicio<br/>GET /"]
        AUDIT["🔄 Auto-auditoría<br/>(AUD-RF-005)"]
    end

    subgraph Servicios Externos
        AUTH["ms-autenticacion"]
        ROLES["ms-roles-permisos"]
    end

    MS -->|X-App-Token| CU01
    MS -->|X-App-Token| CU02
    ADM -->|Bearer + AUD_CONSULTAR_LOGS| CU03
    ADM -->|Bearer + AUD_CONSULTAR_LOGS| CU04
    ADM -->|Bearer + AUD_ADMINISTRAR_RETENCION| CU05
    ADM -->|Bearer + AUD_ADMINISTRAR_RETENCION| CU06
    ADM -->|Bearer + AUD_ROTAR_REGISTROS| CU07
    ADM -->|Bearer + AUD_ADMINISTRAR_RETENCION| CU08
    ADM -->|Bearer + AUD_CONSULTAR_ESTADISTICAS| CU09
    ADM -->|Bearer + AUD_CONSULTAR_ESTADISTICAS| CU10
    ORC --> CU11
    SCHED_RET -.->|Diario a hora config| CU07
    SCHED_STAT -.->|Diario 00:05 UTC| CU09

    CU01 -.-> AUDIT
    CU02 -.-> AUDIT
    CU03 -.-> AUDIT
    CU04 -.-> AUDIT
    CU05 -.-> AUDIT
    CU06 -.-> AUDIT
    CU07 -.-> AUDIT
    CU08 -.-> AUDIT
    CU09 -.-> AUDIT
    CU10 -.-> AUDIT

    CU03 -->|Valida sesión| AUTH
    CU03 -->|Verifica permiso| ROLES
    CU04 -->|Valida sesión| AUTH
    CU04 -->|Verifica permiso| ROLES
```

---

## 2. Diagrama de Clases

### 2.1 Diagrama de Clases Completo

```mermaid
classDiagram
    direction TB

    %% ── CAPA DE PRESENTACIÓN (Routers) ──
    class log_router {
        <<APIRouter>>
        +prefix: /api/v1/logs
        +receive_log(LogCreate) APIResponse~LogReceivedData~
        +receive_log_batch(LogBatchRequest) APIResponse~BatchReceivedData~
        +get_trace(request_id, page, page_size) APIResponse~TraceData~
        +filter_logs(page, page_size, service_name?, date_from?, date_to?) APIResponse~FilteredLogsData~
    }

    class retention_router {
        <<APIRouter>>
        +prefix: /api/v1/retention-config
        +get_retention_config() APIResponse~RetentionConfigData~
        +update_retention_config(RetentionUpdateRequest) APIResponse~RetentionConfigUpdatedData~
        +manual_rotation() APIResponse~RotationResultData~
        +get_rotation_history(page, page_size) APIResponse~RotationHistoryData~
    }

    class stats_router {
        <<APIRouter>>
        +prefix: /api/v1/stats
        +get_general_stats(period, page, page_size, date?) APIResponse~GeneralStatsData~
        +get_service_stats(service_name, period, page, page_size) APIResponse~ServiceStatsData~
    }

    class system_router {
        <<APIRouter>>
        +prefix: /api/v1
        +health_check() HealthResponse | JSONResponse 503
    }

    %% ── CAPA DE SERVICIOS ──
    class AuditService {
        -db: AsyncSession
        +__init__(db: AsyncSession)
        +enqueue_log(data: LogCreate) void
        +enqueue_batch(logs: List~LogCreate~) void
        +get_trace(request_id, page, page_size) Tuple~list, int~
        +get_filtered_logs(page, page_size, filters...) Tuple~list, int~
        +get_rotation_history(page, page_size, date_from?, date_to?) Tuple~list, int~
    }

    class RetentionService {
        -db: AsyncSession
        +__init__(db: AsyncSession)
        +get_config() dict
        +update_config(days: int) dict
        +rotate() dict
    }

    class RetentionScheduler {
        -_running: bool
        -_task: asyncio.Task
        +start() void
        +stop() void
        -_scheduler_loop() void
        -_seconds_until_next_run() int
    }

    class StatisticsService {
        -db: AsyncSession
        +__init__(db: AsyncSession)
        +get_general_stats(period, target_date?, page, page_size) Tuple~list, int~
        +get_service_stats(service_name, period, target_date?, page, page_size) Tuple~list, int~
    }

    class StatisticsScheduler {
        -_running: bool
        -_task: asyncio.Task
        +start() void
        +stop() void
        -_scheduler_loop() void
        -_calculate_daily_stats() void
    }

    class AuthService {
        <<module: services/auth_service>>
        +validate_session(token, request_id) dict | None
        +check_permission(user_id, code, request_id) bool
    }

    class ExternalServiceUnavailable {
        <<exception>>
        +service_name: str
        +detail: str
    }

    class SelfAuditService {
        <<module: services/self_audit_service>>
        +fire_self_audit(request_id, funcionalidad, metodo, codigo, duracion, ...) void
    }

    %% ── CAPA DE REPOSITORIOS ──
    class AuditRepository {
        -db: AsyncSession
        +__init__(db: AsyncSession)
        +save(log: AuditLog) AuditLog
        +save_batch(logs: List~AuditLog~) void
        +find_by_request_id(rid, page, page_size) Tuple~list, int~
        +find_filtered(page, page_size, filters...) Tuple~list, int~
        +find_rotation_history(page, page_size, dates...) Tuple~list, int~
        +delete_before(cutoff: datetime) int
    }

    class RetentionRepository {
        -db: AsyncSession
        +__init__(db: AsyncSession)
        +get_active_config() RetentionConfig | None
        +save_config(config: RetentionConfig) RetentionConfig
    }

    class StatisticsRepository {
        -db: AsyncSession
        +__init__(db: AsyncSession)
        +get_general(period, date?, page, size) Tuple~list, int~
        +get_by_service(name, period, date?, page, size) Tuple~list, int~
        +upsert_daily_stats(service, date, data) void
    }

    %% ── CAPA DE DOMINIO (Modelos ORM) ──
    class AuditLog {
        <<entity: aud_eventos_log>>
        +id: BIGSERIAL [PK]
        +request_id: VARCHAR(36)
        +fecha_hora: TIMESTAMP(tz)
        +microservicio: VARCHAR(50)
        +funcionalidad: VARCHAR(100)
        +metodo: VARCHAR(10)
        +codigo_respuesta: INTEGER
        +duracion_ms: INTEGER
        +usuario_id: VARCHAR(36)?
        +detalle: TEXT?
        +created_at: TIMESTAMP(tz)
        +updated_at: TIMESTAMP(tz)
    }

    class RetentionConfig {
        <<entity: aud_configuracion_retencion>>
        +id: SERIAL [PK]
        +dias_retencion: INTEGER
        +estado: VARCHAR(20)
        +ultima_rotacion: TIMESTAMP(tz)?
        +registros_eliminados_ultima: BIGINT?
        +created_at: TIMESTAMP(tz)
        +updated_at: TIMESTAMP(tz)
    }

    class ServiceStatistics {
        <<entity: aud_estadisticas_servicio>>
        +id: BIGSERIAL [PK]
        +microservicio: VARCHAR(50)
        +periodo: VARCHAR(10)
        +fecha: DATE
        +total_peticiones: BIGINT
        +total_errores: BIGINT
        +tiempo_promedio_ms: NUMERIC(10,2)
        +funcionalidad_top: VARCHAR(100)?
        +fecha_calculo: TIMESTAMP(tz)
        +created_at: TIMESTAMP(tz)
        +updated_at: TIMESTAMP(tz)
    }

    class MicroserviceToken {
        <<entity: microservice_tokens>>
        +id: SERIAL [PK]
        +nombre_microservicio: VARCHAR(50) [UNIQUE]
        +token_hash: VARCHAR(256)
        +activo: BOOLEAN
        +created_at: TIMESTAMP(tz)
        +updated_at: TIMESTAMP(tz)
    }

    %% ── CAPA CORE ──
    class RequestIDMiddleware {
        <<middleware>>
        +dispatch(request, call_next) Response
        -generate_request_id() str "AUD-{ts_ms}-{6char}"
    }

    class RateLimitMiddleware {
        <<middleware>>
        +dispatch(request, call_next) Response
    }

    class verify_app_token {
        <<dependency: core/auth>>
        +__call__(X_App_Token: str, db: AsyncSession) MicroserviceToken
    }

    class get_current_user {
        <<dependency>>
        +__call__(Authorization: str, request: Request) dict
    }

    class require_permission {
        <<dependency factory>>
        +__call__(permission_code: str) Callable
    }

    %% ── SCHEMAS ──
    class LogCreate {
        <<schema>>
        +timestamp: datetime
        +request_id: str?
        +service_name: str
        +functionality: str
        +method: str
        +response_code: int
        +duration_ms: int
        +user_id: str?
        +detail: str?
    }

    class LogRecord {
        <<schema>>
        +id: int
        +timestamp: datetime [alias: fecha_hora]
        +service_name: str [alias: microservicio]
        +functionality: str [alias: funcionalidad]
        +method: str [alias: metodo]
        +response_code: int [alias: codigo_respuesta]
        +duration_ms: int [alias: duracion_ms]
        +user_id: str? [alias: usuario_id]
        +detail: str? [alias: detalle]
    }

    class APIResponse~T~ {
        <<schema>>
        +request_id: str
        +success: bool
        +data: T?
        +message: str
        +timestamp: datetime
    }

    %% ── RELACIONES ──
    log_router --> AuditService : usa
    log_router --> verify_app_token : Depends (POST)
    log_router --> require_permission : Depends (GET)
    retention_router --> RetentionService : usa
    retention_router --> AuditService : usa (rotation-history)
    retention_router --> require_permission : Depends
    stats_router --> StatisticsService : usa
    stats_router --> require_permission : Depends
    system_router ..> AuditLog : health check (SELECT 1)

    AuditService --> AuditRepository : usa
    RetentionService --> RetentionRepository : usa
    RetentionService --> AuditRepository : usa (delete)
    StatisticsService --> StatisticsRepository : usa

    AuditRepository --> AuditLog : opera sobre
    RetentionRepository --> RetentionConfig : opera sobre
    StatisticsRepository --> ServiceStatistics : opera sobre
    verify_app_token --> MicroserviceToken : consulta

    require_permission --> get_current_user : Depends
    get_current_user --> AuthService : valida sesión
    require_permission --> AuthService : verifica permiso
    AuthService --> ExternalServiceUnavailable : lanza en timeout/error

    SelfAuditService ..> AuditRepository : registra auto-log (background)

    RetentionScheduler --> RetentionService : ejecuta purga
    StatisticsScheduler --> StatisticsService : calcula métricas

    log_router ..> LogCreate : valida entrada
    log_router ..> LogRecord : serializa salida
    log_router ..> APIResponse : envuelve respuesta
```

### 2.2 Tabla de Relaciones

| Clase Origen | Relación | Clase Destino | Cardinalidad | Descripción |
|---|---|---|---|---|
| `log_router` | usa | `AuditService` | 1 → 1 | Endpoints POST y GET de logs |
| `log_router` | depends | `verify_app_token` | 1 → 1 | POST requiere X-App-Token |
| `log_router` | depends | `require_permission` | 1 → 1 | GET requiere Bearer + permiso |
| `retention_router` | usa | `RetentionService` | 1 → 1 | Config y rotación |
| `retention_router` | usa | `AuditService` | 1 → 1 | Historial de rotaciones |
| `stats_router` | usa | `StatisticsService` | 1 → 1 | Estadísticas precalculadas |
| `require_permission` | depends | `get_current_user` | 1 → 1 | Primero valida sesión |
| `get_current_user` | llama | `AuthService.validate_session()` | 1 → 1 | HTTP a ms-autenticacion, timeout 3s |
| `require_permission` | llama | `AuthService.check_permission()` | 1 → 1 | HTTP a ms-roles, timeout 3s |
| `AuditService` | usa | `AuditRepository` | 1 → 1 | Composición |
| `RetentionService` | usa | `RetentionRepository` | 1 → 1 | Composición |
| `RetentionService` | usa | `AuditRepository` | 1 → 1 | Para DELETE masivo |
| `StatisticsService` | usa | `StatisticsRepository` | 1 → 1 | Composición |
| `AuditRepository` | opera sobre | `AuditLog` | 1 → * | CRUD sobre tabla aud_eventos_log |
| `RetentionRepository` | opera sobre | `RetentionConfig` | 1 → 1 | Singleton (config única activa) |
| `StatisticsRepository` | opera sobre | `ServiceStatistics` | 1 → * | Métricas precalculadas |
| `verify_app_token` | consulta | `MicroserviceToken` | 1 → 0..1 | Busca token activo por SHA-256 hash |
| `SelfAuditService` | inserta | `AuditLog` | 1 → 1 | Auto-auditoría AUD-RF-005 en background (asyncio.create_task) |
| `RetentionScheduler` | ejecuta | `RetentionService.rotate()` | 1 → 1 | Purga diaria a hora config |
| `StatisticsScheduler` | ejecuta | `StatisticsService` | 1 → 1 | Cálculo diario a 00:05 UTC |

---

## 3. Diagramas de Secuencia

### 3.1 Secuencia: Recibir Log Individual (POST /api/v1/logs) — 202 Accepted

```mermaid
sequenceDiagram
    autonumber
    participant MS as Microservicio Externo
    participant MW as RequestIDMiddleware
    participant RL as RateLimitMiddleware
    participant RT as log_router
    participant AUTH as verify_app_token
    participant SVC as AuditService
    participant SA as SelfAuditService
    participant DB as PostgreSQL

    MS->>MW: POST /api/v1/logs<br/>X-App-Token: xxx<br/>Body: {LogCreate}
    MW->>MW: Genera AUD-{ts}-{6char}<br/>o propaga X-Request-ID recibido
    MW->>RL: Forward request
    RL->>RL: Sliding window por IP<br/>[OK: bajo límite]
    RL->>RT: Forward request

    RT->>AUTH: Depends(verify_app_token)
    AUTH->>AUTH: SHA-256(X-App-Token)
    AUTH->>DB: SELECT FROM microservice_tokens<br/>WHERE token_hash = ? AND activo = True
    DB-->>AUTH: token_record
    AUTH-->>RT: Token válido ✓

    RT->>RT: Pydantic valida LogCreate
    RT->>SVC: enqueue_log(data)
    SVC->>SVC: Mapea LogCreate → AuditLog ORM<br/>(background persist via create_task)
    SVC-->>RT: void (inmediato)

    RT->>SA: fire_self_audit() [create_task]
    Note over SA: Auto-auditoría AUD-RF-005<br/>Persiste en background

    RT-->>MW: 202 Accepted<br/>APIResponse~LogReceivedData~
    MW-->>MS: 202 + X-Request-ID<br/>+ X-Response-Time-ms

    Note over SVC,DB: Background: AuditLog persiste async
    SVC->>DB: INSERT INTO aud_eventos_log
    DB-->>SVC: OK
```

### 3.2 Secuencia: Consultar Logs con Filtros (GET /api/v1/logs) — Autenticación Completa

```mermaid
sequenceDiagram
    autonumber
    participant ADM as Administrador
    participant MW as Middleware Chain
    participant RT as log_router
    participant DEP as require_permission
    participant CUR as get_current_user
    participant AUTS as ms-autenticacion
    participant ROLS as ms-roles-permisos
    participant SVC as AuditService
    participant REPO as AuditRepository
    participant DB as PostgreSQL

    ADM->>MW: GET /api/v1/logs?service_name=ms-matriculas<br/>&page=1&page_size=20<br/>Authorization: Bearer {token}
    MW->>RT: + X-Request-ID + Rate limit OK

    RT->>DEP: Depends(require_permission("AUD_CONSULTAR_LOGS"))
    DEP->>CUR: Depends(get_current_user)

    CUR->>AUTS: GET /sessions/validate<br/>Authorization: Bearer {token}<br/>X-App-Token: {aud_token}<br/>X-Request-ID: {rid}<br/>Timeout: 3s
    AUTS-->>CUR: 200 {valid: true, user_id: "uuid..."}
    CUR-->>DEP: user_data

    DEP->>ROLS: GET /permissions/check<br/>?user_id=uuid&functionality_code=AUD_CONSULTAR_LOGS<br/>X-App-Token: {aud_token}<br/>X-Request-ID: {rid}<br/>Timeout: 3s
    ROLS-->>DEP: 200 {has_permission: true}
    DEP-->>RT: user_data ✓

    RT->>RT: Valida: ≥1 filtro obligatorio ✓
    RT->>SVC: get_filtered_logs(page, page_size, filters)
    SVC->>REPO: find_filtered(...)
    REPO->>DB: SELECT COUNT(*) FROM aud_eventos_log<br/>WHERE microservicio = ?
    DB-->>REPO: total: 150
    REPO->>DB: SELECT * FROM aud_eventos_log<br/>WHERE microservicio = ?<br/>ORDER BY fecha_hora DESC<br/>OFFSET 0 LIMIT 20
    DB-->>REPO: [20 rows]
    REPO-->>SVC: (records, 150)
    SVC-->>RT: (records, total)

    RT-->>ADM: 200 OK<br/>APIResponse~FilteredLogsData~<br/>{records, total_records: 150, page: 1}
```

### 3.3 Secuencia: Manejo de Servicio Externo No Disponible (HTTP 503)

```mermaid
sequenceDiagram
    autonumber
    participant ADM as Administrador
    participant RT as Router
    participant DEP as require_permission
    participant CUR as get_current_user
    participant AUTS as ms-autenticacion

    ADM->>RT: GET /api/v1/logs?...<br/>Authorization: Bearer {token}
    RT->>DEP: Depends(require_permission(...))
    DEP->>CUR: Depends(get_current_user)

    CUR->>AUTS: GET /sessions/validate<br/>Timeout: 3s

    alt Timeout (> 3 segundos)
        AUTS--xCUR: TimeoutException
        CUR->>CUR: raise ExternalServiceUnavailable
        CUR-->>DEP: ExternalServiceUnavailable
        DEP-->>RT: HTTPException 503
        RT-->>ADM: 503 Service Unavailable<br/>{"detail": "Servicio de autenticación no disponible."}
    else Conexión rechazada
        AUTS--xCUR: RequestError
        CUR->>CUR: raise ExternalServiceUnavailable
        CUR-->>RT: HTTPException 503
        RT-->>ADM: 503 Service Unavailable
    end
```

### 3.4 Secuencia: Rotación Automática (RetentionScheduler)

```mermaid
sequenceDiagram
    autonumber
    participant LS as FastAPI Lifespan
    participant RS as RetentionScheduler
    participant RSVC as RetentionService
    participant REPO as AuditRepository
    participant CREPO as RetentionRepository
    participant DB as PostgreSQL
    participant SA as SelfAuditService

    Note over LS,RS: ══ STARTUP ══
    LS->>RS: start()
    RS->>RS: _running = True<br/>asyncio.create_task(_scheduler_loop)
    RS-->>LS: return

    Note over RS: ══ SCHEDULER LOOP ══
    RS->>RS: _seconds_until_next_run()<br/>(ej: 28800s hasta RETENTION_CRON_HOUR UTC)
    RS->>RS: asyncio.sleep(28800)

    Note over RS: ══ HORA DE EJECUCIÓN ══
    RS->>RSVC: rotate()
    RSVC->>CREPO: get_active_config()
    CREPO->>DB: SELECT FROM aud_configuracion_retencion<br/>WHERE estado = 'activo'
    DB-->>CREPO: config (dias_retencion=30)
    CREPO-->>RSVC: RetentionConfig

    RSVC->>RSVC: cutoff = now() - timedelta(30 days)
    RSVC->>REPO: delete_before(cutoff)
    REPO->>DB: DELETE FROM aud_eventos_log<br/>WHERE fecha_hora < cutoff
    DB-->>REPO: rowcount: 1523
    REPO-->>RSVC: 1523

    RSVC->>CREPO: Actualiza ultima_rotacion y registros_eliminados_ultima
    CREPO->>DB: UPDATE aud_configuracion_retencion
    DB-->>CREPO: OK

    RSVC->>SA: fire_self_audit(trigger="automatico", deleted=1523)
    RSVC-->>RS: {deleted_count: 1523}

    RS->>RS: Vuelve al loop → sleep hasta mañana

    Note over LS,RS: ══ SHUTDOWN ══
    LS->>RS: stop()
    RS->>RS: _running = False<br/>task.cancel()
```

### 3.5 Secuencia: Cálculo de Estadísticas (StatisticsScheduler)

```mermaid
sequenceDiagram
    autonumber
    participant LS as FastAPI Lifespan
    participant SS as StatisticsScheduler
    participant SVC as StatisticsService
    participant REPO as StatisticsRepository
    participant DB as PostgreSQL

    Note over LS,SS: ══ STARTUP ══
    LS->>SS: start()
    SS->>SS: _running = True<br/>asyncio.create_task(_scheduler_loop)

    Note over SS: ══ SCHEDULER LOOP ══
    SS->>SS: Espera hasta 00:05 UTC
    SS->>SS: asyncio.sleep(...)

    Note over SS: ══ 00:05 UTC — CÁLCULO ══
    SS->>SVC: _calculate_daily_stats()
    SVC->>DB: SELECT microservicio, COUNT(*), ...<br/>FROM aud_eventos_log<br/>WHERE fecha_hora BETWEEN ayer AND hoy<br/>GROUP BY microservicio
    DB-->>SVC: [{ms, total, errores, avg_ms, top_func}]
    SVC->>REPO: upsert_daily_stats(service, date, data)
    REPO->>DB: INSERT/UPDATE aud_estadisticas_servicio<br/>(UNIQUE: microservicio + periodo + fecha)
    DB-->>REPO: OK

    SS->>SS: Vuelve al loop → sleep 24h
```

### 3.6 Secuencia: Health Check (GET /api/v1/health)

```mermaid
sequenceDiagram
    autonumber
    participant ORC as Orquestador
    participant RT as system_router
    participant DB as PostgreSQL

    ORC->>RT: GET /api/v1/health

    RT->>DB: SELECT 1 (verificar conectividad)

    alt Base de datos saludable
        DB-->>RT: OK (latency medido)
        RT-->>ORC: 200 OK<br/>HealthResponse<br/>{"status": "healthy",<br/>"components": {"database": {"status": "healthy", "latency_ms": 2}}}
    else Base de datos caída
        DB--xRT: Exception
        RT-->>ORC: 503 Service Unavailable<br/>JSONResponse<br/>{"status": "unhealthy",<br/>"components": {"database": {"status": "unhealthy", "error": "..."}}}
    end
```

### 3.7 Secuencia: Validación de X-App-Token (Detalle)

```mermaid
sequenceDiagram
    autonumber
    participant REQ as Request
    participant AUTH as verify_app_token<br/>(core/auth.py)
    participant DB as PostgreSQL

    REQ->>AUTH: Header: X-App-Token

    alt Token ausente
        AUTH-->>REQ: 401 Unauthorized<br/>"Token de autenticación requerido"
    else Token presente
        AUTH->>AUTH: hash = SHA-256(token)
        AUTH->>DB: SELECT FROM microservice_tokens<br/>WHERE token_hash = hash AND activo = True
        alt Token encontrado y activo
            DB-->>AUTH: token_record
            AUTH-->>REQ: token_record ✓
        else Token no encontrado o inactivo
            DB-->>AUTH: None
            AUTH-->>REQ: 401 Unauthorized<br/>"Token inválido o microservicio no autorizado"
        end
    end
```

---

## 4. Diagrama de Componentes

### 4.1 Arquitectura Interna por Capas

```mermaid
graph TB
    subgraph EXT["Clientes Externos"]
        MS["🖥️ Microservicios del ERP<br/>(X-App-Token)"]
        ADM["👤 Administradores<br/>(Bearer Token)"]
        ORC["🐳 Orquestador<br/>(Health Check)"]
    end

    subgraph MW["Middleware Chain (LIFO)"]
        RID["RequestIDMiddleware<br/>• Genera AUD-{ts_ms}-{6char}<br/>• Propaga X-Request-ID<br/>• Valida formato con regex<br/>• Mide duración"]
        RLM["RateLimitMiddleware<br/>• Sliding window por IP<br/>• 100 req/60s (configurable)<br/>• Headers X-RateLimit-*"]
        CORS["CORSMiddleware<br/>• Orígenes configurables<br/>• Headers expuestos"]
    end

    subgraph EH["Exception Handlers"]
        HEH["HTTP 4xx/5xx"]
        VEH["Validation 422"]
        UEH["Unhandled 500"]
    end

    subgraph ROUTES["Presentación — 4 Routers, 12 Endpoints"]
        LR["log_router<br/>/api/v1/logs<br/>POST '' (202), POST /batch (202)<br/>GET /trace/{rid}, GET ''"]
        RR["retention_router<br/>/api/v1/retention-config<br/>GET '', PATCH ''<br/>POST /rotate, GET /rotation-history"]
        SR["stats_router<br/>/api/v1/stats<br/>GET '', GET /{service_name}"]
        SYS["system_router<br/>/api/v1/health (200|503)"]
    end

    subgraph DEPS["Dependencias Inyectadas"]
        VAT["verify_app_token<br/>(SHA-256 → microservice_tokens)"]
        GCU["get_current_user<br/>(Bearer → ms-autenticacion)"]
        RP["require_permission<br/>(user_id + code → ms-roles)"]
        GDB["get_db()<br/>(AsyncSession)"]
    end

    subgraph SERVICES["Servicios de Negocio"]
        AS["AuditService<br/>• enqueue_log/batch<br/>• get_trace/filtered<br/>• get_rotation_history"]
        RS["RetentionService<br/>• get/update config<br/>• rotate (manual)"]
        SS["StatisticsService<br/>• general/service stats"]
        AUTHS["AuthService<br/>• validate_session (3s timeout)<br/>• check_permission (3s timeout)<br/>→ ExternalServiceUnavailable → 503"]
        SAS["SelfAuditService<br/>• fire_self_audit (AUD-RF-005)"]
    end

    subgraph SCHED["Schedulers (Background Tasks)"]
        RSCH["RetentionScheduler<br/>Diario a RETENTION_CRON_HOUR UTC<br/>(default: 03:00)"]
        SSCH["StatisticsScheduler<br/>Diario a 00:05 UTC"]
    end

    subgraph REPOS["Repositorios (SQLAlchemy 2.0 async)"]
        AR["AuditRepository<br/>(aud_eventos_log)"]
        RR2["RetentionRepository<br/>(aud_configuracion_retencion)"]
        SR2["StatisticsRepository<br/>(aud_estadisticas_servicio)"]
    end

    subgraph MODELS["Modelos ORM (4 tablas)"]
        AL["AuditLog<br/>(aud_eventos_log)<br/>12 columnas, 6 índices, 3 CHECK"]
        RC["RetentionConfig<br/>(aud_configuracion_retencion)<br/>7 columnas, 3 CHECK"]
        SSM["ServiceStatistics<br/>(aud_estadisticas_servicio)<br/>11 columnas, 1 UNIQUE, 5 CHECK"]
        MT["MicroserviceToken<br/>(microservice_tokens)<br/>6 columnas, 1 UNIQUE"]
    end

    subgraph DATABASE["Base de Datos"]
        PG["PostgreSQL 16<br/>asyncpg driver<br/>pool_size=10, max_overflow=20"]
    end

    subgraph EXTERNAL["Servicios Externos (httpx async)"]
        MSAUTH["ms-autenticacion<br/>GET /sessions/validate"]
        MSROLES["ms-roles-permisos<br/>GET /permissions/check"]
    end

    MS --> RID
    ADM --> RID
    ORC --> RID
    RID --> RLM --> CORS --> ROUTES

    LR --> VAT
    LR --> RP
    LR --> GDB
    RR --> RP
    RR --> GDB
    SR --> RP
    SR --> GDB
    SYS --> GDB

    RP --> GCU
    GCU --> AUTHS
    RP --> AUTHS
    AUTHS --> MSAUTH
    AUTHS --> MSROLES

    LR --> AS
    RR --> RS
    RR --> AS
    SR --> SS

    AS --> AR
    RS --> RR2
    RS --> AR
    SS --> SR2
    SAS -.-> AR

    AR --> AL
    RR2 --> RC
    SR2 --> SSM
    VAT --> MT

    RSCH --> RS
    SSCH --> SS

    AL --> PG
    RC --> PG
    SSM --> PG
    MT --> PG
```

### 4.2 Diagrama Simplificado por Capas

```mermaid
graph TB
    REQ["📨 Request Entrante"] --> MWL

    MWL["⛓️ Middleware<br/>RequestID → RateLimit → CORS"]
    MWL --> RTR["🌐 Routers<br/>4 routers × 12 endpoints<br/>+ Depends(auth, db)"]
    RTR --> SVC["⚙️ Services<br/>AuditService · RetentionService<br/>StatisticsService · AuthService<br/>SelfAuditService"]
    SVC --> RPO["📦 Repositories<br/>AuditRepository · RetentionRepository<br/>StatisticsRepository"]
    RPO --> DBL["🔌 Database Layer<br/>AsyncSession + AsyncEngine<br/>(asyncpg driver)"]
    DBL --> PG["🐘 PostgreSQL 16<br/>4 tablas · 6+ índices<br/>CHECK constraints"]

    SCHED["⏰ Schedulers<br/>RetentionScheduler (diario)<br/>StatisticsScheduler (00:05 UTC)"]
    SCHED --> SVC
```

---

## 5. Diagrama Entidad-Relación (ER)

### 5.1 Diagrama ER Completo

```mermaid
erDiagram
    aud_eventos_log {
        BIGSERIAL id PK "Autoincremental"
        VARCHAR_36 request_id "NOT NULL — Request ID"
        TIMESTAMP_tz fecha_hora "NOT NULL — Momento del evento"
        VARCHAR_50 microservicio "NOT NULL — Nombre ms emisor"
        VARCHAR_100 funcionalidad "NOT NULL — Endpoint o funcionalidad"
        VARCHAR_10 metodo "NOT NULL — CHECK: GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS"
        INTEGER codigo_respuesta "NOT NULL — CHECK: 100-599"
        INTEGER duracion_ms "NOT NULL — CHECK: >= 0"
        VARCHAR_36 usuario_id "NULLABLE — Ref. ms-usuarios"
        TEXT detalle "NULLABLE — Descripción libre"
        TIMESTAMP_tz created_at "NOT NULL — default now()"
        TIMESTAMP_tz updated_at "NOT NULL — default now(), onupdate"
    }

    aud_configuracion_retencion {
        SERIAL id PK "Autoincremental"
        INTEGER dias_retencion "NOT NULL — default 30, CHECK > 0"
        VARCHAR_20 estado "NOT NULL — CHECK: activo|inactivo"
        TIMESTAMP_tz ultima_rotacion "NULLABLE — Última ejecución"
        BIGINT registros_eliminados_ultima "NULLABLE — CHECK >= 0"
        TIMESTAMP_tz created_at "NOT NULL"
        TIMESTAMP_tz updated_at "NOT NULL"
    }

    aud_estadisticas_servicio {
        BIGSERIAL id PK "Autoincremental"
        VARCHAR_50 microservicio "NOT NULL"
        VARCHAR_10 periodo "NOT NULL — CHECK: diario|semanal|mensual"
        DATE fecha "NOT NULL — Inicio del periodo"
        BIGINT total_peticiones "NOT NULL — CHECK >= 0"
        BIGINT total_errores "NOT NULL — CHECK >= 0 AND <= total_peticiones"
        NUMERIC_10_2 tiempo_promedio_ms "NOT NULL — CHECK >= 0"
        VARCHAR_100 funcionalidad_top "NULLABLE"
        TIMESTAMP_tz fecha_calculo "NOT NULL"
        TIMESTAMP_tz created_at "NOT NULL"
        TIMESTAMP_tz updated_at "NOT NULL"
    }

    microservice_tokens {
        SERIAL id PK "Autoincremental"
        VARCHAR_50 nombre_microservicio "UNIQUE, NOT NULL"
        VARCHAR_256 token_hash "NOT NULL — SHA-256"
        BOOLEAN activo "NOT NULL — default True"
        TIMESTAMP_tz created_at "NOT NULL"
        TIMESTAMP_tz updated_at "NOT NULL"
    }

    microservice_tokens ||--o{ aud_eventos_log : "genera logs (relación lógica vía X-App-Token)"
    aud_configuracion_retencion ||--o{ aud_eventos_log : "configura retención y purga"
    aud_estadisticas_servicio }o--o{ aud_eventos_log : "estadísticas calculadas desde logs"
```

### 5.2 Detalle de Índices

| # | Nombre | Tabla | Tipo | Columna(s) | Propósito |
|---|--------|-------|------|------------|-----------|
| 1 | PK (id) | aud_eventos_log | B-Tree (PK) | id | Clave primaria |
| 2 | `idx_aud_eventos_request_id` | aud_eventos_log | B-Tree | request_id | Trazabilidad por X-Request-ID |
| 3 | `idx_aud_eventos_microservicio` | aud_eventos_log | B-Tree | microservicio | Filtro por servicio |
| 4 | `idx_aud_eventos_fecha_hora` | aud_eventos_log | B-Tree | fecha_hora | Filtro por rango de fechas |
| 5 | `idx_aud_eventos_microservicio_fecha` | aud_eventos_log | B-Tree (compuesto) | microservicio, fecha_hora | Filtro servicio + rango temporal |
| 6 | `idx_aud_eventos_codigo_respuesta` | aud_eventos_log | B-Tree | codigo_respuesta | Filtro por código HTTP |
| 7 | `idx_aud_eventos_usuario_id` | aud_eventos_log | B-Tree (parcial) | usuario_id WHERE IS NOT NULL | Filtro por usuario (sin indexar NULLs) |
| 8 | PK (id) | aud_configuracion_retencion | B-Tree (PK) | id | Clave primaria |
| 9 | PK (id) | aud_estadisticas_servicio | B-Tree (PK) | id | Clave primaria |
| 10 | `uq_aud_estad_ms_periodo_fecha` | aud_estadisticas_servicio | B-Tree (UNIQUE) | microservicio, periodo, fecha | Unicidad por servicio+periodo+fecha |
| 11 | PK (id) | microservice_tokens | B-Tree (PK) | id | Clave primaria |
| 12 | UQ (nombre) | microservice_tokens | B-Tree (UNIQUE) | nombre_microservicio | Unicidad de nombre |

### 5.3 Detalle de CHECK Constraints

| Tabla | Nombre | Expresión |
|-------|--------|-----------|
| aud_eventos_log | `chk_aud_eventos_metodo` | `metodo IN ('GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS')` |
| aud_eventos_log | `chk_aud_eventos_codigo` | `codigo_respuesta BETWEEN 100 AND 599` |
| aud_eventos_log | `chk_aud_eventos_duracion` | `duracion_ms >= 0` |
| aud_configuracion_retencion | `chk_aud_config_dias` | `dias_retencion > 0` |
| aud_configuracion_retencion | `chk_aud_config_estado` | `estado IN ('activo', 'inactivo')` |
| aud_configuracion_retencion | `chk_aud_config_registros` | `registros_eliminados_ultima >= 0` |
| aud_estadisticas_servicio | `chk_aud_estad_periodo` | `periodo IN ('diario', 'semanal', 'mensual')` |
| aud_estadisticas_servicio | `chk_aud_estad_peticiones` | `total_peticiones >= 0` |
| aud_estadisticas_servicio | `chk_aud_estad_errores` | `total_errores >= 0` |
| aud_estadisticas_servicio | `chk_aud_estad_errores_max` | `total_errores <= total_peticiones` |
| aud_estadisticas_servicio | `chk_aud_estad_tiempo` | `tiempo_promedio_ms >= 0` |

### 5.4 Nota sobre Relaciones

Las tablas **no tienen Foreign Keys** entre sí por diseño:

- `aud_eventos_log.microservicio` → `microservice_tokens.nombre_microservicio`: Relación lógica validada en runtime vía X-App-Token. Los logs pueden existir independientemente de los tokens, facilitando la purga masiva sin restricciones de FK.
- `aud_estadisticas_servicio.microservicio` → Corresponde lógicamente a los servicios registrados, pero las estadísticas se calculan por aggregation de `aud_eventos_log`.
- `aud_configuracion_retencion` opera como singleton (una única fila activa) que configura la purga de `aud_eventos_log`.

---

## 6. Diagrama de Despliegue

### 6.1 Docker Compose — Arquitectura de Contenedores

```mermaid
graph TB
    subgraph DOCKER["Docker Compose — Red: erp-net (bridge)"]
        subgraph APP["ms-auditoria (:8019)"]
            UV["Uvicorn<br/>4 workers · uvloop + httptools"]
            FAST["FastAPI App<br/>12 endpoints"]
            ALEMBIC["Alembic<br/>(migraciones al inicio)"]
            UV --> FAST
            ALEMBIC -.-> FAST
        end

        subgraph DB["PostgreSQL 16 (:5432)"]
            PG["postgres:16-alpine<br/>DB: ms_auditoria"]
            VOL["📁 pgdata (volumen persistente)"]
            PG --- VOL
        end

        APP -->|"asyncpg<br/>pool_size=10<br/>max_overflow=20"| DB
    end

    subgraph EXTERNAL["Servicios Externos (Red erp-net)"]
        MSAUTH["ms-autenticacion (:8001)<br/>GET /api/v1/sessions/validate"]
        MSROLES["ms-roles-permisos (:8002)<br/>GET /api/v1/permissions/check"]
    end

    APP -->|"httpx async<br/>timeout: 3s"| MSAUTH
    APP -->|"httpx async<br/>timeout: 3s"| MSROLES

    CLIENT["🌐 Clientes Externos"]
    CLIENT -->|"HTTP :8019"| APP

    HC["🐳 Docker Healthcheck<br/>curl /api/v1/health<br/>interval=30s, timeout=5s, retries=3"]
    HC -.-> APP
```

### 6.2 Lifecycle de la Aplicación

```mermaid
stateDiagram-v2
    [*] --> Starting: docker-compose up
    Starting --> Migrating: Container inicia
    Migrating --> Initializing: alembic upgrade head
    Initializing --> Running: lifespan startup<br/>Inicia schedulers

    state Running {
        [*] --> Healthy
        Healthy --> Serving: Recibe requests
        Serving --> Healthy: Response enviada

        state Background {
            RetentionScheduler: Purga diaria<br/>a RETENTION_CRON_HOUR UTC
            StatisticsScheduler: Cálculo diario<br/>a 00:05 UTC
        }
    }

    Running --> ShuttingDown: SIGTERM / docker stop
    ShuttingDown --> [*]: lifespan shutdown<br/>• Detiene schedulers<br/>• Cierra pool async

    note right of Running
        Health check: GET /api/v1/health
        200 = healthy | 503 = unhealthy
    end note
```

---

## Apéndice: Resumen de Endpoints (12 totales)

| # | Método | Ruta | Auth | Permiso | Código Éxito | Descripción |
|---|--------|------|------|---------|:------------:|-------------|
| 1 | POST | `/api/v1/logs` | X-App-Token | — | 202 | Recibir log individual |
| 2 | POST | `/api/v1/logs/batch` | X-App-Token | — | 202 | Recibir lote (1-1000) |
| 3 | GET | `/api/v1/logs/trace/{request_id}` | Bearer | AUD_CONSULTAR_LOGS | 200 | Traza por request_id |
| 4 | GET | `/api/v1/logs` | Bearer | AUD_CONSULTAR_LOGS | 200 | Filtrar (≥1 filtro requerido) |
| 5 | GET | `/api/v1/retention-config` | Bearer | AUD_ADMINISTRAR_RETENCION | 200 | Config de retención |
| 6 | PATCH | `/api/v1/retention-config` | Bearer | AUD_ADMINISTRAR_RETENCION | 200 | Actualizar días |
| 7 | POST | `/api/v1/retention-config/rotate` | Bearer | AUD_ROTAR_REGISTROS | 200 | Rotación manual |
| 8 | GET | `/api/v1/retention-config/rotation-history` | Bearer | AUD_ADMINISTRAR_RETENCION | 200 | Historial rotaciones (con campo `trigger`) |
| 9 | GET | `/api/v1/stats` | Bearer | AUD_CONSULTAR_ESTADISTICAS | 200 | Estadísticas generales |
| 10 | GET | `/api/v1/stats/{service_name}` | Bearer | AUD_CONSULTAR_ESTADISTICAS | 200 | Estadísticas por servicio |
| 11 | GET | `/api/v1/health` | Ninguna | — | 200/503 | Health check |
| 12 | GET | `/` | Ninguna | — | 200 | Info del microservicio |
