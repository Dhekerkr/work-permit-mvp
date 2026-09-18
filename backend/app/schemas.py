from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    matricule: str
    email: str
    role: str

class LoginIn(BaseModel):
    identifier: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class PermitData(BaseModel):
    permit_date: date | None = None
    site: str = "AGIL Gaz Radès"
    work_location: str = "مستودع عجيلغاز رادس"
    contractor: str = ""
    responsible_person: str = ""
    work_description: str = ""
    work_types: list[str] = Field(default_factory=list)
    other_work_type: str | None = None
    safety_checks: list[dict[str, Any]] = Field(default_factory=list)
    gas_measurement: dict[str, Any] = Field(default_factory=dict)
    hot_work_checks: list[dict[str, Any]] = Field(default_factory=list)
    planned_start_at: datetime | None = None
    expires_at: datetime | None = None

class PermitCreate(PermitData):
    pass

class PermitUpdate(PermitData):
    pass

class CommentIn(BaseModel):
    comment: str = Field(min_length=2, max_length=1000)

class CompletionIn(BaseModel):
    checks: list[dict[str, Any]]

class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_name: str
    action: str
    details: str | None
    previous_status: str | None
    new_status: str | None
    created_at: datetime

class PermitOut(PermitData):
    model_config = ConfigDict(from_attributes=True)
    id: int
    permit_number: str
    status: str
    rejection_reason: str | None
    approval: dict[str, Any]
    closure_checks: list[dict[str, Any]]
    completed_at: datetime | None
    closed_at: datetime | None
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    creator: UserOut
    audit_logs: list[AuditOut] = []

