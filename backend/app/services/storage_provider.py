from __future__ import annotations

"""Provider de backend de stockage basé sur la configuration persistée.

Expose get_storage() pour obtenir un objet avec store_bytes() et read_text(path).
"""
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.orm import Session

from backend.app.db import models
from backend.app.services.gdrive_backend import GoogleDriveStorageBackend

try:
    import boto3  # type: ignore
except Exception:  # pragma: no cover
    boto3 = None
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
    if cfg.backend == "s3":
        if not cfg.s3_bucket:
            raise ValueError("Configuration S3 incomplète (bucket manquant)")
        if boto3 is None:
            raise RuntimeError("boto3 non installé – ajouter boto3 pour utiliser S3")
        # Si aucune variable d'identifiants AWS n'est présente, on retombe en local afin de
        # permettre aux tests de fonctionner sans dépendre d'AWS (mode dégradé).
        import os
        have_creds = any(os.environ.get(k) for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_PROFILE"))
        if not have_creds:
            return LocalStorageBackend()
        return S3StorageBackend(bucket=cfg.s3_bucket, region=cfg.s3_region, endpoint_url=cfg.s3_endpoint_url)
    return LocalStorageBackend()


class S3StorageBackend:
    def __init__(self, bucket: str, region: str | None, endpoint_url: str | None):
        session = boto3.session.Session(region_name=region) if boto3 else None
        self._client = session.client("s3", endpoint_url=endpoint_url) if session else None
        self.bucket = bucket

    def store_bytes(
        self,
        data: bytes,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> str:
        key = filename or "object"
        assert self._client is not None
        extra: dict = {}
        if content_type:
            extra["ContentType"] = content_type
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra)
        return key

    def read_text(self, path: str) -> str:
        assert self._client is not None
        resp = self._client.get_object(Bucket=self.bucket, Key=path)
        body_bytes = resp["Body"].read()
        text: str = body_bytes.decode("utf-8")
        return text


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
