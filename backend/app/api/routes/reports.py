from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db import models
from backend.app.db.models.user import User, UserRole
from backend.app.schemas.report_jobs import (
    ReportJobLaunchResponse,
    ReportJobStatusResponse,
)
from backend.app.services.report_tasks import generate_dummy_report

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


@router.get("/jobs/{job_id}", response_model=ReportJobStatusResponse)
def job_status(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ReportJobStatusResponse:
    require_admin(current_user)
    q = get_queue()
    if job_id == "inline":
        rj = (
            db.query(models.ReportJob)
            .filter(models.ReportJob.status == "completed", models.ReportJob.job_type == "dummy")
            .order_by(models.ReportJob.id.desc())
            .first()
        )
        return ReportJobStatusResponse(job_id=job_id, status="completed", report_job_id=rj.id if rj else None)
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
        return ReportJobStatusResponse(job_id=job.id, status=job.get_status() or "unknown", report_job_id=rj.id if rj else None)
    except Exception:  # pragma: no cover
        return ReportJobStatusResponse(job_id=job_id, status="unknown", report_job_id=None)
