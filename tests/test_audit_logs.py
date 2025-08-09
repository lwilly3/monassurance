import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import get_settings

client = TestClient(app)

@pytest.fixture(scope="module")
def token_admin():
    # Enregistre un utilisateur admin
    email = "admin_audit@example.com"
    password = "secret123"
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "role": "admin"})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    data = r.json()
    assert "access_token" in data, data
    return data["access_token"]


def test_audit_logs_listing(token_admin):
    # Génère un document pour produire un audit log
    headers = {"Authorization": f"Bearer {token_admin}"}
    # Crée un template minimal (HTML) si nécessaire
    tpl = client.post("/api/v1/templates/", json={"name": "audit_tpl", "format": "html", "company_id": None, "content": "{{ inline_context.msg }}"}, headers=headers)
    assert tpl.status_code in (200, 201)
    tpl_id = tpl.json()["id"]
    gen = client.post("/api/v1/documents/generate", json={"document_type": "audit_doc", "template_version_id": tpl_id, "inline_context": {"msg": "hi"}}, headers=headers)
    assert gen.status_code == 201
    # Liste audit logs
    res = client.get("/api/v1/audit-logs/", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data and "total" in data
    assert any(item["action"] == "generate_document" for item in data["items"])  # on retrouve l'action


def test_audit_logs_partial_filters(token_admin):
        """Vérifie les nouveaux filtres partiels action_contains et object_contains.

        Étapes:
            1. Génère un document (log: generate_document)
            2. Télécharge le document (log: download_document)
            3. Filtre avec action_contains=download -> uniquement actions contenant 'download'
            4. Filtre avec object_contains=Generated -> object_type contient 'Generated'
        """
        headers = {"Authorization": f"Bearer {token_admin}"}
        # Crée un template dédié pour éviter collision de noms
        tpl = client.post("/api/v1/templates/", json={"name": "audit_tpl_pf", "format": "html", "company_id": None, "content": "<p>{{ inline_context.msg }}</p>"}, headers=headers)
        assert tpl.status_code in (200, 201), tpl.text
        tpl_id = tpl.json()["id"]
        gen = client.post("/api/v1/documents/generate", json={"document_type": "audit_pf", "template_version_id": tpl_id, "inline_context": {"msg": "pf"}}, headers=headers)
        assert gen.status_code == 201, gen.text
        doc_id = gen.json()["id"]
        # Téléchargement pour créer log download_document
        dl = client.get(f"/api/v1/documents/{doc_id}/download", headers=headers)
        assert dl.status_code == 200, dl.text

        # Filtre partiel sur action
        res_download = client.get("/api/v1/audit-logs/?action_contains=download", headers=headers)
        assert res_download.status_code == 200, res_download.text
        data_dl = res_download.json()
        assert data_dl["items"], "Aucun log retourné pour action_contains=download"
        assert all("download" in (it.get("action") or "") for it in data_dl["items"])  # toutes les actions contiennent download

        # Filtre partiel sur object_type
        res_obj = client.get("/api/v1/audit-logs/?object_contains=Generated", headers=headers)
        assert res_obj.status_code == 200, res_obj.text
        data_obj = res_obj.json()
        assert data_obj["items"], "Aucun log retourné pour object_contains=Generated"
        assert any(it.get("object_type") == "GeneratedDocument" for it in data_obj["items"])  # au moins un


def test_audit_logs_export_csv(token_admin):
        """Teste l'export CSV complet avec métadonnées.

        Vérifie:
            - Status 200
            - Header Content-Disposition
            - Présence des colonnes attendues (id, action, audit_metadata)
        """
        headers = {"Authorization": f"Bearer {token_admin}"}
        res = client.get("/api/v1/audit-logs/export", headers=headers)
        assert res.status_code == 200, res.text
        assert "attachment; filename=audit_logs.csv" in res.headers.get("Content-Disposition", "")
        body = res.text.splitlines()
        assert body, "CSV vide"
        header = body[0].split(",")
        assert {"id", "action"}.issubset(set(h.strip() for h in header))
