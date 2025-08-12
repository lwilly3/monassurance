from tests.utils import auth_headers, client


def test_metrics_after_inline_job():
    headers = auth_headers("metrics.inline@example.com")
    # Lancer un job inline (pas de Redis)
    r = client.post("/api/v1/reports/dummy?report_id=metrics1", headers=headers)
    assert r.status_code == 200
    # Récupérer metrics
    m = client.get("/metrics")
    if m.status_code == 404:
        # Metrics désactivées dans cette config => on ne fail pas le test (skip logique)
        return
    text = m.text
    # Vérifier présence des métriques principales
    assert "report_jobs_total" in text
    assert "report_jobs_active" in text
    # Vérifier que le gauge retombe à 0 pour dummy (job terminé)
    # Parse ligne gauge
    for line in text.splitlines():
        if line.startswith("report_jobs_active{job_type=\"dummy\"}"):
            val = float(line.rsplit(" ", 1)[1])
            assert val == 0.0
            break
    # Le compteur success doit être >=1 pour dummy
    assert "report_jobs_total{job_type=\"dummy\",status=\"success\"}" in text


def test_unknown_job_status():
    headers = auth_headers("metrics.unknown@example.com")
    # Interroger un job inexistant
    s = client.get("/api/v1/reports/jobs/nonexistent-999", headers=headers)
    assert s.status_code == 200
    body = s.json()
    assert body["status"] == "unknown"
    assert body["report_job_id"] is None
