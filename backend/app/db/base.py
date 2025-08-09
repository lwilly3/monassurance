"""Base ORM commune pour toutes les entités.

__tablename__ dérivé automatiquement du nom de classe en lowercase.
"""
from sqlalchemy.orm import DeclarativeBase, declared_attr

class Base(DeclarativeBase):
    id: int  # typing hint placeholder

    @declared_attr.directive
    def __tablename__(cls) -> str:  # type: ignore
        return cls.__name__.lower()
