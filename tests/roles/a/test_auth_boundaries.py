"""A 层边界测试：认证、上传大小、重复注册、空文件、未登录。"""

from __future__ import annotations

import base64
import uuid

from app.services.auth import create_access_token


def _decoded_segment(segment: str) -> bytes:
    """把 JWT 的一段 base64url 还原成字节（补上省略的填充）。"""
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def test_expired_token_rejected(client):
    """过期 token 必须被拒绝。"""
    token = create_access_token("1", expires_in=-1)
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_tampered_signature_rejected(client, auth_headers):
    """改掉签名段中间一个字符后，token 必须失效。

    不能改最后一位：base64 最后一个字符只有 2 个有效 bit，
    翻转它可能解码出完全相同的签名字节，断言会假绿。
    """
    token = auth_headers["Authorization"].removeprefix("Bearer ")
    head, body, signature = token.split(".")
    middle = len(signature) // 2
    replacement = "A" if signature[middle] != "A" else "B"
    tampered_signature = signature[:middle] + replacement + signature[middle + 1 :]

    # 先确认签名内容真的变了，防止测试空翻
    assert _decoded_segment(tampered_signature) != _decoded_segment(signature)

    tampered = f"{head}.{body}.{tampered_signature}"
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
