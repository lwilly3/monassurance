"""Convert JSON to JSONB and add GIN indexes (PostgreSQL only)

Revision ID: 20250809_0005
Revises: 20250808_0004
Create Date: 2025-08-09
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20250809_0005"
down_revision = "20250808_0004"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        # No-op for SQLite and other dialects
        return

    # Ensure JSON columns are JSONB in PG and add GIN indexes for query performance.

    # Convert column types to JSONB explicitly (in case older PG used JSON)
    conversions = [
        ("integration_configs", "extra"),
        ("generated_documents", "doc_metadata"),
        ("declaration_items", "data"),
        ("report_jobs", "params"),
        ("audit_logs", "audit_metadata"),
    ]

    for table, column in conversions:
        op.execute(
            sa.text(
                f"ALTER TABLE {table} ALTER COLUMN {column} TYPE JSONB USING {column}::jsonb"
            )
        )

    # Add GIN indexes (skip if they already exist)
    gin_indexes = {
        "ix_integration_configs_extra_gin": ("integration_configs", "extra"),
        "ix_generated_documents_meta_gin": ("generated_documents", "doc_metadata"),
        "ix_declaration_items_data_gin": ("declaration_items", "data"),
        "ix_report_jobs_params_gin": ("report_jobs", "params"),
        "ix_audit_logs_meta_gin": ("audit_logs", "audit_metadata"),
    }

    for idx_name, (table, column) in gin_indexes.items():
        op.execute(
            sa.text(
                f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} USING GIN ({column})"
            )
        )


def downgrade() -> None:
    if not _is_postgres():
        return
    # Drop GIN indexes only (keep JSONB type; reverting to JSON provides no benefit)
    idx_names = [
        "ix_integration_configs_extra_gin",
        "ix_generated_documents_meta_gin",
        "ix_declaration_items_data_gin",
        "ix_report_jobs_params_gin",
        "ix_audit_logs_meta_gin",
    ]
    for idx in idx_names:
        op.execute(sa.text(f"DROP INDEX IF EXISTS {idx}"))
