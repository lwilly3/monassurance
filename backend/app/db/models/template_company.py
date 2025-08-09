from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class TemplateCompany(Base):
    __tablename__ = "template_companies"
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id", ondelete="CASCADE"), primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
