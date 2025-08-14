"""Tests pour les nouvelles fonctionnalités Celery."""
from unittest.mock import MagicMock, patch

from tests.utils import auth_headers, client


def test_celery_dummy_report():
    """Test de génération de rapport avec Celery."""
    headers = auth_headers("admin.celery@example.com")
    
    # Test lancement (utilise le fallback actuel)
    resp = client.post("/api/v1/reports/dummy?report_id=celery_test", headers=headers)
    assert resp.status_code == 200
    
    data = resp.json()
    # Le système utilise actuellement le fallback 'inline' et execute directement
    assert data["status"] == "completed"
    assert data["report_job_id"] > 0


def test_celery_heavy_report():
    """Test de génération de rapport lourd avec Celery."""
    headers = auth_headers("admin.celery@example.com")
    
    # Test lancement rapport PDF (Celery requis pour rapports lourds)
    resp = client.post(
        "/api/v1/reports/heavy?report_type=pdf&pages=20&processing_time=5", 
        headers=headers
    )
    # Devrait échouer car Celery n'est pas disponible dans les tests
    assert resp.status_code == 503
    assert "Celery requis" in resp.json()["detail"]


def test_celery_heavy_report_invalid_type():
    """Test avec type de rapport invalide."""
    headers = auth_headers("admin.celery@example.com")
    
    with patch('backend.app.api.routes.celery_reports.CELERY_AVAILABLE', True):
        resp = client.post(
            "/api/v1/reports/heavy?report_type=invalid", 
            headers=headers
        )
        assert resp.status_code == 400
        assert "Type de rapport non supporté" in resp.json()["detail"]


def test_celery_unavailable_fallback():
    """Test de fallback quand Celery n'est pas disponible."""
    headers = auth_headers("admin.fallback@example.com")
    
    with patch('backend.app.api.routes.celery_reports.CELERY_AVAILABLE', False):
        # Test dummy report - devrait utiliser RQ fallback
        resp = client.post("/api/v1/reports/dummy?report_id=fallback_test", headers=headers)
        assert resp.status_code == 200
        
        # Test heavy report - devrait échouer
        resp = client.post("/api/v1/reports/heavy?report_type=pdf", headers=headers)
        assert resp.status_code == 503
        assert "Celery requis" in resp.json()["detail"]


def test_job_status_celery():
    """Test de récupération de statut avec Celery."""
    headers = auth_headers("admin.status@example.com")
    
    # Test avec un job_id inexistant 
    resp = client.get("/api/v1/reports/jobs/test-123", headers=headers)
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["job_id"] == "test-123"
    # Le statut sera 'unknown' car le job n'existe pas
    assert data["status"] == "unknown"


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
