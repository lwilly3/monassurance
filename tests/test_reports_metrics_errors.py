from tests.utils import auth_headers, client


def test_metrics_error_counter(monkeypatch):
    headers = auth_headers("metrics.error@example.com")
    from backend.app.services import report_tasks
    # Monkeypatch datetime.now pour provoquer une exception dans le bloc try
    class FakeDateTime:
        @staticmethod
        def now(tz):  # noqa: ANN001
            raise RuntimeError("boom")

    original_datetime = report_tasks.datetime
    report_tasks.datetime = FakeDateTime  # type: ignore
    try:
        r = client.post("/api/v1/reports/dummy?report_id=err1", headers=headers)
        assert r.status_code == 500
    finally:
        report_tasks.datetime = original_datetime  # type: ignore

    m = client.get("/metrics")
    if m.status_code == 404:
        return
    text = m.text
    # Vérifier qu'un compteur error est apparu
    assert "report_jobs_total{job_type=\"dummy\",status=\"error\"}" in text
