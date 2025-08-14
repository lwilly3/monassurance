"""Tests pour les nouvelles fonctionnalités de rapports lourds."""
from tests.utils import auth_headers, client


def test_heavy_report_pdf():
    """Test de génération de rapport PDF lourd."""
    headers = auth_headers("admin.heavy@example.com")
    
    # Test avec Celery indisponible (pas de Redis)
    resp = client.post(
        "/api/v1/reports/heavy?report_type=pdf&pages=20&processing_time=5", 
        headers=headers
    )
    # Devrait échouer car Celery requis pour rapports lourds
    assert resp.status_code == 503
    assert "Celery requis" in resp.json()["detail"]


def test_heavy_report_invalid_type():
    """Test avec type de rapport invalide."""
    headers = auth_headers("admin.heavy@example.com")
    
    resp = client.post(
        "/api/v1/reports/heavy?report_type=invalid", 
        headers=headers
    )
    # Type invalide
    assert resp.status_code == 400
    assert "Type de rapport non supporté" in resp.json()["detail"]


def test_heavy_report_excel():
    """Test de génération de rapport Excel."""
    headers = auth_headers("admin.heavy@example.com")
    
    resp = client.post(
        "/api/v1/reports/heavy?report_type=excel&processing_time=3", 
        headers=headers
    )
    # Devrait échouer car Celery requis
    assert resp.status_code == 503


def test_heavy_report_analysis():
    """Test de génération de rapport d'analyse."""
    headers = auth_headers("admin.heavy@example.com")
    
    resp = client.post(
        "/api/v1/reports/heavy?report_type=analysis&processing_time=15", 
        headers=headers
    )
    # Devrait échouer car Celery requis
    assert resp.status_code == 503
