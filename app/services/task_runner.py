"""后台任务：把一个待处理任务跑完，并写回状态。

注意：这里自己开 session，因为 BackgroundTasks 在请求结束之后才执行，
不能复用请求作用域里的 db 会话。
"""

from __future__ import annotations

import traceback
from collections.abc import Callable
from pathlib import Path

from app.database import SessionLocal
from app.models import Task

MAX_REPAIR_ITERS = 3


def _round_message(round_no: int, max_iters: int) -> str:
    """给前端状态栏看的每轮提示。"""
    if round_no <= 1:
        return f"第 1/{max_iters} 轮：正在生成修复…"
    return f"第 {round_no}/{max_iters} 轮：上一轮未通过，重新生成…"


class _ProgressClient:
    """包住 LLM 客户端，在每次调用模型前写一次轮次。

    repair_source 每轮固定调用一次 client.complete()，所以调用次数
    就是轮次。这样 A 层不用改 llm/ 也能拿到「第几轮开始了」。
    """

    def __init__(self, inner, on_round: Callable[[int], None]) -> None:
        self._inner = inner
        self._on_round = on_round
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        self._on_round(self.calls)
        return self._inner.complete(prompt)


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


def run_repair_task(
    task_id: int,
    *,
    client=None,
    max_iters: int = MAX_REPAIR_ITERS,
) -> None:
    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if task is None:
            return
        stored_path = Path(task.stored_path)
        source_code = stored_path.read_text(encoding="utf-8", errors="replace")
    finally:
        db.close()

    _update(
        task_id,
        status="running",
        iterations=0,
        message=f"准备修复（最多 {max_iters} 轮）…",
    )

    # 延迟导入：让 application 层不硬依赖 llm 层，方便单独测试
    try:
        from llm.client import default_client
        from llm.iterative_fix import repair_source

        def _on_round(round_no: int) -> None:
            _update(
                task_id,
                iterations=round_no,
                message=_round_message(round_no, max_iters),
            )

        progress = _ProgressClient(client or default_client(), _on_round)
        outcome = repair_source(source_code, max_iters=max_iters, client=progress)
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
