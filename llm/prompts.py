"""Prompt 模板。改这里就能整体调整模型行为，不用动流程代码。"""

from __future__ import annotations

SYSTEM_RULES = """你是一个代码修复助手。
规则：
1. 只输出修复后的**完整文件内容**，放在一个 ```python 代码块里。
2. 不要输出解释、不要输出 diff、不要在代码块外写任何东西。
3. 保持原有的函数名、文件名和对外接口不变。
4. 只改导致测试失败的部分，不要顺手重构。
"""


def build_fix_prompt(
    *,
    filename: str,
    source: str,
    feedback: str | None,
    iteration: int,
    max_iters: int,
) -> str:
    """把当前代码 + 上一次的失败信息拼成一次修复请求。"""
    parts = [
        SYSTEM_RULES,
        f"第 {iteration} / {max_iters} 轮。",
        f"文件名：{filename}",
        "当前代码：",
        f"```python\n{source.rstrip()}\n```",
    ]

    if feedback:
        parts.append("上一次修复后，验证仍然失败，输出如下：")
        parts.append(f"```\n{feedback.rstrip()}\n```")
        parts.append("请根据这个失败信息给出新的完整文件。")

    return "\n\n".join(parts)
