"""评估层的基础保证：示例真的坏，且真的能被修好。

两条一起才有意义：
  · 只测「能修好」→ 有人把示例改成正确代码，测试照样绿，但用例失去意义
  · 只测「是坏的」→ 模型完全失效也没人发现
"""

from __future__ import annotations

import pytest

from eval.run_experiments import discover_cases, pick_target
from llm.client import FakeLLM
from llm.iterative_fix import repair_project
from sandbox.runner import run_pytest

CASES = discover_cases()


def ids(path):
    return path.name


@pytest.mark.parametrize("case", CASES, ids=ids)
def test_each_example_is_actually_broken(case):
    """示例项目必须处于「测试挂掉」的状态，否则它就不是一个错例。"""
    result = run_pytest(case)
    assert result.passed is False, f"{case.name} 的测试本来就是绿的，它不该被当作错例"


@pytest.mark.parametrize("case", CASES, ids=ids)
def test_each_example_can_be_repaired(case):
    """每一个错例都能在 3 轮内被假模型修好。"""
    target = pick_target(case)
    assert target, f"{case.name} 根目录下找不到唯一的待修文件"

    outcome = repair_project(case, target, max_iters=3, client=FakeLLM())
    assert outcome.success, f"{case.name} 没修好：{outcome.report}"


def test_there_are_several_cases():
    """数据集太薄会让实验结论没意义，至少留 5 个。"""
    assert len(CASES) >= 5
