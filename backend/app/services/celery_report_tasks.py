"""Tâches de génération de rapports avec Celery.

Remplace l'ancien système RQ par Celery pour une gestion plus robuste
des tâches asynchrones et des rapports lourds.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from celery import Task

from backend.app.core.celery_app import celery_app
from backend.app.db import models
from backend.app.db.session import SessionLocal

try:  # pragma: no cover
    from prometheus_client import Counter, Gauge, Histogram
    REPORT_JOBS_TOTAL = Counter(
        "report_jobs_total", 
        "Total des jobs rapports", 
        ["job_type", "status", "queue"]
    )
    REPORT_JOBS_DURATION = Histogram(
        "report_jobs_duration_seconds",
        "Durée d'exécution des jobs rapports",
        ["job_type", "queue"]
    )
    REPORT_JOBS_ACTIVE = Gauge(
        "report_jobs_active", 
        "Jobs rapports en cours", 
        ["job_type", "queue"]
    )
    REPORT_JOBS_RETRIES = Counter(
        "report_jobs_retries_total",
        "Nombre de tentatives de retry",
        ["job_type", "queue"]
    )
except Exception:  # pragma: no cover
    REPORT_JOBS_TOTAL = None  # type: ignore
    REPORT_JOBS_DURATION = None  # type: ignore
    REPORT_JOBS_ACTIVE = None  # type: ignore
    REPORT_JOBS_RETRIES = None  # type: ignore


def update_job_status(job_id: int, status: str, result: dict[str, Any] | None = None) -> None:
    """Met à jour le statut d'un job dans la base de données."""
    db = SessionLocal()
    try:
        job = db.query(models.ReportJob).filter(models.ReportJob.id == job_id).first()
        if job:
            job.status = status
            if status == "started":
                job.started_at = datetime.now(UTC)
            elif status in ["completed", "failed"]:
                job.finished_at = datetime.now(UTC)
                if result:
                    job.params = {**(job.params or {}), "result": result}
            db.commit()
    finally:
        db.close()


@celery_app.task(bind=True, queue="reports", max_retries=3, default_retry_delay=60)
def generate_dummy_report(self: Task, report_id: str, job_id: int | None = None) -> dict[str, Any]:
    """Génération d'un rapport factice (pour démonstration et tests)."""
    job_type = "dummy"
    queue_name = "reports"
    
    # Métriques début
    if REPORT_JOBS_ACTIVE:
        REPORT_JOBS_ACTIVE.labels(job_type, queue_name).inc()
    
    start_time = datetime.now(UTC)
    
    try:
        # Mise à jour statut démarrage
        if job_id:
            update_job_status(job_id, "started")
        
        # Simulation d'un traitement plus long pour tester la queue
        import time
        time.sleep(2)  # 2 secondes de traitement
        
        # Génération du rapport
        result = {
            "report_id": report_id,
            "generated_at": start_time.isoformat(),
            "task_id": self.request.id,
            "status": "success",
            "processing_time_seconds": (datetime.now(UTC) - start_time).total_seconds(),
            "queue": queue_name
        }
        
        # Mise à jour statut succès
        if job_id:
            update_job_status(job_id, "completed", result)
        
        # Métriques succès
        if REPORT_JOBS_TOTAL:
            REPORT_JOBS_TOTAL.labels(job_type, "success", queue_name).inc()
        if REPORT_JOBS_DURATION:
            duration = (datetime.now(UTC) - start_time).total_seconds()
            REPORT_JOBS_DURATION.labels(job_type, queue_name).observe(duration)
        
        return result
        
    except Exception as exc:
        # Gestion des erreurs et retry
        if self.request.retries < self.max_retries:
            if REPORT_JOBS_RETRIES:
                REPORT_JOBS_RETRIES.labels(job_type, queue_name).inc()
            
            # Mise à jour statut retry
            if job_id:
                update_job_status(job_id, f"retry_{self.request.retries + 1}")
            
            # Retry avec backoff exponentiel
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(exc=exc, countdown=retry_delay)
        
        # Échec définitif
        error_result = {
            "report_id": report_id,
            "error": str(exc),
            "task_id": self.request.id,
            "status": "failed",
            "retries": self.request.retries,
            "queue": queue_name
        }
        
        if job_id:
            update_job_status(job_id, "failed", error_result)
        
        if REPORT_JOBS_TOTAL:
            REPORT_JOBS_TOTAL.labels(job_type, "error", queue_name).inc()
        
        raise exc
        
    finally:
        # Nettoyage métriques
        if REPORT_JOBS_ACTIVE:
            REPORT_JOBS_ACTIVE.labels(job_type, queue_name).dec()


@celery_app.task(bind=True, queue="reports", max_retries=2, default_retry_delay=120)
def generate_heavy_report(self: Task, report_type: str, params: dict[str, Any], job_id: int | None = None) -> dict[str, Any]:
    """Génération d'un rapport lourd (PDF, Excel avec beaucoup de données)."""
    job_type = "heavy"
    queue_name = "reports"
    
    if REPORT_JOBS_ACTIVE:
        REPORT_JOBS_ACTIVE.labels(job_type, queue_name).inc()
    
    start_time = datetime.now(UTC)
    
    try:
        if job_id:
            update_job_status(job_id, "started")
        
        # Simulation traitement lourd (10-30 secondes)
        import time
        processing_time = params.get("processing_time", 10)
        time.sleep(processing_time)
        
        # Génération du rapport selon le type
        if report_type == "pdf":
            result = _generate_pdf_report(params)
        elif report_type == "excel":
            result = _generate_excel_report(params)
        elif report_type == "analysis":
            result = _generate_analysis_report(params)
        else:
            raise ValueError(f"Type de rapport non supporté: {report_type}")
        
        result.update({
            "task_id": self.request.id,
            "generated_at": start_time.isoformat(),
            "processing_time_seconds": (datetime.now(UTC) - start_time).total_seconds(),
            "queue": queue_name
        })
        
        if job_id:
            update_job_status(job_id, "completed", result)
        
        if REPORT_JOBS_TOTAL:
            REPORT_JOBS_TOTAL.labels(job_type, "success", queue_name).inc()
        if REPORT_JOBS_DURATION:
            duration = (datetime.now(UTC) - start_time).total_seconds()
            REPORT_JOBS_DURATION.labels(job_type, queue_name).observe(duration)
        
        return result
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            if REPORT_JOBS_RETRIES:
                REPORT_JOBS_RETRIES.labels(job_type, queue_name).inc()
            
            if job_id:
                update_job_status(job_id, f"retry_{self.request.retries + 1}")
            
            retry_delay = 120 * (2 ** self.request.retries)
            raise self.retry(exc=exc, countdown=retry_delay)
        
        error_result = {
            "report_type": report_type,
            "error": str(exc),
            "task_id": self.request.id,
            "status": "failed",
            "retries": self.request.retries,
            "queue": queue_name
        }
        
        if job_id:
            update_job_status(job_id, "failed", error_result)
        
        if REPORT_JOBS_TOTAL:
            REPORT_JOBS_TOTAL.labels(job_type, "error", queue_name).inc()
        
        raise exc
        
    finally:
        if REPORT_JOBS_ACTIVE:
            REPORT_JOBS_ACTIVE.labels(job_type, queue_name).dec()


def _generate_pdf_report(params: dict[str, Any]) -> dict[str, Any]:
    """Génère un rapport PDF."""
    return {
        "type": "pdf",
        "filename": f"report_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.pdf",
        "size_bytes": 1024 * 512,  # 512KB simulé
        "pages": params.get("pages", 10),
        "status": "success"
    }


def _generate_excel_report(params: dict[str, Any]) -> dict[str, Any]:
    """Génère un rapport Excel."""
    return {
        "type": "excel",
        "filename": f"report_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.xlsx",
        "size_bytes": 1024 * 256,  # 256KB simulé
        "sheets": params.get("sheets", 3),
        "rows": params.get("rows", 1000),
        "status": "success"
    }


def _generate_analysis_report(params: dict[str, Any]) -> dict[str, Any]:
    """Génère un rapport d'analyse avancée."""
    return {
        "type": "analysis",
        "filename": f"analysis_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.pdf",
        "size_bytes": 1024 * 1024 * 2,  # 2MB simulé
        "charts": params.get("charts", 5),
        "data_points": params.get("data_points", 10000),
        "status": "success"
    }


# Tâches de maintenance pour nettoyer les anciens jobs
@celery_app.task(queue="celery")
def cleanup_old_report_jobs() -> dict[str, Any]:
    """Nettoie les anciens jobs de rapport (> 7 jours)."""
    from datetime import timedelta
    
    db = SessionLocal()
    try:
        cutoff_date = datetime.now(UTC) - timedelta(days=7)
        
        # Supprimer les jobs terminés de plus de 7 jours
        deleted_count = db.query(models.ReportJob).filter(
            models.ReportJob.finished_at < cutoff_date,
            models.ReportJob.status.in_(["completed", "failed"])
        ).delete()
        
        db.commit()
        
        return {
            "cleanup_date": datetime.now(UTC).isoformat(),
            "deleted_jobs": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    finally:
        db.close()


# Migration de l'ancienne interface RQ vers Celery
class CeleryTaskWrapper:
    """Wrapper pour maintenir la compatibilité avec l'ancienne interface RQ."""
    
    def __init__(self, task_id: str, celery_result: Any) -> None:
        self.id = task_id
        self._result = celery_result
    
    def get_status(self) -> str:
        """Compatibilité avec l'interface RQ."""
        if self._result.ready():
            return "finished" if self._result.successful() else "failed"
        return "started" if self._result.state == "PROGRESS" else "queued"
    
    def fetch(self, job_id: str, connection: Any = None) -> CeleryTaskWrapper:
        """Interface de compatibilité pour récupérer un job."""
        from celery.result import AsyncResult
        result = AsyncResult(job_id, app=celery_app)
        return CeleryTaskWrapper(job_id, result)


# Fonction utilitaire pour obtenir le statut d'une tâche
def get_task_status(task_id: str) -> dict[str, Any]:
    """Récupère le statut d'une tâche Celery."""
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "state": result.state,
        "status": "finished" if result.ready() else result.state.lower(),
        "result": result.result if result.ready() and result.successful() else None,
        "error": str(result.result) if result.ready() and not result.successful() else None,
        "traceback": result.traceback if result.ready() and not result.successful() else None
    }
