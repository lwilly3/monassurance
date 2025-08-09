"""Initial schema (squashed from previous migrations)

Revision ID: 20250809_0100
Revises: 
Create Date: 2025-08-09
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20250809_0100"
down_revision = None
branch_labels = None
depends_on = None

# Cette migration remplace l'historique précédent (squash)
replaces = (
    "20250808_0001",
    "20250808_0002",
    "20250808_0003",
    "20250808_0004",
    "20250809_0005",
    "20250809_0006",
    "20250809_0007",
    "20250809_0008",
    "20250809_0009",
    "20250809_0010",
)


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # userrole enum (PostgreSQL) or VARCHAR fallback for other dialects
    role_type: sa.types.TypeEngine
    if dialect == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                    CREATE TYPE userrole AS ENUM ('admin', 'agent', 'manager');
                END IF;
            END$$;
            """
        )
        role_type = sa.Enum("admin", "agent", "manager", name="userrole")
    else:
        role_type = sa.String(length=50)

    # boolean defaults by dialect (PostgreSQL vs SQLite/others)
    BOOL_TRUE = sa.text("TRUE") if dialect == "postgresql" else sa.text("1")
    BOOL_FALSE = sa.text("FALSE") if dialect == "postgresql" else sa.text("0")

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=255)),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", role_type, nullable=False, server_default=sa.text("'agent'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=BOOL_TRUE),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # companies
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("api_mode", sa.Boolean(), nullable=False, server_default=BOOL_FALSE),
        sa.Column("api_endpoint", sa.String(length=500)),
        sa.Column("api_key", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # clients
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255)),
        sa.Column("phone", sa.String(length=50)),
        sa.Column("address", sa.Text()),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_clients_email", "clients", ["email"])
    op.create_index("ix_clients_phone", "clients", ["phone"])

    # policies
    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("policy_number", sa.String(length=100), unique=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL")),
        sa.Column("product_name", sa.String(length=255)),
        sa.Column("premium_amount", sa.Integer()),
        sa.Column("effective_date", sa.DateTime(timezone=True)),
        sa.Column("expiry_date", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("status", sa.String(length=30), server_default=sa.text("'active'")),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'XAF'")),
    )
    op.create_index("ix_policies_policy_number", "policies", ["policy_number"])

    # integration_configs
    op.create_table(
        "integration_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("mode", sa.String(length=20)),
        sa.Column("api_base_url", sa.String(length=500)),
        sa.Column("api_auth_type", sa.String(length=30)),
        sa.Column("api_key", sa.String(length=255)),
        sa.Column("api_secret", sa.Text()),
        sa.Column("report_format", sa.String(length=20)),
        sa.Column("callback_url", sa.String(length=500)),
        sa.Column("extra", sa.JSON()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # templates
    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=30)),
        sa.Column("format", sa.String(length=20)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=BOOL_TRUE),
        sa.Column("scope", sa.String(length=20)),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("uq_template_name_type_scope", "templates", ["name", "type", "scope"], unique=True)

    # template_versions
    op.create_table(
        "template_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("storage_backend", sa.String(length=20)),
        sa.Column("content", sa.Text()),
        sa.Column("file_path", sa.String(length=500)),
        sa.Column("checksum", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("uq_template_version", "template_versions", ["template_id", "version"], unique=True)

    # template_companies association
    op.create_table(
        "template_companies",
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("templates.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True),
    )

    # generated_documents
    op.create_table(
        "generated_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_type", sa.String(length=30)),
        sa.Column("policy_id", sa.Integer(), sa.ForeignKey("policies.id", ondelete="SET NULL")),
        sa.Column("template_version_id", sa.Integer(), sa.ForeignKey("template_versions.id", ondelete="SET NULL")),
        sa.Column("file_path", sa.String(length=500)),
        sa.Column("mime_type", sa.String(length=100)),
        sa.Column("size_bytes", sa.BigInteger()),
        sa.Column("status", sa.String(length=20)),
        sa.Column("doc_metadata", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # declaration_batches
    op.create_table(
        "declaration_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL")),
        sa.Column("period_start", sa.DateTime(timezone=True)),
        sa.Column("period_end", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=20)),
        sa.Column("report_document_id", sa.Integer(), sa.ForeignKey("generated_documents.id", ondelete="SET NULL")),
        sa.Column("generated_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # declaration_items
    op.create_table(
        "declaration_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("declaration_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_id", sa.Integer(), sa.ForeignKey("policies.id", ondelete="SET NULL")),
        sa.Column("premium_amount", sa.Integer()),
        sa.Column("commission_amount", sa.Integer()),
        sa.Column("data", sa.JSON()),
    )

    # report_jobs
    op.create_table(
        "report_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_type", sa.String(length=30)),
        sa.Column("scheduled_for", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=20)),
        sa.Column("params", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # refresh_tokens (avec device metadata)
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=128), unique=True, nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("refresh_tokens.id", ondelete="SET NULL")),
        sa.Column("device_label", sa.String(length=100)),
        sa.Column("ip_address", sa.String(length=50)),
        sa.Column("user_agent", sa.String(length=255)),
    )

    # audit_logs + composite index
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(length=100)),
        sa.Column("object_type", sa.String(length=50)),
        sa.Column("object_id", sa.String(length=64)),
        sa.Column("ip_address", sa.String(length=50)),
        sa.Column("user_agent", sa.String(length=255)),
        sa.Column("audit_metadata", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_audit_logs_action_object_created", "audit_logs", ["action", "object_type", "created_at"])

    # attachments
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("object_type", sa.String(length=50)),
        sa.Column("object_id", sa.Integer()),
        sa.Column("file_path", sa.String(length=500)),
        sa.Column("mime_type", sa.String(length=100)),
        sa.Column("size_bytes", sa.BigInteger()),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_table("attachments")
    op.drop_index("ix_audit_logs_action_object_created", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("refresh_tokens")
    op.drop_table("report_jobs")
    op.drop_table("declaration_items")
    op.drop_table("declaration_batches")
    op.drop_table("generated_documents")
    op.drop_table("template_companies")
    op.drop_index("uq_template_version", table_name="template_versions")
    op.drop_table("template_versions")
    op.drop_index("uq_template_name_type_scope", table_name="templates")
    op.drop_table("templates")
    op.drop_table("integration_configs")
    op.drop_index("ix_policies_policy_number", table_name="policies")
    op.drop_table("policies")
    op.drop_index("ix_clients_phone", table_name="clients")
    op.drop_index("ix_clients_email", table_name="clients")
    op.drop_table("clients")
    op.drop_table("companies")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                    DROP TYPE userrole;
                END IF;
            END$$;
            """
        )
