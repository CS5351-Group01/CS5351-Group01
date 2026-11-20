"""补丁解析与落盘。"""

from __future__ import annotations

from agent.patch import extract_code_block, strip_fences, write_atomic


def test_extract_plain_fence():
    reply = "好的，修改如下：\n\n```python\nprint('hi')\n```\n"
    assert extract_code_block(reply) == "print('hi')\n"


def test_extract_fence_without_language():
    assert extract_code_block("```\nx = 1\n```") == "x = 1\n"


def test_extract_returns_none_without_fence():
    assert extract_code_block("我改好了，你去试试吧") is None
    assert extract_code_block("") is None


def test_extract_takes_first_block_only():
    reply = "```python\na = 1\n```\n然后再来一个\n```python\nb = 2\n```"
    assert extract_code_block(reply) == "a = 1\n"


def test_strip_fences_leaves_plain_text():
    result = strip_fences("前言\n```python\nx=1\n```\n后记")
    assert "```" not in result
    assert "x=1" in result
    assert result.startswith("前言") and result.endswith("后记")


def test_write_atomic_replaces_file(tmp_path):
    target = tmp_path / "sub" / "a.py"
    write_atomic(target, "old = 1\n")
    write_atomic(target, "new = 2\n")
    assert target.read_text(encoding="utf-8") == "new = 2\n"
    assert not (tmp_path / "sub" / "a.py.tmp").exists()
