"""Add trigram index on companies.name (PostgreSQL only)

Revision ID: 20250809_0009
Revises: 20250809_0008
Create Date: 2025-08-09
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20250809_0009"
down_revision = "20250809_0008"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_companies_name_trgm ON companies USING GIN (name gin_trgm_ops)"
        )
    )


def downgrade() -> None:
    if not _is_postgres():
        return
    op.execute(sa.text("DROP INDEX IF EXISTS ix_companies_name_trgm"))
