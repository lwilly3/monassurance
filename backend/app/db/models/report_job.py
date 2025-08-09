from datetime import datetime

from sqlalchemy import JSON, DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ReportJob(Base):
    """Job de génération de rapports (pour future exécution asynchrone)."""
    __tablename__ = "report_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[str | None] = mapped_column(String(30))
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(String(20))
    params: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
