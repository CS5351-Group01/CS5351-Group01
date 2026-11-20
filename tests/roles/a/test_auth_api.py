"""认证接口的行为。"""

from __future__ import annotations

import uuid


def _email() -> str:
    return f"t{uuid.uuid4().hex[:10]}@example.com"


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_then_login(client):
    email = _email()
    created = client.post("/auth/register", json={"email": email, "password": "secret123"})
    assert created.status_code == 201
    assert created.json()["email"] == email

    token = client.post("/auth/login", json={"email": email, "password": "secret123"})
    assert token.status_code == 200
    assert token.json()["token_type"] == "bearer"


def test_duplicate_email_rejected(client):
    email = _email()
    assert client.post("/auth/register", json={"email": email, "password": "secret123"}).status_code == 201
    again = client.post("/auth/register", json={"email": email, "password": "secret123"})
    assert again.status_code == 400


def test_wrong_password_rejected(client):
    email = _email()
    client.post("/auth/register", json={"email": email, "password": "secret123"})
    response = client.post("/auth/login", json={"email": email, "password": "wrongpass"})
    assert response.status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert "@example.com" in response.json()["email"]


def test_bad_email_shape_rejected(client):
    response = client.post("/auth/register", json={"email": "not-an-email", "password": "secret123"})
    assert response.status_code == 422
