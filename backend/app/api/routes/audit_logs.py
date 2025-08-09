"""Endpoints de consultation des journaux d'audit.

Fonctionnalités:
 - Listing paginé
 - Filtres: action, object_type, user_id, date min/max
 - Tri (ordre inverse chronologique)
 - Restreint aux rôles MANAGER+ (inclut ADMIN)
"""
import csv
import io
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db import models
from backend.app.db.models.user import User, UserRole
from backend.app.schemas.audit_log import AuditLogList

router = APIRouter(prefix="/audit-logs", tags=["audit"])


def _require_manager(user: User) -> None:
    if user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise HTTPException(status_code=403, detail="Accès restreint")

@router.get("/", response_model=AuditLogList)
def list_audit_logs(
    skip: int = 0,
    limit: int = Query(50, le=200),
    action: str | None = None,
    object_type: str | None = None,
    action_contains: str | None = Query(None, description="Recherche partielle insensible à la casse sur action"),
    object_contains: str | None = Query(None, description="Recherche partielle insensible à la casse sur object_type"),
    user_id: int | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Liste paginée des logs d'audit avec filtres optionnels.

    Paramètres:
      - skip/limit: pagination.
      - action/object_type: filtrage exact.
      - action_contains / object_contains: recherche partielle (AND si combiné avec exact).
      - user_id: filtrer par initiateur (NULL ignoré si log signé sans user).
      - created_from/created_to: bornes temporelles (UTC).

    Notes:
      - Les filtres *contains* utilisent ILIKE (PostgreSQL) ou LIKE (SQLite) selon le backend.
      - Fournir simultanément action et action_contains restreint davantage (intersection).
    """
    _require_manager(current_user)
    q = db.query(models.AuditLog)
    if action:
        q = q.filter(models.AuditLog.action == action)
    if object_type:
        q = q.filter(models.AuditLog.object_type == object_type)
    if action_contains:
        pattern = f"%{action_contains}%"
        q = q.filter(models.AuditLog.action.ilike(pattern))
    if object_contains:
        pattern = f"%{object_contains}%"
        q = q.filter(models.AuditLog.object_type.ilike(pattern))
    if user_id is not None:
        q = q.filter(models.AuditLog.user_id == user_id)
    if created_from:
        q = q.filter(models.AuditLog.created_at >= created_from)
    if created_to:
        q = q.filter(models.AuditLog.created_at <= created_to)
    total = q.with_entities(func.count(models.AuditLog.id)).scalar() or 0
    items = q.order_by(models.AuditLog.id.desc()).offset(skip).limit(limit).all()
    return {"items": items, "total": total}


@router.get("/export", response_class=Response)
def export_audit_logs_csv(
    action: str | None = None,
    object_type: str | None = None,
    action_contains: str | None = None,
    object_contains: str | None = None,
    user_id: int | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    include_metadata: bool = Query(True, description="Inclure la colonne audit_metadata (JSON)"),
    delimiter: str = Query(",", pattern=r"^[,;\t|]$", description="Délimiteur CSV (parmi , ; tab |)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Exporte les logs d'audit en CSV.

    - Applique les mêmes filtres que le listing.
    - Retourne un fichier `audit_logs.csv` (text/csv UTF-8).
    - `audit_metadata` est sérialisé JSON si présent et `include_metadata=True`.
    - Pas de pagination: export complet selon filtres (prudence taille — prévoir pagination/extractions futures si volumétrie importante).
    """
    _require_manager(current_user)
    q = db.query(models.AuditLog)
    if action:
        q = q.filter(models.AuditLog.action == action)
    if object_type:
        q = q.filter(models.AuditLog.object_type == object_type)
    if action_contains:
        pattern = f"%{action_contains}%"
        q = q.filter(models.AuditLog.action.ilike(pattern))
    if object_contains:
        pattern = f"%{object_contains}%"
        q = q.filter(models.AuditLog.object_type.ilike(pattern))
    if user_id is not None:
        q = q.filter(models.AuditLog.user_id == user_id)
    if created_from:
        q = q.filter(models.AuditLog.created_at >= created_from)
    if created_to:
        q = q.filter(models.AuditLog.created_at <= created_to)
    rows = q.order_by(models.AuditLog.id.desc()).all()
    output = io.StringIO()
    fieldnames = [
        "id",
        "created_at",
        "user_id",
        "action",
        "object_type",
        "object_id",
        "ip_address",
        "user_agent",
    ]
    if include_metadata:
        fieldnames.append("audit_metadata")
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
    writer.writeheader()
    for r in rows:
        data = {
            "id": r.id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "user_id": r.user_id,
            "action": r.action,
            "object_type": r.object_type,
            "object_id": r.object_id,
            "ip_address": r.ip_address,
            "user_agent": r.user_agent,
        }
        if include_metadata:
            data["audit_metadata"] = json.dumps(r.audit_metadata, ensure_ascii=False) if r.audit_metadata else ""
        writer.writerow(data)
    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )
