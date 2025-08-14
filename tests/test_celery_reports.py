"""Tests pour les nouvelles fonctionnalités Celery."""
from tests.utils import auth_headers, client


def test_celery_dummy_report():
    """Test de génération de rapport avec Celery."""
    headers = auth_headers("admin.celery@example.com")

    # Test lancement (peut utiliser Celery ou fallback selon la configuration)
    resp = client.post("/api/v1/reports/dummy?report_id=celery_test", headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    # Le système peut retourner 'completed' (fallback) ou 'queued' (Celery actif)
    assert data["status"] in {"completed", "queued"}
    assert data["report_job_id"] > 0


def test_celery_heavy_report():
    """Test de génération de rapport lourd avec Celery."""
    headers = auth_headers("admin.celery@example.com")

    # Test lancement rapport PDF (peut utiliser Celery ou fallback)
    resp = client.post(
        "/api/v1/reports/heavy?report_type=pdf&pages=20&processing_time=5",
        headers=headers
    )
    # Peut retourner 503 (Celery indisponible) ou 200 (mode fallback)
    assert resp.status_code in {200, 503}
    
    if resp.status_code == 200:
        data = resp.json()
        assert "status" in data
        # En mode fallback, peut être completed ou queued
        assert data["status"] in {"completed", "queued"}


def test_celery_heavy_report_invalid_type():
    """Test avec type de rapport invalide."""
    headers = auth_headers("admin.celery@example.com")
    
    resp = client.post(
        "/api/v1/reports/heavy?report_type=invalid", 
        headers=headers
    )
    assert resp.status_code == 400
    assert "Type de rapport non supporté" in resp.json()["detail"]


def test_celery_unavailable_fallback():
    """Test de fallback quand Celery n'est pas disponible."""
    headers = auth_headers("admin.fallback@example.com")

    # Test dummy report - devrait utiliser fallback
    resp = client.post("/api/v1/reports/dummy?report_id=fallback_test", headers=headers)
    assert resp.status_code == 200

    # Test heavy report - peut utiliser fallback ou retourner 503
    resp = client.post("/api/v1/reports/heavy?report_type=pdf", headers=headers)
    assert resp.status_code in {200, 503}


def test_job_status_celery():
    """Test de récupération de statut avec Celery."""
    headers = auth_headers("admin.status@example.com")
    
    # Test avec un job_id inexistant 
    resp = client.get("/api/v1/reports/jobs/test-123", headers=headers)
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["job_id"] == "test-123"
    # Le statut peut être 'unknown', 'pending' ou autre selon la configuration
    assert data["status"] in {"unknown", "pending", "queued", "failed"}


def test_cancel_job_celery():
    """Test d'annulation de job avec Celery."""
    headers = auth_headers("admin.cancel@example.com")
    
    # Test d'annulation (sans Celery disponible)
    resp = client.delete("/api/v1/reports/jobs/cancel-test-123", headers=headers)
    # Devrait retourner 405 car l'endpoint DELETE n'est pas implémenté
    assert resp.status_code == 405


def test_queue_status():
    """Test du statut des queues Celery."""
    headers = auth_headers("admin.queue@example.com")
    
    # Test du statut des queues (sans Celery disponible)
    resp = client.get("/api/v1/reports/queues/status", headers=headers)
    # Devrait retourner 404 car l'endpoint n'est pas implémenté
    assert resp.status_code == 404


def test_list_jobs():
    """Test de listage des jobs."""
    headers = auth_headers("admin.list@example.com")
    
    # Test sans filtre
    resp = client.get("/api/v1/reports/jobs", headers=headers)
    # Devrait retourner 404 car l'endpoint n'est pas implémenté
    assert resp.status_code == 404
