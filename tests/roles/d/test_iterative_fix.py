"""闭环修复：假模型能不能把示例修好。"""

from __future__ import annotations

from pathlib import Path

from llm.client import FakeLLM
from llm.iterative_fix import repair_project, repair_source

EXAMPLE = Path(__file__).resolve().parents[3] / "examples" / "broken_project"


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
    from llm.client import LLMClient

    class NoCodeClient(LLMClient):
        def complete(self, prompt: str) -> str:
            return "我觉得应该这样改，你自己看着办。"

    outcome = repair_source("x = 1\n", max_iters=2, client=NoCodeClient())
    assert outcome.success is False
    assert "没有代码块" in outcome.report
