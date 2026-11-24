"""沙箱的「刹车」：总时间预算 + 输出截断。

`SandboxWorkspace` 管的是「别改坏原目录」「路径出不去」，
`runner` 管的是「怎么跑 pytest」。这一层补的是另外两件事：

1. 一个修复任务最多能花多少时间 —— 死循环不能把服务拖死；
2. 单次输出最多留多少 —— 一个打印十万行的测试不能把内存和 prompt 撑爆。

两条都是**硬上限**，触发后统一表现为 `RunResult(passed=False)`，由上层标记 failed。
"""

from __future__ import annotations

import time

# 单次运行保留的最大字符数（stdout / stderr 各自独立计算）
MAX_OUTPUT = 8_000

# 截断标记。放在文本开头，因为保留下来的永远是「尾部」——
# pytest 的结论在最后几行，头部的环境信息价值最低。
TRUNCATION_MARKER = "\n…[输出已截断]…\n"


class BudgetExceeded(RuntimeError):
    """总时间预算已经用完。"""


class TimeBudget:
    """一个修复任务的总时间预算。

    用法::

        budget = TimeBudget(120)          # 整个任务最多 120 秒
        result = run_pytest(root, budget=budget)
        # 每次只拿走 min(timeout, 剩余预算)；预算见底后不再启动新的子进程

    用 ``time.monotonic()`` 计时，不受系统时钟调整影响。
    """

    def __init__(self, total_seconds: float) -> None:
        if total_seconds <= 0:
            raise ValueError("总时间预算必须大于 0")
        self.total_seconds = float(total_seconds)
        self._started = time.monotonic()
        self._deadline = self._started + self.total_seconds

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self._started

    @property
    def remaining(self) -> float:
        return max(0.0, self._deadline - time.monotonic())

    @property
    def expired(self) -> bool:
        return self.remaining <= 0.0

    def clamp(self, timeout: float) -> float:
        """把单次 timeout 压到剩余预算之内。"""
        return max(0.0, min(float(timeout), self.remaining))

    def check(self) -> None:
        """预算已耗尽时抛 `BudgetExceeded`。"""
        if self.expired:
            raise BudgetExceeded(f"总时间预算 {self.total_seconds:g}s 已用完")


def truncate_output(text: str | None, limit: int = MAX_OUTPUT) -> tuple[str, bool]:
    """超长输出截断，并留下明确标记。

    返回 ``(文本, 是否被截断)``。保尾部、丢开头，并在开头补一行标记，
    这样既保住了 pytest 的结论行，又能让模型 / 前端知道「这里不完整」。
    """
    text = text or ""
    if len(text) <= limit:
        return text, False
    keep = max(limit - len(TRUNCATION_MARKER), 0)
    return TRUNCATION_MARKER + (text[-keep:] if keep else ""), True
