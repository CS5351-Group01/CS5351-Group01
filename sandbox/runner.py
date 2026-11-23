"""在沙箱里跑 pytest，把结果变成结构化数据。

不做 shell=True，参数一律走列表，避免命令行注入。
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

MAX_OUTPUT = 8_000


@dataclass
class RunResult:
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False

    @property
    def summary(self) -> str:
        if self.timed_out:
            return "超时"
        tail = (self.stdout or self.stderr).strip().splitlines()
        return tail[-1] if tail else f"exit={self.exit_code}"

    def as_feedback(self) -> str:
        """给模型看的失败信息，裁剪到合理长度。"""
        body = (self.stdout + "\n" + self.stderr).strip()
        if len(body) > MAX_OUTPUT:
            body = body[-MAX_OUTPUT:]
        return f"exit_code={self.exit_code}\n{body}"


def run_pytest(root: Path | str, target: str | None = None, timeout: float = 60.0) -> RunResult:
    """在 root 目录里跑 pytest。

    参数：
      root    沙箱根目录
      target  只跑某个文件/目录（相对 root），None 表示全跑
      timeout 秒
    """
    root = Path(root).resolve()
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
        return RunResult(
            passed=proc.returncode == 0,
            exit_code=proc.returncode,
            stdout=proc.stdout[-MAX_OUTPUT:],
            stderr=proc.stderr[-MAX_OUTPUT:],
            duration_ms=elapsed,
        )
    except subprocess.TimeoutExpired:
        elapsed = int((time.perf_counter() - started) * 1000)
        return RunResult(
            passed=False,
            exit_code=-1,
            stdout="",
            stderr=f"pytest 超过 {timeout} 秒未结束",
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
    return RunResult(
        passed=proc.returncode == 0,
        exit_code=proc.returncode,
        stdout=proc.stdout[-MAX_OUTPUT:],
        stderr=proc.stderr[-MAX_OUTPUT:],
        duration_ms=elapsed,
    )
