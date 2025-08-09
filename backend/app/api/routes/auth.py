"""Endpoints d'authentification: inscription, login, refresh, logout.

Principes:
 - Access token (JWT) courte durée.
 - Refresh token stocké hashé en base, rotation à chaque usage.
 - Logout = révocation du refresh token passé.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.config import get_settings
from backend.app.core.redis import get_redis
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    use_refresh_token,
    verify_password,
)
from backend.app.db import models
from backend.app.db.session import get_db
from backend.app.schemas.auth import DeviceSession, RefreshRequest, Token
from backend.app.schemas.user import UserCreate, UserLogin, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> models.User:
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
def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    settings = get_settings()
    # Throttle tentatives: IP et compte (email)
    if settings.login_attempts_enabled:
        ip = (request.client.host if request and request.client else "unknown").replace(":", "_")
        email_key = (payload.email or "").lower()
        ip_limit = settings.login_attempts_ip_per_minute
        acct_limit = settings.login_attempts_account_per_minute
        import time
        minute_bucket = int(time.time()) // 60
        def inc(key: str, limit: int) -> bool:
            try:
                r = get_redis()
                k = f"la:{key}:{minute_bucket}"
                cur = r.incr(k)
                if cur == 1:
                    r.expire(k, 65)
                return cur > limit
            except Exception:
                # fallback mémoire local à la fonction (variable statique)
                if not hasattr(inc, "mem"):
                    inc.mem = {}
                prev, cnt = inc.mem.get(key, (minute_bucket, 0))
                if prev != minute_bucket:
                    cnt = 0
                    prev = minute_bucket
                cnt += 1
                inc.mem[key] = (prev, cnt)
                return cnt > limit
        if inc(f"ip:{ip}", ip_limit) or inc(f"acct:{email_key}", acct_limit):
            raise HTTPException(status_code=429, detail="Trop de tentatives de connexion – réessayez plus tard")
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
    access = create_access_token(subject=user.email)
    ua = request.headers.get("user-agent") if request else None
    ip = request.client.host if request and request.client else None
    refresh = create_refresh_token(subject=user.email, db=db, device_label="login", ip_address=ip, user_agent=ua)
    return Token(access_token=access, refresh_token=refresh)

@router.post("/refresh", response_model=Token)
def refresh_token(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)) -> Token:
    subject = use_refresh_token(payload.refresh_token, db=db)
    if not subject:
        raise HTTPException(status_code=401, detail="Refresh token invalide")
    access = create_access_token(subject=subject)
    ua = request.headers.get("user-agent") if request else None
    ip = request.client.host if request and request.client else None
    new_refresh = create_refresh_token(subject=subject, db=db, device_label="refresh", ip_address=ip, user_agent=ua)
    return Token(access_token=access, refresh_token=new_refresh)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> Response:
    revoke_refresh_token(payload.refresh_token, db=db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def revoke(payload: RefreshRequest, db: Session = Depends(get_db)) -> Response:
    """Alias explicite de logout pour révoquer un refresh token.

    N'exige pas d'auth car la preuve de possession du refresh token suffit.
    """
    revoke_refresh_token(payload.refresh_token, db=db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/revoke-all", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def revoke_all(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)) -> Response:
    """Révoque tous les refresh tokens actifs de l'utilisateur courant (logout global)."""
    revoke_all_refresh_tokens(user_id=current_user.id, db=db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/devices", response_model=list[DeviceSession])
def list_devices(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.RefreshToken]:
    """Liste les sessions d'appareils (refresh tokens actifs) de l'utilisateur courant."""
    now_utc = datetime.now(timezone.utc)
    tokens = (
        db.query(models.RefreshToken)
        .filter(
            models.RefreshToken.user_id == current_user.id,
            models.RefreshToken.revoked_at.is_(None),
            models.RefreshToken.expires_at > now_utc,
        )
        .order_by(models.RefreshToken.issued_at.desc())
        .all()
    )
    return tokens


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def revoke_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> Response:
    """Révoque un appareil (refresh token) par id, si appartenant à l'utilisateur courant."""
    token = (
        db.query(models.RefreshToken)
        .filter(
            models.RefreshToken.id == device_id,
            models.RefreshToken.user_id == current_user.id,
            models.RefreshToken.revoked_at.is_(None),
        )
        .first()
    )
    if not token:
        raise HTTPException(status_code=404, detail="Appareil introuvable")
    token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
