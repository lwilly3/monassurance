"""Tâches de traitement de documents avec Celery."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from celery import Task

from backend.app.core.celery_app import celery_app


@celery_app.task(bind=True, queue="documents", max_retries=2)
def process_document_upload(self: Task, document_id: int, file_path: str) -> dict[str, Any]:
    """Traite un document uploadé (scan, OCR, validation)."""
    try:
        # Simulation du traitement
        import time
        time.sleep(3)  # 3 secondes de traitement
        
        return {
            "document_id": document_id,
            "file_path": file_path,
            "processed_at": datetime.now(UTC).isoformat(),
            "task_id": self.request.id,
            "status": "success",
            "ocr_confidence": 0.95,
            "pages_processed": 1
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            retry_delay = 30 * (2 ** self.request.retries)
            raise self.retry(exc=exc, countdown=retry_delay)
        raise exc


@celery_app.task(bind=True, queue="documents", max_retries=1)
def generate_document_thumbnail(self: Task, document_id: int) -> dict[str, Any]:
    """Génère une miniature pour un document."""
    try:
        import time
        time.sleep(1)  # 1 seconde de traitement
        
        return {
            "document_id": document_id,
            "thumbnail_path": f"/thumbnails/doc_{document_id}_thumb.jpg",
            "generated_at": datetime.now(UTC).isoformat(),
            "task_id": self.request.id,
            "status": "success"
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=15)
        raise exc
