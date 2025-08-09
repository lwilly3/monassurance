from __future__ import annotations

"""Endpoints de gestion des documents générés.

Ce module couvre:
 - Génération multi-format (HTML, PDF, XLSX)
 - Signature d'URL avec rotation de clés (kid) et expiration TTL
 - Téléchargement sécurisé avec contrôle RBAC + ownership
 - Rate limiting (Redis + fallback mémoire) pour limiter abus
 - Compression (zlib) & chiffrement (Fernet) optionnels, métadonnées enregistrées
 - Purge de fichiers orphelins sur disque
 - Audit logging systématique (génération, téléchargement, purge)
"""
import base64
import hashlib
import hmac
import time
import zlib
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.config import get_settings
from backend.app.core.redis import get_redis
from backend.app.db import models
from backend.app.db.models.user import User, UserRole
from backend.app.schemas.generated_document import (
    DocumentGenerateRequest,
    GeneratedDocumentList,
    GeneratedDocumentRead,
)
from backend.app.services.document_renderer import OUTPUT_DIR, render_template, store_output

router = APIRouter(prefix="/documents", tags=["documents"])  # Regroupe tous les endpoints liés aux documents

ALLOWED_DOWNLOADS_PER_MINUTE = 3
_mem_counts: dict[str, tuple[int, int]] = {}  # key -> (minute_bucket, count)

def _rate_limit(key: str, limit: int = ALLOWED_DOWNLOADS_PER_MINUTE) -> None:
    """Applique une limite simple de téléchargements par minute.

    Priorise Redis (atomique via INCR/EXPIRE). En cas d'échec (ex: tests sans Redis),
    bascule sur un compteur en mémoire de meilleure effort.
    Lève HTTP 429 si la limite est dépassée.
    """
    minute_bucket = int(time.time()) // 60
    try:
        r = get_redis()
        bucket_key = f"dl:{key}:{minute_bucket}"
        current = r.incr(bucket_key)
        if current == 1:
            r.expire(bucket_key, 65)
        if current > limit:
            raise HTTPException(status_code=429, detail="Trop de téléchargements – réessayez plus tard (redis)")
    except Exception:
        # fallback mémoire (meilleur effort pour tests/offline)
        prev_bucket, count = _mem_counts.get(key, (minute_bucket, 0))
        if prev_bucket != minute_bucket:
            count = 0
            prev_bucket = minute_bucket
        count += 1
        _mem_counts[key] = (prev_bucket, count)
        if count > limit:
            raise HTTPException(status_code=429, detail="Trop de téléchargements – réessayez plus tard")


def can_generate(user: User) -> None:  # Génération permise pour AGENT+
    if user.role not in {UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT}:
        raise HTTPException(status_code=403, detail="Accès refusé")

def can_admin(user: User) -> None:
    if user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise HTTPException(status_code=403, detail="Autorisation requise")

def can_superadmin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Réservé admin")

def _active_key() -> tuple[str, bytes]:
    settings = get_settings()
    kid = settings.signature_active_kid
    secret = settings.signature_keys.get(kid, settings.jwt_secret_key).encode()
    return kid, secret

def _sign(doc_id: int, expires: int) -> str:
    """Calcule signature HMAC (kid.prefixed) pour un doc et timestamp d'expiration."""
    kid, secret = _active_key()
    msg = f"{kid}:{doc_id}:{expires}".encode()
    sig = hmac.new(secret, msg, hashlib.sha256).digest()
    return f"{kid}.{base64.urlsafe_b64encode(sig).decode().rstrip('=')}"

def _verify_signature(doc_id: int, expires: int, signature: str) -> bool:
    """Vérifie signature/expiration d'une URL signée.

    Retourne False si expirée, format invalide ou signature ne correspond pas.
    """
    if time.time() > expires:
        return False
    try:
        kid, sig_part = signature.split('.', 1)
    except ValueError:
        return False
    settings = get_settings()
    secret = settings.signature_keys.get(kid, settings.jwt_secret_key).encode()
    msg = f"{kid}:{doc_id}:{expires}".encode()
    expected_bytes = hmac.new(secret, msg, hashlib.sha256).digest()
    expected = base64.urlsafe_b64encode(expected_bytes).decode().rstrip('=')
    return hmac.compare_digest(expected, sig_part)

@router.post("/generate", response_model=GeneratedDocumentRead, status_code=201)
def generate_document(payload: DocumentGenerateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> models.GeneratedDocument:
    can_generate(current_user)
    template_version = None
    if payload.template_version_id:
        template_version = db.query(models.TemplateVersion).filter(models.TemplateVersion.id == payload.template_version_id).first()
        if not template_version:
            raise HTTPException(status_code=404, detail="Template version introuvable")
    fmt = payload.output_format or (template_version.template.format if template_version and template_version.template and template_version.template.format else "html")  # type: ignore
    if fmt not in {"html", "pdf", "xlsx"}:
        raise HTTPException(status_code=400, detail="Format non supporté")
    content_source = template_version.content if template_version and template_version.content else "{{ inline_context | default('') }}"
    ctx = {"inline_context": payload.inline_context or {}}
    rendered = render_template(content_source, ctx , fmt)  # Production binaire du document
    original_size = len(rendered)
    compress = bool(payload.inline_context and payload.inline_context.get("_compress"))
    encrypt = bool(payload.inline_context and payload.inline_context.get("_encrypt"))
    encryption_key_id = None
    if compress:
        rendered = zlib.compress(rendered)
    if encrypt:
        # Clé déterminée par kid actif pour rotation simplifiée
        kid, secret = _active_key()
        fkey = base64.urlsafe_b64encode(hashlib.sha256(secret).digest()[:32])
        f = Fernet(fkey)
        rendered = f.encrypt(rendered)
        encryption_key_id = kid
    result = store_output(rendered, fmt)
    doc = models.GeneratedDocument(
        document_type=payload.document_type,
        policy_id=payload.policy_id,
        template_version_id=payload.template_version_id,
        file_path=result.file_path,
        mime_type=result.mime_type,
        size_bytes=result.size,
        status="generated",
        doc_metadata={
            "checksum": result.checksum,
            "format": fmt,
            "compressed": compress,
            "encrypted": encrypt,
            "orig_size": original_size,
            "enc_kid": encryption_key_id
        },
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    # Audit
    db.add(models.AuditLog(user_id=current_user.id, action="generate_document", object_type="GeneratedDocument", object_id=str(doc.id), audit_metadata={"format": fmt, "compressed": compress, "encrypted": encrypt}))
    db.commit()
    return doc

@router.get("/", response_model=GeneratedDocumentList)
def list_documents(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, int | list[models.GeneratedDocument]]:
    can_generate(current_user)
    q = db.query(models.GeneratedDocument)
    total = q.with_entities(func.count(models.GeneratedDocument.id)).scalar() or 0
    items = q.order_by(models.GeneratedDocument.id.desc()).offset(skip).limit(limit).all()
    return {"items": items, "total": total}

@router.get("/{doc_id}", response_model=GeneratedDocumentRead)
def get_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> models.GeneratedDocument:
    can_generate(current_user)
    doc = db.query(models.GeneratedDocument).filter(models.GeneratedDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    return doc

@router.post("/{doc_id}/signed-url")
def create_signed_download_url(doc_id: int, ttl_seconds: int = 300, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, int | str]:
    can_generate(current_user)
    doc = db.query(models.GeneratedDocument).filter(models.GeneratedDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if ttl_seconds <= 0 or ttl_seconds > 3600:
        raise HTTPException(status_code=400, detail="TTL invalide")
    expires = int(time.time()) + ttl_seconds
    sig = _sign(doc_id, expires)
    return {"url": f"/api/v1/documents/{doc_id}/download?exp={expires}&sig={sig}", "expires": expires}

@router.get("/{doc_id}/download")
def download_document(request: Request, doc_id: int, exp: Optional[int] = None, sig: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> FileResponse:
    # Si signature présente, on autorise sans rôle supplémentaire sinon contrôle standard
    if sig and exp:
        if not _verify_signature(doc_id, exp, sig):
            raise HTTPException(status_code=401, detail="Lien expiré ou signature invalide")
        rate_key = f"signed:{doc_id}:{sig}"
    else:
        can_generate(current_user)
        rate_key = f"user:{current_user.id}"
    _rate_limit(rate_key)
    doc = db.query(models.GeneratedDocument).filter(models.GeneratedDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    # Ownership check via policy -> client.owner
    if doc.policy_id and not sig:
        pol = db.query(models.Policy).filter(models.Policy.id == doc.policy_id).first()
        if pol and pol.client and pol.client.owner_id and pol.client.owner_id != current_user.id and current_user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
            raise HTTPException(status_code=403, detail="Accès restreint au propriétaire")
    if not doc.file_path:
        raise HTTPException(status_code=404, detail="Fichier non disponible")
    file_path = Path(doc.file_path)  # Chemin sur disque; on revalide confinement répertoire OUTPUT_DIR
    try:
        if not file_path.resolve().is_relative_to(Path(OUTPUT_DIR).resolve()):
            raise HTTPException(status_code=400, detail="Chemin invalide")
    except AttributeError:
        root = str(Path(OUTPUT_DIR).resolve())
        if not str(file_path.resolve()).startswith(root):
            raise HTTPException(status_code=400, detail="Chemin invalide")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable sur disque")
    # Audit
    db.add(models.AuditLog(user_id=current_user.id if not sig else None, action="download_document", object_type="GeneratedDocument", object_id=str(doc.id), audit_metadata={"signed": bool(sig)}))
    db.commit()
    return FileResponse(
        path=str(file_path),
        media_type=doc.mime_type or "application/octet-stream",
        filename=file_path.name,
        headers={
            "X-Doc-Id": str(doc.id),
            "X-Checksum": (doc.doc_metadata or {}).get("checksum", ""),
            "X-Signed": "1" if sig else "0"
        },
    )

@router.post("/purge-orphans")
def purge_orphans(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, int | list[str]]:
    can_superadmin(current_user)
    existing_paths = {Path(p[0]).resolve() for p in db.query(models.GeneratedDocument.file_path).filter(models.GeneratedDocument.file_path.isnot(None)).all()}
    root = Path(OUTPUT_DIR).resolve()
    removed = []
    for f in root.glob("doc_*"):
        if f.resolve() not in existing_paths:
            try:
                f.unlink()
                removed.append(f.name)
            except OSError:
                pass
    db.add(models.AuditLog(user_id=current_user.id, action="purge_orphans", object_type="GeneratedDocument", object_id="*", audit_metadata={"removed": len(removed)}))
    db.commit()
    return {"removed": removed, "count": len(removed)}
