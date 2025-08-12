from datetime import datetime

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class StorageConfig(Base):
    """Configuration persistée du backend de stockage (local, google_drive ou s3).

    Une seule ligne utilisée (id=1).

    Champs S3 ajoutés pour préparer une migration future vers stockage objet.
    """

    __tablename__ = "storage_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    backend: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'local'"))
    gdrive_folder_id: Mapped[str | None] = mapped_column(String(128))
    gdrive_service_account_json_path: Mapped[str | None] = mapped_column(String(500))
    # S3 (optionnel)
    s3_bucket: Mapped[str | None] = mapped_column(String(255))
    s3_region: Mapped[str | None] = mapped_column(String(50))
    s3_endpoint_url: Mapped[str | None] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
