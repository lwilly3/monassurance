"""init

Revision ID: 20250808_0001
Revises: 
Create Date: 2025-08-08
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

from alembic import op

# revision identifiers, used by Alembic.
revision = '20250808_0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    dialect = op.get_context().dialect.name
    if dialect == 'postgresql':
        # Crée le type ENUM userrole de manière idempotente (si absent)
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
        # Référencer le type existant sans tenter de le re-créer
        userrole = psql.ENUM('admin', 'agent', 'manager', name='userrole', create_type=False)
    else:
        # Dialectes non-PG: fallback String
        userrole = sa.String(length=50)

    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', userrole, nullable=False, server_default='agent'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table('companies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('code', sa.String(length=50), nullable=False, unique=True),
        sa.Column('api_mode', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('api_endpoint', sa.String(length=500)),
        sa.Column('api_key', sa.String(length=255)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table('clients',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255)),
        sa.Column('phone', sa.String(length=50)),
        sa.Column('address', sa.Text()),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_clients_email', 'clients', ['email'])
    op.create_index('ix_clients_phone', 'clients', ['phone'])

    op.create_table('policies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('policy_number', sa.String(length=100), unique=True),
        sa.Column('client_id', sa.Integer(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='SET NULL')),
        sa.Column('product_name', sa.String(length=255)),
        sa.Column('premium_amount', sa.Integer()),
        sa.Column('effective_date', sa.DateTime(timezone=True)),
        sa.Column('expiry_date', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_policies_policy_number', 'policies', ['policy_number'])


def downgrade() -> None:
    op.drop_index('ix_policies_policy_number', table_name='policies')
    op.drop_table('policies')
    op.drop_index('ix_clients_phone', table_name='clients')
    op.drop_index('ix_clients_email', table_name='clients')
    op.drop_table('clients')
    op.drop_table('companies')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    if op.get_context().dialect.name == 'postgresql':
        # Supprimer le type ENUM s'il existe encore
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
