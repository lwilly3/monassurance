"""PostgreSQL: materialize server defaults

Revision ID: 20250809_0101
Revises: 20250809_0100
Create Date: 2025-08-09
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20250809_0101"
down_revision = "20250809_0100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Helper to run SQL safely
    def exec(sql: str) -> None:
        op.execute(sa.text(sql))

    # users
    exec("ALTER TABLE users ALTER COLUMN is_active SET DEFAULT TRUE;")
    exec("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'agent'::userrole;")
    exec("ALTER TABLE users ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;")

    # companies
    exec("ALTER TABLE companies ALTER COLUMN api_mode SET DEFAULT FALSE;")
    exec("ALTER TABLE companies ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;")

    # clients
    exec("ALTER TABLE clients ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;")

    # policies
    exec("ALTER TABLE policies ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;")
    exec("ALTER TABLE policies ALTER COLUMN status SET DEFAULT 'active';")
    exec("ALTER TABLE policies ALTER COLUMN currency SET DEFAULT 'XAF';")

    # integration_configs
    exec("ALTER TABLE integration_configs ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;")

    # templates
    exec("ALTER TABLE templates ALTER COLUMN is_active SET DEFAULT TRUE;")
    exec("ALTER TABLE templates ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;")

    # template_versions
    exec("ALTER TABLE template_versions ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;")

    # generated_documents
    exec("ALTER TABLE generated_documents ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;")

    # declaration_batches
    exec("ALTER TABLE declaration_batches ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;")

    # report_jobs
    exec("ALTER TABLE report_jobs ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;")

    # refresh_tokens
    exec("ALTER TABLE refresh_tokens ALTER COLUMN issued_at SET DEFAULT CURRENT_TIMESTAMP;")

    # audit_logs
    exec("ALTER TABLE audit_logs ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;")

    # attachments
    exec("ALTER TABLE attachments ALTER COLUMN uploaded_at SET DEFAULT CURRENT_TIMESTAMP;")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    def exec(sql: str) -> None:
        op.execute(sa.text(sql))

    # Drop defaults (revert to no default)
    exec("ALTER TABLE attachments ALTER COLUMN uploaded_at DROP DEFAULT;")
    exec("ALTER TABLE audit_logs ALTER COLUMN created_at DROP DEFAULT;")
    exec("ALTER TABLE refresh_tokens ALTER COLUMN issued_at DROP DEFAULT;")
    exec("ALTER TABLE report_jobs ALTER COLUMN created_at DROP DEFAULT;")
    exec("ALTER TABLE declaration_batches ALTER COLUMN created_at DROP DEFAULT;")
    exec("ALTER TABLE generated_documents ALTER COLUMN created_at DROP DEFAULT;")
    exec("ALTER TABLE template_versions ALTER COLUMN created_at DROP DEFAULT;")
    exec("ALTER TABLE templates ALTER COLUMN created_at DROP DEFAULT;")
    exec("ALTER TABLE templates ALTER COLUMN is_active DROP DEFAULT;")
    exec("ALTER TABLE integration_configs ALTER COLUMN updated_at DROP DEFAULT;")
    exec("ALTER TABLE policies ALTER COLUMN currency DROP DEFAULT;")
    exec("ALTER TABLE policies ALTER COLUMN status DROP DEFAULT;")
    exec("ALTER TABLE policies ALTER COLUMN created_at DROP DEFAULT;")
    exec("ALTER TABLE clients ALTER COLUMN created_at DROP DEFAULT;")
    exec("ALTER TABLE companies ALTER COLUMN created_at DROP DEFAULT;")
    exec("ALTER TABLE companies ALTER COLUMN api_mode DROP DEFAULT;")
    exec("ALTER TABLE users ALTER COLUMN created_at DROP DEFAULT;")
    exec("ALTER TABLE users ALTER COLUMN role DROP DEFAULT;")
    exec("ALTER TABLE users ALTER COLUMN is_active DROP DEFAULT;")
