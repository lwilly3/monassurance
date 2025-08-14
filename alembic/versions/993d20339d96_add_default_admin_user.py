"""add_default_admin_user

Revision ID: 993d20339d96
Revises: 20250812_0003
Create Date: 2025-08-14 16:27:17.654878
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, DateTime, Boolean
from datetime import datetime
from passlib.context import CryptContext


# revision identifiers, used by Alembic.
revision = '993d20339d96'
down_revision = '20250812_0003'
branch_labels = None
depends_on = None

# Configuration du hashage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def upgrade() -> None:
    """Crée un utilisateur administrateur par défaut."""
    
    # Définir la table users pour cette migration
    users_table = table('users',
        column('id', sa.Integer),
        column('email', String),
        column('full_name', String),
        column('hashed_password', String),
        column('role', String),
        column('is_active', Boolean),
        column('created_at', DateTime)
    )
    
    # Hash du mot de passe par défaut
    hashed_password = pwd_context.hash("D3faultpass")
    
    # Insertion de l'utilisateur admin par défaut
    op.execute(
        users_table.insert().values(
            email="admin@monassurance.com",
            full_name="Administrateur",
            hashed_password=hashed_password,
            role="admin",
            is_active=True,
            created_at=datetime.utcnow()
        )
    )
    
    print("✅ Utilisateur administrateur créé :")
    print("   Email: admin@monassurance.com")
    print("   Mot de passe: D3faultpass")
    print("   ⚠️  CHANGEZ ce mot de passe après la première connexion !")


def downgrade() -> None:
    """Supprime l'utilisateur administrateur par défaut."""
    
    # Définir la table users pour cette migration
    users_table = table('users',
        column('email', String)
    )
    
    # Suppression de l'utilisateur admin par défaut
    op.execute(
        users_table.delete().where(
            users_table.c.email == "admin@monassurance.com"
        )
    )
    
    print("❌ Utilisateur administrateur par défaut supprimé")
