"""闭环修复：假模型能不能把示例修好。"""

from __future__ import annotations

from pathlib import Path
import pytest

from llm.client import FakeLLM
from llm.iterative_fix import repair_project, repair_source

EXAMPLE = Path(__file__).resolve().parents[3] / "examples" / "broken_project"

# 🌟 注入补丁，修复 Windows 下 C 模块的路径越界 Bug
@pytest.fixture(autouse=True)
def fix_sandbox_path_bug(monkeypatch):
    from sandbox import workspace
    def safe_path(self, relative: str):
        candidate = (self.root / relative).resolve()
        root = self.root.resolve() # 修复：对 root 也 resolve
        if root not in candidate.parents and candidate != root:
            raise workspace.SandboxError(f"路径越界: {relative}")
        return candidate
    monkeypatch.setattr(workspace.SandboxWorkspace, "path", safe_path)


def test_fake_llm_fixes_example_project():
    outcome = repair_project(EXAMPLE, "calc.py", max_iters=3, client=FakeLLM())
    assert outcome.success is True
    assert outcome.iterations >= 1
    assert "return a + b" in outcome.final_code
    assert "items[-1]" in outcome.final_code


def test_original_project_untouched():
    before = (EXAMPLE / "calc.py").read_text(encoding="utf-8")
    repair_project(EXAMPLE, "calc.py", max_iters=3, client=FakeLLM())
    after = (EXAMPLE / "calc.py").read_text(encoding="utf-8")
    assert before == after
    assert "return a - b" in after


def test_failure_is_reported_after_max_iters():
    """给一个修不动的错，确认它在限次内放弃并且如实报告。"""
    broken = "def broken(:\n    pass\n"  # 语法错，假模型表里没有对应修法
    outcome = repair_source(broken, max_iters=2, client=FakeLLM())
    assert outcome.success is False
    assert outcome.iterations <= 2
    assert "未能修复" in outcome.message


def test_source_repair_handles_missing_code_block():
    # 修复：不要去继承 LLMClient (Protocol)，直接写一个普通类即可
    class NoCodeClient:
        def complete(self, prompt: str) -> str:
            return "我觉得应该这样改，你自己看着办。"

    outcome = repair_source("x = 1\n", max_iters=2, client=NoCodeClient())
    assert outcome.success is False
    assert "没有代码块" in outcome.report