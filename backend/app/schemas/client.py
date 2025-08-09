from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class ClientBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None

class ClientRead(ClientBase):
    id: int
    owner_id: int | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
