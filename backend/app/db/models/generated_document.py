from datetime import datetime, timezone
from sqlalchemy import String, DateTime, BigInteger, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base

class GeneratedDocument(Base):
    """Document généré et stocké (path + métadonnées de rendu)."""
    __tablename__ = "generated_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_type: Mapped[str | None] = mapped_column(String(30))
    policy_id: Mapped[int | None] = mapped_column(ForeignKey("policies.id", ondelete="SET NULL"))
    template_version_id: Mapped[int | None] = mapped_column(ForeignKey("template_versions.id", ondelete="SET NULL"))
    file_path: Mapped[str | None] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str | None] = mapped_column(String(20))
    doc_metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
