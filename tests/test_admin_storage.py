from fastapi.testclient import TestClient

from backend.app.core.security import get_password_hash
from backend.app.db import models
from backend.app.db.session import SessionLocal
from backend.app.main import app

client = TestClient(app)


def create_admin(email: str) -> models.User:
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        return user
    user = models.User(email=email, full_name="Admin", hashed_password=get_password_hash("pass"), role=models.UserRole.ADMIN)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(email: str) -> dict[str, str]:
    create_admin(email)
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "pass"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_default_storage_config():
    headers = login("admin.storage@example.com")
    resp = client.get("/api/v1/admin/storage-config", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["backend"] == "local"


def test_update_storage_config_local():
    headers = login("admin.storage2@example.com")
    resp = client.put("/api/v1/admin/storage-config", headers=headers, json={"backend": "local"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["backend"] == "local"


def test_update_storage_config_gdrive_missing_params():
    headers = login("admin.storage3@example.com")
    resp = client.put("/api/v1/admin/storage-config", headers=headers, json={"backend": "google_drive"})
    assert resp.status_code == 400

