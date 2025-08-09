from __future__ import annotations
"""Routes CRUD pour les templates et leurs versions.

Règles:
 - Seuls ADMIN et MANAGER peuvent manipuler les templates.
 - Création d'une première version (v1) facultative lors du create si contenu fourni.
 - Numérotation des versions incrémentale et immuable.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.api.deps import get_db, get_current_user
from backend.app.db import models
from backend.app.schemas.template import (
    TemplateCreate, TemplateRead, TemplateUpdate,
    TemplateVersionCreate, TemplateVersionRead, TemplateWithVersions
)
from backend.app.db.models.user import User, UserRole
from hashlib import sha256

router = APIRouter(prefix="/templates", tags=["templates"])


def ensure_admin_or_manager(user: User):
    # Limiter aux rôles ADMIN et MANAGER pour gestion des templates
    if user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

@router.post("/", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
def list_templates(skip: int = 0, limit: int = 100, active: Optional[bool] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_admin_or_manager(current_user)
    q = db.query(models.Template)
    if active is not None:
        q = q.filter(models.Template.is_active == active)
    return q.offset(skip).limit(limit).all()

@router.get("/{template_id}", response_model=TemplateWithVersions)
def get_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_admin_or_manager(current_user)
    tpl = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    versions = db.query(models.TemplateVersion).filter(models.TemplateVersion.template_id == tpl.id).order_by(models.TemplateVersion.version).all()
    tpl.versions = versions  # type: ignore
    return tpl

@router.patch("/{template_id}", response_model=TemplateRead)
def update_template(template_id: int, payload: TemplateUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
def add_template_version(template_id: int, payload: TemplateVersionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
def get_template_version(template_id: int, version: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_admin_or_manager(current_user)
    ver = db.query(models.TemplateVersion).filter(models.TemplateVersion.template_id == template_id, models.TemplateVersion.version == version).first()
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")
    return ver

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_admin_or_manager(current_user)
    tpl = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(tpl)
    db.commit()
    return None
