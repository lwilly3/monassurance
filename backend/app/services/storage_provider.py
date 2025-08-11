from __future__ import annotations

"""Provider de backend de stockage basé sur la configuration persistée.

Expose get_storage() pour obtenir un objet avec store_bytes() et read_text(path).
"""
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.orm import Session

from backend.app.db import models
from backend.app.services.gdrive_backend import GoogleDriveStorageBackend
from backend.app.services.template_storage import (
    read_template_text_from_file,
    store_template_bytes,
)


class StorageBackend(Protocol):
    def store_bytes(
        self,
        data: bytes,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> str:
        ...

    def read_text(self, path: str) -> str:
        ...


@dataclass
class LocalStorageBackend:
    def store_bytes(
        self,
        data: bytes,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> str:
        return store_template_bytes(data, filename=filename, content_type=content_type)

    def read_text(self, path: str) -> str:
        return read_template_text_from_file(path)


def _make_backend(cfg: models.StorageConfig) -> StorageBackend:
    if cfg.backend == "google_drive":
        # Placeholder: pour l'instant on revient à local tant que l'implémentation GDrive n'est pas prête
        if not cfg.gdrive_folder_id or not cfg.gdrive_service_account_json_path:
            raise ValueError("Configuration Google Drive incomplète")
        return GoogleDriveStorageBackend(cfg.gdrive_service_account_json_path, cfg.gdrive_folder_id)
    return LocalStorageBackend()


def get_storage(db: Session) -> StorageBackend:
    cfg = db.query(models.StorageConfig).order_by(models.StorageConfig.id.asc()).first()
    if not cfg:
        cfg = models.StorageConfig(backend="local")
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return _make_backend(cfg)

def invalidate_storage_cache():
    """À appeler après modification de la config pour invalider le cache du backend."""
    # Si un cache est utilisé, l’invalider ici (ex: lru_cache, etc.)
    pass
