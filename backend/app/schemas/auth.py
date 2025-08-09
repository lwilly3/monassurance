from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str


class DeviceSession(BaseModel):
    id: int
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    device_label: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    model_config = ConfigDict(from_attributes=True)
