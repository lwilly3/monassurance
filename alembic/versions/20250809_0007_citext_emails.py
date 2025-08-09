"""Convert email columns to CITEXT (PostgreSQL) and tidy indexes

Revision ID: 20250809_0007
Revises: 20250809_0006
Create Date: 2025-08-09
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20250809_0007"
down_revision = "20250809_0006"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return
    # Ensure extension exists (idempotent)
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS citext"))

    # Convert columns to CITEXT
    op.execute(sa.text("ALTER TABLE users ALTER COLUMN email TYPE CITEXT"))
    op.execute(sa.text("ALTER TABLE clients ALTER COLUMN email TYPE CITEXT"))

    # Drop redundant non-unique email index on users (unique constraint already indexes the column)
    op.execute(sa.text("DROP INDEX IF EXISTS ix_users_email"))


def downgrade() -> None:
    if not _is_postgres():
        return
    # Revert to VARCHAR(255)
    op.execute(sa.text("ALTER TABLE users ALTER COLUMN email TYPE VARCHAR(255)"))
    op.execute(sa.text("ALTER TABLE clients ALTER COLUMN email TYPE VARCHAR(255)"))
    # Re-create non-unique index as it existed originally
    op.create_index("ix_users_email", "users", ["email"], unique=False, if_not_exists=True)
