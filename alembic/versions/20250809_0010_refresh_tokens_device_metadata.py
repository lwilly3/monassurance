"""Add device metadata columns to refresh_tokens

Revision ID: 20250809_0010
Revises: 20250809_0009
Create Date: 2025-08-09
"""
import sqlalchemy as sa

from alembic import op

revision = '20250809_0010'
down_revision = '20250809_0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch for SQLite compatibility
    with op.batch_alter_table('refresh_tokens') as batch_op:
        batch_op.add_column(sa.Column('device_label', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('ip_address', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('user_agent', sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('refresh_tokens') as batch_op:
        batch_op.drop_column('user_agent')
        batch_op.drop_column('ip_address')
        batch_op.drop_column('device_label')
