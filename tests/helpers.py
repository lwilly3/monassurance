from backend.app.core.security import get_password_hash
from backend.app.db import models
from backend.app.db.session import SessionLocal


def create_user(email: str, role: models.UserRole = models.UserRole.ADMIN, full_name: str = "User") -> models.User:
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        return user
    user = models.User(email=email, full_name=full_name, hashed_password=get_password_hash("pass"), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
