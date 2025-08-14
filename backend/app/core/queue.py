"""Initialisation de la file RQ.

Expose get_queue() pour publier des jobs et un décorateur task pour déclarer une tâche.
Fallback: si Redis/RQ indisponible, exécute la fonction inline (mode dégradé tests).
"""
from __future__ import annotations

from functools import lru_cache, wraps
from typing import Any, Callable, Protocol

from backend.app.core.redis import get_redis

try:  # pragma: no cover - import défensif
    import rq
    from rq import Queue as RQQueue
    from rq.job import Job as RQJob
except Exception:  # pragma: no cover
    rq = None  # type: ignore
    RQQueue = None  # type: ignore
    RQJob = None  # type: ignore


class EnqueueCallable(Protocol):  # typing surface minimale pour notre usage
    def enqueue(self, f: Callable[..., Any], *args: Any, **kwargs: Any) -> Any: ...


@lru_cache(maxsize=1)
def get_queue() -> EnqueueCallable | None:
    q: EnqueueCallable | None = None
    if RQQueue is not None:
        try:
            r = get_redis()
            try:
                q = RQQueue("default", connection=r)
            except Exception:  # pragma: no cover
                q = None
        except Exception:  # pragma: no cover
            q = None
    return q


def task(func: Callable[..., Any]) -> Callable[..., Any]:
    """Décorateur simple: si queue dispo -> enqueue, sinon exécute inline.

    Utilisation: my_task.delay(args...)
    """

    @wraps(func)
    def delay_wrapper(*args: Any, **kwargs: Any) -> Any:
        # Import local pour éviter dépendance circulaire au module import
        try:  # pragma: no cover
            from backend.app.services import report_tasks
        except Exception:  # pragma: no cover
            report_tasks = None  # type: ignore

        q = get_queue()
        target = getattr(func, "impl", func)
        job_type = "dummy" if target.__name__.endswith("dummy_report_impl") else "generic"
        if q is None:
            res = target(*args, **kwargs)
            try:  # pragma: no cover
                if report_tasks and getattr(report_tasks, "REPORT_JOBS_MODE", None):
                    report_tasks.REPORT_JOBS_MODE.labels(job_type, "inline").inc()
            except Exception:
                pass
            return res
        try:
            job = q.enqueue(target, *args, **kwargs)
            try:  # pragma: no cover
                if report_tasks and getattr(report_tasks, "REPORT_JOBS_MODE", None):
                    report_tasks.REPORT_JOBS_MODE.labels(job_type, "queued").inc()
            except Exception:
                pass
            return job
        except Exception:  # pragma: no cover
            res = target(*args, **kwargs)
            try:  # pragma: no cover
                if report_tasks and getattr(report_tasks, "REPORT_JOBS_MODE", None):
                    report_tasks.REPORT_JOBS_MODE.labels(job_type, "inline").inc()
            except Exception:
                pass
            return res

    func.delay = delay_wrapper  # type: ignore[attr-defined]
    return func
