from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr


class BatchCreateRequest(BaseModel):
    name: str


class BatchCreateResponse(BaseModel):
    batch_id: uuid.UUID


class BatchListItem(BaseModel):
    id: uuid.UUID
    name: str


class BatchListResponse(BaseModel):
    items: list[BatchListItem]


class BatchAddMemberRequest(BaseModel):
    email: EmailStr


class BatchAddMemberResponse(BaseModel):
    batch_member_id: uuid.UUID
    user_id: uuid.UUID
