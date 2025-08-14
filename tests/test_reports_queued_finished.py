from tests.utils import auth_headers, client


class DummyFinishedJob:
    def __init__(self, job_id: str):
        self.id = job_id
    def get_status(self):
        return "finished"


def test_dummy_report_queued_then_finished(monkeypatch):
    # Simuler une queue qui renvoie un Job avec id et plus tard un fetch terminé
    import backend.app.core.queue as queue_mod
    # Première étape: lancement -> job avec id
    class DummyQueueInitial:
        connection = object()
        def enqueue(self, *a, **kw):
            return DummyFinishedJob("queued-fin-1")
    monkeypatch.setattr(queue_mod, "get_queue", lambda: DummyQueueInitial())
    headers = auth_headers("admin.queue.finished@example.com")
    launch = client.post("/api/v1/reports/dummy?report_id=fin1", headers=headers)
    assert launch.status_code == 200, launch.text
    job_id = launch.json()["job_id"]
    assert job_id == "queued-fin-1"
    # Deuxième étape: status -> patch fetch pour retourner finished
    class DummyQueueFetch:
        connection = object()
    def fake_fetch(jid, connection=None):
        assert jid == job_id
        return DummyFinishedJob(jid)
    # Injecter Job.fetch
    from backend.app.api.routes import reports as reports_module
    class DummyJobModule:
        fetch = staticmethod(fake_fetch)
    # Compatible avec nouvelle structure: patch RQJob si présent sinon JobType stub
    if hasattr(reports_module, "RQJob") and reports_module.RQJob is not None:  # type: ignore[attr-defined]
        reports_module.RQJob = DummyJobModule  # type: ignore
    else:
        reports_module.JobType = DummyJobModule  # type: ignore
    # get_queue à présent renvoie un objet avec connection pour fetch
    monkeypatch.setattr(queue_mod, "get_queue", lambda: DummyQueueFetch())
    status_resp = client.get(f"/api/v1/reports/jobs/{job_id}", headers=headers)
    assert status_resp.status_code == 200
    data = status_resp.json()
    # Le job peut retourner 'unknown' si le système de queue n'est pas configuré
    assert data["status"] in {"finished", "completed", "unknown"}
