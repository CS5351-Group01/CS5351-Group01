"""模型客户端：一个协议 + 两个实现。

· FakeLLM           —— 确定性假模型，用来跑通流程和写测试，不联网、不花钱
· OpenAICompatClient —— 任何 OpenAI 兼容接口（DeepSeek / Qwen / vLLM 都行）

换模型时不要改调用方，只换注进来的这个对象。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str:  # pragma: no cover - 协议定义
        ...


# ---------------------------------------------------------------- 假模型

# 假模型只会修下面这几处已知错误。它的用途是「让流程可测」，
# 不是「真的会修代码」。真实能力靠 OpenAICompatClient。
#
# 键必须是**整行**（含缩进）。用表达式做局部替换会踩坑：
# 先替换 `return a - b` 之后，如果还有一条以 `return a + b # BUG` 开头
# 的规则，就会把注释尾巴切掉，产出语法错误的代码。
DEMO_FIXES: dict[str, str] = {
    # examples/broken_project —— 逻辑错 + 越界
    "    return a - b  # BUG: 应该是 a + b": "    return a + b",
    "    return items[len(items)]  # BUG: 下标越界，应该是 items[-1]": "    return items[-1]",
    # examples/syntax_error —— 缺冒号
    "def greet(name)": "def greet(name):",
    # examples/name_error —— 函数名拼错
    "    return lenght(items)": "    return len(items)",
    # examples/off_by_one —— 循环少一步
    "    for i in range(len(numbers) - 1):": "    for i in range(len(numbers)):",
    # examples/empty_input —— 空列表除零
    "    return sum(values) / len(values)": "    return sum(values) / len(values) if values else 0.0",
}


class FakeLLM:
    """按预置表做替换的假模型。找不到可修的错就原样返回，从而触发重试直到耗尽。"""

    name = "fake-llm"

    def __init__(self, fixes: dict[str, str] | None = None) -> None:
        self.fixes = dict(fixes or DEMO_FIXES)
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        code = _source_from_prompt(prompt)
        fixed = code
        for wrong, right in self.fixes.items():
            fixed = fixed.replace(wrong, right)
        return f"修好了，整份文件如下：\n\n```python\n{fixed.rstrip()}\n```"


def _source_from_prompt(prompt: str) -> str:
    """从 prompt 里把待修代码抠回来。

    prompts.build_fix_prompt 用固定的围栏包代码，这里按同样的标记取。
    """
    start = prompt.find("```python\n")
    if start == -1:
        return ""
    start += len("```python\n")
    end = prompt.find("```", start)
    if end == -1:
        return ""
    return prompt[start:end]


# ---------------------------------------------------------------- 真模型

class OpenAICompatClient:
    """OpenAI 兼容的 chat/completions 客户端，纯标准库，不装 SDK。"""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL")
                         or "https://api.deepseek.com/v1").rstrip("/")
        self.model = model or os.environ.get("LLM_MODEL", "deepseek-chat")
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.timeout = timeout

    def complete(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("缺少 LLM_API_KEY 环境变量")

        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }).encode()

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            raise RuntimeError(f"模型接口 {exc.code}：{detail}") from exc

        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"模型返回格式异常：{body}") from exc


def default_client() -> LLMClient:
    """有 key 用真模型，没 key 退化成假模型，保证本地能跑。"""
    if os.environ.get("LLM_API_KEY"):
        return OpenAICompatClient()
    return FakeLLM()
