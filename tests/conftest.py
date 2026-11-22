"""测试公共配置。

必须在导入 app 之前把数据库指到临时文件，
否则测试会往仓库根目录写 app.db。
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_TMP_DIR = Path(tempfile.mkdtemp(prefix="codefix-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP_DIR / 'test.db').as_posix()}"
os.environ.setdefault("APP_SECRET", "test-secret-do-not-use-in-prod")

import pytest  # noqa: E402

# 上传目录也挪到临时目录，否则测试会往仓库根目录扔 storage/
import app.services.storage as _storage  # noqa: E402

_storage.STORAGE_ROOT = _TMP_DIR / "storage"

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_PROJECT = REPO_ROOT / "examples" / "broken_project"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    """注册并登录一个随机用户，返回可直接用的 Authorization 头。"""
    import uuid

    email = f"u{uuid.uuid4().hex[:10]}@example.com"
    password = "secret123"

    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
