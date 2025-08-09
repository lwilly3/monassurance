"""Add composite index on audit_logs for frequent filters

Revision ID: 20250808_0004
Revises: 20250808_0003
Create Date: 2025-08-08
"""
from alembic import op
import sqlalchemy as sa

revision = '20250808_0004'
down_revision = '20250808_0003'
branch_labels = None
depends_on = None

INDEX_NAME = 'ix_audit_logs_action_object_created'


def upgrade() -> None:
    # SQLite: create_index is acceptable; PostgreSQL: will speed up composite queries
    op.create_index(INDEX_NAME, 'audit_logs', ['action', 'object_type', 'created_at'])


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name='audit_logs')
