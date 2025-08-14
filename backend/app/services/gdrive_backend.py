from __future__ import annotations

"""
Backend Google Drive pour le stockage des templates.
"""
import io
from pathlib import Path
from typing import Any

from google.oauth2 import service_account  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload  # type: ignore


class GoogleDriveStorageBackend:
    def __init__(self, service_account_path: str, folder_id: str):
        self.service_account_path = service_account_path
        self.folder_id = folder_id
        self._client = None
        self._drive: Any = None  # Pour mypy
        self._creds = None
        self._init_client()

    def _init_client(self):
        if not Path(self.service_account_path).exists():
            raise FileNotFoundError(f"Service account JSON introuvable: {self.service_account_path}")
        self._creds = service_account.Credentials.from_service_account_file(
            self.service_account_path,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        self._drive = build("drive", "v3", credentials=self._creds)

    def store_bytes(self, data: bytes, filename: str | None = None, content_type: str | None = None) -> str:
        assert self._drive is not None  # Pour mypy
        name = filename or "untitled"
        media = MediaIoBaseUpload(io.BytesIO(data), mimetype=content_type or "text/plain")
        file_metadata = {
            "name": name,
            "parents": [self.folder_id],
        }
        file = self._drive.files().create(body=file_metadata, media_body=media, fields="id").execute()
        return str(file["id"])

    def read_text(self, file_id: str) -> str:
        assert self._drive is not None  # Pour mypy
        request = self._drive.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read().decode("utf-8")
