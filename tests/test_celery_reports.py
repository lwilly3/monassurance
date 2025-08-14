"""Tests pour les nouvelles fonctionnalités Celery."""
from unittest.mock import MagicMock, patch

from tests.utils import auth_headers, client


def test_celery_dummy_report():
    """Test de génération de rapport avec Celery."""
    headers = auth_headers("admin.celery@example.com")
    
    with patch('backend.app.api.routes.celery_reports.CELERY_AVAILABLE', True):
        with patch('backend.app.services.celery_report_tasks.generate_dummy_report') as mock_task:
            # Mock de la tâche Celery
            mock_result = MagicMock()
            mock_result.id = "celery-task-123"
            mock_task.delay.return_value = mock_result
            
            # Test lancement
            resp = client.post("/api/v1/reports/dummy?report_id=celery_test", headers=headers)
            assert resp.status_code == 200
            
            data = resp.json()
            assert data["job_id"] == "celery-task-123"
            assert data["status"] == "queued"
            assert data["report_job_id"] > 0


def test_celery_heavy_report():
    """Test de génération de rapport lourd avec Celery."""
    headers = auth_headers("admin.celery@example.com")
    
    with patch('backend.app.api.routes.celery_reports.CELERY_AVAILABLE', True):
        with patch('backend.app.services.celery_report_tasks.generate_heavy_report') as mock_task:
            mock_result = MagicMock()
            mock_result.id = "heavy-task-456"
            mock_task.delay.return_value = mock_result
            
            # Test lancement rapport PDF
            resp = client.post(
                "/api/v1/reports/heavy?report_type=pdf&pages=20&processing_time=5", 
                headers=headers
            )
            assert resp.status_code == 200
            
            data = resp.json()
            assert data["job_id"] == "heavy-task-456"
            assert data["status"] == "queued"


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
    
    with patch('backend.app.api.routes.celery_reports.CELERY_AVAILABLE', True):
        with patch('backend.app.services.celery_report_tasks.get_task_status') as mock_status:
            mock_status.return_value = {
                "task_id": "test-123",
                "state": "SUCCESS", 
                "status": "finished",
                "result": {"report_id": "test", "status": "success"}
            }
            
            resp = client.get("/api/v1/reports/jobs/test-123", headers=headers)
            assert resp.status_code == 200
            
            data = resp.json()
            assert data["job_id"] == "test-123"
            assert data["status"] == "finished"


def test_cancel_job_celery():
    """Test d'annulation de job avec Celery."""
    headers = auth_headers("admin.cancel@example.com")
    
    with patch('backend.app.api.routes.celery_reports.CELERY_AVAILABLE', True):
        with patch('celery.result.AsyncResult') as mock_result:
            mock_instance = MagicMock()
            mock_result.return_value = mock_instance
            
            resp = client.delete("/api/v1/reports/jobs/cancel-test-123", headers=headers)
            assert resp.status_code == 200
            
            data = resp.json()
            assert "annulé avec succès" in data["message"]
            mock_instance.revoke.assert_called_once_with(terminate=True)


def test_queue_status():
    """Test du statut des queues Celery."""
    headers = auth_headers("admin.queue@example.com")
    
    with patch('backend.app.api.routes.celery_reports.CELERY_AVAILABLE', True):
        with patch('backend.app.core.celery_app.celery_app.control.inspect') as mock_inspect:
            mock_inspect_instance = MagicMock()
            mock_inspect.return_value = mock_inspect_instance
            mock_inspect_instance.active.return_value = {
                "celery@worker1": [{"id": "task1"}],
                "celery@worker2": []
            }
            mock_inspect_instance.stats.return_value = {
                "celery@worker1": {"total": {"tasks.dummy": 10}}
            }
            
            resp = client.get("/api/v1/reports/queues/status", headers=headers)
            assert resp.status_code == 200
            
            data = resp.json()
            assert data["celery_available"] is True
            assert data["total_active_tasks"] == 1
            assert len(data["workers"]) == 2


def test_list_jobs():
    """Test de listage des jobs."""
    headers = auth_headers("admin.list@example.com")
    
    # Test sans filtre
    resp = client.get("/api/v1/reports/jobs", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    
    # Test avec filtre de statut
    resp = client.get("/api/v1/reports/jobs?status=completed&limit=10", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
