"""沙箱隔离边界（加强版）。

对应 Week 11 沙箱角色的 5 条任务。基础路径已由 test_sandbox.py 覆盖，
这里补的是更硬的断言：

  1) 超时不只是标记位，必须在预算时间内真的把子进程掐断；
  2) 清理必须在「with 块内部抛异常」的路径下也发生；
  3) 源目录不仅内容不变，连 mtime 都不能变；
  4) 相对越界（../）和绝对路径越界都要拒；
  5) 空目录建出来的沙箱必须是空的，且不是源目录本身。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from sandbox.runner import check_syntax, run_pytest
from sandbox.workspace import SandboxError, SandboxWorkspace

EXAMPLE = Path(__file__).resolve().parents[3] / "examples" / "broken_project"


# 1 ------------------------------------------------------------------ 超时
def test_timeout_really_interrupts_within_budget(tmp_path):
    """timeout=1 时必须 1 秒左右中断，而不是等 sleep 自己跑完。"""
    (tmp_path / "test_slow.py").write_text(
        "import time\n\n\ndef test_slow():\n    time.sleep(10)\n",
        encoding="utf-8",
    )

    result = run_pytest(tmp_path, timeout=1.0)

    assert result.timed_out is True
    assert result.passed is False
    assert result.exit_code == -1
    # 下限排除「根本没等」的情况，上限排除「跑满 10 秒才返回」的情况
    assert 900 <= result.duration_ms <= 5_000


# 2 ------------------------------------------------------------------ 清理
def test_workspace_cleans_up_even_when_exception_raised():
    """with 块里抛异常，沙箱目录照样要被删掉。"""
    leaked: Path | None = None

    with pytest.raises(RuntimeError, match="boom"):
        with SandboxWorkspace(EXAMPLE) as ws:
            leaked = ws.root
            assert leaked.exists()
            raise RuntimeError("boom")

    assert leaked is not None
    assert not leaked.exists()


# 3 -------------------------------------------------------------- 原件不动
def test_source_file_untouched_including_mtime():
    """沙箱里改文件，原件的内容和 mtime 都不能变。"""
    target = EXAMPLE / "calc.py"
    before_bytes = target.read_bytes()
    before_mtime = target.stat().st_mtime_ns

    with SandboxWorkspace(EXAMPLE) as ws:
        ws.write("calc.py", "def calc(a, b):\n    return 0\n")
        assert ws.read("calc.py") != before_bytes.decode("utf-8")

    assert target.read_bytes() == before_bytes
    assert target.stat().st_mtime_ns == before_mtime


# 4 ------------------------------------------------------------------ 越界
@pytest.mark.parametrize(
    "bad",
    [
        "../outside.txt",
        "../../../etc/passwd",
        "C:/Windows/win.ini",
    ],
)
def test_path_rejects_traversal_and_absolute(bad):
    """相对越界和绝对路径都必须抛 SandboxError。"""
    with SandboxWorkspace(EXAMPLE) as ws:
        with pytest.raises(SandboxError):
            ws.path(bad)


# 5 -------------------------------------------------------------- 空目录
def test_empty_dir_makes_empty_sandbox(tmp_path):
    """空目录也要能建沙箱，且沙箱本身是空的、不是源目录。"""
    with SandboxWorkspace(tmp_path) as ws:
        assert ws.root.exists()
        assert ws.root.is_dir()
        assert ws.root != tmp_path
        assert list(ws.root.iterdir()) == []


# ---------------------------------------------------------------- Day 3 新增
def test_missing_source_raises_and_leaves_no_temp_dir(monkeypatch, tmp_path):
    """源目录不存在 → 抛 SandboxError，且进入失败时不能泄漏临时目录。"""
    created: list[Path] = []
    real_mkdtemp = tempfile.mkdtemp

    def spy(prefix=None, dir=None):  # noqa: A002 - 跟随 tempfile 的参数名
        p = real_mkdtemp(prefix=prefix, dir=tmp_path)
        created.append(Path(p))
        return p

    monkeypatch.setattr("sandbox.workspace.tempfile.mkdtemp", spy)

    with pytest.raises(SandboxError):
        with SandboxWorkspace(tmp_path / "definitely-missing"):
            pass

    assert created, "应当先创建过临时目录"
    assert not created[0].exists(), "进入失败后临时目录必须被清理"


def test_run_pytest_on_missing_dir_returns_failed(tmp_path):
    """cwd 不存在时不能抛异常、不能挂死，必须返回 passed=False。"""
    result = run_pytest(tmp_path / "no-such-dir", timeout=20)

    assert result.passed is False
    assert result.timed_out is False
    assert result.exit_code != 0
    assert result.stderr.strip() != ""


def test_check_syntax_flags_broken_file(tmp_path):
    """残缺文件必须被判失败，并且 stderr 里要有原因。"""
    (tmp_path / "broken.py").write_text("def f(\n", encoding="utf-8")

    result = check_syntax(tmp_path, "broken.py")

    assert result.passed is False
    assert result.exit_code != 0
    assert result.stderr.strip() != ""


def test_two_sandboxes_are_isolated():
    """先后开两个沙箱：路径不同，互相看不到对方写的文件。"""
    with SandboxWorkspace(EXAMPLE) as first:
        first_root = first.root
        first.write("marker.txt", "only-in-first")

        with SandboxWorkspace(EXAMPLE) as second:
            assert second.root != first_root
            assert not (second.root / "marker.txt").exists()

        assert first_root.exists()
        assert (first_root / "marker.txt").read_text(encoding="utf-8") == "only-in-first"
