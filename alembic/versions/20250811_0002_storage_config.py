"""storage_config table

Revision ID: 20250811_0002_storage_config
Revises: 20250809_0101_pg_defaults
Create Date: 2025-08-11 00:02:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20250811_0002_storage_config'
down_revision: Union[str, None] = '20250809_0101_pg_defaults'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'storage_config',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('backend', sa.String(length=30), nullable=False, server_default='local'),
        sa.Column('gdrive_folder_id', sa.String(length=128), nullable=True),
        sa.Column('gdrive_service_account_json_path', sa.String(length=500), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    # Insert default row
    op.execute("INSERT INTO storage_config (id, backend) VALUES (1, 'local')")


def downgrade() -> None:
    op.drop_table('storage_config')
