# =============================================================================
# ms-auditoria | models/service_statistics.py
# =============================================================================
# Modelo ORM para la tabla: aud_estadisticas_servicio.
# Almacena métricas precalculadas por microservicio y periodo.
# =============================================================================

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Date,
    Numeric,
    TIMESTAMP,
    UniqueConstraint,
    CheckConstraint,
)

from app.database.base import Base


class ServiceStatistics(Base):
    """
    Estadísticas de uso precalculadas por microservicio y periodo.
    Evita agregar la tabla aud_eventos_log en tiempo real para consultas analíticas.
    """

    __tablename__ = "aud_estadisticas_servicio"

    # ── Columnas ───────────────────────────────────────────────────────────
    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        comment="Identificador interno autoincremental",
    )
    microservicio = Column(
        String(50),
        nullable=False,
        comment="Nombre del microservicio al que corresponde la estadística",
    )
    periodo = Column(
        String(10),
        nullable=False,
        comment="Periodo de agrupación: diario | semanal | mensual",
    )
    fecha = Column(
        Date,
        nullable=False,
        comment="Fecha de inicio del periodo estadístico",
    )
    total_peticiones = Column(
        BigInteger,
        nullable=False,
        default=0,
        comment="Total de peticiones registradas en el periodo",
    )
    total_errores = Column(
        BigInteger,
        nullable=False,
        default=0,
        comment="Total de respuestas con código de error (>= 400) en el periodo",
    )
    tiempo_promedio_ms = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,
        comment="Tiempo promedio de respuesta en milisegundos durante el periodo",
    )
    funcionalidad_top = Column(
        String(100),
        nullable=True,
        comment="Nombre de la funcionalidad más utilizada en el periodo",
    )
    fecha_calculo = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="Fecha y hora en que se calculó y almacenó esta estadística",
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
        comment="Fecha/hora de última modificación",
    )

    # ── Restricciones ──────────────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint(
            "microservicio", "periodo", "fecha",
            name="uq_aud_estad_ms_periodo_fecha",
        ),
        CheckConstraint(
            "periodo IN ('diario', 'semanal', 'mensual')",
            name="chk_aud_estad_periodo",
        ),
        CheckConstraint("total_peticiones >= 0", name="chk_aud_estad_peticiones"),
        CheckConstraint("total_errores >= 0", name="chk_aud_estad_errores"),
        CheckConstraint("total_errores <= total_peticiones", name="chk_aud_estad_errores_max"),
        CheckConstraint("tiempo_promedio_ms >= 0", name="chk_aud_estad_tiempo"),
    )

    def __repr__(self) -> str:
        return (
            f"<ServiceStatistics(microservicio='{self.microservicio}', "
            f"periodo='{self.periodo}', fecha='{self.fecha}')>"
        )
