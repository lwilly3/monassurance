from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from backend.app.db.models import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = True

class UserCreate(UserBase):
    password: str
    role: UserRole | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
