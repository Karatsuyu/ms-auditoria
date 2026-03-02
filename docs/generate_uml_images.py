"""
Genera 5 imágenes PNG de los diagramas UML para ms-auditoria.
Ejecutar: python docs/generate_uml_images.py
Requiere: pip install matplotlib Pillow
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Ellipse, FancyArrowPatch
from matplotlib.path import Path
import matplotlib.patheffects as pe
import numpy as np
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════
# Colores corporativos
# ═══════════════════════════════════════════════════════════════
C_BG = "#FAFBFC"
C_BLUE = "#1A478A"
C_BLUE_LIGHT = "#D6E4F0"
C_BLUE_MED = "#4A90D9"
C_GREEN = "#2E7D32"
C_GREEN_LIGHT = "#E8F5E9"
C_ORANGE = "#E65100"
C_ORANGE_LIGHT = "#FFF3E0"
C_PURPLE = "#6A1B9A"
C_PURPLE_LIGHT = "#F3E5F5"
C_RED = "#C62828"
C_RED_LIGHT = "#FFEBEE"
C_GRAY = "#455A64"
C_GRAY_LIGHT = "#ECEFF1"
C_YELLOW_LIGHT = "#FFFDE7"
C_TEAL = "#00695C"
C_TEAL_LIGHT = "#E0F2F1"
C_WHITE = "#FFFFFF"
C_BLACK = "#212121"


def save_fig(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"  ✅ {name}")


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def draw_actor(ax, x, y, label, color=C_BLACK):
    """Dibuja un actor UML (stickman)."""
    head_r = 0.12
    ax.add_patch(plt.Circle((x, y + 0.55), head_r, fill=False, ec=color, lw=1.8, zorder=5))
    # body
    ax.plot([x, x], [y + 0.43, y + 0.15], color=color, lw=1.8, zorder=5)
    # arms
    ax.plot([x - 0.15, x + 0.15], [y + 0.35, y + 0.35], color=color, lw=1.8, zorder=5)
    # legs
    ax.plot([x, x - 0.12], [y + 0.15, y - 0.05], color=color, lw=1.8, zorder=5)
    ax.plot([x, x + 0.12], [y + 0.15, y - 0.05], color=color, lw=1.8, zorder=5)
    ax.text(x, y - 0.18, label, ha="center", va="top", fontsize=7, fontweight="bold", color=color, zorder=5)


def draw_usecase(ax, x, y, text, color=C_BLUE_LIGHT, ec=C_BLUE):
    """Dibuja un caso de uso (elipse)."""
    e = Ellipse((x, y), 2.2, 0.55, fc=color, ec=ec, lw=1.5, zorder=3)
    ax.add_patch(e)
    ax.text(x, y, text, ha="center", va="center", fontsize=5.8, color=C_BLACK, zorder=4, wrap=True)


def draw_class_box(ax, x, y, w, h, title, attrs, methods, title_color=C_BLUE, bg=C_WHITE):
    """Dibuja un rectángulo de clase UML con 3 compartimentos."""
    # Fondo completo
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=bg, ec=title_color, lw=1.5, zorder=3)
    ax.add_patch(rect)

    title_h = 0.35
    # Título
    title_rect = FancyBboxPatch((x, y + h - title_h), w, title_h, boxstyle="round,pad=0.02", fc=title_color, ec=title_color, lw=0, zorder=4)
    ax.add_patch(title_rect)
    ax.text(x + w / 2, y + h - title_h / 2, title, ha="center", va="center",
            fontsize=6.5, fontweight="bold", color=C_WHITE, zorder=5)

    # Atributos
    attr_start_y = y + h - title_h - 0.05
    for i, attr in enumerate(attrs):
        ax.text(x + 0.08, attr_start_y - i * 0.18, attr, ha="left", va="top",
                fontsize=4.8, color=C_BLACK, fontfamily="monospace", zorder=5)

    # Línea divisoria
    div_y = attr_start_y - len(attrs) * 0.18 - 0.02
    ax.plot([x + 0.03, x + w - 0.03], [div_y, div_y], color=title_color, lw=0.8, zorder=5)

    # Métodos
    meth_start_y = div_y - 0.05
    for i, m in enumerate(methods):
        ax.text(x + 0.08, meth_start_y - i * 0.18, m, ha="left", va="top",
                fontsize=4.8, color=C_BLACK, fontfamily="monospace", zorder=5)


def draw_arrow(ax, x1, y1, x2, y2, style="-|>", color=C_GRAY, lw=1.2, ls="-"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw, ls=ls), zorder=2)


def draw_diamond(ax, cx, cy, w, h, text, fc="#FFF9C4", ec=C_BLACK):
    """Dibuja un rombo (para ER)."""
    verts = [
        (cx, cy + h / 2),  # top
        (cx + w / 2, cy),  # right
        (cx, cy - h / 2),  # bottom
        (cx - w / 2, cy),  # left
        (cx, cy + h / 2),  # close
    ]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
    path = Path(verts, codes)
    patch = mpatches.PathPatch(path, fc=fc, ec=ec, lw=1.5, zorder=3)
    ax.add_patch(patch)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=6, fontweight="bold", color=C_BLACK, zorder=4)


def draw_er_entity(ax, x, y, w, h, name, attrs, pk_indices=None, fc=C_BLUE_LIGHT, ec=C_BLUE):
    """Dibuja una entidad ER con atributos como óvalos."""
    # Rectángulo principal
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=ec, lw=2, zorder=3)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, name, ha="center", va="center",
            fontsize=9, fontweight="bold", color=C_BLACK, zorder=4)
    return (x + w / 2, y + h / 2)


def draw_er_attribute(ax, cx, cy, text, is_pk=False, is_derived=False, fc=C_WHITE, ec=C_BLACK):
    """Dibuja un atributo ER como óvalo."""
    w_ellipse = max(1.3, len(text) * 0.1 + 0.6)
    h_ellipse = 0.36
    ls = "--" if is_derived else "-"
    e = Ellipse((cx, cy), w_ellipse, h_ellipse, fc=fc, ec=ec, lw=1.2, ls=ls, zorder=3)
    ax.add_patch(e)
    style = "bold" if is_pk else "normal"
    decoration = "underline" if is_pk else "none"
    t = ax.text(cx, cy, text, ha="center", va="center", fontsize=5.2,
                fontweight=style, color=C_BLACK, zorder=4)
    if is_pk:
        t.set_path_effects([])
        # Subrayado manual para PK
        ax.plot([cx - len(text) * 0.035, cx + len(text) * 0.035], [cy - 0.08, cy - 0.08],
                color=C_BLACK, lw=1, zorder=5)


# ═══════════════════════════════════════════════════════════════
# 1. DIAGRAMA DE CASOS DE USO
# ═══════════════════════════════════════════════════════════════

def generate_use_case_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(16, 11))
    fig.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_xlim(-1, 15)
    ax.set_ylim(-1, 10.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # Título
    ax.text(7, 10.2, "Diagrama de Casos de Uso — ms-auditoria", ha="center", va="center",
            fontsize=14, fontweight="bold", color=C_BLUE)
    ax.text(7, 9.85, "Microservicio #19: Auditoría y Logging del ERP Universitario", ha="center",
            fontsize=9, color=C_GRAY)

    # ── Sistema boundary ──
    sys_rect = FancyBboxPatch((2.5, 0.2), 10, 9.2, boxstyle="round,pad=0.1",
                               fc=C_WHITE, ec=C_BLUE, lw=2, ls="--", zorder=1)
    ax.add_patch(sys_rect)
    ax.text(7.5, 9.15, "«system» ms-auditoria", ha="center", fontsize=10,
            fontweight="bold", color=C_BLUE, zorder=2)

    # ── Actores ──
    draw_actor(ax, 0.5, 7.5, "Microservicio\nExterno", C_BLUE)
    draw_actor(ax, 0.5, 4.5, "Administrador\ndel Sistema", C_GREEN)
    draw_actor(ax, 14, 2.5, "Scheduler\n(Retention)", C_ORANGE)
    
    # Sistemas externos (cajas)
    ext1 = FancyBboxPatch((13, 7.3), 1.8, 0.6, boxstyle="round,pad=0.05", fc=C_PURPLE_LIGHT, ec=C_PURPLE, lw=1.2, zorder=3)
    ax.add_patch(ext1)
    ax.text(13.9, 7.6, "ms-autenticación", ha="center", fontsize=5.5, color=C_PURPLE, fontweight="bold", zorder=4)
    
    ext2 = FancyBboxPatch((13, 6.4), 1.8, 0.6, boxstyle="round,pad=0.05", fc=C_PURPLE_LIGHT, ec=C_PURPLE, lw=1.2, zorder=3)
    ax.add_patch(ext2)
    ax.text(13.9, 6.7, "ms-roles-permisos", ha="center", fontsize=5.5, color=C_PURPLE, fontweight="bold", zorder=4)

    # ── Grupo: Gestión de Logs ──
    grp1 = FancyBboxPatch((3, 7, ), 4.5, 2, boxstyle="round,pad=0.05", fc=C_BLUE_LIGHT, ec=C_BLUE, lw=1, ls=":", alpha=0.3, zorder=1)
    ax.add_patch(grp1)
    ax.text(5.25, 8.8, "Gestión de Logs", fontsize=7, fontstyle="italic", color=C_BLUE, ha="center")

    draw_usecase(ax, 4.2, 8.2, "CU-01\nRegistrar Log", C_BLUE_LIGHT)
    draw_usecase(ax, 6.5, 8.2, "CU-02\nRegistrar Batch", C_BLUE_LIGHT)
    draw_usecase(ax, 5.35, 7.35, "CU-03\nValidar API Key", C_ORANGE_LIGHT, C_ORANGE)

    # ── Grupo: Consulta ──
    grp2 = FancyBboxPatch((3, 3.7), 6, 3, boxstyle="round,pad=0.05", fc=C_GREEN_LIGHT, ec=C_GREEN, lw=1, ls=":", alpha=0.3, zorder=1)
    ax.add_patch(grp2)
    ax.text(6, 6.5, "Consulta de Logs", fontsize=7, fontstyle="italic", color=C_GREEN, ha="center")

    draw_usecase(ax, 4.2, 6.0, "CU-04\nConsultar Logs", C_GREEN_LIGHT, C_GREEN)
    draw_usecase(ax, 6.8, 6.0, "CU-05\nFiltrar Avanzado", C_GREEN_LIGHT, C_GREEN)
    draw_usecase(ax, 4.2, 5.3, "CU-06\nObtener por ID", C_GREEN_LIGHT, C_GREEN)
    draw_usecase(ax, 6.8, 5.3, "CU-07\nTraza Request", C_GREEN_LIGHT, C_GREEN)
    draw_usecase(ax, 4.2, 4.55, "CU-08\nLogs por Usuario", C_GREEN_LIGHT, C_GREEN)
    draw_usecase(ax, 6.8, 4.55, "CU-09\nFull-Text Search", C_GREEN_LIGHT, C_GREEN)
    draw_usecase(ax, 5.5, 3.9, "CU-10\nEstadísticas", C_TEAL_LIGHT, C_TEAL)

    # ── Grupo: Administración ──
    grp3 = FancyBboxPatch((3, 0.5), 6.5, 2.9, boxstyle="round,pad=0.05", fc=C_ORANGE_LIGHT, ec=C_ORANGE, lw=1, ls=":", alpha=0.3, zorder=1)
    ax.add_patch(grp3)
    ax.text(6.25, 3.2, "Administración", fontsize=7, fontstyle="italic", color=C_ORANGE, ha="center")

    draw_usecase(ax, 4.5, 2.6, "CU-11\nPurgar Manual", C_RED_LIGHT, C_RED)
    draw_usecase(ax, 7.5, 2.6, "CU-12\nPurga Auto (TTL)", C_ORANGE_LIGHT, C_ORANGE)
    draw_usecase(ax, 4.5, 1.6, "CU-13\nHealth Check", C_GRAY_LIGHT, C_GRAY)
    draw_usecase(ax, 7.5, 1.6, "CU-14\nEstado Servicio", C_GRAY_LIGHT, C_GRAY)

    # ── Líneas Actor → CU ──
    # Microservicio externo
    ax.plot([0.9, 3.1], [7.8, 8.2], color=C_BLUE, lw=1, zorder=2)
    ax.plot([0.9, 5.3], [7.8, 8.2], color=C_BLUE, lw=1, zorder=2)

    # Administrador
    for cy in [6.0, 5.3, 4.55]:
        ax.plot([0.9, 3.1], [4.7, cy], color=C_GREEN, lw=0.8, zorder=2)
    ax.plot([0.9, 5.6], [4.7, 6.0], color=C_GREEN, lw=0.8, zorder=2)
    ax.plot([0.9, 4.4], [4.7, 3.9], color=C_GREEN, lw=0.8, zorder=2)
    ax.plot([0.9, 3.4], [4.4, 2.6], color=C_GREEN, lw=0.8, zorder=2)
    ax.plot([0.9, 3.4], [4.2, 1.6], color=C_GREEN, lw=0.8, zorder=2)

    # Scheduler
    ax.plot([13.6, 8.6], [2.8, 2.6], color=C_ORANGE, lw=1.2, zorder=2)

    # ── «include» ──
    ax.annotate("", xy=(5.35, 7.62), xytext=(4.2, 7.93),
                arrowprops=dict(arrowstyle="-|>", color=C_ORANGE, lw=1, ls="--"), zorder=2)
    ax.text(4.5, 7.85, "«include»", fontsize=4.5, color=C_ORANGE, fontstyle="italic", rotation=-25)

    ax.annotate("", xy=(5.35, 7.62), xytext=(6.5, 7.93),
                arrowprops=dict(arrowstyle="-|>", color=C_ORANGE, lw=1, ls="--"), zorder=2)
    ax.text(6.1, 7.85, "«include»", fontsize=4.5, color=C_ORANGE, fontstyle="italic", rotation=25)

    ax.annotate("", xy=(5.35, 7.08), xytext=(4.5, 2.87),
                arrowprops=dict(arrowstyle="-|>", color=C_ORANGE, lw=1, ls="--"), zorder=2)
    ax.text(4.7, 5.0, "«include»", fontsize=4.5, color=C_ORANGE, fontstyle="italic", rotation=80)
    
    # Auth service connections
    ax.plot([6.45, 13], [7.35, 7.6], color=C_PURPLE, lw=0.8, ls=":", zorder=2)
    ax.plot([6.45, 13], [7.35, 6.7], color=C_PURPLE, lw=0.8, ls=":", zorder=2)

    save_fig(fig, "diagrama_1_casos_de_uso.png")


# ═══════════════════════════════════════════════════════════════
# 2. DIAGRAMA DE CLASES UML
# ═══════════════════════════════════════════════════════════════

def generate_class_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(20, 14))
    fig.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_xlim(-0.5, 19.5)
    ax.set_ylim(-0.5, 13.5)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.text(10, 13.2, "Diagrama de Clases UML — ms-auditoria", ha="center",
            fontsize=14, fontweight="bold", color=C_BLUE)

    # ══ CAPA PRESENTACIÓN ══
    layer_p = FancyBboxPatch((0, 10.5), 19, 2.3, boxstyle="round,pad=0.05",
                              fc="#E3F2FD", ec=C_BLUE, lw=1.5, ls="--", alpha=0.4, zorder=0)
    ax.add_patch(layer_p)
    ax.text(0.3, 12.55, "«Capa de Presentación»", fontsize=8, fontstyle="italic", color=C_BLUE)

    draw_class_box(ax, 3, 10.6, 5.5, 2.0,
                   "«controller» audit_routes",
                   ["+ router: APIRouter"],
                   ["+ health_check(): MessageResponse",
                    "+ create_audit_log(data,db): DataResponse",
                    "+ create_audit_logs_batch(): DataResponse",
                    "+ get_audit_logs(page,filters): Paginated",
                    "+ get_audit_log_by_id(id): DataResponse",
                    "+ trace_request(rid): DataResponse",
                    "+ get_user_audit_logs(uid): Paginated",
                    "+ get_statistics(db): StatsResponse",
                    "+ purge_logs(date,db): MessageResponse"],
                   title_color=C_BLUE, bg=C_WHITE)

    # Dependencies
    draw_class_box(ax, 10, 11.3, 2.5, 0.9,
                   "verify_api_key()",
                   ["Depends()"],
                   ["SHA-256 → BD"],
                   title_color=C_ORANGE, bg=C_ORANGE_LIGHT)

    draw_class_box(ax, 13.5, 11.3, 2.5, 0.9,
                   "get_db()",
                   ["Depends()"],
                   ["→ AsyncSession"],
                   title_color=C_TEAL, bg=C_TEAL_LIGHT)

    # ══ CAPA NEGOCIO ══
    layer_s = FancyBboxPatch((0, 6.2), 19, 4.0, boxstyle="round,pad=0.05",
                              fc=C_GREEN_LIGHT, ec=C_GREEN, lw=1.5, ls="--", alpha=0.3, zorder=0)
    ax.add_patch(layer_s)
    ax.text(0.3, 9.95, "«Capa de Negocio (Services)»", fontsize=8, fontstyle="italic", color=C_GREEN)

    draw_class_box(ax, 0.5, 6.5, 4.5, 2.9,
                   "«service» AuditService",
                   ["- db: AsyncSession", "- repo: AuditRepository"],
                   ["+ __init__(db: AsyncSession)",
                    "+ create_log(data): AuditLogResponse",
                    "+ create_logs_batch(logs): List",
                    "+ get_by_id(id): AuditLogResponse?",
                    "+ get_logs(page,filters): Paginated",
                    "+ get_by_request_id(rid): List",
                    "+ get_by_usuario(uid,pg): Paginated",
                    "+ purge_old_logs(date): int"],
                   title_color=C_GREEN, bg=C_WHITE)

    draw_class_box(ax, 5.8, 7.5, 3.8, 1.8,
                   "«service» StatisticsService",
                   ["- repo: AuditRepository"],
                   ["+ __init__(db: AsyncSession)",
                    "+ get_general_stats(): dict",
                    "  → count_total, by_servicio",
                    "  → by_codigo, avg_dur, err_rate"],
                   title_color=C_GREEN, bg=C_WHITE)

    draw_class_box(ax, 10.3, 6.5, 4.0, 2.8,
                   "«service» RetentionService",
                   ["- _task: asyncio.Task | None", "- _running: bool"],
                   ["+ start(): None",
                    "+ stop(): None",
                    "+ purge_old_logs(): int",
                    "- _scheduler_loop(): None",
                    "- _seconds_until_next(): float",
                    "  Singleton: retention_service"],
                   title_color=C_ORANGE, bg=C_WHITE)

    draw_class_box(ax, 15, 7.5, 3.5, 1.5,
                   "«service» AuthService",
                   [],
                   ["+ validate_session(token): dict?",
                    "+ check_permission(token,p): bool",
                    "  HTTP → ms-autenticación",
                    "  HTTP → ms-roles-permisos"],
                   title_color=C_PURPLE, bg=C_WHITE)

    # ══ CAPA DATOS ══
    layer_r = FancyBboxPatch((0, 2.8), 12, 3.1, boxstyle="round,pad=0.05",
                              fc=C_TEAL_LIGHT, ec=C_TEAL, lw=1.5, ls="--", alpha=0.3, zorder=0)
    ax.add_patch(layer_r)
    ax.text(0.3, 5.65, "«Capa de Datos (Repository)»", fontsize=8, fontstyle="italic", color=C_TEAL)

    draw_class_box(ax, 1, 2.9, 5.5, 2.7,
                   "«repository» AuditRepository",
                   ["- session: AsyncSession"],
                   ["+ save(log): AuditLog",
                    "+ save_batch(logs): List[AuditLog]",
                    "+ find_by_id(id): AuditLog?",
                    "+ find_all(page,size,**f): (List,int)",
                    "+ find_by_request_id(rid): List",
                    "+ find_by_usuario(uid,pg,sz): (List,int)",
                    "+ count_total() / count_by_servicio()",
                    "+ count_by_codigo() / avg_duration()",
                    "+ error_rate_by_servicio()",
                    "+ delete_before(date): int"],
                   title_color=C_TEAL, bg=C_WHITE)

    draw_class_box(ax, 7.5, 3.8, 3.5, 1.2,
                   "«security» AESCipher",
                   ["- key: bytes (32)", "- Singleton: aes_cipher"],
                   ["+ encrypt(text): str (Base64)",
                    "+ decrypt(token): str"],
                   title_color=C_RED, bg=C_RED_LIGHT)

    # ══ CAPA DOMINIO ══
    layer_d = FancyBboxPatch((0, -0.3), 19, 2.8, boxstyle="round,pad=0.05",
                              fc=C_YELLOW_LIGHT, ec="#F9A825", lw=1.5, ls="--", alpha=0.4, zorder=0)
    ax.add_patch(layer_d)
    ax.text(0.3, 2.2, "«Capa de Dominio (Models + Schemas)»", fontsize=8, fontstyle="italic", color="#F57F17")

    draw_class_box(ax, 0.3, -0.1, 3.8, 2.2,
                   "«entity» AuditLog",
                   ["+ id: UUID [PK]", "+ request_id: Str(50)",
                    "+ servicio: Str(50)", "+ endpoint: Str(200)",
                    "+ metodo: Str(10)", "+ codigo_resp: Integer",
                    "+ duracion_ms: Integer", "+ usuario_id: UUID?",
                    "+ detalle: Text?", "+ ip_origen: Str(45)?",
                    "+ timestamp_evento: TS(tz)", "+ created_at: TS(tz)"],
                   [],
                   title_color="#E65100", bg=C_WHITE)

    draw_class_box(ax, 4.5, 0.5, 3.2, 1.3,
                   "«entity» MicroserviceToken",
                   ["+ id: UUID [PK]", "+ nombre_ms: Str(50) [UQ]",
                    "+ token_hash: Str(256)", "+ activo: Boolean",
                    "+ created_at: TS(tz)", "+ updated_at: TS(tz)"],
                   [],
                   title_color="#E65100", bg=C_WHITE)

    draw_class_box(ax, 8.3, 0.2, 2.8, 1.5,
                   "«schema» AuditLogCreate",
                   ["+ timestamp: datetime",
                    "+ nombre_ms: str", "+ endpoint: str",
                    "+ metodo_http: str", "+ codigo_resp: int",
                    "+ duracion_ms: int", "+ usuario_id: UUID?",
                    "+ detalle: str?", "+ ip_origen: str?",
                    "+ request_id: str?"],
                   [],
                   title_color=C_PURPLE, bg=C_PURPLE_LIGHT)

    draw_class_box(ax, 11.5, 0.2, 2.8, 1.5,
                   "«schema» AuditLogResponse",
                   ["+ id: UUID", "+ request_id: str",
                    "+ servicio: str", "+ metodo: str",
                    "+ codigo_respuesta: int",
                    "+ timestamp_evento: datetime",
                    "+ created_at: datetime",
                    "  (from_attributes=True)"],
                   [],
                   title_color=C_PURPLE, bg=C_PURPLE_LIGHT)

    draw_class_box(ax, 14.7, 0.2, 2.5, 1.2,
                   "«schema» Responses",
                   ["MessageResponse",
                    "DataResponse[T]",
                    "PaginatedResponse[T]",
                    "ErrorResponse",
                    "StatsResponse"],
                   [],
                   title_color=C_PURPLE, bg=C_PURPLE_LIGHT)

    draw_class_box(ax, 17.5, 0.2, 1.8, 0.9,
                   "«schema» AuditLogFilter",
                   ["servicio?, metodo?",
                    "codigo?, usuario_id?",
                    "fecha_ini?, fecha_fin?",
                    "request_id?, search?"],
                   [],
                   title_color=C_PURPLE, bg=C_PURPLE_LIGHT)

    # ── Flechas de relación ──
    # Router → AuditService
    draw_arrow(ax, 5.5, 10.6, 2.75, 9.4, color=C_BLUE, lw=1.2)
    ax.text(3.8, 10.1, "usa", fontsize=6, color=C_BLUE, fontstyle="italic")

    # Router → StatisticsService
    draw_arrow(ax, 6.5, 10.6, 7.5, 9.3, color=C_BLUE, lw=1.2)

    # Router → Dependencies
    draw_arrow(ax, 8.5, 11.6, 10, 11.8, color=C_ORANGE, lw=1, style="-|>")
    draw_arrow(ax, 8.5, 11.5, 13.5, 11.7, color=C_TEAL, lw=1, style="-|>")

    # Service → Repository
    draw_arrow(ax, 2.75, 6.5, 3.5, 5.6, color=C_GREEN, lw=1.2)
    ax.text(2.5, 6.1, "usa", fontsize=6, color=C_GREEN, fontstyle="italic")

    # StatisticsService → Repository
    draw_arrow(ax, 7.7, 7.5, 5.5, 5.6, color=C_GREEN, lw=1.0)

    # Repository → AuditLog
    draw_arrow(ax, 3.5, 2.9, 2.2, 2.1, color=C_TEAL, lw=1.2)
    ax.text(2.5, 2.6, "opera sobre", fontsize=5, color=C_TEAL, fontstyle="italic")

    save_fig(fig, "diagrama_2_clases_uml.png")


# ═══════════════════════════════════════════════════════════════
# 3. DIAGRAMA DE SECUENCIA (Crear Log)
# ═══════════════════════════════════════════════════════════════

def generate_sequence_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(18, 13))
    fig.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_xlim(-0.5, 17.5)
    ax.set_ylim(-0.5, 13)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.text(8.5, 12.7, "Diagrama de Secuencia — POST /api/v1/audit/log", ha="center",
            fontsize=14, fontweight="bold", color=C_BLUE)
    ax.text(8.5, 12.35, "Flujo completo: Crear Log de Auditoría", ha="center",
            fontsize=9, color=C_GRAY)

    # ── Participantes (lifelines) ──
    participants = [
        (0.5, "Microservicio\nExterno", C_BLUE),
        (3.0, "RequestID\nMiddleware", C_GRAY),
        (5.5, "RateLimit\nMiddleware", C_GRAY),
        (8.0, "audit_routes\n(Controller)", C_GREEN),
        (10.5, "verify_api_key\n(Auth)", C_ORANGE),
        (13.0, "AuditService\n(Service)", C_TEAL),
        (15.5, "AuditRepo\n(Repository)", C_PURPLE),
    ]

    for px, label, color in participants:
        # Header box
        rect = FancyBboxPatch((px - 0.9, 11.5), 1.8, 0.7, boxstyle="round,pad=0.05",
                               fc=color, ec=color, lw=1.5, zorder=3)
        ax.add_patch(rect)
        ax.text(px, 11.85, label, ha="center", va="center", fontsize=6,
                fontweight="bold", color=C_WHITE, zorder=4)
        # Lifeline
        ax.plot([px, px], [11.5, 0.2], color=color, lw=1, ls="--", alpha=0.5, zorder=1)
        # Activation bar
        ax.add_patch(FancyBboxPatch((px - 0.12, 0.5), 0.24, 10.8, boxstyle="square,pad=0",
                                     fc=color, ec="none", alpha=0.1, zorder=1))

    # ── Mensajes ──
    y = 11.0
    step = 0.7

    def msg(x1, x2, y_pos, text, color=C_BLACK, dashed=False):
        ls = "--" if dashed else "-"
        ax.annotate("", xy=(x2, y_pos), xytext=(x1, y_pos),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2, ls=ls), zorder=3)
        mid_x = (x1 + x2) / 2
        offset = 0.12
        ax.text(mid_x, y_pos + offset, text, ha="center", va="bottom",
                fontsize=5.5, color=color, fontweight="bold", zorder=4,
                bbox=dict(boxstyle="round,pad=0.1", fc=C_WHITE, ec="none", alpha=0.8))

    def self_msg(x, y_pos, text, color=C_BLACK):
        ax.annotate("", xy=(x + 0.05, y_pos - 0.25), xytext=(x + 0.8, y_pos - 0.25),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1), zorder=3)
        ax.plot([x + 0.05, x + 0.8], [y_pos, y_pos], color=color, lw=1, zorder=3)
        ax.plot([x + 0.8, x + 0.8], [y_pos, y_pos - 0.25], color=color, lw=1, zorder=3)
        ax.text(x + 0.9, y_pos - 0.05, text, ha="left", fontsize=5, color=color, fontstyle="italic", zorder=4)

    # 1. POST /log
    msg(0.5, 3.0, y, "POST /api/v1/audit/log\nX-API-Key: xxx, Body:{...}", C_BLUE)
    y -= step

    # 2. RequestID MW
    self_msg(3.0, y, "Inyecta X-Request-ID\nInicia perf_counter", C_GRAY)
    y -= step

    # 3. → RateLimit
    msg(3.0, 5.5, y, "forward request", C_GRAY)
    y -= step * 0.7

    # 4. RateLimit check
    self_msg(5.5, y, "Verifica IP sliding window\n[OK: bajo límite 100/60s]", C_GRAY)
    y -= step

    # 5. → Controller
    msg(5.5, 8.0, y, "forward request", C_GRAY)
    y -= step * 0.8

    # 6. → verify_api_key
    msg(8.0, 10.5, y, "Depends(verify_api_key)", C_ORANGE)
    y -= step * 0.7

    # 7. SHA-256
    self_msg(10.5, y, "hash = SHA-256(X-API-Key)", C_ORANGE)
    y -= step * 0.7

    # 8. DB lookup
    msg(10.5, 15.5, y, "SELECT * FROM microservice_tokens\nWHERE token_hash=? AND activo=true", C_PURPLE)
    y -= step * 0.6

    # 9. Return token
    msg(15.5, 10.5, y, "token_record ✓", C_PURPLE, dashed=True)
    y -= step * 0.6

    # 10. Auth OK
    msg(10.5, 8.0, y, "[API Key válido] ✓", C_ORANGE, dashed=True)
    y -= step

    # 11. Pydantic validation
    self_msg(8.0, y, "Pydantic valida\nAuditLogCreate", C_GREEN)
    y -= step

    # 12. → Service
    msg(8.0, 13.0, y, "service.create_log(data)", C_GREEN)
    y -= step * 0.7

    # 13. Service → Repo
    msg(13.0, 15.5, y, "repo.save(audit_log)", C_TEAL)
    y -= step * 0.6

    # 14. Repo operations
    self_msg(15.5, y, "session.add(log)\nflush() → refresh()", C_PURPLE)
    y -= step * 0.7

    # 15. Repo returns
    msg(15.5, 13.0, y, "AuditLog (persisted)", C_PURPLE, dashed=True)
    y -= step * 0.6

    # 16. Commit
    self_msg(13.0, y, "db.commit()", C_TEAL)
    y -= step * 0.7

    # 17. Service returns
    msg(13.0, 8.0, y, "AuditLogResponse\n(model_validate)", C_GREEN, dashed=True)
    y -= step * 0.7

    # 18. 201 back through middleware
    msg(8.0, 3.0, y, "201 Created + headers", C_GRAY, dashed=True)
    y -= step * 0.5

    # 19. Add headers
    self_msg(3.0, y, "X-Request-ID\nX-Response-Time-ms", C_GRAY)
    y -= step * 0.6

    # 20. Final response
    msg(3.0, 0.5, y, "201 Created\n{success:true, data:{...}}", C_BLUE, dashed=True)

    save_fig(fig, "diagrama_3_secuencia_crear_log.png")


# ═══════════════════════════════════════════════════════════════
# 4. DIAGRAMA DE COMPONENTES
# ═══════════════════════════════════════════════════════════════

def generate_component_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(16, 13))
    fig.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_xlim(-0.5, 15.5)
    ax.set_ylim(-1, 13)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.text(7.5, 12.7, "Diagrama de Componentes — ms-auditoria", ha="center",
            fontsize=14, fontweight="bold", color=C_BLUE)

    def draw_component(ax, x, y, w, h, title, items, fc, ec):
        """Dibuja un componente UML con el icono de componente."""
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc=fc, ec=ec, lw=2, zorder=3)
        ax.add_patch(rect)
        # Component icon (small rectangles on left)
        icon_x = x - 0.15
        icon_y = y + h - 0.35
        for dy in [0, -0.25]:
            r = FancyBboxPatch((icon_x, icon_y + dy), 0.3, 0.18, boxstyle="square,pad=0",
                                fc=ec, ec=ec, lw=1, zorder=4)
            ax.add_patch(r)
        ax.text(x + w / 2, y + h - 0.25, f"«component»\n{title}", ha="center", va="top",
                fontsize=8, fontweight="bold", color=ec, zorder=4)
        for i, item in enumerate(items):
            ax.text(x + 0.3, y + h - 0.75 - i * 0.3, item, ha="left", fontsize=6,
                    color=C_BLACK, zorder=4)

    # ── System boundary ──
    sys = FancyBboxPatch((0.5, -0.5), 14, 12.5, boxstyle="round,pad=0.1",
                          fc=C_WHITE, ec=C_BLUE, lw=2.5, ls="-", zorder=0)
    ax.add_patch(sys)
    ax.text(7.5, 11.75, "ms-auditoria (:8019)", ha="center", fontsize=11,
            fontweight="bold", color=C_BLUE)

    # ── Middleware Chain ──
    draw_component(ax, 2, 9.8, 11, 1.7, "MIDDLEWARE CHAIN",
                   ["[RequestID MW] → [RateLimit MW] → [CORS MW]",
                    "• X-Request-ID + timer    • 100 req/60s sliding    • Orígenes configurables"],
                   C_GRAY_LIGHT, C_GRAY)

    # ── Exception Handlers ──
    draw_component(ax, 2, 8.3, 5, 1.2, "EXCEPTION HANDLERS",
                   ["HTTP 4xx/5xx │ Validation 422 │ Generic 500"],
                   C_RED_LIGHT, C_RED)

    # Flecha MW → Handlers (lateral)
    ax.annotate("", xy=(4.5, 8.3 + 1.2), xytext=(4.5, 9.8),
                arrowprops=dict(arrowstyle="-|>", color=C_GRAY, lw=1.2, ls="--"), zorder=2)

    # ── Presentación ──
    draw_component(ax, 2, 6.0, 11, 1.9, "PRESENTACIÓN (Routes)",
                   ["audit_routes.py — APIRouter /api/v1/audit/*",
                    "9 endpoints: health, log, batch, logs, log/{id}, trace/{rid}, user/{uid}, stats, purge",
                    "Depends: verify_api_key() + get_db() → AsyncSession"],
                   C_BLUE_LIGHT, C_BLUE)

    # Arrow MW → Routes
    ax.annotate("", xy=(7.5, 6.0 + 1.9), xytext=(7.5, 9.8),
                arrowprops=dict(arrowstyle="-|>", color=C_GRAY, lw=1.5), zorder=2)

    # ── Lógica de Negocio ──
    draw_component(ax, 2, 3.4, 11, 2.2, "LÓGICA DE NEGOCIO (Services)",
                   ["[AuditService]         — CRUD + paginación + purga (7 métodos)",
                    "[StatisticsService]   — Métricas: count, avg, error_rate (5 queries)",
                    "[RetentionService]    — Scheduler asyncio, purga TTL 90 días @03:00 UTC",
                    "[AuthService]           — HTTP → ms-autenticación, ms-roles-permisos",
                    "[AESCipher]              — AES-256-GCM cifrado (disponible, no auto-aplicado)"],
                   C_GREEN_LIGHT, C_GREEN)

    # Arrow Routes → Services
    ax.annotate("", xy=(7.5, 3.4 + 2.2), xytext=(7.5, 6.0),
                arrowprops=dict(arrowstyle="-|>", color=C_BLUE, lw=1.5), zorder=2)

    # ── Repository ──
    draw_component(ax, 2, 1.3, 11, 1.7, "ACCESO A DATOS (Repository)",
                   ["AuditRepository — 12 métodos async",
                    "CRUD: save, save_batch, find_by_id, find_all, find_by_request_id, find_by_usuario",
                    "Stats: count_total, count_by_servicio, count_by_codigo, avg_duration, error_rate, delete_before"],
                   C_TEAL_LIGHT, C_TEAL)

    # Arrow Services → Repo
    ax.annotate("", xy=(7.5, 1.3 + 1.7), xytext=(7.5, 3.4),
                arrowprops=dict(arrowstyle="-|>", color=C_GREEN, lw=1.5), zorder=2)

    # ── Database infra ──
    draw_component(ax, 2, -0.3, 5.5, 1.2, "DATABASE INFRA",
                   ["connection.py: async_engine (asyncpg, pool=10/20)",
                    "session.py: AsyncSessionLocal │ base.py: DeclarativeBase"],
                   C_YELLOW_LIGHT, "#F57F17")

    # Arrow Repo → DB Infra
    ax.annotate("", xy=(5, -0.3 + 1.2), xytext=(5, 1.3),
                arrowprops=dict(arrowstyle="-|>", color=C_TEAL, lw=1.5), zorder=2)

    # ── Dominio ──
    draw_component(ax, 8.5, -0.3, 4.5, 1.2, "DOMINIO (Models+Schemas)",
                   ["AuditLog (12 cols) │ MicroserviceToken (6 cols)",
                    "Pydantic: Create, Response, Filter, Paginated"],
                   C_PURPLE_LIGHT, C_PURPLE)

    # ── PostgreSQL (external) ──
    pg_rect = FancyBboxPatch((4, -2.8), 7, 1.5, boxstyle="round,pad=0.1",
                              fc="#E3F2FD", ec=C_BLUE, lw=2.5, zorder=3)
    ax.add_patch(pg_rect)
    # DB cylinder icon
    ax.add_patch(Ellipse((5, -1.6), 1.2, 0.4, fc="#BBDEFB", ec=C_BLUE, lw=1.5, zorder=4))
    ax.text(7.5, -1.8, "PostgreSQL 16 (:5432)\naudit_logs │ microservice_tokens\n8 B-Tree + 1 GIN (full-text español)",
            ha="center", va="center", fontsize=7, color=C_BLUE, fontweight="bold", zorder=4)

    # Arrow DB Infra → PostgreSQL
    ax.annotate("", xy=(5, -1.3), xytext=(5, -0.3),
                arrowprops=dict(arrowstyle="-|>", color="#F57F17", lw=2), zorder=2)
    ax.text(5.3, -0.8, "asyncpg", fontsize=7, color="#F57F17", fontweight="bold")

    # ── Logger (cross-cutting) ──
    logger_rect = FancyBboxPatch((13.5, 4.0), 1.3, 5.0, boxstyle="round,pad=0.05",
                                  fc=C_GRAY_LIGHT, ec=C_GRAY, lw=1.5, zorder=3)
    ax.add_patch(logger_rect)
    ax.text(14.15, 8.5, "«util»\nJSON\nLogger", ha="center", fontsize=6.5,
            fontweight="bold", color=C_GRAY, zorder=4, rotation=0)
    ax.text(14.15, 7.0, "JSON\nForma-\ntter\n→\nstdout", ha="center", fontsize=5.5,
            color=C_GRAY, zorder=4)

    save_fig(fig, "diagrama_4_componentes.png")


# ═══════════════════════════════════════════════════════════════
# 5. DIAGRAMA ENTIDAD-RELACIÓN (con rombos, óvalos, etc.)
# ═══════════════════════════════════════════════════════════════

def generate_er_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(20, 14))
    fig.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_xlim(-2, 20)
    ax.set_ylim(-1, 13.5)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.text(9, 13.1, "Diagrama Entidad-Relación — ms-auditoria", ha="center",
            fontsize=15, fontweight="bold", color=C_BLUE)
    ax.text(9, 12.7, "Notación Chen — Entidades, Atributos (óvalos), Relaciones (rombos)", ha="center",
            fontsize=9, color=C_GRAY)

    # ════════════════════════════════════════════════════
    # ENTIDAD: audit_logs
    # ════════════════════════════════════════════════════
    ent1_x, ent1_y = 4.5, 6.5
    ent1_w, ent1_h = 3.0, 1.0
    rect1 = FancyBboxPatch((ent1_x - ent1_w / 2, ent1_y - ent1_h / 2), ent1_w, ent1_h,
                             boxstyle="square,pad=0.05", fc=C_BLUE_LIGHT, ec=C_BLUE, lw=2.5, zorder=3)
    ax.add_patch(rect1)
    ax.text(ent1_x, ent1_y, "AUDIT_LOGS", ha="center", va="center",
            fontsize=12, fontweight="bold", color=C_BLUE, zorder=4)

    # Atributos de audit_logs (óvalos alrededor)
    audit_attrs = [
        # (cx, cy, name, is_pk)
        (0.5, 11.0, "id", True),
        (2.8, 11.5, "request_id", False),
        (5.2, 11.5, "servicio", False),
        (7.5, 11.2, "endpoint", False),
        (9.2, 10.5, "metodo", False),
        (0.0, 9.0, "codigo_respuesta", False),
        (2.5, 9.5, "duracion_ms", False),
        (0.0, 7.5, "usuario_id", False),
        (7.8, 8.8, "detalle", False),
        (8.5, 7.5, "ip_origen", False),
        (1.0, 4.5, "timestamp_evento", False),
        (4.5, 3.5, "created_at", False),
    ]

    for acx, acy, aname, is_pk in audit_attrs:
        fc = "#FFF9C4" if is_pk else C_WHITE
        ec = C_ORANGE if is_pk else C_BLUE
        draw_er_attribute(ax, acx, acy, aname, is_pk=is_pk, fc=fc, ec=ec)
        # Línea entidad → atributo
        ax.plot([ent1_x, acx], [ent1_y, acy], color=C_BLUE, lw=0.8, zorder=1)

    # ════════════════════════════════════════════════════
    # ENTIDAD: microservice_tokens
    # ════════════════════════════════════════════════════
    ent2_x, ent2_y = 15.5, 6.5
    ent2_w, ent2_h = 3.5, 1.0
    rect2 = FancyBboxPatch((ent2_x - ent2_w / 2, ent2_y - ent2_h / 2), ent2_w, ent2_h,
                             boxstyle="square,pad=0.05", fc=C_GREEN_LIGHT, ec=C_GREEN, lw=2.5, zorder=3)
    ax.add_patch(rect2)
    ax.text(ent2_x, ent2_y, "MICROSERVICE\nTOKENS", ha="center", va="center",
            fontsize=10, fontweight="bold", color=C_GREEN, zorder=4)

    # Atributos de microservice_tokens
    token_attrs = [
        (14.0, 11.0, "id", True),
        (16.5, 11.2, "nombre_ms", False),
        (18.5, 10.0, "token_hash", False),
        (19.0, 8.2, "activo", False),
        (18.0, 4.5, "created_at", False),
        (15.5, 3.5, "updated_at", False),
    ]

    for acx, acy, aname, is_pk in token_attrs:
        fc = "#FFF9C4" if is_pk else C_WHITE
        ec = C_ORANGE if is_pk else C_GREEN
        draw_er_attribute(ax, acx, acy, aname, is_pk=is_pk, fc=fc, ec=ec)
        ax.plot([ent2_x, acx], [ent2_y, acy], color=C_GREEN, lw=0.8, zorder=1)

    # ════════════════════════════════════════════════════
    # RELACIÓN (ROMBO): "genera"
    # ════════════════════════════════════════════════════
    rel_x = 10.0
    rel_y = 6.5
    draw_diamond(ax, rel_x, rel_y, 2.0, 1.2, "genera", fc="#FFF9C4", ec=C_RED)

    # Líneas entidad → rombo
    ax.plot([ent1_x + ent1_w / 2, rel_x - 1.0], [ent1_y, rel_y], color=C_RED, lw=2, zorder=2)
    ax.plot([ent2_x - ent2_w / 2, rel_x + 1.0], [ent2_y, rel_y], color=C_RED, lw=2, zorder=2)

    # Cardinalidades
    ax.text(7.0, 6.9, "N", fontsize=14, fontweight="bold", color=C_RED, ha="center", zorder=5)
    ax.text(7.0, 6.05, "(0..*)", fontsize=8, color=C_RED, ha="center")
    ax.text(12.8, 6.9, "1", fontsize=14, fontweight="bold", color=C_RED, ha="center", zorder=5)
    ax.text(12.8, 6.05, "(1..1)", fontsize=8, color=C_RED, ha="center")

    # ════════════════════════════════════════════════════
    # Nota explicativa
    # ════════════════════════════════════════════════════
    note_rect = FancyBboxPatch((5.5, 0.3), 9.0, 2.2, boxstyle="round,pad=0.1",
                                fc="#FFF9C4", ec="#F9A825", lw=1.5, zorder=3)
    ax.add_patch(note_rect)
    # Fold corner
    ax.plot([14.1, 14.5, 14.1], [2.5, 2.1, 2.1], color="#F9A825", lw=1.5, zorder=4)

    note_text = (
        "Nota: La relación «genera» es lógica, NO existe como Foreign Key en la BD.\n"
        "• Un microservice_token (identificado por nombre_microservicio) puede generar 0..* audit_logs\n"
        "• El campo audit_logs.servicio corresponde a microservice_tokens.nombre_microservicio\n"
        "• La validación se realiza en runtime mediante verify_api_key() (SHA-256)\n"
        "• Diseño intencional: los logs existen independientemente de los tokens (facilita purga masiva)"
    )
    ax.text(10, 1.4, note_text, ha="center", va="center", fontsize=6.5,
            color=C_BLACK, zorder=4, linespacing=1.6)

    # ════════════════════════════════════════════════════
    # Leyenda
    # ════════════════════════════════════════════════════
    legend_y = -0.3
    # Entidad
    r_leg = FancyBboxPatch((1, legend_y - 0.15), 1.2, 0.3, boxstyle="square,pad=0.02",
                            fc=C_BLUE_LIGHT, ec=C_BLUE, lw=1.5, zorder=3)
    ax.add_patch(r_leg)
    ax.text(2.5, legend_y, "= Entidad", fontsize=7, va="center", color=C_BLACK)

    # Atributo
    e_leg = Ellipse((5.5, legend_y), 1.0, 0.3, fc=C_WHITE, ec=C_BLACK, lw=1, zorder=3)
    ax.add_patch(e_leg)
    ax.text(6.3, legend_y, "= Atributo", fontsize=7, va="center", color=C_BLACK)

    # PK
    e_pk = Ellipse((9, legend_y), 0.6, 0.3, fc="#FFF9C4", ec=C_ORANGE, lw=1, zorder=3)
    ax.add_patch(e_pk)
    ax.text(9, legend_y, "PK", ha="center", fontsize=5, fontweight="bold", zorder=4)
    ax.plot([8.85, 9.15], [legend_y - 0.08, legend_y - 0.08], color=C_BLACK, lw=1, zorder=5)
    ax.text(9.5, legend_y, "= Clave Primaria (subrayado)", fontsize=7, va="center", color=C_BLACK)

    # Relación (rombo)
    draw_diamond(ax, 14, legend_y, 0.8, 0.4, "", fc="#FFF9C4", ec=C_RED)
    ax.text(14.7, legend_y, "= Relación", fontsize=7, va="center", color=C_BLACK)

    # Cardinalidad
    ax.text(16.5, legend_y, "N ↔ 1 = Cardinalidad", fontsize=7, va="center", color=C_RED, fontweight="bold")

    save_fig(fig, "diagrama_5_entidad_relacion.png")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("🎨 Generando imágenes de diagramas UML...")
    print(f"   Directorio: {OUTPUT_DIR}")
    print()
    
    print("1/5 Diagrama de Casos de Uso")
    generate_use_case_diagram()
    
    print("2/5 Diagrama de Clases UML")
    generate_class_diagram()
    
    print("3/5 Diagrama de Secuencia")
    generate_sequence_diagram()
    
    print("4/5 Diagrama de Componentes")
    generate_component_diagram()
    
    print("5/5 Diagrama Entidad-Relación")
    generate_er_diagram()
    
    print()
    print("═" * 50)
    print("✅ ¡5 imágenes generadas exitosamente!")
    print("   • diagrama_1_casos_de_uso.png")
    print("   • diagrama_2_clases_uml.png")
    print("   • diagrama_3_secuencia_crear_log.png")
    print("   • diagrama_4_componentes.png")
    print("   • diagrama_5_entidad_relacion.png")


if __name__ == "__main__":
    main()
