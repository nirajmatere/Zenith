from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from zenith_api.auth.deps import get_current_user
from zenith_api.auth.rbac import require_batch_member, require_org_role
from zenith_api.db.models import (
    Attempt,
    AttemptAnswer,
    Batch,
    Membership,
    Question,
    QuestionOption,
    Test,
    User,
)
from zenith_api.db.session import get_db
from zenith_api.routers.tests_schemas import (
    AnswerUpsertRequest,
    AttemptStartResponse,
    QuestionCreateRequest,
    QuestionCreateResponse,
    SubmitAttemptResponse,
    TestCreateRequest,
    TestCreateResponse,
    TestListItem,
    TestListResponse,
)

router = APIRouter()


@router.post("/{org_id}/tests", response_model=TestCreateResponse)
def create_test(
    org_id: uuid.UUID,
    payload: TestCreateRequest,
    db: Session = Depends(get_db),
    _m: Membership = Depends(require_org_role("admin", "teacher")),
) -> TestCreateResponse:
    batch = db.scalar(select(Batch).where(Batch.id == payload.batch_id))
    if batch is None or batch.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    t = Test(
        organization_id=org_id,
        batch_id=payload.batch_id,
        title=payload.title,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return TestCreateResponse(test_id=t.id)


@router.get("/{org_id}/tests", response_model=TestListResponse)
def list_tests(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    _m: Membership = Depends(require_org_role("admin", "teacher", "student")),
) -> TestListResponse:
    rows = db.scalars(
        select(Test).where(Test.organization_id == org_id).order_by(Test.created_at.desc())
    ).all()
    return TestListResponse(
        items=[
            TestListItem(
                id=t.id,
                title=t.title,
                batch_id=t.batch_id,
                starts_at=t.starts_at,
                ends_at=t.ends_at,
            )
            for t in rows
        ]
    )


@router.post("/{org_id}/tests/{test_id}/questions", response_model=QuestionCreateResponse)
def add_question(
    org_id: uuid.UUID,
    test_id: uuid.UUID,
    payload: QuestionCreateRequest,
    db: Session = Depends(get_db),
    _m: Membership = Depends(require_org_role("admin", "teacher")),
) -> QuestionCreateResponse:
    test = db.scalar(select(Test).where(Test.id == test_id))
    if test is None or test.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    if not payload.options:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Options required")

    if payload.correct_position not in {o.position for o in payload.options}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid correct_position"
        )

    q = Question(test_id=test_id, prompt=payload.prompt, position=payload.position)
    db.add(q)
    db.commit()
    db.refresh(q)

    for o in payload.options:
        opt = QuestionOption(
            question_id=q.id,
            text=o.text,
            position=o.position,
            is_correct=(o.position == payload.correct_position),
        )
        db.add(opt)

    db.commit()
    return QuestionCreateResponse(question_id=q.id)


@router.post("/{org_id}/tests/{test_id}/attempts/start", response_model=AttemptStartResponse)
def start_attempt(
    org_id: uuid.UUID,
    test_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AttemptStartResponse:
    test = db.scalar(select(Test).where(Test.id == test_id))
    if test is None or test.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    # must be in the test batch
    _ = require_batch_member()(org_id=org_id, batch_id=test.batch_id, db=db, user=user)

    now = datetime.now(UTC)
    if test.starts_at and now < test.starts_at:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Test not started")
    if test.ends_at and now > test.ends_at:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Test ended")

    a = Attempt(test_id=test_id, user_id=user.id)
    db.add(a)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Attempt).where(and_(Attempt.test_id == test_id, Attempt.user_id == user.id))
        )
        if existing is None:
            raise
        return AttemptStartResponse(attempt_id=existing.id)

    db.refresh(a)
    return AttemptStartResponse(attempt_id=a.id)


@router.put("/{org_id}/attempts/{attempt_id}/answers/{question_id}")
def upsert_answer(
    org_id: uuid.UUID,
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: AnswerUpsertRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    attempt = db.scalar(select(Attempt).where(Attempt.id == attempt_id))
    if attempt is None or attempt.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

    test = db.scalar(select(Test).where(Test.id == attempt.test_id))
    if test is None or test.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    q = db.scalar(select(Question).where(Question.id == question_id))
    if q is None or q.test_id != test.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    opt = db.scalar(select(QuestionOption).where(QuestionOption.id == payload.selected_option_id))
    if opt is None or opt.question_id != q.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid option")

    row = db.scalar(
        select(AttemptAnswer).where(
            AttemptAnswer.attempt_id == attempt_id,
            AttemptAnswer.question_id == question_id,
        )
    )
    if row is None:
        row = AttemptAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_id=payload.selected_option_id,
        )
        db.add(row)
    else:
        row.selected_option_id = payload.selected_option_id

    db.commit()
    return {"status": "ok"}


@router.post("/{org_id}/attempts/{attempt_id}/submit", response_model=SubmitAttemptResponse)
def submit_attempt(
    org_id: uuid.UUID,
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubmitAttemptResponse:
    attempt = db.scalar(select(Attempt).where(Attempt.id == attempt_id))
    if attempt is None or attempt.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

    test = db.scalar(select(Test).where(Test.id == attempt.test_id))
    if test is None or test.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Test not found"
        )

    total = db.scalar(
        select(func.count())
        .select_from(Question)
        .where(Question.test_id == test.id)
    ) or 0

    correct = db.scalar(
        select(func.count())
        .select_from(AttemptAnswer)
        .join(QuestionOption, AttemptAnswer.selected_option_id == QuestionOption.id)
        .join(Question, AttemptAnswer.question_id == Question.id)
        .where(
            AttemptAnswer.attempt_id == attempt.id,
            Question.test_id == test.id,
            QuestionOption.is_correct.is_(True),
        )
    ) or 0

    attempt.submitted_at = datetime.now(UTC)
    attempt.score = int(correct)
    db.commit()

    return SubmitAttemptResponse(score=int(correct), total=int(total))
