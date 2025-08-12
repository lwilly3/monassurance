from __future__ import annotations

from pydantic import BaseModel


class ReportJobLaunchResponse(BaseModel):
    job_id: str
    status: str
    report_job_id: int


class ReportJobStatusResponse(BaseModel):
    job_id: str
    status: str
    report_job_id: int | None = None
