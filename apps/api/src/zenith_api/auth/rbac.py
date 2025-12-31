from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from zenith_api.auth.deps import get_current_user
from zenith_api.db.models import Membership, User
from zenith_api.db.session import get_db


def require_org_role(*allowed_roles: str) -> Callable[..., Membership]:
    def _dep(
        org_id: uuid.UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ) -> Membership:
        membership = db.scalar(
            select(Membership)
            .options(joinedload(Membership.role))
            .where(
                Membership.organization_id == org_id,
                Membership.user_id == user.id,
            )
        )

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this organization",
            )

        if membership.role.code not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return membership

    return _dep
