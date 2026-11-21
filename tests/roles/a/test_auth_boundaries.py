"""A 层边界测试：认证、上传大小、重复注册、空文件、未登录。"""

from __future__ import annotations

import uuid

from app.services.auth import create_access_token


def test_expired_token_rejected(client):
    """过期 token 必须被拒绝。"""
    token = create_access_token("1", expires_in=-1)
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_tampered_signature_rejected(client, auth_headers):
    """改掉签名段一个字符后，token 必须失效。"""
    token = auth_headers["Authorization"].removeprefix("Bearer ")
    head, body, signature = token.split(".")
    flipped = ("A" if signature[-1] != "A" else "B")
    tampered = f"{head}.{body}.{signature[:-1]}{flipped}"

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {tampered}"})
    assert response.status_code == 401


def test_oversized_upload_rejected(client, auth_headers):
    """1MB + 1 字节的文件必须在落盘前被拒。"""
    too_big = b"x" * 1_000_001
    response = client.post(
        "/tasks",
        headers=auth_headers,
        files={"file": ("big.py", too_big, "text/x-python")},
    )
    assert response.status_code == 400


def test_duplicate_email_rejected(client):
    """同一邮箱注册两次，第二次必须是 400。"""
    email = f"dup{uuid.uuid4().hex[:10]}@example.com"
    payload = {"email": email, "password": "secret123"}

    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 400


def test_empty_file_creates_task(client, auth_headers):
    """空文件也要能建任务（后台修复失败是另一回事）。"""
    response = client.post(
        "/tasks",
        headers=auth_headers,
        files={"file": ("empty.py", b"", "text/x-python")},
    )
    assert response.status_code == 201
    assert response.json()["filename"] == "empty.py"


def test_list_tasks_requires_auth(client):
    """不带 Authorization 访问任务列表必须是 401。"""
    response = client.get("/tasks")
    assert response.status_code == 401
