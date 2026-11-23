"""在沙箱里跑 pytest，把结果变成结构化数据。

不做 shell=True，参数一律走列表，避免命令行注入。
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from sandbox.limits import MAX_OUTPUT, TimeBudget, truncate_output


@dataclass
class RunResult:
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False
    truncated: bool = False

    @property
    def summary(self) -> str:
        if self.timed_out:
            return "超时"
        tail = (self.stdout or self.stderr).strip().splitlines()
        return tail[-1] if tail else f"exit={self.exit_code}"

    def as_feedback(self) -> str:
        """给模型看的失败信息，裁剪到合理长度（带「已截断」标记）。"""
        body, _ = truncate_output((self.stdout + "\n" + self.stderr).strip())
        return f"exit_code={self.exit_code}\n{body}"


def run_pytest(
    root: Path | str,
    target: str | None = None,
    timeout: float = 60.0,
    budget: TimeBudget | None = None,
) -> RunResult:
    """在 root 目录里跑 pytest。

    参数：
      root    沙箱根目录
      target  只跑某个文件/目录（相对 root），None 表示全跑
      timeout 单次最长秒数
      budget  整个修复任务的总时间预算；给了就取 min(timeout, 剩余预算)，
              预算见底后不再启动子进程，直接判本轮失败
    """
    root = Path(root).resolve()

    if budget is not None:
        exhausted = f"总时间预算 {budget.total_seconds:g}s 已用完，任务中止"
        if budget.expired:
            return RunResult(
                passed=False, exit_code=-1, stdout="", stderr=exhausted,
                duration_ms=0, timed_out=True,
            )
        timeout = budget.clamp(timeout)
        if timeout <= 0:
            return RunResult(
                passed=False, exit_code=-1, stdout="", stderr=exhausted,
                duration_ms=0, timed_out=True,
            )

    command = [
        sys.executable, "-m", "pytest",
        "-q", "--no-header",
        "-p", "no:cacheprovider",       # 不写 .pytest_cache
        "-o", "addopts=",               # 忽略外层项目的 pytest 配置
    ]
    if target:
        command.append(target)

    started = time.perf_counter()
    try:
        proc = subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        elapsed = int((time.perf_counter() - started) * 1000)
        stdout, out_cut = truncate_output(proc.stdout)
        stderr, err_cut = truncate_output(proc.stderr)
        return RunResult(
            passed=proc.returncode == 0,
            exit_code=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            duration_ms=elapsed,
            truncated=out_cut or err_cut,
        )
    except subprocess.TimeoutExpired:
        elapsed = int((time.perf_counter() - started) * 1000)
        timeout_msg = (
            f"总时间预算 {budget.total_seconds:g}s 已用完，任务中止"
            if budget is not None
            else f"pytest 超过 {timeout} 秒未结束"
        )
        return RunResult(
            passed=False,
            exit_code=-1,
            stdout="",
            stderr=timeout_msg,
            duration_ms=elapsed,
            timed_out=True,
        )
    except OSError as exc:
        # cwd 不存在 / 解释器起不来：同样按「运行失败」返回，不能把异常抛给调用方。
        elapsed = int((time.perf_counter() - started) * 1000)
        return RunResult(
            passed=False,
            exit_code=-1,
            stdout="",
            stderr=f"无法在 {root} 下启动 pytest：{exc}",
            duration_ms=elapsed,
        )


def check_syntax(root: Path | str, target: str) -> RunResult:
    """只做语法检查，用于「没有测试文件」时的兜底验证。"""
    root = Path(root).resolve()
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", target],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        elapsed = int((time.perf_counter() - started) * 1000)
        return RunResult(
            passed=False,
            exit_code=-1,
            stdout="",
            stderr=f"无法在 {root} 下执行 py_compile：{exc}",
            duration_ms=elapsed,
        )
    elapsed = int((time.perf_counter() - started) * 1000)
    stdout, out_cut = truncate_output(proc.stdout)
    stderr, err_cut = truncate_output(proc.stderr)
    return RunResult(
        passed=proc.returncode == 0,
        exit_code=proc.returncode,
        stdout=stdout,
        stderr=stderr,
        duration_ms=elapsed,
        truncated=out_cut or err_cut,
    )
