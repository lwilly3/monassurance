from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.db import models
from backend.app.db.session import SessionLocal
from backend.app.main import app

client = TestClient(app)


def register_and_login(email: str = "user@example.com", password: str = "pass1234"):
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    data = r.json()
    return data["access_token"], data["refresh_token"]


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_company_crud():
    access, _ = register_and_login("admin@example.com")
    # Promote user to admin in DB
    db = SessionLocal()
    u = db.query(models.User).filter(models.User.email == "admin@example.com").first()
    u.role = models.UserRole.ADMIN
    db.commit()
    db.close()
    suffix = uuid4().hex[:6]
    r = client.post("/api/v1/companies", json={"name": f"CompA_{suffix}", "code": f"C{suffix}"}, headers=auth_header(access))
    assert r.status_code == 201, r.text
    comp_id = r.json()["id"]
    r = client.get(f"/api/v1/companies/{comp_id}", headers=auth_header(access))
    assert r.status_code == 200
    r = client.put(f"/api/v1/companies/{comp_id}", json={"api_mode": True}, headers=auth_header(access))
    assert r.status_code == 200
    r = client.delete(f"/api/v1/companies/{comp_id}", headers=auth_header(access))
    assert r.status_code == 204


def test_policy_crud_flow():
    access, _ = register_and_login("agent@example.com")
    # Create client
    r = client.post("/api/v1/clients", json={"first_name": "John", "last_name": "Doe"}, headers=auth_header(access))
    assert r.status_code == 201
    client_id = r.json()["id"]
    # Create company directly in DB for association
    db = SessionLocal()
    unique_suffix = uuid4().hex[:6]
    company = models.Company(name=f"CompTest_{unique_suffix}", code=f"CT{unique_suffix}")
    db.add(company)
    db.commit()
    db.refresh(company)
    db.close()
    # Create policy
    policy_suffix = uuid4().hex[:8]
    r = client.post("/api/v1/policies", json={
        "policy_number": f"P{policy_suffix}",
        "client_id": client_id,
        "company_id": company.id,
        "product_name": "AUTO",
        "premium_amount": 10000,
        "effective_date": "2025-01-01T00:00:00Z",
        "expiry_date": "2026-01-01T00:00:00Z"
    }, headers=auth_header(access))
    assert r.status_code == 201, r.text
    policy_id = r.json()["id"]
    # Update policy
    r = client.put(f"/api/v1/policies/{policy_id}", json={"product_name": "AUTO+"}, headers=auth_header(access))
    assert r.status_code == 200
    # List policies
    r = client.get("/api/v1/policies", headers=auth_header(access))
    assert r.status_code == 200
    # Delete policy
    r = client.delete(f"/api/v1/policies/{policy_id}", headers=auth_header(access))
    assert r.status_code == 204


def test_refresh_and_logout():
    access, refresh = register_and_login("refresh@example.com")
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    new_refresh = r.json()["refresh_token"]
    # logout old refresh (should already be rotated but test revoke path)
    client.post("/api/v1/auth/logout", json={"refresh_token": new_refresh})
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert r.status_code == 401
