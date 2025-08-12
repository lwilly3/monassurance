"""Tâches de génération de rapports (squelettes).

Pour un vrai usage: implémenter génération PDF / Excel & stockage via storage_provider.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.core.queue import task

try:  # pragma: no cover
    from prometheus_client import Counter, Gauge
    REPORT_JOBS_TOTAL = Counter("report_jobs_total", "Total des jobs rapports", ["job_type", "status"])
    REPORT_JOBS_MODE = Counter("report_jobs_mode_total", "Jobs rapports par mode d'exécution", ["job_type", "mode"])  # mode = inline|queued
    REPORT_JOBS_ACTIVE = Gauge("report_jobs_active", "Jobs rapports en cours", ["job_type"])
except Exception:  # pragma: no cover
    REPORT_JOBS_TOTAL = None  # type: ignore
    REPORT_JOBS_MODE = None  # type: ignore
    REPORT_JOBS_ACTIVE = None  # type: ignore


def _generate_dummy_report_impl(report_id: str) -> dict[str, Any]:
    job_type = "dummy"
    if REPORT_JOBS_ACTIVE:
        REPORT_JOBS_ACTIVE.labels(job_type).inc()
    try:
        now = datetime.now(UTC).isoformat()
        result = {"report_id": report_id, "generated_at": now, "status": "ok"}
        if REPORT_JOBS_TOTAL:
            REPORT_JOBS_TOTAL.labels(job_type, "success").inc()
        # Le mode sera renseigné dans le décorateur selon l'exécution (inline vs queued)
        return result
    except Exception:  # pragma: no cover
        if REPORT_JOBS_TOTAL:
            REPORT_JOBS_TOTAL.labels(job_type, "error").inc()
        raise
    finally:
        if REPORT_JOBS_ACTIVE:
            REPORT_JOBS_ACTIVE.labels(job_type).dec()

# Décoré séparément pour exposer l'implémentation interne aux tests
generate_dummy_report = task(_generate_dummy_report_impl)
generate_dummy_report.impl = _generate_dummy_report_impl  # type: ignore[attr-defined]
