"""任务进度可见性：修复还在跑的时候，就能轮询到 iterations 在涨。"""

from __future__ import annotations

import threading
import uuid
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.models import Task, User
from app.services.task_runner import run_repair_task

# 这个文件直接建 Task 行，不经过 TestClient；先把表建好（app.main 里也是这句）
Base.metadata.create_all(bind=engine)

SOURCE = "def add(a, b):\n    return a - b\n"
# 语法错的候选：repair_source 会在语法检查处失败直接进下一轮，不用跑 pytest，测试更快
BAD_REPLY = "```python\ndef broken(:\n```"


class _BlockingClient:
    """每轮进入 complete() 时通知测试，并卡住等放行。"""

    def __init__(self, rounds: int) -> None:
        self.entered = [threading.Event() for _ in range(rounds)]
        self.release = [threading.Event() for _ in range(rounds)]
        self.calls = 0

    def complete(self, prompt: str) -> str:
        index = self.calls
        self.calls += 1
        assert index < len(self.entered), "模型调用次数超过预期轮数"
        self.entered[index].set()
        assert self.release[index].wait(10), "测试没有及时放行模型调用"
        return BAD_REPLY

    def release_all(self) -> None:
        for event in self.release:
            event.set()


def _make_task(tmp_path: Path, *, owner_id: int | None = None) -> int:
    source = tmp_path / "target.py"
    source.write_text(SOURCE, encoding="utf-8")

    db = SessionLocal()
    try:
        if owner_id is None:
            user = User(email=f"p{uuid.uuid4().hex[:10]}@example.com", password_hash="x")
            db.add(user)
            db.commit()
            db.refresh(user)
            owner_id = user.id

        task = Task(owner_id=owner_id, filename="target.py", stored_path=str(source))
        db.add(task)
        db.commit()
        db.refresh(task)
        return task.id
    finally:
        db.close()


def _snapshot(task_id: int) -> dict:
    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        assert task is not None
        return {
            "status": task.status,
            "iterations": task.iterations,
            "message": task.message or "",
        }
    finally:
        db.close()


def _start(task_id: int, client, max_iters: int) -> threading.Thread:
    thread = threading.Thread(
        target=run_repair_task,
        args=(task_id,),
        kwargs={"client": client, "max_iters": max_iters},
        daemon=True,
    )
    thread.start()
    return thread


def test_iterations_increase_while_task_is_running(tmp_path):
    """第 1 轮还没放行时就能读到 1，放行后第 2 轮开始能读到 2。"""
    task_id = _make_task(tmp_path)
    llm = _BlockingClient(rounds=2)
    thread = _start(task_id, llm, max_iters=2)
    try:
        assert llm.entered[0].wait(10), "第 1 轮没有开始"
        first = _snapshot(task_id)
        assert first["status"] == "running"
        assert first["iterations"] == 1
        assert "第 1/2 轮" in first["message"]

        llm.release[0].set()
        assert llm.entered[1].wait(10), "第 2 轮没有开始"
        second = _snapshot(task_id)
        assert second["iterations"] == 2
        assert "第 2/2 轮" in second["message"]

        llm.release[1].set()
        thread.join(10)
        assert not thread.is_alive()
    finally:
        llm.release_all()
        thread.join(10)

    final = _snapshot(task_id)
    assert final["status"] == "failed"
    assert final["iterations"] == 2


def test_api_shows_progress_before_repair_finishes(client, auth_headers, tmp_path):
    """前端轮询走的 GET /tasks/{id} 在任务跑完前就能看到轮数。"""
    user_id = client.get("/auth/me", headers=auth_headers).json()["id"]
    task_id = _make_task(tmp_path, owner_id=user_id)

    llm = _BlockingClient(rounds=1)
    thread = _start(task_id, llm, max_iters=1)
    try:
        assert llm.entered[0].wait(10), "第 1 轮没有开始"
        body = client.get(f"/tasks/{task_id}", headers=auth_headers).json()
        assert body["status"] == "running"
        assert body["iterations"] == 1
        assert "第 1/1 轮" in body["message"]

        llm.release[0].set()
        thread.join(10)
        assert not thread.is_alive()
    finally:
        llm.release_all()
        thread.join(10)

    final = client.get(f"/tasks/{task_id}", headers=auth_headers).json()
    assert final["status"] == "failed"
