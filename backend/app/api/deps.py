"""Dépendances FastAPI partagées (auth & DB).

Expose helpers:
 - get_db_session: alias de get_db
 - get_current_user: extrait le user depuis JWT
 - require_role: fabrique un dépendance de contrôle de rôle
"""
from collections.abc import Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.security import decode_token
from backend.app.db import models
from backend.app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db_session)) -> models.User:
    subject = decode_token(token)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")
    user = db.query(models.User).filter(models.User.email == subject).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")
    return user

def require_role(required_roles: list[models.UserRole]) -> Callable[[models.User], models.User]:
    def checker(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in required_roles:
            raise HTTPException(status_code=403, detail="Accès refusé")
        return user
    return checker
