# =============================================================================
# ms-auditoria | services/statistics_service.py
# =============================================================================
# Servicio ASYNC de estadísticas y métricas de auditoría.
# Proporciona resúmenes, promedios y tasas de error para dashboards.
# =============================================================================

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_repository import AuditRepository
from app.utils.logger import logger


class StatisticsService:
    """Servicio async de estadísticas de auditoría."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = AuditRepository(db)

    async def get_general_stats(self) -> dict:
        """
        Retorna estadísticas generales del sistema de auditoría:
        - Total de registros
        - Logs por microservicio
        - Logs por código de respuesta
        - Duración promedio por microservicio
        - Tasa de errores por microservicio
        """
        total = await self.repo.count_total()

        logs_por_servicio = [
            {"servicio": row[0], "total": row[1]}
            for row in await self.repo.count_by_servicio()
        ]

        logs_por_codigo = [
            {"codigo_respuesta": row[0], "total": row[1]}
            for row in await self.repo.count_by_codigo_respuesta()
        ]

        duracion_promedio = [
            {
                "servicio": row[0],
                "avg_duration_ms": round(float(row[1]), 2) if row[1] else 0,
                "total_requests": row[2],
            }
            for row in await self.repo.average_duration_by_servicio()
        ]

        tasa_errores = []
        for row in await self.repo.error_rate_by_servicio():
            total_ms = row[1]
            errors = row[2] or 0
            tasa_errores.append({
                "servicio": row[0],
                "total": total_ms,
                "errors": errors,
                "error_rate": round((errors / total_ms) * 100, 2) if total_ms > 0 else 0,
            })

        logger.info("statistics_generated", extra={"total_records": total})

        return {
            "total_registros": total,
            "logs_por_servicio": logs_por_servicio,
            "logs_por_codigo_respuesta": logs_por_codigo,
            "duracion_promedio_por_servicio": duracion_promedio,
            "tasa_errores_por_servicio": tasa_errores,
        }
