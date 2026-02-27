"""add_gin_index_detalle_fulltext

Revision ID: b2a3c4d5e6f7
Revises: fae4016df4b8
Create Date: 2026-02-27T01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b2a3c4d5e6f7'
down_revision: Union[str, None] = 'fae4016df4b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear índice GIN para búsqueda full-text en el campo detalle
    # Usa to_tsvector con configuración 'spanish' para tokenización en español
    op.execute(
        "CREATE INDEX ix_audit_detalle_fulltext "
        "ON audit_logs "
        "USING GIN (to_tsvector('spanish', COALESCE(detalle, '')))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_audit_detalle_fulltext")
