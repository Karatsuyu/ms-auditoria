# =============================================================================
# ms-auditoria | repositories/retention_repository.py
# =============================================================================
# Capa de acceso a datos para la tabla aud_configuracion_retencion.
# =============================================================================

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.retention_config import RetentionConfig


class RetentionRepository:
    """Repositorio async para aud_configuracion_retencion."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active(self) -> Optional[RetentionConfig]:
        """Obtiene la configuración activa (singleton)."""
        stmt = (
            select(RetentionConfig)
            .where(RetentionConfig.estado == "activo")
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, config: RetentionConfig) -> RetentionConfig:
        """Actualiza un registro de configuración ya en sesión."""
        await self.session.flush()
        await self.session.refresh(config)
        return config
