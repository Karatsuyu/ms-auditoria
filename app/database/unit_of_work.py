# =============================================================================
# ms-auditoria | database/unit_of_work.py
# =============================================================================
# Patrón Unit of Work para transacciones atómicas.
#
# Garantiza que todas las operaciones de una transacción se confirman o
# revierten juntas. Cada "unidad de trabajo" encapsula una sesión async.
#
# Uso:
#   async with UnitOfWork() as uow:
#       uow.session.add(entity)
#       await uow.commit()
# =============================================================================

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal


class UnitOfWork:
    """
    Patrón Unit of Work para gestión transaccional.

    - Abre una AsyncSession al entrar en el context manager.
    - commit() confirma la transacción.
    - rollback() revierte la transacción.
    - Al salir, si hay excepción, revierte automáticamente y cierra.
    """

    def __init__(self) -> None:
        self._session_factory = AsyncSessionLocal
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()
        if self.session:
            await self.session.close()

    async def commit(self) -> None:
        """Confirma todos los cambios de la transacción actual."""
        if self.session:
            await self.session.commit()

    async def rollback(self) -> None:
        """Revierte todos los cambios de la transacción actual."""
        if self.session:
            await self.session.rollback()
