import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.db import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # Gestion du hash des mots de passe

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un access token JWT court-terme.

    subject: identifiant (email) de l'utilisateur.
    expires_delta: durée personnalisée sinon valeur config.
    """
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond au hash stocké."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash sécurisé (bcrypt) du mot de passe utilisateur."""
    return pwd_context.hash(password)

def decode_token(token: str) -> Optional[str]:
    """Décode un JWT et retourne le subject ou None si invalide/expiré."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None

def _hash_token(token: str) -> str:
    """Hash SHA-256 d'un refresh token (stockage en base sans original)."""
    return hashlib.sha256(token.encode()).hexdigest()

def create_refresh_token(
    subject: str,
    db: Session,
    *,
    device_label: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> str:
    """Crée un refresh token aléatoire (retourne la valeur en clair) et enregistre son hash.
    Durée: 30 jours. La rotation est gérée lors de l'utilisation.

    Permet d'enregistrer des métadonnées de device (liste des appareils).
    """
    plain = f"rt_{uuid4().hex}"
    token_hash = _hash_token(plain)
    user = db.query(models.User).filter(models.User.email == subject).first()
    if user is None:
        # Pas d'utilisateur correspondant: on ne crée pas de token
        return ""
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    db_token = models.RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        device_label=device_label,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(db_token)
    db.commit()
    return plain

def revoke_refresh_token(token: str, db: Session) -> None:
    """Révocation explicite d'un refresh token (marque revoked_at)."""
    token_hash = _hash_token(token)
    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token_hash == token_hash, models.RefreshToken.revoked_at.is_(None)).first()
    if db_token:
        db_token.revoked_at = datetime.now(timezone.utc)
        db.commit()

def revoke_all_refresh_tokens(user_id: int, db: Session) -> int:
    """Révoque tous les refresh tokens actifs d'un utilisateur. Retourne le nombre révoqué."""
    now = datetime.now(timezone.utc)
    q = db.query(models.RefreshToken).filter(models.RefreshToken.user_id == user_id, models.RefreshToken.revoked_at.is_(None))
    count = 0
    for t in q.all():
        t.revoked_at = now
        count += 1
    if count:
        db.commit()
    return count

def use_refresh_token(token: str, db: Session) -> Optional[str]:
    """Consomme un refresh token: vérifie validité, révoque l'ancien et retourne le subject.
    Retourne None si invalide ou expiré."""
    token_hash = _hash_token(token)
    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token_hash == token_hash).first()
    if not db_token:
        return None
    # Normalize datetimes to timezone-aware UTC
    now_utc = datetime.now(timezone.utc)
    expires_at = db_token.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    revoked_at = db_token.revoked_at
    if revoked_at and revoked_at.tzinfo is None:
        revoked_at = revoked_at.replace(tzinfo=timezone.utc)
    if revoked_at or (expires_at and expires_at < now_utc):
        return None
    user = db.query(models.User).filter(models.User.id == db_token.user_id).first()
    # rotate old token (mark revoked)
    db_token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return user.email if user else None
