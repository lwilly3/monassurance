from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db import models
from backend.app.db.models.user import User, UserRole
from backend.app.schemas.storage_config import StorageConfigRead, StorageConfigUpdate

router = APIRouter(prefix="/admin", tags=["admin"])  # espace admin


def require_admin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Réservé admin")


def _get_singleton(db: Session) -> models.StorageConfig:
    cfg = db.query(models.StorageConfig).order_by(models.StorageConfig.id.asc()).first()
    if not cfg:
        cfg = models.StorageConfig(backend="local")
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


@router.get("/storage-config", response_model=StorageConfigRead)
def get_storage_config(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> models.StorageConfig:
    require_admin(current_user)
    return _get_singleton(db)


@router.put("/storage-config", response_model=StorageConfigRead)
def update_storage_config(payload: StorageConfigUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> models.StorageConfig:
    require_admin(current_user)
    cfg = _get_singleton(db)
    if payload.backend == "google_drive":
        if not payload.gdrive_folder_id or not payload.gdrive_service_account_json_path:
            raise HTTPException(status_code=400, detail="Paramètres Google Drive requis")
        import os
        if not os.path.exists(payload.gdrive_service_account_json_path):
            raise HTTPException(status_code=400, detail="Fichier Service Account introuvable")
    cfg.backend = payload.backend
    cfg.gdrive_folder_id = payload.gdrive_folder_id
    cfg.gdrive_service_account_json_path = payload.gdrive_service_account_json_path
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    # Invalider le cache du provider après modification
    from backend.app.services.storage_provider import invalidate_storage_cache
    invalidate_storage_cache()
    return cfg
