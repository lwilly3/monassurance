"""Endpoints d'authentification: inscription, login, refresh, logout.

Principes:
 - Access token (JWT) courte durée.
 - Refresh token stocké hashé en base, rotation à chaque usage.
 - Logout = révocation du refresh token passé.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    revoke_refresh_token,
    use_refresh_token,
    verify_password,
)
from backend.app.db import models
from backend.app.db.session import get_db
from backend.app.schemas.auth import RefreshRequest, Token
from backend.app.schemas.user import UserCreate, UserLogin, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role or models.UserRole.AGENT,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
    access = create_access_token(subject=user.email)
    refresh = create_refresh_token(subject=user.email, db=db)
    return Token(access_token=access, refresh_token=refresh)

@router.post("/refresh", response_model=Token)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    subject = use_refresh_token(payload.refresh_token, db=db)
    if not subject:
        raise HTTPException(status_code=401, detail="Refresh token invalide")
    access = create_access_token(subject=subject)
    new_refresh = create_refresh_token(subject=subject, db=db)
    return Token(access_token=access, refresh_token=new_refresh)

@router.post("/logout", status_code=204)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    revoke_refresh_token(payload.refresh_token, db=db)
    return None
