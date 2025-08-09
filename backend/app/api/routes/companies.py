"""CRUD des compagnies (entités globales).

Accès en écriture restreint aux rôles MANAGER/ADMIN (delete: ADMIN).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from backend.app.db import models
from backend.app.api.deps import get_db_session, require_role

router = APIRouter(prefix="/companies", tags=["companies"])

@router.post("", response_model=CompanyRead, status_code=201)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db_session), user=Depends(require_role([models.UserRole.ADMIN, models.UserRole.MANAGER]))):
    if db.query(models.Company).filter((models.Company.name == payload.name) | (models.Company.code == payload.code)).first():
        raise HTTPException(status_code=400, detail="Company déjà existante")
    company = models.Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

@router.get("", response_model=list[CompanyRead])
def list_companies(db: Session = Depends(get_db_session)):
    return db.query(models.Company).order_by(models.Company.created_at.desc()).all()

@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db_session)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company introuvable")
    return company

@router.put("/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db_session), user=Depends(require_role([models.UserRole.ADMIN, models.UserRole.MANAGER]))):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company introuvable")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(company, k, v)
    db.commit()
    db.refresh(company)
    return company

@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: int, db: Session = Depends(get_db_session), user=Depends(require_role([models.UserRole.ADMIN]))):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company introuvable")
    db.delete(company)
    db.commit()
    return None
