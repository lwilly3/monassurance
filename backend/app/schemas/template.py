from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TemplateBase(BaseModel):
    name: str = Field(..., max_length=255)
    type: Optional[str] = Field(None, max_length=30)
    format: Optional[str] = Field(None, max_length=20)
    scope: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = True

class TemplateCreate(TemplateBase):
    content: Optional[str] = None  # initial inline content (creates version=1 if provided)
    storage_backend: Optional[str] = "db"

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    format: Optional[str] = None
    scope: Optional[str] = None
    is_active: Optional[bool] = None

class TemplateRead(TemplateBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_by: Optional[int] = None
    created_at: datetime

class TemplateVersionBase(BaseModel):
    storage_backend: Optional[str] = "db"
    content: Optional[str] = None
    file_path: Optional[str] = None

class TemplateVersionCreate(TemplateVersionBase):
    pass

class TemplateVersionRead(TemplateVersionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    template_id: int
    version: int
    checksum: Optional[str] = None
    created_at: datetime

class TemplateWithVersions(TemplateRead):
    versions: list[TemplateVersionRead] = []
