"""
Genera imagenes PNG para cada diagrama UML a partir de su representacion ASCII.

Ejecutar:
1. Instalar dependencias: pip install Pillow
2. Correr el script:    python docs/generate_diagram_images.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

# Directorio de salida para las imagenes
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "diagram_images")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- Definicion de los diagramas como texto ASCII ---

DIAGRAMS = {
    "1_casos_de_uso": {
        "title": "Diagrama de Casos de Uso",
        "content": """
╔═══════════════════════════════════════════════════════════════════════════╗
║                          ms-auditoria (Sistema)                         ║
║                                                                         ║
║  ┌──────────────────────── GESTIÓN DE LOGS ─────────────────────────┐   ║
║  │                                                                   │   ║
║  │  (CU-01) Registrar Log         (CU-02) Registrar Logs en Batch   │   ║
║  │        │ «include»                    │ «include»                 │   ║
║  │        └────────► (CU-03) Validar API Key ◄───────┘              │   ║
║  │                                                                   │   ║
║  └───────────────────────────────────────────────────────────────────┘   ║
║                                                                         ║
║  ┌──────────────────────── CONSULTA DE LOGS ────────────────────────┐   ║
║  │                                                                   │   ║
║  │  (CU-04) Consultar Logs      (CU-05) Filtrar Logs Avanzado      │   ║
║  │  (CU-06) Obtener por ID      (CU-07) Trazar Request (X-Req-ID)  │   ║
║  │  (CU-08) Logs por Usuario    (CU-09) Buscar Full-Text en Detalle│   ║
║  │                                                                   │   ║
║  └───────────────────────────────────────────────────────────────────┘   ║
║                                                                         ║
║  ┌──────────────────────── ESTADÍSTICAS ────────────────────────────┐   ║
║  │  (CU-10) Obtener Estadísticas (logs/servicio, errores, avg dur) │   ║
║  └───────────────────────────────────────────────────────────────────┘   ║
║                                                                         ║
║  ┌──────────────────────── ADMINISTRACIÓN ──────────────────────────┐   ║
║  │                                                                   │   ║
║  │  (CU-11) Purgar Logs Antiguos (Manual)  ──«include»──► CU-03    │   ║
║  │  (CU-12) Purga Automática (TTL Scheduler)                       │   ║
║  │  (CU-13) Verificar Estado    (CU-14) Health Check               │   ║
║  │                                                                   │   ║
║  └───────────────────────────────────────────────────────────────────┘   ║
║                                                                         ║
╚═══════════════════════════════════════════════════════════════════════════╝

ACTORES:
  [Microservicio Externo] ──────► CU-01, CU-02 (vía CU-03)
  [Administrador]         ──────► CU-04..CU-11, CU-13, CU-14
  [Scheduler/Retention]   ──────► CU-12 (automático)
"""
    },
    "2_clases": {
        "title": "Diagrama de Clases",
        "content": """
╔═══════════════════════ CAPA DE PRESENTACIÓN ════════════════════════╗
║                                                                     ║
║  ┌──────────────────────────────────────────────────────────┐      ║
║  │            «controller» audit_routes                      │      ║
║  │            (APIRouter: /api/v1/audit)                     │      ║
║  ├──────────────────────────────────────────────────────────┤      ║
║  │ + router: APIRouter                                       │      ║
║  ├──────────────────────────────────────────────────────────┤      ║
║  │ + health_check() : MessageResponse                        │      ║
║  │ + create_audit_log(data, db, _api_key) : DataResponse     │      ║
║  │ + create_audit_logs_batch(logs, db, _api_key): DataResponse│     ║
║  │ + get_audit_logs(page, size, filtros, db): PaginatedResp  │      ║
║  │ + get_audit_log_by_id(audit_id, db): DataResponse         │      ║
║  │ + trace_request(request_id, db): DataResponse             │      ║
║  │ + get_user_audit_logs(usuario_id, page, db): Paginated    │      ║
║  │ + get_statistics(db): StatsResponse                       │      ║
║  │ + purge_logs(before_date, db, _api_key): MessageResponse  │      ║
║  └────────────────────────────┬─────────────────────────────┘      ║
║                               │ usa                                  ║
╚═══════════════════════════════╪═════════════════════════════════════╝
                                │
                                ▼
╔══════════════════════ CAPA DE NEGOCIO ══════════════════════════════╗
║                                                                     ║
║  ┌─────────────────────────┐  ┌───────────────────────────────┐    ║
║  │  «service» AuditService │  │ «service» StatisticsService   │    ║
║  ├─────────────────────────┤  ├───────────────────────────────┤    ║
║  │ - db: AsyncSession      │  │ - repo: AuditRepository       │    ║
║  │ - repo: AuditRepository │  ├───────────────────────────────┤    ║
║  ├─────────────────────────┤  │ + __init__(db: AsyncSession)  │    ║
║  │ + __init__(db)          │  │ + get_general_stats(): dict   │    ║
║  │ + create_log(): Response│  └───────────────────────────────┘    ║
║  │ + create_logs_batch():[]│                                        ║
║  │ + get_by_id(): Resp?    │  ┌───────────────────────────────┐    ║
║  │ + get_logs(): Paginated │  │ «service» RetentionService    │    ║
║  │ + get_by_request_id():[]│  ├───────────────────────────────┤    ║
║  │ + get_by_usuario(): Pg  │  │ - _task: asyncio.Task | None  │    ║
║  │ + purge_old_logs(): int │  │ - _running: bool              │    ║
║  └────────┬────────────────┘  ├───────────────────────────────┤    ║
║           │                    │ + start(): None               │    ║
║  ┌────────┴────────────────┐  │ + stop(): None                │    ║
║  │ «service» AuthService   │  │ + purge_old_logs(): int       │    ║
║  ├─────────────────────────┤  │ - _scheduler_loop(): None     │    ║
║  │ + validate_session()    │  │ - _seconds_until_next(): float│    ║
║  │ + check_permission()    │  └───────────────────────────────┘    ║
║  └─────────────────────────┘                                        ║
║                                                                     ║
╚═══════════════════════════════╪═════════════════════════════════════╝
                                │
                                ▼
╔══════════════════════ CAPA DE DATOS ════════════════════════════════╗
║                                                                     ║
║  ┌──────────────────────────────────────────────────────────┐      ║
║  │          «repository» AuditRepository                     │      ║
║  ├──────────────────────────────────────────────────────────┤      ║
║  │ - session: AsyncSession                                   │      ║
║  ├──────────────────────────────────────────────────────────┤      ║
║  │ + save(audit_log): AuditLog                               │      ║
║  │ + save_batch(logs): List[AuditLog]                        │      ║
║  │ + find_by_id(id): AuditLog?                               │      ║
║  │ + find_all(page, size, **filtros): (List, int)            │      ║
║  │ + find_by_request_id(rid): List[AuditLog]                 │      ║
║  │ + find_by_usuario(uid, page, size): (List, int)           │      ║
║  │ + count_total(): int                                      │      ║
║  │ + count_by_servicio(): List[tuple]                        │      ║
║  │ + count_by_codigo_respuesta(): List[tuple]                │      ║
║  │ + average_duration_by_servicio(): List[tuple]             │      ║
║  │ + error_rate_by_servicio(): List[tuple]                   │      ║
║  │ + delete_before(date): int                                │      ║
║  └──────────────────────────────────────────────────────────┘      ║
║                                                                     ║
╚═══════════════════════════════╪═════════════════════════════════════╝
                                │
                                ▼
╔═════════════════ CAPA DE DOMINIO (Modelos + Schemas) ══════════════╗
║                                                                     ║
║  ┌──────────────────────┐    ┌──────────────────────┐              ║
║  │ «entity» AuditLog    │    │ «entity» Microservice│              ║
║  │ (audit_logs)          │    │ Token                │              ║
║  ├──────────────────────┤    ├──────────────────────┤              ║
║  │ + id: UUID [PK]      │    │ + id: UUID [PK]      │              ║
║  │ + request_id: Str(50) │    │ + nombre_ms: Str(50) │              ║
║  │ + servicio: Str(50)  │    │ + token_hash: Str(256)│              ║
║  │ + endpoint: Str(200) │    │ + activo: Boolean     │              ║
║  │ + metodo: Str(10)    │    │ + created_at: TS(tz)  │              ║
║  │ + codigo_resp: Int   │    │ + updated_at: TS(tz)  │              ║
║  │ + duracion_ms: Int   │    └──────────────────────┘              ║
║  │ + usuario_id: UUID?  │                                           ║
║  │ + detalle: Text?     │    ┌──────────────────────┐              ║
║  │ + ip_origen: Str(45)?│    │ AuditLogCreate (Pyda)│              ║
║  │ + timestamp_evt: TS  │    │ AuditLogResponse     │              ║
║  │ + created_at: TS     │    │ AuditLogFilter       │              ║
║  └──────────────────────┘    │ MessageResponse      │              ║
║                               │ DataResponse<T>      │              ║
║                               │ PaginatedResponse<T> │              ║
║                               │ ErrorResponse        │              ║
║                               │ StatsResponse        │              ║
║                               └──────────────────────┘              ║
║                                                                     ║
╚═════════════════════════════════════════════════════════════════════╝
"""
    },
    "3_secuencia_crear_log": {
        "title": "Secuencia - Crear Log de Auditoria",
        "content": """
Microservicio    RequestID MW    RateLimit MW    audit_routes    verify_api_key    AuditService    AuditRepo
─────┬──────     ────┬─────     ────┬──────     ────┬──────     ────┬────────     ────┬──────     ───┬─────
     │                │              │               │              │                  │             │
     │ POST /log      │              │               │              │                  │             │
     │ X-API-Key: xxx │              │               │              │                  │             │
     │ Body: {...}    │              │               │              │                  │             │
     │───────────────►│              │               │              │                  │             │
     │                │ Inyecta      │               │              │                  │             │
     │                │ X-Request-ID │               │              │                  │             │
     │                │ Inicia timer │               │              │                  │             │
     │                │─────────────►│               │              │                  │             │
     │                │              │ Verifica IP   │              │                  │             │
     │                │              │ sliding window│              │                  │             │
     │                │              │ [OK: < límite]│              │                  │             │
     │                │              │──────────────►│              │                  │             │
     │                │              │               │              │                  │             │
     │                │              │               │ Depends(     │                  │             │
     │                │              │               │ verify_api_key)                 │             │
     │                │              │               │─────────────►│                  │             │
     │                │              │               │              │ SHA-256(key)     │             │
     │                │              │               │              │ SELECT FROM      │             │
     │                │              │               │              │ microservice_tokens             │
     │                │              │               │              │ WHERE hash=? AND activo=true   │
     │                │              │               │ [API Key OK] │                  │             │
     │                │              │               │◄─────────────│                  │             │
     │                │              │               │              │                  │             │
     │                │              │               │ Pydantic valida AuditLogCreate  │             │
     │                │              │               │                                 │             │
     │                │              │               │ service.create_log(data)        │             │
     │                │              │               │────────────────────────────────►│             │
     │                │              │               │                                 │ repo.save() │
     │                │              │               │                                 │────────────►│
     │                │              │               │                                 │ session.add │
     │                │              │               │                                 │ flush()     │
     │                │              │               │                                 │ refresh()   │
     │                │              │               │                                 │◄────────────│
     │                │              │               │                                 │ db.commit() │
     │                │              │               │  AuditLogResponse               │             │
     │                │              │               │◄────────────────────────────────│             │
     │                │              │  201 Created   │                                 │             │
     │                │              │◄───────────────│                                 │             │
     │                │ + X-Request-ID               │                                 │             │
     │                │ + X-Response-Time-ms         │                                 │             │
     │                │◄──────────────               │                                 │             │
     │  201 Created    │              │               │              │                  │             │
     │  {success:true} │              │               │              │                  │             │
     │◄────────────────│              │               │              │                  │             │
"""
    },
    "4_componentes": {
        "title": "Diagrama de Componentes",
        "content": """
╔═════════════════════════════════════════════════════════════════════════════╗
║                        ms-auditoria (:8019)                               ║
║                                                                           ║
║  ┌─────────────── «component» MIDDLEWARE CHAIN ───────────────────┐       ║
║  │  [RequestID MW] ──► [RateLimit MW] ──► [CORS MW]              │       ║
║  │  • X-Request-ID     • 100 req/60s      • Orígenes             │       ║
║  │  • Response time    • Sliding window   • Methods              │       ║
║  └────────────────────────────────┬───────────────────────────────┘       ║
║                                   │                                       ║
║  ┌──────── «component» EXCEPTION HANDLERS ────────────────────────┐       ║
║  │  [HTTP 4xx/5xx]  [Validation 422]  [Unhandled 500]            │       ║
║  └────────────────────────────────┬───────────────────────────────┘       ║
║                                   │                                       ║
║                                   ▼                                       ║
║  ┌─────────────── «component» PRESENTACIÓN ───────────────────────┐       ║
║  │  audit_routes.py (APIRouter /api/v1/audit/*)                   │       ║
║  │  9 endpoints + Depends(verify_api_key, get_db)                 │       ║
║  └────────────────────────────────┬───────────────────────────────┘       ║
║                                   │                                       ║
║                                   ▼                                       ║
║  ┌─────────────── «component» LÓGICA DE NEGOCIO ─────────────────┐       ║
║  │  [AuditService]  [StatisticsService]  [RetentionService]      │       ║
║  │  [AuthService]   [AESCipher (disponible)]                     │       ║
║  └────────────────────────────────┬───────────────────────────────┘       ║
║                                   │                                       ║
║                                   ▼                                       ║
║  ┌─────────────── «component» ACCESO A DATOS ────────────────────┐       ║
║  │  AuditRepository (12 métodos: CRUD + stats + delete)          │       ║
║  └────────────────────────────────┬───────────────────────────────┘       ║
║                                   │                                       ║
║                                   ▼                                       ║
║  ┌─────────────── «component» BASE DE DATOS ─────────────────────┐       ║
║  │  [connection.py: async_engine + pool]  [session.py: AsyncSess] │       ║
║  │  [base.py: DeclarativeBase]  [config.py: Settings + env vars] │       ║
║  └────────────────────────────────┬───────────────────────────────┘       ║
║                                   │                                       ║
║  ┌─────── «component» DOMINIO ────┼────────────── «component» UTILS ─┐   ║
║  │  AuditLog, MicroserviceToken,  │   logger.py (JSON Structured)    │   ║
║  │  GUID, Schemas (Pydantic)      │   JSONFormatter → stdout         │   ║
║  └────────────────────────────────┼──────────────────────────────────┘   ║
║                                   │                                       ║
╚═══════════════════════════════════╪═══════════════════════════════════════╝
                                    │ asyncpg (pool_size=10, max_overflow=20)
                                    ▼
                        ┌──────────────────────┐
                        │    PostgreSQL 16      │
                        │    (:5432)            │
                        │  • audit_logs         │
                        │  • microservice_tokens│
                        │  • 8 índices + GIN    │
                        └──────────────────────┘
"""
    },
    "5_entidad_relacion": {
        "title": "Diagrama Entidad-Relacion",
        "content": """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                      DIAGRAMA ENTIDAD-RELACIÓN                              ║
║                      ms-auditoria — PostgreSQL 16                           ║
║                                                                             ║
║  ┌───────────────────────────────────────────────────────┐                 ║
║  │                     audit_logs                         │                 ║
║  │                     (Tabla principal)                  │                 ║
║  ├───────────────────────────────────────────────────────┤                 ║
║  │ «PK» id               UUID            NOT NULL        │                 ║
║  │───────────────────────────────────────────────────────│                 ║
║  │      request_id       VARCHAR(50)     NOT NULL        │ ◄── IX         ║
║  │      servicio         VARCHAR(50)     NOT NULL        │ ◄── IX         ║
║  │      endpoint         VARCHAR(200)    NOT NULL        │                 ║
║  │      metodo           VARCHAR(10)     NOT NULL        │                 ║
║  │      codigo_respuesta INTEGER         NULLABLE        │ ◄── IX         ║
║  │      duracion_ms      INTEGER         NULLABLE        │                 ║
║  │      usuario_id       UUID            NULLABLE        │ ◄── IX         ║
║  │      detalle          TEXT            NULLABLE        │ ◄── GIN(FTS)   ║
║  │      ip_origen        VARCHAR(45)     NULLABLE        │                 ║
║  │      timestamp_evento TIMESTAMP(tz)   NOT NULL        │                 ║
║  │      created_at       TIMESTAMP(tz)   NOT NULL        │                 ║
║  ├───────────────────────────────────────────────────────┤                 ║
║  │  Índices compuestos:                                  │                 ║
║  │  • (servicio, timestamp_evento)                       │                 ║
║  │  • (usuario_id, timestamp_evento)                     │                 ║
║  │  • (codigo_respuesta, servicio)                       │                 ║
║  │  Índice GIN: to_tsvector('spanish', detalle)          │                 ║
║  └───────────────────────────────────────────────────────┘                 ║
║                                                                             ║
║         Sin FK directa — relación lógica vía API Key en runtime            ║
║                                                                             ║
║  ┌───────────────────────────────────────────────────────┐                 ║
║  │                  microservice_tokens                   │                 ║
║  │                  (Tabla de autenticación)              │                 ║
║  ├───────────────────────────────────────────────────────┤                 ║
║  │ «PK» id                     UUID          NOT NULL    │                 ║
║  │───────────────────────────────────────────────────────│                 ║
║  │ «UQ» nombre_microservicio   VARCHAR(50)   NOT NULL    │                 ║
║  │      token_hash             VARCHAR(256)  NOT NULL    │                 ║
║  │      activo                 BOOLEAN       NOT NULL    │                 ║
║  │      created_at             TIMESTAMP(tz) NOT NULL    │                 ║
║  │      updated_at             TIMESTAMP(tz) NOT NULL    │                 ║
║  └───────────────────────────────────────────────────────┘                 ║
║                                                                             ║
║  Relación lógica: microservice_tokens 1 ─────── 0..* audit_logs           ║
║  (nombre_microservicio ≈ servicio, validada en runtime, no FK en BD)       ║
║                                                                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
    }
}

def get_font():
    """Intenta cargar una fuente monoespaciada comúnmente disponible."""
    try:
        # Windows
        return ImageFont.truetype("consola.ttf", 10)
    except IOError:
        try:
            # macOS
            return ImageFont.truetype("Menlo.ttc", 10)
        except IOError:
            try:
                # Linux (Debian/Ubuntu)
                return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
            except IOError:
                # Fuente por defecto de Pillow si no se encuentran otras
                return ImageFont.load_default()

def generate_images():
    """Genera una imagen PNG para cada diagrama ASCII."""
    font = get_font()
    padding = 20  # Espacio en blanco alrededor del texto
    line_spacing = 4

    for name, data in DIAGRAMS.items():
        title = data["title"]
        content = data["content"].strip()
        
        # Crear un dummy draw para medir el texto
        dummy_img = Image.new('RGB', (1, 1))
        d = ImageDraw.Draw(dummy_img)
        
        # Medir el tamaño del texto
        lines = content.split('
')
        
        # Usar textbbox para obtener el tamaño correcto
        try:
            # Pillow >= 9.2.0
            text_width = 0
            text_height = 0
            for line in lines:
                line_bbox = d.textbbox((0,0), line, font=font)
                text_width = max(text_width, line_bbox[2] - line_bbox[0])
                text_height += (line_bbox[3] - line_bbox[1]) + line_spacing
        except AttributeError:
            # Versiones antiguas de Pillow
            text_width = 0
            text_height = 0
            for line in lines:
                w, h = d.textsize(line, font=font)
                text_width = max(text_width, w)
                text_height += h + line_spacing

        img_width = text_width + (2 * padding)
        img_height = text_height + (2 * padding)

        # Crear la imagen final con el tamaño calculado
        img = Image.new('RGB', (int(img_width), int(img_height)), color='white')
        draw = ImageDraw.Draw(img)

        # Dibujar el texto línea por línea
        y = padding
        for line in lines:
            draw.text((padding, y), line, font=font, fill='black')
            try:
                line_bbox = draw.textbbox((0,0), line, font=font)
                y += (line_bbox[3] - line_bbox[1]) + line_spacing
            except AttributeError:
                 _, h = draw.textsize(line, font=font)
                 y += h + line_spacing

        # Guardar la imagen
        output_path = os.path.join(OUTPUT_DIR, f"{name}.png")
        img.save(output_path)
        print(f"✅ Imagen generada: {output_path}")

if __name__ == "__main__":
    print("Generando imágenes de diagramas...")
    try:
        generate_images()
        print("
Proceso completado.")
        print(f"Las imágenes se han guardado en la carpeta: {os.path.abspath(OUTPUT_DIR)}")
    except ImportError:
        print("
❌ Error: La librería 'Pillow' no está instalada.")
        print("Por favor, instálala ejecutando: pip install Pillow")
    except Exception as e:
        print(f"
❌ Ocurrió un error inesperado: {e}")
