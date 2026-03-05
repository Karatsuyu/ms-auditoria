# =============================================================================
# ms-auditoria | models/retention_config.py
# =============================================================================
# Modelo ORM para la tabla: aud_configuracion_retencion.
# Almacena los parámetros de rotación automática de registros de log.
# Opera como singleton (un único registro activo).
# =============================================================================

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, BigInteger, TIMESTAMP, CheckConstraint

from app.database.base import Base


class RetentionConfig(Base):
    """
    Configuración de retención de logs.
    Define cuántos días se conservan los registros antes de ser eliminados.
    """

    __tablename__ = "aud_configuracion_retencion"

    # ── Columnas ───────────────────────────────────────────────────────────
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Identificador interno",
    )
    dias_retencion = Column(
        Integer,
        nullable=False,
        default=30,
        comment="Cantidad de días que se conservan los registros de log antes de ser eliminados",
    )
    estado = Column(
        String(20),
        nullable=False,
        default="activo",
        comment="Estado de la configuración: activo | inactivo",
    )
    ultima_rotacion = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        default=None,
        comment="Fecha y hora de la última ejecución de rotación",
    )
    registros_eliminados_ultima = Column(
        BigInteger,
        nullable=True,
        default=0,
        comment="Cantidad de registros eliminados en la última ejecución de rotación",
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Fecha/hora de creación del registro",
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Fecha/hora de última modificación",
    )

    # ── Restricciones ──────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint("dias_retencion > 0", name="chk_aud_config_dias"),
        CheckConstraint("estado IN ('activo', 'inactivo')", name="chk_aud_config_estado"),
        CheckConstraint("registros_eliminados_ultima >= 0", name="chk_aud_config_registros"),
    )

    def __repr__(self) -> str:
        return (
            f"<RetentionConfig(id={self.id}, dias={self.dias_retencion}, "
            f"estado='{self.estado}')>"
        )
