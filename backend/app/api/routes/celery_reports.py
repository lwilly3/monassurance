"""Routes API pour les rapports avec support Celery.

Migration de RQ vers Celery pour une gestion plus robuste des tâches asynchrones.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db import models
from backend.app.db.models.user import User, UserRole
from backend.app.schemas.report_jobs import (
    ReportJobLaunchResponse,
    ReportJobStatusResponse,
)

# Import conditionnel pour support Celery et compatibilité RQ
try:
    from backend.app.services.celery_report_tasks import (
        generate_dummy_report,
        generate_heavy_report,
        get_task_status,
    )
    CELERY_AVAILABLE = True
except ImportError:
    # Fallback vers l'ancien système RQ
    from backend.app.core.queue import get_queue
    from backend.app.services.report_tasks import generate_dummy_report
    try:
        from rq.job import Job as RQJob
        RQ_AVAILABLE = True
    except Exception:
        RQJob = None  # type: ignore[assignment,misc]
        RQ_AVAILABLE = False
    CELERY_AVAILABLE = False

if TYPE_CHECKING:
    from rq.job import Job as JobType
else:
    class JobType:
        fetch = None


router = APIRouter(prefix="/reports", tags=["reports"])


def require_admin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Réservé admin")


@router.post("/dummy", response_model=ReportJobLaunchResponse)
def launch_dummy(
    report_id: str, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
) -> ReportJobLaunchResponse:
    """Lance un rapport factice (démo/test) avec Celery ou RQ fallback."""
    require_admin(current_user)
    
    # Créer enregistrement report_jobs (status pending)
    rj = models.ReportJob(job_type="dummy", status="pending", params={"report_id": report_id})
    db.add(rj)
    db.commit()
    db.refresh(rj)
    
    if CELERY_AVAILABLE:
        # Utilisation de Celery (nouveau système)
        task = generate_dummy_report.delay(report_id, rj.id)
        rj.status = "queued"
        rj.params = {**(rj.params or {}), "celery_task_id": task.id}
        db.add(rj)
        db.commit()
        
        return ReportJobLaunchResponse(
            job_id=task.id, 
            status="queued", 
            report_job_id=rj.id
        )
    else:
        # Fallback vers RQ (ancien système)
        job = generate_dummy_report.delay(report_id)
        if hasattr(job, "id"):
            rj.status = "queued"
            db.add(rj)
            db.commit()
            return ReportJobLaunchResponse(job_id=job.id, status="queued", report_job_id=rj.id)
        
        # Inline fallback
        rj.status = "completed"
        db.add(rj)
        db.commit()
        return ReportJobLaunchResponse(job_id="inline", status="completed", report_job_id=rj.id)


@router.post("/heavy", response_model=ReportJobLaunchResponse)
def launch_heavy_report(
    report_type: str = Query(..., description="Type de rapport: pdf, excel, analysis"),
    pages: int = Query(10, description="Nombre de pages (pour PDF)"),
    processing_time: int = Query(10, description="Temps de traitement simulé (secondes)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ReportJobLaunchResponse:
    """Lance un rapport lourd avec Celery."""
    require_admin(current_user)
    
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Service indisponible - Celery requis pour les rapports lourds"
        )
    
    # Validation du type de rapport
    if report_type not in ["pdf", "excel", "analysis"]:
        raise HTTPException(
            status_code=400,
            detail="Type de rapport non supporté. Valeurs acceptées: pdf, excel, analysis"
        )
    
    # Créer enregistrement report_jobs
    params = {
        "report_type": report_type,
        "pages": pages,
        "processing_time": processing_time
    }
    
    rj = models.ReportJob(
        job_type="heavy", 
        status="pending", 
        params=params
    )
    db.add(rj)
    db.commit()
    db.refresh(rj)
    
    # Lancer la tâche Celery
    task = generate_heavy_report.delay(report_type, params, rj.id)
    rj.status = "queued"
    rj.params = {**(rj.params or {}), "celery_task_id": task.id}
    db.add(rj)
    db.commit()
    
    return ReportJobLaunchResponse(
        job_id=task.id,
        status="queued",
        report_job_id=rj.id
    )


@router.get("/jobs/{job_id}", response_model=ReportJobStatusResponse)
def job_status(
    job_id: str, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
) -> ReportJobStatusResponse:
    """Récupère le statut d'un job avec support Celery et RQ."""
    require_admin(current_user)
    
    if job_id == "inline":
        # Gestion des jobs inline (ancienne compatibilité)
        rj = (
            db.query(models.ReportJob)
            .filter(models.ReportJob.status == "completed", models.ReportJob.job_type == "dummy")
            .order_by(models.ReportJob.id.desc())
            .first()
        )
        return ReportJobStatusResponse(job_id=job_id, status="completed", report_job_id=rj.id if rj else None)
    
    if CELERY_AVAILABLE:
        # Utilisation de Celery (nouveau système)
        try:
            task_info = get_task_status(job_id)
            
            # Rechercher le job correspondant en base
            rj = (
                db.query(models.ReportJob)
                .filter(models.ReportJob.params.op("->>")('"celery_task_id"') == job_id)
                .first()
            )
            
            # Mettre à jour le statut en base si nécessaire
            if rj and task_info["status"] == "finished" and rj.status not in ["completed", "failed"]:
                rj.status = "completed" if task_info.get("result") else "failed"
                if task_info["status"] == "finished":
                    from datetime import UTC, datetime
                    rj.finished_at = datetime.now(UTC)
                db.add(rj)
                db.commit()
            
            return ReportJobStatusResponse(
                job_id=job_id,
                status=task_info["status"],
                report_job_id=rj.id if rj else None,
                result=task_info.get("result"),
                error=task_info.get("error")
            )
            
        except Exception:
            return ReportJobStatusResponse(job_id=job_id, status="unknown", report_job_id=None)
    
    else:
        # Fallback vers RQ (ancien système)
        if not RQ_AVAILABLE:
            return ReportJobStatusResponse(job_id=job_id, status="unknown", report_job_id=None)
        
        q = get_queue()
        if q is None:
            return ReportJobStatusResponse(job_id=job_id, status="unknown", report_job_id=None)
        
        try:
            assert RQJob is not None
            assert q is not None
            job_cls = RQJob if RQJob is not None else JobType
            job = job_cls.fetch(job_id, connection=q.connection)  # type: ignore[attr-defined]
            rj = (
                db.query(models.ReportJob)
                .filter(models.ReportJob.status.in_(["pending", "queued"]))
                .order_by(models.ReportJob.id.desc())
                .first()
            )
            if job.get_status() == "finished" and rj:
                rj.status = "completed"
                db.add(rj)
                db.commit()
            return ReportJobStatusResponse(
                job_id=job.id, 
                status=job.get_status() or "unknown", 
                report_job_id=rj.id if rj else None
            )
        except Exception:
            return ReportJobStatusResponse(job_id=job_id, status="unknown", report_job_id=None)


@router.get("/jobs", response_model=list[dict])
def list_jobs(
    status: str | None = Query(None, description="Filtrer par statut"),
    limit: int = Query(50, description="Nombre max de résultats"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> list[dict]:
    """Liste les jobs de rapport avec pagination."""
    require_admin(current_user)
    
    query = db.query(models.ReportJob).order_by(models.ReportJob.id.desc())
    
    if status:
        query = query.filter(models.ReportJob.status == status)
    
    jobs = query.limit(limit).all()
    
    return [
        {
            "id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "params": job.params
        }
        for job in jobs
    ]


@router.delete("/jobs/{job_id}")
def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """Annule un job en cours (Celery uniquement)."""
    require_admin(current_user)
    
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Annulation indisponible - Celery requis"
        )
    
    try:
        from celery.result import AsyncResult

        from backend.app.core.celery_app import celery_app
        
        # Annuler la tâche Celery
        result = AsyncResult(job_id, app=celery_app)
        result.revoke(terminate=True)
        
        # Mettre à jour le statut en base
        rj = (
            db.query(models.ReportJob)
            .filter(models.ReportJob.params.op("->>")('"celery_task_id"') == job_id)
            .first()
        )
        
        if rj:
            rj.status = "cancelled"
            from datetime import UTC, datetime
            rj.finished_at = datetime.now(UTC)
            db.add(rj)
            db.commit()
        
        return {"message": f"Job {job_id} annulé avec succès"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'annulation: {str(e)}")


@router.get("/queues/status", response_model=None)
def queue_status(current_user: User = Depends(get_current_user)) -> dict:
    """Statut des queues Celery."""
    require_admin(current_user)
    
    if not CELERY_AVAILABLE:
        return {"error": "Celery non disponible", "queues": []}
    
    try:
        from backend.app.core.celery_app import celery_app
        
        # Inspection des workers actifs
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active() or {}
        stats = inspect.stats() or {}
        
        queue_info = []
        for worker, tasks in active_tasks.items():
            queue_info.append({
                "worker": worker,
                "active_tasks": len(tasks),
                "stats": stats.get(worker, {})
            })
        
        return {
            "celery_available": True,
            "workers": queue_info,
            "total_active_tasks": sum(len(tasks) for tasks in active_tasks.values())
        }
        
    except Exception as e:
        return {"error": f"Erreur inspection Celery: {str(e)}", "queues": []}
