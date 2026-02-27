# =============================================================================
# ms-auditoria | models/audit_log.py
# =============================================================================
# Modelo ORM para la tabla principal: audit_logs.
# Almacena cada evento de auditoría recibido de los 18 microservicios.
# =============================================================================

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Index
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.database.base import Base


class GUID(TypeDecorator):
    """
    Tipo UUID compatible con PostgreSQL y SQLite.
    En PostgreSQL usa UUID nativo, en SQLite almacena como CHAR(36).
    """
    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return str(value) if dialect.name != "postgresql" else value
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and not isinstance(value, uuid.UUID):
            return uuid.UUID(str(value))
        return value


class AuditLog(Base):
    """
    Registro de auditoría.
    Cada fila representa un evento auditado de cualquier microservicio del ERP.
    """

    __tablename__ = "audit_logs"

    # ── Columnas ───────────────────────────────────────────────────────────
    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        comment="Identificador único del registro de auditoría",
    )
    request_id = Column(
        String(50),
        index=True,
        nullable=False,
        comment="ID de trazabilidad de la petición (X-Request-ID)",
    )
    servicio = Column(
        String(50),
        index=True,
        nullable=False,
        comment="Nombre del microservicio que genera el evento",
    )
    endpoint = Column(
        String(200),
        nullable=False,
        comment="Ruta del endpoint invocado",
    )
    metodo = Column(
        String(10),
        nullable=False,
        comment="Método HTTP (GET, POST, PUT, DELETE, PATCH)",
    )
    codigo_respuesta = Column(
        Integer,
        index=True,
        comment="Código de respuesta HTTP",
    )
    duracion_ms = Column(
        Integer,
        comment="Duración del request en milisegundos",
    )
    usuario_id = Column(
        GUID(),
        nullable=True,
        index=True,
        comment="UUID del usuario que realizó la acción (puede ser null si es anónimo)",
    )
    detalle = Column(
        Text,
        nullable=True,
        comment="Detalle adicional del evento (JSON stringificado, cifrado si es sensible)",
    )
    ip_origen = Column(
        String(45),
        nullable=True,
        comment="Dirección IP de origen del request",
    )
    timestamp_evento = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="Momento exacto en que ocurrió el evento en el microservicio origen",
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Momento en que se registró en ms-auditoria",
    )

    # ── Índices compuestos para consultas frecuentes ───────────────────────
    __table_args__ = (
        Index("ix_audit_servicio_timestamp", "servicio", "timestamp_evento"),
        Index("ix_audit_usuario_timestamp", "usuario_id", "timestamp_evento"),
        Index("ix_audit_codigo_servicio", "codigo_respuesta", "servicio"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, servicio='{self.servicio}', "
            f"endpoint='{self.endpoint}', metodo='{self.metodo}', "
            f"codigo={self.codigo_respuesta})>"
        )
