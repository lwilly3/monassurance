"""CRUD des polices d'assurance.

Filtré par ownership via le client.owner_id de l'utilisateur authentifié.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db_session
from backend.app.db import models
from backend.app.schemas.policy import PolicyCreate, PolicyRead, PolicyUpdate

router = APIRouter(prefix="/policies", tags=["policies"])

@router.post("", response_model=PolicyRead, status_code=201)
def create_policy(payload: PolicyCreate, db: Session = Depends(get_db_session), user: models.User = Depends(get_current_user)):
    if db.query(models.Policy).filter(models.Policy.policy_number == payload.policy_number).first():
        raise HTTPException(status_code=400, detail="Numéro de police déjà existant")
    # Validate foreign keys
    client = db.query(models.Client).filter(models.Client.id == payload.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    if payload.company_id:
        company = db.query(models.Company).filter(models.Company.id == payload.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company introuvable")
    policy = models.Policy(**payload.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy

@router.get("", response_model=list[PolicyRead])
def list_policies(db: Session = Depends(get_db_session), user: models.User = Depends(get_current_user)):
    # Limiter aux policies des clients de l'utilisateur
    return (db.query(models.Policy)
              .join(models.Client)
              .filter(models.Client.owner_id == user.id)
              .order_by(models.Policy.created_at.desc())
              .all())

@router.get("/{policy_id}", response_model=PolicyRead)
def get_policy(policy_id: int, db: Session = Depends(get_db_session), user: models.User = Depends(get_current_user)):
    policy = (db.query(models.Policy)
                .join(models.Client)
                .filter(models.Policy.id == policy_id, models.Client.owner_id == user.id)
                .first())
    if not policy:
        raise HTTPException(status_code=404, detail="Police introuvable")
    return policy

@router.put("/{policy_id}", response_model=PolicyRead)
def update_policy(policy_id: int, payload: PolicyUpdate, db: Session = Depends(get_db_session), user: models.User = Depends(get_current_user)):
    policy = (db.query(models.Policy)
                .join(models.Client)
                .filter(models.Policy.id == policy_id, models.Client.owner_id == user.id)
                .first())
    if not policy:
        raise HTTPException(status_code=404, detail="Police introuvable")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(policy, k, v)
    db.commit()
    db.refresh(policy)
    return policy

@router.delete("/{policy_id}", status_code=204)
def delete_policy(policy_id: int, db: Session = Depends(get_db_session), user: models.User = Depends(get_current_user)):
    policy = (db.query(models.Policy)
                .join(models.Client)
                .filter(models.Policy.id == policy_id, models.Client.owner_id == user.id)
                .first())
    if not policy:
        raise HTTPException(status_code=404, detail="Police introuvable")
    db.delete(policy)
    db.commit()
    return None
