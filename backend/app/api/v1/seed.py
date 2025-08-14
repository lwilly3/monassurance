"""
API endpoints pour la gestion des données de remplissage
"""
import os
import subprocess
import sys

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db_session, require_role
from backend.app.db import models

router = APIRouter()

class SeedStatusResponse(BaseModel):
    has_data: bool
    companies_count: int = 0
    clients_count: int = 0
    policies_count: int = 0
    message: str = ""

class SeedActionResponse(BaseModel):
    success: bool
    message: str
    data: SeedStatusResponse | None = None

@router.get("/status", response_model=SeedStatusResponse)
def get_seed_status(
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(require_role([models.UserRole.ADMIN]))
) -> SeedStatusResponse:
    """Vérifie le statut des données de remplissage"""
    try:
        # Compter les enregistrements dans chaque table
        companies_result = db.execute(text("SELECT COUNT(*) FROM companies"))
        clients_result = db.execute(text("SELECT COUNT(*) FROM clients"))
        policies_result = db.execute(text("SELECT COUNT(*) FROM policies"))
        
        companies_count = companies_result.scalar() or 0
        clients_count = clients_result.scalar() or 0
        policies_count = policies_result.scalar() or 0
        
        has_data = companies_count > 0 or clients_count > 0 or policies_count > 0
        
        message = "Base de données vide" if not has_data else f"Données présentes: {companies_count} compagnies, {clients_count} clients, {policies_count} polices"
        
        return SeedStatusResponse(
            has_data=has_data,
            companies_count=companies_count,
            clients_count=clients_count,
            policies_count=policies_count,
            message=message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la vérification du statut: {str(e)}"
        ) from e


@router.post("/populate", response_model=SeedActionResponse)
def populate_database(
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(require_role([models.UserRole.ADMIN]))
) -> SeedActionResponse:
    """Remplit la base de données avec des données de test"""
    try:
        # Vérifier si des données existent déjà
        seed_status = get_seed_status(db, current_user)
        
        if seed_status.has_data:
            return SeedActionResponse(
                success=False,
                message="La base de données contient déjà des données. Videz-la d'abord si nécessaire.",
                data=seed_status
            )
        
        # Exécuter le script de remplissage
        script_path = os.path.join(os.getcwd(), "seed_database.py")
        
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            # Récupérer le nouveau statut
            new_status = get_seed_status(db, current_user)
            return SeedActionResponse(
                success=True,
                message="Base de données remplie avec succès!",
                data=new_status
            )
        else:
            return SeedActionResponse(
                success=False,
                message=f"Erreur lors du remplissage: {result.stderr}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du remplissage: {str(e)}"
        ) from e

@router.post("/clear", response_model=SeedActionResponse)
def clear_database(
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(require_role([models.UserRole.ADMIN]))
) -> SeedActionResponse:
    """Vide la base de données des données de test"""
    try:
        # Exécuter le script de nettoyage
        script_path = os.path.join(os.getcwd(), "seed_database.py")
        
        result = subprocess.run(
            [sys.executable, script_path, "clear"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            # Récupérer le nouveau statut
            new_status = get_seed_status(db, current_user)
            return SeedActionResponse(
                success=True,
                message="Données de test supprimées avec succès!",
                data=new_status
            )
        else:
            return SeedActionResponse(
                success=False,
                message=f"Erreur lors du nettoyage: {result.stderr}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du nettoyage: {str(e)}"
        ) from e
