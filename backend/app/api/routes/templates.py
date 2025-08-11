from __future__ import annotations

"""Routes CRUD pour les templates et leurs versions.

Règles:
 - Seuls ADMIN et MANAGER peuvent manipuler les templates.
 - Création d'une première version (v1) facultative lors du create si contenu fourni.
 - Numérotation des versions incrémentale et immuable.
"""
from hashlib import sha256
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db import models
from backend.app.db.models.user import User, UserRole
from backend.app.schemas.template import (
    TemplateCreate,
    TemplateRead,
    TemplateUpdate,
    TemplateVersionCreate,
    TemplateVersionRead,
    TemplateWithVersions,
)
from backend.app.services.document_renderer import render_template
from backend.app.services.storage_provider import get_storage
from backend.app.services.template_storage import sha256_hex

router = APIRouter(prefix="/templates", tags=["templates"])


def ensure_admin_or_manager(user: User) -> None:
    # Limiter aux rôles ADMIN et MANAGER pour gestion des templates
    if user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

@router.post("/", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> models.Template:
    ensure_admin_or_manager(current_user)
    tpl = models.Template(
        name=payload.name,
        type=payload.type,
        format=payload.format,
        scope=payload.scope,
        is_active=payload.is_active if payload.is_active is not None else True,
        created_by=current_user.id,
    )
    db.add(tpl)
    db.flush()  # pour obtenir l'ID avant de créer éventuellement la version
    if payload.content is not None:
        # Calcule version initiale (devrait être 1 mais on sécurise en cas de race condition)
        last_version = db.query(models.TemplateVersion).filter(models.TemplateVersion.template_id == tpl.id).order_by(models.TemplateVersion.version.desc()).first()
        next_version = 1 if not last_version else last_version.version + 1
        checksum = sha256(payload.content.encode("utf-8")).hexdigest()
        version = models.TemplateVersion(
            template_id=tpl.id,
            version=next_version,
            storage_backend=payload.storage_backend,
            content=payload.content,
            checksum=checksum,
        )
        db.add(version)
    db.commit()
    db.refresh(tpl)
    return tpl

@router.get("/", response_model=List[TemplateRead])
def list_templates(skip: int = 0, limit: int = 100, active: Optional[bool] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[models.Template]:
    ensure_admin_or_manager(current_user)
    q = db.query(models.Template)
    if active is not None:
        q = q.filter(models.Template.is_active == active)
    return q.offset(skip).limit(limit).all()

@router.get("/{template_id}", response_model=TemplateWithVersions)
def get_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> models.Template:
    ensure_admin_or_manager(current_user)
    tpl = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    versions = db.query(models.TemplateVersion).filter(models.TemplateVersion.template_id == tpl.id).order_by(models.TemplateVersion.version).all()
    # attache dynamiquement l'attribut pour la réponse enrichie
    tpl.versions = versions
    return tpl

@router.patch("/{template_id}", response_model=TemplateRead)
def update_template(template_id: int, payload: TemplateUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> models.Template:
    ensure_admin_or_manager(current_user)
    tpl = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(tpl, k, v)
    db.commit()
    db.refresh(tpl)
    return tpl

@router.post("/{template_id}/versions", response_model=TemplateVersionRead, status_code=status.HTTP_201_CREATED)
def add_template_version(template_id: int, payload: TemplateVersionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> models.TemplateVersion:
    ensure_admin_or_manager(current_user)
    tpl = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    last_version = db.query(models.TemplateVersion).filter(models.TemplateVersion.template_id == template_id).order_by(models.TemplateVersion.version.desc()).first()  # Récupère dernière version pour incrément
    new_version_number = 1 if not last_version else last_version.version + 1
    checksum = None
    if payload.content:
        checksum = sha256(payload.content.encode("utf-8")).hexdigest()
    version = models.TemplateVersion(
        template_id=template_id,
        version=new_version_number,
        storage_backend=payload.storage_backend,
        content=payload.content,
        file_path=payload.file_path,
        checksum=checksum,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version

@router.get("/{template_id}/versions/{version}", response_model=TemplateVersionRead)
def get_template_version(template_id: int, version: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> models.TemplateVersion:
    ensure_admin_or_manager(current_user)
    ver = db.query(models.TemplateVersion).filter(models.TemplateVersion.template_id == template_id, models.TemplateVersion.version == version).first()
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")
    return ver

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Response:
    ensure_admin_or_manager(current_user)
    tpl = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(tpl)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{template_id}/upload", response_model=TemplateVersionRead, status_code=status.HTTP_201_CREATED)
def upload_template_file(
    template_id: int,
    file: UploadFile = File(...),
    checksum: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> models.TemplateVersion:
    """Upload binaire sécurisé d'un template. Stocke sur disque et crée une nouvelle version.

    Si un checksum (sha256 hex) est fourni, il est validé côté serveur.
    """
    ensure_admin_or_manager(current_user)
    tpl = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    data = file.file.read()
    if checksum:
        calc = sha256_hex(data)
        if calc != checksum:
            raise HTTPException(status_code=400, detail="Checksum mismatch")
    storage = get_storage(db)
    stored_path = storage.store_bytes(data, filename=file.filename, content_type=file.content_type)
    last_version = db.query(models.TemplateVersion).filter(models.TemplateVersion.template_id == template_id).order_by(models.TemplateVersion.version.desc()).first()
    new_version_number = 1 if not last_version else last_version.version + 1
    version = models.TemplateVersion(
        template_id=template_id,
        version=new_version_number,
        storage_backend="file",
        content=None,
        file_path=stored_path,
        checksum=sha256_hex(data),
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.get("/{template_id}/versions/{version}/preview", response_class=HTMLResponse)
def preview_template(
    template_id: int,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HTMLResponse:
    """Prévisualise une version de template en HTML.

    - Si le template est stocké en base (content), on le rend tel quel avec un contexte neutre.
    - Si stocké fichier, on lit le fichier et on renvoie le rendu HTML.
    """
    ensure_admin_or_manager(current_user)
    ver = db.query(models.TemplateVersion).filter(models.TemplateVersion.template_id == template_id, models.TemplateVersion.version == version).first()
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")
    # Détermine le contenu brut
    if ver.content:
        raw = ver.content
    elif ver.file_path:
        try:
            storage = get_storage(db)
            raw = storage.read_text(ver.file_path)
        except Exception:
            raise HTTPException(status_code=400, detail="Fichier de template illisible")
    else:
        raise HTTPException(status_code=400, detail="Aucun contenu")
    # Construit un mini contexte
    ctx = {"inline_context": {"example": "Aperçu"}}
    html_bytes = render_template(raw, ctx, "html")
    return HTMLResponse(content=html_bytes.decode("utf-8"))


@router.get("/{template_id}/versions/{version}/preview.pdf")
def preview_template_pdf(
    template_id: int,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FastAPIResponse:
    """Prévisualise une version de template en PDF.

    Lit le contenu (DB ou fichier), puis rend en PDF via le moteur existant.
    """
    ensure_admin_or_manager(current_user)
    ver = db.query(models.TemplateVersion).filter(models.TemplateVersion.template_id == template_id, models.TemplateVersion.version == version).first()
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")
    if ver.content:
        raw = ver.content
    elif ver.file_path:
        try:
            storage = get_storage(db)
            raw = storage.read_text(ver.file_path)
        except Exception:
            raise HTTPException(status_code=400, detail="Fichier de template illisible")
    else:
        raise HTTPException(status_code=400, detail="Aucun contenu")
    ctx = {"inline_context": {"example": "Aperçu"}}
    pdf_bytes = render_template(raw, ctx, "pdf")
    return FastAPIResponse(content=pdf_bytes, media_type="application/pdf")
