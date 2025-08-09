from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CompanyBase(BaseModel):
    name: str
    code: str
    api_mode: bool = False
    api_endpoint: str | None = None
    api_key: str | None = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    api_mode: bool | None = None
    api_endpoint: str | None = None
    api_key: str | None = None

class CompanyRead(CompanyBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
