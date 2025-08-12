from tests.utils import auth_headers, client


def test_job_status_inline():
    headers = auth_headers("admin.report2@example.com")
    # Lancement inline (pas de Redis) => job_id inline immédiat
    r = client.post("/api/v1/reports/dummy?report_id=j1", headers=headers)
    assert r.status_code == 200
    job_id = r.json()["job_id"]
    s = client.get(f"/api/v1/reports/jobs/{job_id}", headers=headers)
    assert s.status_code == 200
    assert s.json()["status"] in {"completed", "queued"}
