from datetime import datetime

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class StorageConfig(Base):
    """Configuration persistée du backend de stockage (local ou google_drive).

    Une seule ligne utilisée (id=1)."""

    __tablename__ = "storage_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    backend: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'local'"))
    gdrive_folder_id: Mapped[str | None] = mapped_column(String(128))
    gdrive_service_account_json_path: Mapped[str | None] = mapped_column(String(500))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
