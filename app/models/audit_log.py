# =============================================================================
# ms-auditoria | models/audit_log.py
# =============================================================================
# Modelo ORM para la tabla principal: aud_eventos_log.
# Almacena cada evento de auditoría recibido de los 18+ microservicios.
# Nombres de columnas alineados con el DDL del modelo de datos oficial.
# =============================================================================

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Integer,
    Text,
    TIMESTAMP,
    Index,
    CheckConstraint,
    text,
)

from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.database.base import Base


class GUID(TypeDecorator):
    """UUID portable.

    Compatibilidad retroactiva: algunas migraciones Alembic antiguas importan
    `GUID` desde este módulo.
    """

    cache_ok = True
    impl = CHAR

    def __init__(self, length: int = 36, **kwargs):
        super().__init__(**kwargs)
        self.length = length

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(self.length))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class AuditLog(Base):
    """
    Registro de auditoría (aud_eventos_log).
    Cada fila representa un evento auditado de cualquier microservicio del ERP,
    incluyendo las operaciones propias de ms-auditoria (auto-auditoría).
    """

    __tablename__ = "aud_eventos_log"

    # ── Columnas ───────────────────────────────────────────────────────────
    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        comment="Identificador interno autoincremental del registro de log",
    )
    request_id = Column(
        String(36),
        nullable=False,
        comment="Identificador de rastreo de la petición (Request ID)",
    )
    fecha_hora = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="Fecha y hora exacta en que se ejecutó la operación en el ms origen",
    )
    microservicio = Column(
        String(50),
        nullable=False,
        comment="Nombre del microservicio que generó el log",
    )
    funcionalidad = Column(
        String(100),
        nullable=False,
        comment="Nombre de la funcionalidad o endpoint ejecutado",
    )
    metodo = Column(
        String(10),
        nullable=False,
        comment="Método HTTP (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)",
    )
    codigo_respuesta = Column(
        Integer,
        nullable=False,
        comment="Código de respuesta HTTP",
    )
    duracion_ms = Column(
        Integer,
        nullable=False,
        comment="Duración de la operación en milisegundos",
    )
    usuario_id = Column(
        String(36),
        nullable=True,
        comment="Ref. externa — ms-usuarios. ID del usuario. NULL para operaciones de sistema",
    )
    detalle = Column(
        Text,
        nullable=True,
        comment="Descripción libre del contexto o resultado de la operación",
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Fecha/hora de inserción del registro",
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Fecha/hora de última modificación del registro",
    )

    # ── Índices y Restricciones ────────────────────────────────────────────
    __table_args__ = (
        Index("idx_aud_eventos_request_id", "request_id"),
        Index("idx_aud_eventos_microservicio", "microservicio"),
        Index("idx_aud_eventos_fecha_hora", "fecha_hora"),
        Index("idx_aud_eventos_microservicio_fecha", "microservicio", "fecha_hora"),
        Index("idx_aud_eventos_codigo_respuesta", "codigo_respuesta"),
        Index(
            "idx_aud_eventos_usuario_id",
            "usuario_id",
            postgresql_where=text("usuario_id IS NOT NULL"),
        ),
        CheckConstraint(
            "metodo IN ('GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS')",
            name="chk_aud_eventos_metodo",
        ),
        CheckConstraint(
            "codigo_respuesta BETWEEN 100 AND 599",
            name="chk_aud_eventos_codigo",
        ),
        CheckConstraint("duracion_ms >= 0", name="chk_aud_eventos_duracion"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, microservicio='{self.microservicio}', "
            f"funcionalidad='{self.funcionalidad}', metodo='{self.metodo}', "
            f"codigo={self.codigo_respuesta})>"
        )
