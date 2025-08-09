"""CRUD des clients appartenant à l'utilisateur authentifié.

Chaque client est attaché via owner_id; isolation stricte par utilisateur.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from backend.app.db import models
from backend.app.api.deps import get_db_session, get_current_user

router = APIRouter(prefix="/clients", tags=["clients"])

@router.post("", response_model=ClientRead, status_code=201)
def create_client(payload: ClientCreate, db: Session = Depends(get_db_session), user: models.User = Depends(get_current_user)):
    client = models.Client(**payload.model_dump(), owner_id=user.id)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.get("", response_model=list[ClientRead])
def list_clients(db: Session = Depends(get_db_session), user: models.User = Depends(get_current_user)):
    q = db.query(models.Client).filter(models.Client.owner_id == user.id)
    return q.order_by(models.Client.created_at.desc()).all()

@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db_session), user: models.User = Depends(get_current_user)):
    client = db.query(models.Client).filter(models.Client.id == client_id, models.Client.owner_id == user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    return client

@router.put("/{client_id}", response_model=ClientRead)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db_session), user: models.User = Depends(get_current_user)):
    client = db.query(models.Client).filter(models.Client.id == client_id, models.Client.owner_id == user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    data = payload.model_dump(exclude_unset=True)
    for k,v in data.items():
        setattr(client, k, v)
    db.commit()
    db.refresh(client)
    return client

@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, db: Session = Depends(get_db_session), user: models.User = Depends(get_current_user)):
    client = db.query(models.Client).filter(models.Client.id == client_id, models.Client.owner_id == user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    db.delete(client)
    db.commit()
    return None
