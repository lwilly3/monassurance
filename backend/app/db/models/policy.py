from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from .client import Client
    from .company import Company


class Policy(Base):
    """Police d'assurance (lien client + compagnie)."""

    __tablename__ = "policies"
    id: Mapped[int] = mapped_column(primary_key=True)
    policy_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"))
    product_name: Mapped[str] = mapped_column(String(255))
    premium_amount: Mapped[int] = mapped_column(Integer)
    effective_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    status: Mapped[str | None] = mapped_column(String(30), server_default=text("'active'"))
    currency: Mapped[str | None] = mapped_column(String(3), server_default=text("'XAF'"))

    client: Mapped[Client] = relationship(back_populates="policies")
    company: Mapped[Company | None] = relationship(back_populates="policies")
