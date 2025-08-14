"""Extension du schéma de réponse pour supporter Celery."""
from typing import Any, Optional

from pydantic import BaseModel


class ReportJobLaunchResponse(BaseModel):
    """Réponse de lancement d'un job de rapport."""
    job_id: str
    status: str
    report_job_id: int
    queue: Optional[str] = None  # Nouvelle: indication de la queue utilisée
    estimated_duration: Optional[int] = None  # Nouvelle: durée estimée en secondes


class ReportJobStatusResponse(BaseModel):
    """Réponse de statut d'un job de rapport."""
    job_id: str
    status: str
    report_job_id: Optional[int] = None
    result: Optional[dict[str, Any]] = None  # Nouvelle: résultat complet
    error: Optional[str] = None  # Nouvelle: détails d'erreur
    progress: Optional[dict[str, Any]] = None  # Nouvelle: progression
    started_at: Optional[str] = None  # Nouvelle: timestamp de démarrage
    estimated_completion: Optional[str] = None  # Nouvelle: estimation de fin


class HeavyReportRequest(BaseModel):
    """Requête pour un rapport lourd."""
    report_type: str  # pdf, excel, analysis
    pages: Optional[int] = 10
    processing_time: Optional[int] = 10  # Pour simulation
    priority: Optional[str] = "normal"  # normal, high, low
    callback_url: Optional[str] = None  # URL de callback à la fin


class QueueStatusResponse(BaseModel):
    """Statut des queues Celery."""
    celery_available: bool
    workers: list[dict[str, Any]]
    total_active_tasks: int
    queue_lengths: Optional[dict[str, int]] = None


class JobListResponse(BaseModel):
    """Réponse de listage des jobs."""
    jobs: list[dict[str, Any]]
    total: int
    page: int
    per_page: int
