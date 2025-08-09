"""Add trigram indexes for faster LIKE/ILIKE searches (PostgreSQL only)

Revision ID: 20250809_0008
Revises: 20250809_0007
Create Date: 2025-08-09
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20250809_0008"
down_revision = "20250809_0007"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return
    # Ensure pg_trgm is available (idempotent)
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

    # Trigram indexes for ILIKE/contains searches
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_clients_email_trgm ON clients USING GIN (email gin_trgm_ops)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_clients_phone_trgm ON clients USING GIN (phone gin_trgm_ops)"
        )
    )


def downgrade() -> None:
    if not _is_postgres():
        return
    op.execute(sa.text("DROP INDEX IF EXISTS ix_clients_email_trgm"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_clients_phone_trgm"))
