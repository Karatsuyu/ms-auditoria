# =============================================================================
# ms-auditoria | models/microservice_token.py
# =============================================================================
# Modelo ORM para tokens de autenticación inter-microservicios.
# Cada microservicio autorizado tiene un token registrado para enviar logs.
# =============================================================================

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, TIMESTAMP

from app.database.base import Base
from app.models.audit_log import GUID


class MicroserviceToken(Base):
    """
    Token de autenticación para microservicios.
    Solo microservicios registrados pueden enviar eventos de auditoría.
    """

    __tablename__ = "microservice_tokens"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    nombre_microservicio = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Nombre del microservicio (ej: ms-matricula, ms-finanzas)",
    )
    token_hash = Column(
        String(256),
        nullable=False,
        comment="Hash del token de autenticación del microservicio",
    )
    activo = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Indica si el microservicio está autorizado para enviar logs",
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<MicroserviceToken(nombre='{self.nombre_microservicio}', activo={self.activo})>"
