"""沙箱层：隔离执行代码，保证试错不污染原目录。"""

from sandbox.runner import RunResult, check_syntax, run_pytest
from sandbox.workspace import SandboxError, SandboxWorkspace

__all__ = ["RunResult", "SandboxError", "SandboxWorkspace", "check_syntax", "run_pytest"]
