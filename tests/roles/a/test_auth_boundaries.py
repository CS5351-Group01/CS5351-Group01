"""A 层边界测试：认证、上传大小、重复注册、空文件、未登录。"""

from __future__ import annotations

import base64
import uuid

from app.services.auth import create_access_token


def _decoded_segment(segment: str) -> bytes:
    """把 JWT 的一段 base64url 还原成字节（补上省略的填充）。"""
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def _new_user(client) -> dict[str, str]:
    """注册并登录一个全新用户，返回 Authorization 头。"""
    email = f"u{uuid.uuid4().hex[:10]}@example.com"
    password = "secret123"

    created = client.post("/auth/register", json={"email": email, "password": password})
    assert created.status_code == 201

    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


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


def test_exe_extension_current_behavior(client, auth_headers):
    """先锁定现状：后端没有扩展名白名单，.exe 目前也能建任务。

    这是记录「当前行为」的回归测试。以后如果加了白名单改成 400，
    这个用例会红，提醒同步更新预期并补真正的拒绝测试。
    """
    response = client.post(
        "/tasks",
        headers=auth_headers,
        files={"file": ("virus.exe", b"print('hi')\n", "application/octet-stream")},
    )
    assert response.status_code == 201
    assert response.json()["filename"] == "virus.exe"


def test_other_user_cannot_read_task(client):
    """B 用自己的 token 读 A 的任务，必须 404，不能是 200 或 403。"""
    alice = _new_user(client)
    bob = _new_user(client)

    created = client.post(
        "/tasks",
        headers=alice,
        files={"file": ("mine.py", b"print('hi')\n", "text/x-python")},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    response = client.get(f"/tasks/{task_id}", headers=bob)
    assert response.status_code == 404


def test_password_length_boundary(client):
    """密码 5 位注册 422，6 位（下限）注册 201。"""
    short_email = f"short{uuid.uuid4().hex[:10]}@example.com"
    exact_email = f"exact{uuid.uuid4().hex[:10]}@example.com"

    short = client.post("/auth/register", json={"email": short_email, "password": "12345"})
    assert short.status_code == 422

    exact = client.post("/auth/register", json={"email": exact_email, "password": "123456"})
    assert exact.status_code == 201


def test_token_for_missing_user_rejected(client):
    """签名合法但 sub 对应用户不存在，GET /auth/me 必须 401。"""
    token = create_access_token("99999")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
