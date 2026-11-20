"""从模型回复里把代码抠出来，并安全落盘。

为什么让模型返回「整份文件」而不是 diff：
写一个正确的 unified-diff 应用器比写一个正确的整文件替换要难得多，
而修复任务本来就是「给一份错代码，还一份对代码」，整文件更稳。
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_FENCE = re.compile(r"```[a-zA-Z0-9_+-]*\s*\n(.*?)```", re.DOTALL)


def extract_code_block(text: str) -> str | None:
    """取第一个围栏代码块的内容。

    没有围栏时返回 None —— 宁可让调用方重试，也不要瞎猜整篇回复就是代码。
    """
    if not text:
        return None
    match = _FENCE.search(text)
    if match is None:
        return None
    code = match.group(1)
    return code.rstrip() + "\n"


def strip_fences(text: str) -> str:
    """把围栏连同语言标记一起删掉，返回纯文本（用于展示）。"""
    return re.sub(
        r"```[a-zA-Z0-9_+-]*\s*\n(.*?)```[ \t]*\n?",
        lambda m: m.group(1),
        text or "",
        flags=re.DOTALL,
    ).strip()


def write_atomic(path: Path, content: str) -> None:
    """先写临时文件再替换，避免中途失败留下半截文件。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)
