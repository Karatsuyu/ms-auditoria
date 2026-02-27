# =============================================================================
# ms-auditoria | database/base.py
# =============================================================================
# Declaración de la clase Base de SQLAlchemy para todos los modelos ORM.
# Todos los modelos heredan de esta clase.
# =============================================================================

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM del microservicio."""
    pass
