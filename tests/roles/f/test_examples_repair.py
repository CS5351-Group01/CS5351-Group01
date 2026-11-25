"""评估层的基础保证。

三条一起才有意义：
  · 每个用例必须**真的是坏的** —— 有人改成正确代码，用例就失去意义
  · 简单用例必须**能被假模型修好** —— 否则模型层悄悄失效也没人发现
  · 难例必须**修不好** —— 否则说明它不够难，区分度是假的
"""

from __future__ import annotations

import pytest

from eval.run_experiments import EXAMPLES_DIR, discover_cases, is_hard_case, pick_target
from llm.client import FakeLLM
from llm.iterative_fix import repair_project
from sandbox.runner import run_pytest

ALL_CASES = discover_cases()
SIMPLE_CASES = [c for c in ALL_CASES if not is_hard_case(c)]
HARD_CASES = [c for c in ALL_CASES if is_hard_case(c)]


def ids(path):
    return str(path.relative_to(EXAMPLES_DIR))


@pytest.mark.parametrize("case", ALL_CASES, ids=ids)
def test_each_example_is_actually_broken(case):
    """用例必须处于「测试挂掉」的状态，否则它就不是一个错例。"""
    result = run_pytest(case)
    assert result.passed is False, f"{case.name} 的测试本来就是绿的，它不该被当作错例"


@pytest.mark.parametrize("case", SIMPLE_CASES, ids=ids)
def test_each_simple_example_can_be_repaired(case):
    """简单用例：假模型必须在 3 轮内修好。"""
    target = pick_target(case)
    assert target, f"{case.name} 根目录下找不到唯一的待修文件"

    outcome = repair_project(case, target, max_iters=3, client=FakeLLM())
    assert outcome.success, f"{case.name} 没修好：{outcome.report}"


@pytest.mark.parametrize("case", HARD_CASES, ids=ids)
def test_each_hard_example_resists_fake_llm(case):
    """难例：假模型必须修不了。

    这条才是「区分度」的证据——如果假模型也能修好，
    说明这个用例根本没比简单用例难，实验结论就没有说服力。
    """
    target = pick_target(case)
    assert target, f"{case.name} 根目录下找不到唯一的待修文件"

    outcome = repair_project(case, target, max_iters=3, client=FakeLLM())
    assert outcome.success is False, f"{case.name} 被假模型修好了，它不够难"


def test_corpus_has_both_difficulties():
    """语料必须同时有简单和难的，否则实验区分不出模型能力。"""
    assert len(SIMPLE_CASES) >= 5, f"简单用例只有 {len(SIMPLE_CASES)} 个，太薄"
    assert len(HARD_CASES) >= 2, f"难例只有 {len(HARD_CASES)} 个，区分度不足"
