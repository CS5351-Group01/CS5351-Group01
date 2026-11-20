"""Agent 技能与路径安全。"""

from __future__ import annotations

import pytest

from agent.core import Agent
from agent.skills import Skills, Workspace


@pytest.fixture
def ws(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "mod.py").write_text("def f():\n    return 42\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    return Workspace(tmp_path)


def test_ls_lists_entries(ws):
    listing = ws.ls(".")
    assert "pkg/" in listing
    assert "README.md" in listing


def test_read_file(ws):
    assert "return 42" in ws.read("pkg/mod.py")


def test_grep_finds_line(ws):
    hits = ws.grep("return 42")
    assert "pkg/mod.py:2:" in hits


def test_grep_with_subpath(ws):
    assert "pkg/mod.py:2:" in ws.grep("return 42 in pkg")
    assert "路径不存在" in ws.grep("return 42 in nowhere")


def test_grep_reports_miss(ws):
    assert "没找到" in ws.grep("不存在的关键字")


def test_write_creates_nested_file(ws):
    ws.write("a/b/c.py\nx = 1\n")
    assert (ws.root / "a" / "b" / "c.py").read_text(encoding="utf-8") == "x = 1\n"


@pytest.mark.parametrize("bad", ["../outside.py", "../../etc/passwd", "pkg/../../x.py"])
def test_path_traversal_blocked(ws, bad):
    with pytest.raises(PermissionError):
        ws.path(bad)


def test_agent_dispatches_skill(ws):
    agent = Agent()
    agent.register_all(Skills(workspace=ws).registry)
    assert "42" in agent.run("read: pkg/mod.py")


def test_agent_handles_unknown_command(ws):
    agent = Agent()
    agent.register_all(Skills(workspace=ws).registry)
    assert "未识别指令" in agent.run("rm -rf /")


def test_agent_records_memory(ws):
    agent = Agent()
    agent.register_all(Skills(workspace=ws).registry)
    agent.run("ls: .")
    assert len(agent.memory.recent()) == 2  # 一问一答
