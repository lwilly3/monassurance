"""Enable PG extensions and add helpful indexes (PostgreSQL only)

Revision ID: 20250809_0006
Revises: 20250809_0005
Create Date: 2025-08-09
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20250809_0006"
down_revision = "20250809_0005"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return
    # Enable useful extensions
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS citext"))

    # Indexes for frequent FKs/filters
    idx_specs = [
        ("ix_policies_client_id", "policies", ["client_id"], False),
        ("ix_policies_company_id", "policies", ["company_id"], False),
        ("ix_generated_documents_policy_id", "generated_documents", ["policy_id"], False),
        ("ix_template_versions_template_id", "template_versions", ["template_id"], False),
        ("ix_audit_logs_user_id", "audit_logs", ["user_id"], False),
    ]
    for name, table, cols, unique in idx_specs:
        op.create_index(name, table, cols, unique=unique, if_not_exists=True)

    # Example partial index: only ready documents by created_at for fast listing
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_generated_documents_ready_created_at ON generated_documents (created_at) WHERE status = 'ready'"
        )
    )


def downgrade() -> None:
    if not _is_postgres():
        return
    # Drop created indexes (extensions kept)
    for name in [
        "ix_policies_client_id",
        "ix_policies_company_id",
        "ix_generated_documents_policy_id",
        "ix_template_versions_template_id",
        "ix_audit_logs_user_id",
        "ix_generated_documents_ready_created_at",
    ]:
        op.execute(sa.text(f"DROP INDEX IF EXISTS {name}"))
