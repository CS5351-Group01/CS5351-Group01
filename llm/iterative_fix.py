"""闭环修复：生成 → 落盘到沙箱 → 跑测试 → 用失败信息再生成。

这是整个项目的核心循环。三个角色在这里交汇：
  · llm 层：怎么问模型、怎么解析回复
  · sandbox 层：在哪儿验证
  · agent 层：补丁怎么落盘
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from agent.patch import extract_code_block
from llm.client import FakeLLM, LLMClient
from llm.prompts import build_fix_prompt
from sandbox.runner import check_syntax, run_pytest
from sandbox.workspace import SandboxWorkspace
from sandbox.limits import TimeBudget  # 🌟 新增：导入 C 同学写的时间预算类

SMOKE_TEST = """\
import target  # noqa: F401


def test_module_imports():
    assert target is not None
"""


@dataclass
class RepairOutcome:
    success: bool
    iterations: int
    final_code: str
    message: str
    report: str = ""
    history: list[str] = field(default_factory=list)


def repair_project(
    project_root: Path | str,
    target: str,
    *,
    max_iters: int = 3,
    client: LLMClient | None = None,
    test_target: str | None = None,
) -> RepairOutcome:
    """对 project_root 里的 target 文件做迭代修复。

    project_root 不会被改动 —— 全程在副本里跑。
    """
    client = client or FakeLLM()
    history: list[str] = []
    feedback: str | None = None
    last_code = ""
    budget = TimeBudget(120)  # 🌟 新增：为整个任务设置 120 秒总预算

    with SandboxWorkspace(project_root) as workspace:
        last_code = workspace.read(target)

        for iteration in range(1, max_iters + 1):
            prompt = build_fix_prompt(
                filename=target,
                source=last_code,
                feedback=feedback,
                iteration=iteration,
                max_iters=max_iters,
            )
            reply = client.complete(prompt)
            candidate = extract_code_block(reply)

            if candidate is None:
                message = f"第 {iteration} 轮：模型回复里没有代码块"
                history.append(message)
                feedback = "你的回复里没有 ```python 代码块，请只输出完整文件。"
                continue

            workspace.write(target, candidate)
            last_code = candidate

            # 🌟 修改：传入 budget
            result = run_pytest(workspace.root, target=test_target, budget=budget)
            history.append(f"第 {iteration} 轮：{result.summary}")

            # 🌟 新增：超时直接退出，不浪费后续轮次
            if result.timed_out:
                return RepairOutcome(
                    success=False,
                    iterations=iteration,
                    final_code=candidate,
                    message=result.failure_reason(),
                    history=history,
                )

            if result.passed:
                return RepairOutcome(
                    success=True,
                    iterations=iteration,
                    final_code=candidate,
                    message=f"第 {iteration} 轮修复通过",
                    history=history,
                )

            feedback = result.as_feedback()

    return RepairOutcome(
        success=False,
        iterations=len(history),
        final_code=last_code,
        message=f"{max_iters} 轮内未能修复",
        report="\n".join(history),
        history=history,
    )


def repair_source(
    source_code: str,
    *,
    max_iters: int = 3,
    client: LLMClient | None = None,
    timeout: float = 60.0,
) -> RepairOutcome:
    """修复用户上传的单文件。

    单文件没有配套测试，所以验证分两层：
      1. 先 py_compile 看语法；
      2. 语法过了再跑一个「能被 import」的冒烟测试。
    """
    client = client or FakeLLM()
    budget = TimeBudget(120)  # 🌟 新增：为整个任务设置 120 秒总预算

    with SandboxWorkspace() as workspace:
        workspace.write("target.py", source_code)
        workspace.write("tests/test_smoke.py", SMOKE_TEST)

        current = source_code
        history: list[str] = []
        feedback: str | None = None

        for iteration in range(1, max_iters + 1):
            syntax = check_syntax(workspace.root, "target.py")
            if not syntax.passed:
                feedback = syntax.as_feedback()

            prompt = build_fix_prompt(
                filename="target.py",
                source=current,
                feedback=feedback,
                iteration=iteration,
                max_iters=max_iters,
            )
            reply = client.complete(prompt)
            candidate = extract_code_block(reply)
            if candidate is None:
                history.append(f"第 {iteration} 轮：回复里没有代码块")
                feedback = "请只输出完整文件的 ```python 代码块。"
                continue

            workspace.write("target.py", candidate)
            current = candidate

            syntax = check_syntax(workspace.root, "target.py")
            if not syntax.passed:
                history.append(f"第 {iteration} 轮：语法仍不通过")
                feedback = syntax.as_feedback()
                continue

            # 🌟 修改：传入 budget
            result = run_pytest(workspace.root, target="tests/test_smoke.py", timeout=timeout, budget=budget)
            history.append(f"第 {iteration} 轮：{result.summary}")

            # 🌟 新增：超时直接退出
            if result.timed_out:
                return RepairOutcome(
                    success=False,
                    iterations=iteration,
                    final_code=candidate,
                    message=result.failure_reason(),
                    history=history,
                )

            if result.passed:
                return RepairOutcome(
                    success=True,
                    iterations=iteration,
                    final_code=candidate,
                    message=f"第 {iteration} 轮修复通过",
                    history=history,
                )
            feedback = result.as_feedback()

    return RepairOutcome(
        success=False,
        iterations=len(history),
        final_code=current,
        message=f"{max_iters} 轮内未能修复",
        report="\n".join(history),
        history=history,
    )