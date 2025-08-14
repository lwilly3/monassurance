"""add s3 columns to storage_config

Revision ID: 20250812_0003
Revises: e63672f17369
Create Date: 2025-08-12
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20250812_0003'
down_revision: Union[str, None] = 'e63672f17369'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('storage_config') as batch:
        batch.add_column(sa.Column('s3_bucket', sa.String(length=255), nullable=True))
        batch.add_column(sa.Column('s3_region', sa.String(length=50), nullable=True))
        batch.add_column(sa.Column('s3_endpoint_url', sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('storage_config') as batch:
        batch.drop_column('s3_endpoint_url')
        batch.drop_column('s3_region')
        batch.drop_column('s3_bucket')
