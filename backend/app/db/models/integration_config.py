from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base

class IntegrationConfig(Base):
    """Configuration d'intégration externe pour une compagnie."""
    __tablename__ = "integration_configs"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), unique=True)
    mode: Mapped[str | None] = mapped_column(String(20))
    api_base_url: Mapped[str | None] = mapped_column(String(500))
    api_auth_type: Mapped[str | None] = mapped_column(String(30))
    api_key: Mapped[str | None] = mapped_column(String(255))
    api_secret: Mapped[str | None] = mapped_column(Text)
    report_format: Mapped[str | None] = mapped_column(String(20))
    callback_url: Mapped[str | None] = mapped_column(String(500))
    extra: Mapped[dict | None] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
