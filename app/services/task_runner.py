"""后台任务：把一个待处理任务跑完，并写回状态。

注意：这里自己开 session，因为 BackgroundTasks 在请求结束之后才执行，
不能复用请求作用域里的 db 会话。
"""

from __future__ import annotations

import traceback
from pathlib import Path

from app.database import SessionLocal
from app.models import Task


def _update(task_id: int, **fields) -> None:
    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if task is None:
            return
        for key, value in fields.items():
            setattr(task, key, value)
        db.commit()
    finally:
        db.close()


def run_repair_task(task_id: int) -> None:
    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if task is None:
            return
        stored_path = Path(task.stored_path)
        source_code = stored_path.read_text(encoding="utf-8", errors="replace")
    finally:
        db.close()

    _update(task_id, status="running")

    # 延迟导入：让 application 层不硬依赖 llm 层，方便单独测试
    try:
        from llm.iterative_fix import repair_source

        outcome = repair_source(source_code, max_iters=3)
    except Exception as exc:  # noqa: BLE001 - 任何异常都要落到任务状态里
        _update(
            task_id,
            status="failed",
            message=f"{type(exc).__name__}: {exc}",
            result=traceback.format_exc()[-4000:],
        )
        return

    _update(
        task_id,
        status="success" if outcome.success else "failed",
        iterations=outcome.iterations,
        message=outcome.message,
        result=outcome.final_code if outcome.success else outcome.report,
    )
