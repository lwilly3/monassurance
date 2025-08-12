from fastapi.testclient import TestClient

from backend.app.core.security import get_password_hash
from backend.app.db import models
from backend.app.db.session import SessionLocal

client = TestClient(__import__("backend.app.main", fromlist=["app"]).app)


def _ensure_user(email: str, role: models.UserRole) -> models.User:
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        return user
    user = models.User(
        email=email,
        full_name=f"{role.name.title()}Test",
        hashed_password=get_password_hash("pass"),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def ensure_admin(email: str) -> models.User:
    return _ensure_user(email, models.UserRole.ADMIN)


def ensure_user(email: str) -> models.User:
    return _ensure_user(email, models.UserRole.USER)


def auth_headers(email: str, role: str | None = None):
    if role == "user":
        ensure_user(email)
    else:
        ensure_admin(email)
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "pass"})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def bearer(headers: dict[str, str]) -> str:
    return headers["Authorization"].split()[1]


def admin_headers(email: str = "admin@example.com") -> dict[str, str]:
    return auth_headers(email)

# Pytest fixture d'email réutilisable (si import via from tests.utils import default_admin_email)
default_admin_email = "admin@example.com"
