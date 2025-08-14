from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from .client import Client


class UserRole(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"
    MANAGER = "manager"

class User(Base):
    """Utilisateur applicatif (auth + ownership de clients)."""

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # Utiliser les valeurs (minuscules) de l'Enum pour l'ENUM PostgreSQL
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, values_callable=lambda e: [m.value for m in e], name="userrole"),
        nullable=False,
        server_default=text("'agent'"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    clients: Mapped[list[Client]] = relationship(back_populates="owner")
