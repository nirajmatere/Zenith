from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from zenith_api.main import app

client = TestClient(app)


def _register(email: str) -> dict:
    r = client.post("/auth/register", json={"email": email, "password": "Password123!"})
    assert r.status_code == 200, r.text
    return r.json()


def test_org_create_add_member_and_me() -> None:
    admin_email = f"admin-{uuid.uuid4().hex}@example.com"
    tokens = _register(admin_email)

    org_name = f"Zenith Coaching {uuid.uuid4().hex}"  # <-- make unique

    # Create org
    r = client.post(
        "/orgs",
        json={"name": org_name},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r.status_code == 200, r.text
    org_id = r.json()["organization_id"]

    # Add teacher
    teacher_email = f"teacher-{uuid.uuid4().hex}@example.com"
    r2 = client.post(
        f"/orgs/{org_id}/members",
        json={"email": teacher_email, "role": "teacher", "password": "Password123!"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r2.status_code == 200, r2.text

    # Teacher login
    teacher_tokens = client.post(
        "/auth/login",
        json={"email": teacher_email, "password": "Password123!"},
    ).json()

    # Teacher /me in org
    r3 = client.get(
        f"/orgs/{org_id}/me",
        headers={"Authorization": f"Bearer {teacher_tokens['access_token']}"},
    )
    assert r3.status_code == 200, r3.text
    assert r3.json()["role"] == "teacher"
