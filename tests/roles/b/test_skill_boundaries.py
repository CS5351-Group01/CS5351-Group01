"""B 角色补充测试：边界与异常情况（对应 Week 11 任务）"""
import pytest
from pathlib import Path
from agent.skills import Workspace, Skills, resolve_within
from agent.memory import Memory
from agent.patch import extract_code_block

# 准备一个干净的测试环境
@pytest.fixture
def ws(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "mod.py").write_text("def f():\n    return 42\n", encoding="utf-8")
    return Workspace(tmp_path)

# 1. ls 不存在的路径 → 返回「不存在」，不抛异常
def test_ls_nonexistent_path(ws):
    result = ws.ls("does_not_exist")
    assert "不存在" in result

# 2. ls 一个文件 → 返回文件名
def test_ls_a_file(ws):
    result = ws.ls("pkg/mod.py")
    assert result == "mod.py"

# 3. read 一个目录 → 返回「不是文件」
def test_read_a_directory(ws):
    result = ws.read("pkg")
    assert "不是文件" in result

# 4. write 带 ../ 的路径 → 抛 PermissionError
def test_write_path_traversal(ws):
    with pytest.raises(PermissionError):
        # 注意 write 的参数格式是 "路径\n内容"
        ws.write("../hack.py\nprint('hacked')")

# 5. grep 用「关键词 in 子目录」的写法能定位
def test_grep_with_subpath(ws):
    result = ws.grep("return 42 in pkg")
    assert "pkg/mod.py" in result
    assert "return 42" in result

# 6. Memory 超过 limit 时丢掉最旧的
def test_memory_limit_drops_oldest():
    mem = Memory(limit=2) # 限制只能存 2 条
    mem.add("user", "msg1")
    mem.add("assistant", "msg2")
    mem.add("user", "msg3") # 存入第 3 条，最早的 msg1 应该被丢弃
    recent = mem.recent(10) # 取最近的
    assert len(recent) == 2
    assert recent[0].content == "msg2" # 确认第一条是 msg2，msg1 被删了
    assert recent[1].content == "msg3"

# 7. extract_code_block：只有开头围栏、没有结尾围栏 → 返回 None
def test_extract_code_block_unclosed_fence():
    reply = "修改如下：\n```python\nprint('hi')\n" # 故意不写结尾的 ```
    result = extract_code_block(reply)
    assert result is None