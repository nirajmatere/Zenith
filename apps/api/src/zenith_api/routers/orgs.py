from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from zenith_api.auth.deps import get_current_user
from zenith_api.auth.rbac import require_org_role
from zenith_api.auth.security import hash_password
from zenith_api.db.models import Membership, Organization, Role, User
from zenith_api.db.session import get_db
from zenith_api.routers.orgs_schemas import (
    AddMemberRequest,
    AddMemberResponse,
    MeResponse,
    OrgCreateRequest,
    OrgCreateResponse,
)

router = APIRouter()


def _get_role(db: Session, code: str) -> Role:
    role = db.scalar(select(Role).where(Role.code == code))
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Role '{code}' not found. Run seed.",
        )
    return role


@router.post("", response_model=OrgCreateResponse)
def create_org(
    payload: OrgCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrgCreateResponse:
    org = Organization(name=payload.name)
    db.add(org)
    db.commit()
    db.refresh(org)

    admin_role = _get_role(db, "admin")

    existing = db.scalar(
        select(Membership).where(
            Membership.organization_id == org.id,
            Membership.user_id == user.id,
        )
    )
    if existing is None:
        m = Membership(
            organization_id=org.id,
            user_id=user.id,
            role_id=admin_role.id,
        )
        db.add(m)
        db.commit()

    return OrgCreateResponse(organization_id=org.id)


@router.post("/{org_id}/members", response_model=AddMemberResponse)
def add_member(
    org_id: uuid.UUID,
    payload: AddMemberRequest,
    db: Session = Depends(get_db),
    _admin_membership: Membership = Depends(require_org_role("admin")),
) -> AddMemberResponse:
    # Ensure org exists
    org = db.scalar(select(Organization).where(Organization.id == org_id))
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    role = _get_role(db, payload.role)

    # Find or create user
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        # If creating a user, password must be provided
        if not payload.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password required when creating a new user",
            )
        user = User(email=payload.email, hashed_password=hash_password(payload.password))
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create membership if missing, else update role
    membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == org_id,
            Membership.user_id == user.id,
        )
    )

    if membership is None:
        membership = Membership(
            organization_id=org_id,
            user_id=user.id,
            role_id=role.id,
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)
    else:
        membership.role_id = role.id
        db.commit()
        db.refresh(membership)

    return AddMemberResponse(user_id=user.id, membership_id=membership.id)


@router.get("/{org_id}/me", response_model=MeResponse)
def me_in_org(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MeResponse:
    membership = db.scalar(
        select(Membership)
        .options(joinedload(Membership.role))
        .where(
            Membership.organization_id == org_id,
            Membership.user_id == user.id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

    return MeResponse(
        user_id=user.id,
        organization_id=org_id,
        role=membership.role.code,
    )
