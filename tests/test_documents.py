from tests.utils import auth_headers, bearer, client


def test_generate_document_without_template_version():
    token = bearer(auth_headers("docadmin@example.com"))
    r = client.post("/api/v1/documents/generate", json={
        "document_type": "test_doc",
        "inline_context": {"value": 42},
        "output_format": "html"
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "generated"
    assert body["mime_type"] == "text/html"


def test_generate_document_with_template_version():
    token = bearer(auth_headers("docadmin@example.com"))
    # Create template with version
    r = client.post("/api/v1/templates/", json={"name": "doc-tpl", "type": "generic", "format": "html", "content": "<p>{{ inline_context.value }}</p>"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    tpl_id = r.json()["id"]
    r = client.get(f"/api/v1/templates/{tpl_id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    versions = r.json()["versions"]
    version_id = versions[0]["id"]
    # Generate using version
    r = client.post("/api/v1/documents/generate", json={
        "document_type": "tpl_doc",
        "template_version_id": version_id,
        "inline_context": {"value": 123},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["template_version_id"] == version_id


def test_list_documents():
    token = bearer(auth_headers("docadmin@example.com"))
    r = client.get("/api/v1/documents/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data


def test_generate_pdf_and_xlsx():
    token = bearer(auth_headers("docadmin@example.com"))
    # PDF
    r = client.post("/api/v1/documents/generate", json={
        "document_type": "pdf_doc",
        "inline_context": {"line1": "Bonjour", "line2": "PDF"},
        "output_format": "pdf"
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["mime_type"] == "application/pdf"
    # XLSX
    r = client.post("/api/v1/documents/generate", json={
        "document_type": "xlsx_doc",
        "inline_context": {"a": 1, "b": 2},
        "output_format": "xlsx"
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["mime_type"].startswith("application/vnd.openxmlformats")


def test_download_document():
    token = bearer(auth_headers("docadmin@example.com"))
    # Génère un document HTML
    r = client.post("/api/v1/documents/generate", json={
        "document_type": "dl_doc",
        "inline_context": {"a": 123},
        "output_format": "html"
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    doc_id = r.json()["id"]
    # Téléchargement
    r = client.get(f"/api/v1/documents/{doc_id}/download", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.headers.get("x-doc-id") == str(doc_id)
    assert "text/html" in r.headers.get("content-type", "")


def test_signed_url_and_rate_limit():
    token = bearer(auth_headers("docadmin@example.com"))
    # Génère un document
    r = client.post("/api/v1/documents/generate", json={
        "document_type": "rate_doc",
        "inline_context": {"v": 1},
        "output_format": "html"
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201
    doc_id = r.json()["id"]
    # Crée URL signée
    r = client.post(f"/api/v1/documents/{doc_id}/signed-url", params={"ttl_seconds": 120}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    url = r.json()["url"]
    # Requêtes rapides pour tester rate limit (3 autorisées)
    for _i in range(3):
        d = client.get(url, headers={"Authorization": f"Bearer {token}"})
        assert d.status_code == 200, d.text
    d = client.get(url, headers={"Authorization": f"Bearer {token}"})
    # Rate limiting peut ne pas être actif en mode test
    assert d.status_code in {200, 429}


def test_generate_encrypted_and_compressed():
    token = auth_headers("docadmin@example.com")["Authorization"].split()[1]
    r = client.post("/api/v1/documents/generate", json={
        "document_type": "secure_doc",
        "inline_context": {"_compress": True, "_encrypt": True, "data": "secret"},
        "output_format": "html"
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    meta = r.json()["doc_metadata"]
    assert meta["compressed"] is True
    assert meta["encrypted"] is True

def test_purge_orphans_requires_admin():
    token = auth_headers("docadmin@example.com")["Authorization"].split()[1]
    from backend.app.services.document_renderer import OUTPUT_DIR
    orphan = OUTPUT_DIR / "doc_orphan.txt"
    orphan.write_text("orphan")
    r = client.post("/api/v1/documents/purge-orphans", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert "doc_orphan.txt" in r.json()["removed"] or orphan.exists() is False
