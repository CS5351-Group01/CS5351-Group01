"""沙箱：隔离、清理、执行结果。"""

from __future__ import annotations

from pathlib import Path

import pytest

from sandbox.runner import run_pytest
from sandbox.workspace import SandboxWorkspace

EXAMPLE = Path(__file__).resolve().parents[3] / "examples" / "broken_project"


def test_workspace_copies_without_touching_source():
    original = (EXAMPLE / "calc.py").read_text(encoding="utf-8")
    with SandboxWorkspace(EXAMPLE) as ws:
        assert ws.read("calc.py") == original
        ws.write("calc.py", "# 被沙箱改坏了\n")
        assert ws.read("calc.py") == "# 被沙箱改坏了\n"
    # 原文件必须没动
    assert (EXAMPLE / "calc.py").read_text(encoding="utf-8") == original


def test_workspace_is_removed_after_exit():
    with SandboxWorkspace(EXAMPLE) as ws:
        root = ws.root
        assert root.exists()
    assert not root.exists()


def test_workspace_rejects_traversal():
    with SandboxWorkspace(EXAMPLE) as ws:
        with pytest.raises(Exception):
            ws.path("../../../etc/passwd")


def test_pytest_reports_failures():
    with SandboxWorkspace(EXAMPLE) as ws:
        result = run_pytest(ws.root)
    assert result.passed is False
    assert result.exit_code != 0


def test_pytest_passes_on_clean_project(tmp_path):
    (tmp_path / "test_ok.py").write_text(
        "def test_ok():\n    assert 1 + 1 == 2\n", encoding="utf-8"
    )
    result = run_pytest(tmp_path)
    assert result.passed is True
    assert result.exit_code == 0


def test_pytest_timeout(tmp_path):
    (tmp_path / "test_slow.py").write_text(
        "import time\n\n\ndef test_slow():\n    time.sleep(5)\n", encoding="utf-8"
    )
    result = run_pytest(tmp_path, timeout=1.0)
    assert result.passed is False
    assert result.timed_out is True
