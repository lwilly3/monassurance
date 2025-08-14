from tests.utils import auth_headers, client


def test_job_status_unknown_when_redis_down(monkeypatch):
    headers = auth_headers("admin.report2@example.com")

    # Force get_queue à None pour simuler Redis/RQ indisponible
    import backend.app.core.queue as queue_mod

    monkeypatch.setattr(queue_mod, "get_queue", lambda: None)

    # Requête statut avec un job id arbitraire
    resp = client.get("/api/v1/reports/jobs/some-job-id", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    # Peut retourner "unknown" ou "pending" selon l'implémentation
    assert data["status"] in {"unknown", "pending"}
    assert data["report_job_id"] is None
