"""Make policies.company_id nullable to align with updated model

Revision ID: 20250808_0002
Revises: 20250808_0001
Create Date: 2025-08-08
"""
import sqlalchemy as sa

from alembic import op

revision = '20250808_0002'
down_revision = '20250808_0001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.alter_column('policies', 'company_id', existing_type=sa.Integer(), nullable=True)
    # SQLite note: altering nullability not supported directly; recreate DB if needed.

def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.alter_column('policies', 'company_id', existing_type=sa.Integer(), nullable=False)
