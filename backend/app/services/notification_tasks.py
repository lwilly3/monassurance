"""Tâches de notification avec Celery."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from celery import Task

from backend.app.core.celery_app import celery_app


@celery_app.task(bind=True, queue="notifications", max_retries=3)
def send_email_notification(self: Task, email: str, subject: str, content: str) -> dict[str, Any]:
    """Envoie une notification par email."""
    try:
        # Simulation d'envoi d'email
        import time
        time.sleep(0.5)  # 500ms de traitement
        
        return {
            "email": email,
            "subject": subject,
            "sent_at": datetime.now(UTC).isoformat(),
            "task_id": self.request.id,
            "status": "success"
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            retry_delay = 30 * (2 ** self.request.retries)
            raise self.retry(exc=exc, countdown=retry_delay)
        raise exc


@celery_app.task(bind=True, queue="notifications", max_retries=2)
def send_bulk_notifications(self: Task, recipients: list[str], subject: str, content: str) -> dict[str, Any]:
    """Envoie des notifications en masse."""
    try:
        # Simulation d'envoi en masse
        import time
        time.sleep(len(recipients) * 0.1)  # 100ms par destinataire
        
        return {
            "recipients_count": len(recipients),
            "sent_at": datetime.now(UTC).isoformat(),
            "task_id": self.request.id,
            "status": "success",
            "successful_sends": len(recipients),
            "failed_sends": 0
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(exc=exc, countdown=retry_delay)
        raise exc
