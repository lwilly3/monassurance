from datetime import datetime
from pydantic import BaseModel, model_validator, ConfigDict

class PolicyBase(BaseModel):
    policy_number: str
    client_id: int
    company_id: int | None = None
    product_name: str
    premium_amount: int
    effective_date: datetime
    expiry_date: datetime

    @model_validator(mode="after")
    def check_dates(self):
        if self.expiry_date <= self.effective_date:
            raise ValueError("expiry_date doit être postérieure à effective_date")
        return self

class PolicyCreate(PolicyBase):
    pass

class PolicyUpdate(BaseModel):
    product_name: str | None = None
    premium_amount: int | None = None
    expiry_date: datetime | None = None

class PolicyRead(PolicyBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
