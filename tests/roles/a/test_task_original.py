"""原始代码接口：给前端做「修复前后对比」用。"""

from __future__ import annotations

import uuid

SOURCE = 'def add(a, b):\n    return a + b\n'


def _register_and_login(client) -> dict:
    email = f"o{uuid.uuid4().hex[:10]}@example.com"
    password = "secret123"
    client.post("/auth/register", json={"email": email, "password": password})
    token = client.post("/auth/login", json={"email": email, "password": password}).json()
    return {"Authorization": f"Bearer {token['access_token']}"}


def _upload(client, headers, filename="target.py", content=SOURCE) -> int:
    response = client.post(
        "/tasks",
        files={"file": (filename, content.encode("utf-8"), "text/x-python")},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_original_returns_exactly_what_was_uploaded(client, auth_headers):
    task_id = _upload(client, auth_headers)

    response = client.get(f"/tasks/{task_id}/original", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["content"] == SOURCE
    assert body["filename"] == "target.py"


def test_original_requires_login(client, auth_headers):
    task_id = _upload(client, auth_headers)
    assert client.get(f"/tasks/{task_id}/original").status_code == 401


def test_original_of_another_users_task_is_404(client, auth_headers):
    task_id = _upload(client, auth_headers)
    other = _register_and_login(client)

    assert client.get(f"/tasks/{task_id}/original", headers=other).status_code == 404


def test_original_of_missing_task_is_404(client, auth_headers):
    assert client.get("/tasks/999999/original", headers=auth_headers).status_code == 404


def test_original_does_not_leak_server_path(client, auth_headers):
    """接口只能返回文件内容，不能把服务器上的绝对路径吐出去。

    不靠搜字符串——`str(dict)` 会把换行渲染成 `\\n`，用 `:\\` 判断会误报。
    直接锁定「只有两个字段」+「内容逐字节相同」，多一个字节都算泄漏。
    """
    task_id = _upload(client, auth_headers)

    body = client.get(f"/tasks/{task_id}/original", headers=auth_headers).json()

    assert set(body) == {"filename", "content"}
    assert body["content"] == SOURCE
    assert body["filename"] == "target.py"
