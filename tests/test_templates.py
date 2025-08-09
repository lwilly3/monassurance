import uuid
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.db import models
from backend.app.core.security import get_password_hash

client = TestClient(app)


def create_user(db, email: str, role=models.UserRole.ADMIN):
    user = models.User(email=email, full_name="Admin", hashed_password=get_password_hash("pass"), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_headers(email: str = "tpladmin@example.com"):
    db = SessionLocal()
    existing = db.query(models.User).filter(models.User.email == email).first()
    if not existing:
        create_user(db, email)
    # login
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "pass"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_template_crud_flow():
    headers = get_auth_headers()
    name = "tpl-" + str(uuid.uuid4())
    # create
    resp = client.post("/api/v1/templates/", json={"name": name, "type": "policy", "format": "html", "content": "<h1>Hi</h1>"}, headers=headers)
    assert resp.status_code == 201, resp.text
    tpl = resp.json()
    tpl_id = tpl["id"]
    # list
    resp = client.get("/api/v1/templates/", headers=headers)
    assert resp.status_code == 200
    assert any(t["id"] == tpl_id for t in resp.json())
    # get detail with versions
    resp = client.get(f"/api/v1/templates/{tpl_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body.get("versions", [])) == 1
    # add version
    resp = client.post(f"/api/v1/templates/{tpl_id}/versions", json={"content": "<h1>Hi v2</h1>"}, headers=headers)
    assert resp.status_code == 201, resp.text
    v2 = resp.json()
    assert v2["version"] == 2
    # fetch v2
    resp = client.get(f"/api/v1/templates/{tpl_id}/versions/2", headers=headers)
    assert resp.status_code == 200
    # patch template
    resp = client.patch(f"/api/v1/templates/{tpl_id}", json={"is_active": False}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False
    # delete
    resp = client.delete(f"/api/v1/templates/{tpl_id}", headers=headers)
    assert resp.status_code == 204
    # confirm gone
    resp = client.get(f"/api/v1/templates/{tpl_id}", headers=headers)
    assert resp.status_code == 404
