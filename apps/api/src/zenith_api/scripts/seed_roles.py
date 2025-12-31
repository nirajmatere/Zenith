from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from zenith_api.db.models import Role
from zenith_api.db.session import SessionLocal
from zenith_api.rbac.constants import ALL_ROLE_CODES


def ensure_roles(db: Session) -> int:
    existing = set(db.scalars(select(Role.code)).all())
    created = 0
    for code in ALL_ROLE_CODES:
        if code not in existing:
            db.add(Role(code=code, name=code.title()))
            created += 1
    if created:
        db.commit()
    return created


def main() -> None:
    db = SessionLocal()
    try:
        created = ensure_roles(db)
    finally:
        db.close()

    print(f"seed_roles: created={created}")


if __name__ == "__main__":
    main()
