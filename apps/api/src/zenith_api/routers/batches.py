from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from zenith_api.auth.rbac import require_org_role
from zenith_api.db.models import Batch, BatchMember, Membership, User
from zenith_api.db.session import get_db
from zenith_api.routers.batches_schemas import (
    BatchAddMemberRequest,
    BatchAddMemberResponse,
    BatchCreateRequest,
    BatchCreateResponse,
    BatchListItem,
    BatchListResponse,
)

router = APIRouter()


@router.post("/{org_id}/batches", response_model=BatchCreateResponse)
def create_batch(
    org_id: uuid.UUID,
    payload: BatchCreateRequest,
    db: Session = Depends(get_db),
    _m: Membership = Depends(require_org_role("admin", "teacher")),
) -> BatchCreateResponse:
    batch = Batch(organization_id=org_id, name=payload.name)
    db.add(batch)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Batch name already exists"
        ) from None
    db.refresh(batch)
    return BatchCreateResponse(batch_id=batch.id)


@router.get("/{org_id}/batches", response_model=BatchListResponse)
def list_batches(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    _m: Membership = Depends(require_org_role("admin", "teacher", "student")),
) -> BatchListResponse:
    rows = db.scalars(
        select(Batch).
        where(Batch.organization_id == org_id)
        .order_by(Batch.name)
    ).all()
    return BatchListResponse(items=[BatchListItem(id=b.id, name=b.name) for b in rows])


@router.post("/{org_id}/batches/{batch_id}/members", response_model=BatchAddMemberResponse)
def add_batch_member(
    org_id: uuid.UUID,
    batch_id: uuid.UUID,
    payload: BatchAddMemberRequest,
    db: Session = Depends(get_db),
    _m: Membership = Depends(require_org_role("admin", "teacher")),
) -> BatchAddMemberResponse:
    batch = db.scalar(select(Batch).where(Batch.id == batch_id))
    if batch is None or batch.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Batch not found"
        )

    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    org_membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == org_id,
            Membership.user_id == user.id,
        )
    )
    if org_membership is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not in org")

    bm = db.scalar(
        select(BatchMember).where(
            BatchMember.batch_id == batch_id,
            BatchMember.user_id == user.id,
        )
    )
    if bm is None:
        bm = BatchMember(batch_id=batch_id, user_id=user.id)
        db.add(bm)
        db.commit()
        db.refresh(bm)

    return BatchAddMemberResponse(batch_member_id=bm.id, user_id=user.id)
