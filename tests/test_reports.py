from tests.utils import auth_headers, client


def test_dummy_report_inline_fallback():
    headers = auth_headers("admin.report@example.com")
    resp = client.post("/api/v1/reports/dummy?report_id=rep123", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Peut retourner "inline" (fallback) ou un UUID (Celery actif)
    assert body["job_id"] == "inline" or len(body["job_id"]) > 10
    assert body["status"] in {"completed", "queued"}
