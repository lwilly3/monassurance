"""Base ORM commune pour toutes les entités.

Utiliser une Base minimale afin que mypy (avec le plugin SQLAlchemy)
n'entre pas en conflit avec les attributs déclarés dans les sous-classes.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
