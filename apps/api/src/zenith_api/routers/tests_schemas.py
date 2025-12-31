from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class TestCreateRequest(BaseModel):
    batch_id: uuid.UUID
    title: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class TestCreateResponse(BaseModel):
    test_id: uuid.UUID


class OptionCreate(BaseModel):
    text: str
    position: int


class QuestionCreateRequest(BaseModel):
    prompt: str
    position: int
    options: list[OptionCreate]
    correct_position: int  # which option position is correct


class QuestionCreateResponse(BaseModel):
    question_id: uuid.UUID


class TestListItem(BaseModel):
    id: uuid.UUID
    title: str
    batch_id: uuid.UUID
    starts_at: datetime | None
    ends_at: datetime | None


class TestListResponse(BaseModel):
    items: list[TestListItem]


class AttemptStartResponse(BaseModel):
    attempt_id: uuid.UUID


class AnswerUpsertRequest(BaseModel):
    selected_option_id: uuid.UUID


class SubmitAttemptResponse(BaseModel):
    score: int
    total: int
