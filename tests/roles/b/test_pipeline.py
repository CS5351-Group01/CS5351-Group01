"""测试 Agent 的管道（Pipeline）调度能力。"""
import pytest
from agent.core import Agent
from agent.skills import Skills, Workspace

@pytest.fixture
def agent(tmp_path):
    # 建一个简单的工作区
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    ws = Workspace(tmp_path)
    a = Agent()
    a.register_all(Skills(workspace=ws).registry)
    return a

def test_pipeline_two_commands(agent):
    """1. 正常跑两条指令"""
    result = agent.run("ls: . | read: main.py")
    assert "main.py" in result
    assert "print('hello')" in result

def test_pipeline_with_unknown(agent):
    """2. 管道中有一条无法识别，不应崩溃，其余照常执行"""
    result = agent.run("ls: . | unknown_cmd: xx | read: main.py")
    assert "main.py" in result
    assert "未识别指令" in result
    assert "print('hello')" in result

def test_pipeline_memory_records(agent):
    """3. 管道执行后，记忆应该正确记录每条指令"""
    agent.run("ls: . | read: main.py")
    # 两条指令，每条都有 user 和 assistant，共 4 条记录
    assert len(agent.memory.recent(10)) == 4