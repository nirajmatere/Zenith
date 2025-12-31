from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from zenith_api.auth.deps import get_current_user
from zenith_api.db.models import Batch, BatchMember, Membership, Role, User
from zenith_api.db.session import get_db


def require_org_role(*allowed_roles: str) -> Callable[..., Membership]:
    allowed = set(allowed_roles)

    def _dep(
        org_id: uuid.UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ) -> Membership:
        membership = db.scalar(
            select(Membership).where(
                Membership.organization_id == org_id,
                Membership.user_id == user.id,
            )
        )
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membership not found",
            )


        role = db.scalar(select(Role).where(Role.id == membership.role_id))
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Role not found. Run seed.",
            )

        if role.code not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Forbidden"
            )

        return membership

    return _dep


def require_batch_member() -> Callable[..., BatchMember]:
    def _dep(
        org_id: uuid.UUID,
        batch_id: uuid.UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ) -> BatchMember:
        batch = db.scalar(select(Batch).where(Batch.id == batch_id))
        if batch is None or batch.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Batch not found"
            )

        bm = db.scalar(
            select(BatchMember).where(
                BatchMember.batch_id == batch_id,
                BatchMember.user_id == user.id,
            )
        )
        if bm is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not in batch"
            )

        return bm

    return _dep
