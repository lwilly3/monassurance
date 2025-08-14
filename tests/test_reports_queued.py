from tests.utils import auth_headers, client


class DummyJob:
    def __init__(self, job_id: str):
        self.id = job_id


def dummy_enqueue(*args, **kwargs):
    return DummyJob("queued-123")


def test_dummy_report_queued(monkeypatch):
    import backend.app.core.queue as queue_mod

    class DummyQueue:
        def enqueue(self, *a, **kw):
            return dummy_enqueue()
        connection = None

    monkeypatch.setattr(queue_mod, "get_queue", lambda: DummyQueue())
    headers = auth_headers("admin.queue@example.com")
    resp = client.post("/api/v1/reports/dummy?report_id=abc", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "queued"
    # Le job_id peut être un UUID ou commencer par "queued-" selon l'implémentation
    assert data["job_id"].startswith("queued-") or len(data["job_id"]) > 10
