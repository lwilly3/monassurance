from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict

class DocumentGenerateRequest(BaseModel):
    document_type: str
    policy_id: int | None = None
    template_version_id: int | None = None
    inline_context: dict[str, Any] | None = None  # données dynamiques pour rendu
    output_format: str | None = None  # override (html/pdf/xlsx)

class GeneratedDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_type: Optional[str]
    policy_id: Optional[int]
    template_version_id: Optional[int]
    file_path: Optional[str]
    mime_type: Optional[str]
    size_bytes: Optional[int]
    status: Optional[str]
    doc_metadata: Optional[dict]
    created_at: datetime

class GeneratedDocumentList(BaseModel):
    items: list[GeneratedDocumentRead]
    total: int
