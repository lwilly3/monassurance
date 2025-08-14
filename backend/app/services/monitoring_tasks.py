"""Tâches de monitoring et maintenance système avec Celery."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.core.celery_app import celery_app
from backend.app.db import models
from backend.app.db.session import SessionLocal


@celery_app.task(queue="celery")
def system_health_check() -> dict[str, Any]:
    """Vérifie la santé générale du système."""
    db = SessionLocal()
    try:
        # Vérification base de données
        db_status = "healthy"
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
        except Exception:
            db_status = "unhealthy"
        
        # Vérification Redis
        redis_status = "healthy"
        try:
            from backend.app.core.redis import get_redis
            redis_client = get_redis()
            redis_client.ping()
        except Exception:
            redis_status = "unhealthy"
        
        # Statistiques jobs
        pending_jobs = db.query(models.ReportJob).filter(
            models.ReportJob.status.in_(["pending", "queued", "started"])
        ).count()
        
        completed_jobs_today = db.query(models.ReportJob).filter(
            models.ReportJob.status == "completed",
            models.ReportJob.finished_at >= datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "database_status": db_status,
            "redis_status": redis_status,
            "pending_jobs": pending_jobs,
            "completed_jobs_today": completed_jobs_today,
            "overall_status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"
        }
        
    finally:
        db.close()


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


@celery_app.task(queue="celery")
def generate_daily_metrics_report() -> dict[str, Any]:
    """Génère un rapport quotidien de métriques."""
    db = SessionLocal()
    try:
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Statistiques du jour
        jobs_by_status = {}
        for status in ["completed", "failed", "pending", "queued", "started"]:
            count = db.query(models.ReportJob).filter(
                models.ReportJob.status == status,
                models.ReportJob.created_at >= today_start
            ).count()
            jobs_by_status[status] = count
        
        # Utilisateurs actifs (basé sur le statut is_active)
        active_users = db.query(models.User).filter(
            models.User.is_active
        ).count()
        
        return {
            "report_date": today_start.date().isoformat(),
            "generated_at": datetime.now(UTC).isoformat(),
            "jobs_by_status": jobs_by_status,
            "active_users": active_users,
            "total_jobs_today": sum(jobs_by_status.values())
        }
        
    finally:
        db.close()
