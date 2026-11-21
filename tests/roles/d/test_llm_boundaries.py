import pytest
from llm.iterative_fix import repair_source, RepairOutcome
from llm.prompts import build_fix_prompt
from llm.client import DEMO_FIXES

# 🌟 核心补丁：绕过 C 模块在 Windows 下的路径越界 Bug
@pytest.fixture(autouse=True)
def fix_sandbox_path_bug(monkeypatch):
    from sandbox import workspace
    def safe_path(self, relative: str):
        candidate = (self.root / relative).resolve()
        root = self.root.resolve() # 修复：对 self.root 也进行 resolve
        if root not in candidate.parents and candidate != root:
            raise workspace.SandboxError(f"路径越界: {relative}")
        return candidate
    monkeypatch.setattr(workspace.SandboxWorkspace, "path", safe_path)

# ==========================================
# 1. 模型回复里没有代码块
# ==========================================
def test_no_code_block():
    class NoCodeClient:
        def complete(self, prompt: str) -> str:
            return "抱歉，这段代码太复杂了，我无法修复。" # 故意不带代码块

    outcome = repair_source("print(1)", max_iters=1, client=NoCodeClient())
    assert outcome.success is False
    assert "没有代码块" in outcome.report

# ==========================================
# 2. 每次都给错代码（连续失败）
# ==========================================
def test_continuous_failure():
    class WrongCodeClient:
        def complete(self, prompt: str) -> str:
            return "```python\nsyntax error here\n```"

    outcome = repair_source("print(1)", max_iters=3, client=WrongCodeClient())
    assert outcome.success is False
    assert outcome.iterations == 3

# ==========================================
# 3. 空字符串当源码传入
# ==========================================
def test_empty_source():
    class DummyClient:
        def complete(self, prompt: str) -> str:
            return "```python\n# empty\n```"

    outcome = repair_source("", max_iters=1, client=DummyClient())
    assert isinstance(outcome, RepairOutcome)

# ==========================================
# 4. build_fix_prompt 生成的文本里包含原始代码
# ==========================================
def test_prompt_contains_source():
    source_code = "def my_func():\n    return 42"
    prompt = build_fix_prompt(
        filename="test.py",
        source=source_code,
        feedback="NameError: name 'x' is not defined",
        iteration=1,
        max_iters=3
    )
    assert source_code in prompt
    assert "NameError" in prompt

# ==========================================
# 5. 参数化：跑 DEMO_FIXES 确认写完的代码能编译
# ==========================================
@pytest.mark.parametrize("wrong, right", list(DEMO_FIXES.items()))
def test_demo_fixes_compile(wrong, right):
    if right.startswith(" "):
        code_to_compile = f"def dummy_func():\n{right}"
    else:
        code_to_compile = right
    compile(code_to_compile, "<string>", "exec")

# ==========================================
# 6. 数调用次数的假客户端 (max_iters=1)
# ==========================================
def test_call_count():
    class CountingClient:
        def __init__(self):
            self.calls = 0
            
        def complete(self, prompt: str) -> str:
            self.calls += 1
            return "```python\nraise Exception('boom')\n```"
            
    client = CountingClient()
    repair_source("print(1)", max_iters=1, client=client)
    assert client.calls == 1