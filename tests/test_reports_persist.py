from tests.utils import auth_headers, client


def test_report_job_inline_persist():
    headers = auth_headers("admin.persist@example.com")
    r = client.post("/api/v1/reports/dummy?report_id=persist1", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["report_job_id"] > 0
    # Status inline
    s = client.get(f"/api/v1/reports/jobs/{data['job_id']}", headers=headers)
    assert s.status_code == 200
    body = s.json()
    assert body["status"] == "completed"
    assert body["report_job_id"] == data["report_job_id"]
