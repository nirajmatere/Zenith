from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field


class OrgCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)


class OrgCreateResponse(BaseModel):
    organization_id: uuid.UUID


class AddMemberRequest(BaseModel):
    email: EmailStr
    role: str = Field(pattern="^(teacher|student|admin)$")
    password: str | None = Field(default=None, min_length=8, max_length=128)


class AddMemberResponse(BaseModel):
    user_id: uuid.UUID
    membership_id: uuid.UUID


class MeResponse(BaseModel):
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: str
