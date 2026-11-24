"""沙箱层：隔离执行代码，保证试错不污染原目录，并且跑不飞。"""

from sandbox.limits import MAX_OUTPUT, BudgetExceeded, TimeBudget, truncate_output
from sandbox.runner import RunResult, check_syntax, run_pytest
from sandbox.workspace import SandboxError, SandboxWorkspace

__all__ = [
    "MAX_OUTPUT",
    "BudgetExceeded",
    "RunResult",
    "SandboxError",
    "SandboxWorkspace",
    "TimeBudget",
    "check_syntax",
    "run_pytest",
    "truncate_output",
]
