"""Add extended domain models and policy extra fields

Revision ID: 20250808_0003
Revises: 20250808_0002
Create Date: 2025-08-08
"""
import sqlalchemy as sa

from alembic import op

revision = '20250808_0003'
down_revision = '20250808_0002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add new columns to policies
    with op.batch_alter_table('policies') as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=30), server_default='active'))
        batch_op.add_column(sa.Column('currency', sa.String(length=3), server_default='XAF'))

    # integration_configs
    op.create_table('integration_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('mode', sa.String(length=20)),
        sa.Column('api_base_url', sa.String(length=500)),
        sa.Column('api_auth_type', sa.String(length=30)),
        sa.Column('api_key', sa.String(length=255)),
        sa.Column('api_secret', sa.Text()),
        sa.Column('report_format', sa.String(length=20)),
        sa.Column('callback_url', sa.String(length=500)),
        sa.Column('extra', sa.JSON()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # templates
    op.create_table('templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=30)),
        sa.Column('format', sa.String(length=20)),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')),
        sa.Column('scope', sa.String(length=20)),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    # SQLite ne supporte pas ALTER TABLE ADD CONSTRAINT pour UNIQUE après création.
    # Utilisation d'un index unique portable.
    op.create_index('uq_template_name_type_scope', 'templates', ['name','type','scope'], unique=True)

    # template_versions
    op.create_table('template_versions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('templates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('storage_backend', sa.String(length=20)),
        sa.Column('content', sa.Text()),
        sa.Column('file_path', sa.String(length=500)),
        sa.Column('checksum', sa.String(length=64)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('uq_template_version', 'template_versions', ['template_id','version'], unique=True)

    # template_companies association
    op.create_table('template_companies',
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('templates.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), primary_key=True),
    )

    # generated_documents
    op.create_table('generated_documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_type', sa.String(length=30)),
        sa.Column('policy_id', sa.Integer(), sa.ForeignKey('policies.id', ondelete='SET NULL')),
        sa.Column('template_version_id', sa.Integer(), sa.ForeignKey('template_versions.id', ondelete='SET NULL')),
        sa.Column('file_path', sa.String(length=500)),
        sa.Column('mime_type', sa.String(length=100)),
        sa.Column('size_bytes', sa.BigInteger()),
        sa.Column('status', sa.String(length=20)),
    # Nom aligné avec le modèle SQLAlchemy: GeneratedDocument.doc_metadata
    sa.Column('doc_metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # declaration_batches
    op.create_table('declaration_batches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='SET NULL')),
        sa.Column('period_start', sa.DateTime(timezone=True)),
        sa.Column('period_end', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(length=20)),
        sa.Column('report_document_id', sa.Integer(), sa.ForeignKey('generated_documents.id', ondelete='SET NULL')),
        sa.Column('generated_at', sa.DateTime(timezone=True)),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # declaration_items
    op.create_table('declaration_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('batch_id', sa.Integer(), sa.ForeignKey('declaration_batches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('policy_id', sa.Integer(), sa.ForeignKey('policies.id', ondelete='SET NULL')),
        sa.Column('premium_amount', sa.Integer()),
        sa.Column('commission_amount', sa.Integer()),
        sa.Column('data', sa.JSON()),
    )

    # report_jobs
    op.create_table('report_jobs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('job_type', sa.String(length=30)),
        sa.Column('scheduled_for', sa.DateTime(timezone=True)),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('finished_at', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(length=20)),
        sa.Column('params', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # refresh_tokens
    op.create_table('refresh_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(length=128), unique=True, nullable=False),
        sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('refresh_tokens.id', ondelete='SET NULL')),
    )

    # audit_logs
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('action', sa.String(length=100)),
        sa.Column('object_type', sa.String(length=50)),
        sa.Column('object_id', sa.String(length=64)),
        sa.Column('ip_address', sa.String(length=50)),
        sa.Column('user_agent', sa.String(length=255)),
    # Nom aligné avec le modèle SQLAlchemy: AuditLog.audit_metadata
    sa.Column('audit_metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # attachments
    op.create_table('attachments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('object_type', sa.String(length=50)),
        sa.Column('object_id', sa.Integer()),
        sa.Column('file_path', sa.String(length=500)),
        sa.Column('mime_type', sa.String(length=100)),
        sa.Column('size_bytes', sa.BigInteger()),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

def downgrade() -> None:
    op.drop_table('attachments')
    op.drop_table('audit_logs')
    op.drop_table('refresh_tokens')
    op.drop_table('report_jobs')
    op.drop_table('declaration_items')
    op.drop_table('declaration_batches')
    op.drop_table('generated_documents')
    op.drop_table('template_companies')
    op.drop_index('uq_template_version', table_name='template_versions')
    op.drop_table('template_versions')
    op.drop_index('uq_template_name_type_scope', table_name='templates')
    op.drop_table('templates')
    op.drop_table('integration_configs')
    with op.batch_alter_table('policies') as batch_op:
        batch_op.drop_column('status')
        batch_op.drop_column('currency')
