from tests.utils import auth_headers, client


def test_dummy_report_inline_fallback():
    headers = auth_headers("admin.report@example.com")
    resp = client.post("/api/v1/reports/dummy?report_id=rep123", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Sans Redis lancé dans l'environnement de tests => fallback inline
    assert body["job_id"] == "inline"
    assert body["status"] in {"completed", "queued"}
