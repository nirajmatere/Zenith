from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from zenith_api.main import app

client = TestClient(app)


def test_register_login_refresh() -> None:
    email = f"a-{uuid.uuid4().hex}@example.com"

    # Register
    r = client.post("/auth/register", json={"email": email, "password": "Password123!"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data

    # Login
    r2 = client.post("/auth/login", json={"email": email, "password": "Password123!"})
    assert r2.status_code == 200, r2.text
    data2 = r2.json()
    assert "access_token" in data2
    assert "refresh_token" in data2

    # Refresh
    r3 = client.post("/auth/refresh", json={"refresh_token": data2["refresh_token"]})
    assert r3.status_code == 200, r3.text
    data3 = r3.json()
    assert "access_token" in data3
    assert data3["refresh_token"] == data2["refresh_token"]


def test_login_wrong_password() -> None:
    email = f"b-{uuid.uuid4().hex}@example.com"

    # Ensure user exists
    client.post("/auth/register", json={"email": email, "password": "Password123!"})

    r = client.post("/auth/login", json={"email": email, "password": "wrong"})
    assert r.status_code == 401
