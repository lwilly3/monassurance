from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    """Représentation lecture d'une entrée d'audit.

    Pas d'exposition d'informations sensibles au-delà des champs déjà stockés.
    """

    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int]
    action: Optional[str]
    object_type: Optional[str]
    object_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    audit_metadata: Optional[dict[str, Any]]
    created_at: datetime

class AuditLogList(BaseModel):
    items: list[AuditLogRead]
    total: int
