#!/usr/bin/env python3
"""批量跑修复实验，输出一张对照表。

  python -m eval.run_experiments                 # 用假模型（不联网）
  LLM_API_KEY=xxx python -m eval.run_experiments # 用真模型

评估层干的事：拿一堆已知错例，跑闭环，统计修好几条、平均几轮。
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

from llm.client import FakeLLM, default_client, describe_client
from llm.iterative_fix import repair_project

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


@dataclass
class CaseResult:
    case: str
    success: bool
    iterations: int
    duration_s: float
    message: str


def discover_cases() -> list[Path]:
    """每个带 tests/ 的目录算一个用例。

    支持两层：`examples/<case>/` 和 `examples/hard/<case>/`。
    难例单独放一层，是为了让「假模型修不了」成为一条**可断言的测试**，
    而不是让 F 的回归测试集体变红。
    """
    if not EXAMPLES_DIR.is_dir():
        return []
    cases: list[Path] = []
    for path in sorted(EXAMPLES_DIR.iterdir()):
        if not path.is_dir():
            continue
        if (path / "tests").is_dir():
            cases.append(path)
            continue
        for sub in sorted(path.iterdir()):
            if sub.is_dir() and (sub / "tests").is_dir():
                cases.append(sub)
    return cases


def is_hard_case(case: Path) -> bool:
    """是否属于难例目录（`examples/hard/` 下）。"""
    try:
        return "hard" in case.relative_to(EXAMPLES_DIR).parts
    except ValueError:
        return False


def pick_target(case: Path) -> str | None:
    """用例根目录下唯一那个 .py（conftest.py 除外）就是待修文件。"""
    candidates = [
        item.name for item in case.iterdir()
        if item.is_file() and item.suffix == ".py" and item.name != "conftest.py"
    ]
    return candidates[0] if len(candidates) == 1 else None


def run_case(case: Path, client, max_iters: int) -> CaseResult:
    started = time.perf_counter()
    target = pick_target(case)
    if target is None:
        return CaseResult(
            case=case.name,
            success=False,
            iterations=0,
            duration_s=0.0,
            message="找不到唯一的待修文件",
        )
    outcome = repair_project(case, target, max_iters=max_iters, client=client)
    return CaseResult(
        case=case.name,
        success=outcome.success,
        iterations=outcome.iterations,
        duration_s=round(time.perf_counter() - started, 2),
        message=outcome.message,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="批量修复实验")
    parser.add_argument("--max-iters", type=int, default=3)
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    cases = discover_cases()
    if not cases:
        print(f"{EXAMPLES_DIR} 下没有带 tests/ 的用例")
        return 1

    client = default_client()
    identity = describe_client(client)
    print(f"客户端: {identity}")
    if "FakeLLM" in identity:
        print("⚠️  这一份结果来自假模型，不能写进真模型报告。")
    print()

    results = [run_case(case, client, args.max_iters) for case in cases]

    if args.json:
        payload = {"client": identity, "results": [asdict(r) for r in results]}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"{'用例':<24}{'结果':<8}{'轮数':<6}{'耗时':<8}说明")
    print("-" * 70)
    for r in results:
        print(f"{r.case:<24}{'PASS' if r.success else 'FAIL':<8}"
              f"{r.iterations:<6}{r.duration_s:<8}{r.message}")

    passed = sum(1 for r in results if r.success)
    print("-" * 70)
    print(f"通过 {passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
