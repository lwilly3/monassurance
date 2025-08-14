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
from backend.app.services.report_tasks import generate_dummy_report

# Support Celery hybride
try:
    from backend.app.services.celery_report_tasks import generate_dummy_report as celery_generate_dummy_report
    from backend.app.services.celery_report_tasks import generate_heavy_report, get_task_status
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

try:  # pragma: no cover
    from rq.job import Job as RQJob
except Exception:  # pragma: no cover
    RQJob = None  # type: ignore
if TYPE_CHECKING:  # pragma: no cover
    from rq.job import Job as JobType  # real type for type-checkers
else:  # pragma: no cover
    class JobType:  # minimal runtime stub for tests monkeypatch
        fetch = None  # type: ignore
from backend.app.core.queue import get_queue

router = APIRouter(prefix="/reports", tags=["reports"])  # endpoints de génération de rapports


def require_admin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Réservé admin")


@router.post("/dummy", response_model=ReportJobLaunchResponse)
def launch_dummy(report_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ReportJobLaunchResponse:
    require_admin(current_user)
    # Créer enregistrement report_jobs (status pending)
    rj = models.ReportJob(job_type="dummy", status="pending", params={"report_id": report_id})
    db.add(rj)
    db.commit()
    db.refresh(rj)
    
    # Utiliser Celery si disponible, sinon fallback RQ
    if CELERY_AVAILABLE:
        try:
            task = celery_generate_dummy_report.delay(report_id, rj.id)
            rj.status = "queued"
            rj.params = {**(rj.params or {}), "celery_task_id": task.id}
            db.add(rj)
            db.commit()
            return ReportJobLaunchResponse(job_id=task.id, status="queued", report_job_id=rj.id)
        except Exception:
            # Fallback vers RQ si Celery échoue (pas de Redis par exemple)
            pass
    
    # Fallback RQ (ancien système) ou si Celery a échoué
    job = generate_dummy_report.delay(report_id)  # type: ignore[attr-defined]
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
    try:
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
    except Exception:
        # Si Celery échoue (pas de Redis), nettoyer et retourner erreur 503
        db.delete(rj)
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Service indisponible - Celery requis pour les rapports lourds (Redis non disponible)"
        )


@router.get("/jobs/{job_id}", response_model=ReportJobStatusResponse)
def job_status(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ReportJobStatusResponse:
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
                report_job_id=rj.id if rj else None
            )
            
        except Exception:
            return ReportJobStatusResponse(job_id=job_id, status="unknown", report_job_id=None)
    
    else:
        # Fallback vers RQ (ancien système)
        q = get_queue()
        if q is None or RQJob is None:
            return ReportJobStatusResponse(job_id=job_id, status="unknown", report_job_id=None)
        
        try:
            assert RQJob is not None
            assert q is not None
            job_cls = RQJob if RQJob is not None else JobType  # fallback pour monkeypatch tests
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
        except Exception:  # pragma: no cover
            return ReportJobStatusResponse(job_id=job_id, status="unknown", report_job_id=None)
