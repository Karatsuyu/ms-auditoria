"""v2_full_schema_redesign

Complete schema redesign per modelo-datos-ms-auditoria.md spec.
Drops old audit_logs table, creates 3 new tables:
  - aud_eventos_log (replaces audit_logs)
  - aud_configuracion_retencion (new)
  - aud_estadisticas_servicio (new)
Preserves microservice_tokens (updated PK to UUID native).

Revision ID: c3d4e5f6a7b8
Revises: b2a3c4d5e6f7
Create Date: 2026-03-01T00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2a3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Drop old audit_logs table and its indexes ───────────────────────
    op.execute("DROP INDEX IF EXISTS ix_audit_detalle_fulltext")
    op.execute("DROP INDEX IF EXISTS ix_audit_usuario_timestamp")
    op.execute("DROP INDEX IF EXISTS ix_audit_servicio_timestamp")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_usuario_id")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_servicio")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_request_id")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_codigo_respuesta")
    op.execute("DROP INDEX IF EXISTS ix_audit_codigo_servicio")
    op.drop_table("audit_logs")

    # ── 2. Create aud_configuracion_retencion ──────────────────────────────
    op.create_table(
        "aud_configuracion_retencion",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "dias_retencion",
            sa.Integer(),
            nullable=False,
            server_default="30",
            comment="Cantidad de días que se conservan los registros de log",
        ),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="activo",
            comment="Estado: activo | inactivo",
        ),
        sa.Column(
            "ultima_rotacion",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="Fecha/hora de la última rotación ejecutada",
        ),
        sa.Column(
            "registros_eliminados_ultima",
            sa.BigInteger(),
            nullable=True,
            server_default="0",
            comment="Registros eliminados en la última rotación",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_aud_configuracion_retencion"),
        sa.CheckConstraint("dias_retencion > 0", name="chk_aud_config_dias"),
        sa.CheckConstraint(
            "estado IN ('activo', 'inactivo')", name="chk_aud_config_estado"
        ),
        sa.CheckConstraint(
            "registros_eliminados_ultima >= 0", name="chk_aud_config_registros"
        ),
        comment="Parámetros de rotación automática de registros de log. Singleton.",
    )

    op.create_index(
        "idx_aud_config_estado",
        "aud_configuracion_retencion",
        ["estado"],
    )

    # ── 3. Create aud_eventos_log ──────────────────────────────────────────
    op.create_table(
        "aud_eventos_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "request_id",
            sa.String(36),
            nullable=False,
            comment="Identificador de rastreo de la petición (Request ID)",
        ),
        sa.Column(
            "fecha_hora",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            comment="Fecha y hora exacta del evento en el ms origen",
        ),
        sa.Column(
            "microservicio",
            sa.String(50),
            nullable=False,
            comment="Nombre del microservicio que generó el log",
        ),
        sa.Column(
            "funcionalidad",
            sa.String(100),
            nullable=False,
            comment="Nombre de la funcionalidad o endpoint ejecutado",
        ),
        sa.Column(
            "metodo",
            sa.String(10),
            nullable=False,
            comment="Método HTTP utilizado",
        ),
        sa.Column(
            "codigo_respuesta",
            sa.Integer(),
            nullable=False,
            comment="Código de respuesta HTTP",
        ),
        sa.Column(
            "duracion_ms",
            sa.Integer(),
            nullable=False,
            comment="Duración de la operación en milisegundos",
        ),
        sa.Column(
            "usuario_id",
            sa.String(36),
            nullable=True,
            comment="Ref. externa — ms-usuarios. NULL para ops de sistema",
        ),
        sa.Column(
            "detalle",
            sa.Text(),
            nullable=True,
            comment="Descripción libre del contexto o resultado",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_aud_eventos_log"),
        sa.CheckConstraint(
            "metodo IN ('GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS')",
            name="chk_aud_eventos_metodo",
        ),
        sa.CheckConstraint(
            "codigo_respuesta BETWEEN 100 AND 599",
            name="chk_aud_eventos_codigo",
        ),
        sa.CheckConstraint("duracion_ms >= 0", name="chk_aud_eventos_duracion"),
        comment="Registro central de operaciones (logs) de todos los microservicios.",
    )

    # Indexes per spec section 5
    op.create_index(
        "idx_aud_eventos_request_id", "aud_eventos_log", ["request_id"]
    )
    op.create_index(
        "idx_aud_eventos_microservicio", "aud_eventos_log", ["microservicio"]
    )
    op.create_index(
        "idx_aud_eventos_fecha_hora", "aud_eventos_log", ["fecha_hora"]
    )
    op.create_index(
        "idx_aud_eventos_microservicio_fecha",
        "aud_eventos_log",
        ["microservicio", "fecha_hora"],
    )
    op.create_index(
        "idx_aud_eventos_codigo_respuesta",
        "aud_eventos_log",
        ["codigo_respuesta"],
    )
    # Partial index for usuario_id WHERE NOT NULL
    op.execute(
        "CREATE INDEX idx_aud_eventos_usuario_id "
        "ON aud_eventos_log (usuario_id) "
        "WHERE usuario_id IS NOT NULL"
    )

    # ── 4. Create aud_estadisticas_servicio ────────────────────────────────
    op.create_table(
        "aud_estadisticas_servicio",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("microservicio", sa.String(50), nullable=False),
        sa.Column("periodo", sa.String(10), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column(
            "total_peticiones",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_errores",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "tiempo_promedio_ms",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("funcionalidad_top", sa.String(100), nullable=True),
        sa.Column(
            "fecha_calculo",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_aud_estadisticas_servicio"),
        sa.UniqueConstraint(
            "microservicio",
            "periodo",
            "fecha",
            name="uq_aud_estad_ms_periodo_fecha",
        ),
        sa.CheckConstraint(
            "periodo IN ('diario', 'semanal', 'mensual')",
            name="chk_aud_estad_periodo",
        ),
        sa.CheckConstraint("total_peticiones >= 0", name="chk_aud_estad_peticiones"),
        sa.CheckConstraint("total_errores >= 0", name="chk_aud_estad_errores"),
        sa.CheckConstraint(
            "total_errores <= total_peticiones",
            name="chk_aud_estad_errores_max",
        ),
        sa.CheckConstraint("tiempo_promedio_ms >= 0", name="chk_aud_estad_tiempo"),
        comment="Estadísticas de uso precalculadas por microservicio y periodo.",
    )

    op.create_index(
        "idx_aud_estadisticas_ms_periodo_fecha",
        "aud_estadisticas_servicio",
        ["microservicio", "periodo", "fecha"],
    )


def downgrade() -> None:
    # Drop new tables
    op.drop_index(
        "idx_aud_estadisticas_ms_periodo_fecha",
        table_name="aud_estadisticas_servicio",
    )
    op.drop_table("aud_estadisticas_servicio")

    op.execute("DROP INDEX IF EXISTS idx_aud_eventos_usuario_id")
    op.drop_index(
        "idx_aud_eventos_codigo_respuesta", table_name="aud_eventos_log"
    )
    op.drop_index(
        "idx_aud_eventos_microservicio_fecha", table_name="aud_eventos_log"
    )
    op.drop_index("idx_aud_eventos_fecha_hora", table_name="aud_eventos_log")
    op.drop_index("idx_aud_eventos_microservicio", table_name="aud_eventos_log")
    op.drop_index("idx_aud_eventos_request_id", table_name="aud_eventos_log")
    op.drop_table("aud_eventos_log")

    op.drop_index(
        "idx_aud_config_estado", table_name="aud_configuracion_retencion"
    )
    op.drop_table("aud_configuracion_retencion")

    # Recreate old audit_logs table (from original migration)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("request_id", sa.String(50), nullable=False),
        sa.Column("servicio", sa.String(50), nullable=False),
        sa.Column("endpoint", sa.String(200), nullable=False),
        sa.Column("metodo", sa.String(10), nullable=False),
        sa.Column("codigo_respuesta", sa.Integer(), nullable=True),
        sa.Column("duracion_ms", sa.Integer(), nullable=True),
        sa.Column("usuario_id", sa.String(36), nullable=True),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.Column("ip_origen", sa.String(45), nullable=True),
        sa.Column(
            "timestamp_evento",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])
    op.create_index("ix_audit_logs_servicio", "audit_logs", ["servicio"])
    op.create_index(
        "ix_audit_logs_codigo_respuesta", "audit_logs", ["codigo_respuesta"]
    )
    op.create_index("ix_audit_logs_usuario_id", "audit_logs", ["usuario_id"])
    op.create_index(
        "ix_audit_servicio_timestamp",
        "audit_logs",
        ["servicio", "timestamp_evento"],
    )
    op.create_index(
        "ix_audit_usuario_timestamp",
        "audit_logs",
        ["usuario_id", "timestamp_evento"],
    )
    op.create_index(
        "ix_audit_codigo_servicio",
        "audit_logs",
        ["codigo_respuesta", "servicio"],
    )
