from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class StorageConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    backend: Literal["local", "google_drive", "s3"]
    gdrive_folder_id: Optional[str] = Field(None, max_length=128)
    gdrive_service_account_json_path: Optional[str] = Field(None, max_length=500)
    s3_bucket: Optional[str] = Field(None, max_length=255)
    s3_region: Optional[str] = Field(None, max_length=50)
    s3_endpoint_url: Optional[str] = Field(None, max_length=255)
    updated_at: datetime


class StorageConfigUpdate(BaseModel):
    backend: Literal["local", "google_drive", "s3"]
    gdrive_folder_id: Optional[str] = Field(None, max_length=128)
    gdrive_service_account_json_path: Optional[str] = Field(None, max_length=500)
    s3_bucket: Optional[str] = Field(None, max_length=255)
    s3_region: Optional[str] = Field(None, max_length=50)
    s3_endpoint_url: Optional[str] = Field(None, max_length=255)
