from sqlalchemy import JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class DeclarationItem(Base):
    """Ligne d'une déclaration (montants + référence police)."""
    __tablename__ = "declaration_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("declaration_batches.id", ondelete="CASCADE"))
    policy_id: Mapped[int | None] = mapped_column(ForeignKey("policies.id", ondelete="SET NULL"))
    premium_amount: Mapped[int | None] = mapped_column(Integer)
    commission_amount: Mapped[int | None] = mapped_column(Integer)
    data: Mapped[dict | None] = mapped_column(JSON)
