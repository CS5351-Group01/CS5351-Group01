"""Agent 核心：技能注册 + 极简调度。

真正的「多轮修复」编排在 llm/iterative_fix.py；这里只管
「收到一句指令，找到对应技能，跑它，记进记忆」。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from agent.memory import Memory

SkillFn = Callable[[str], str]


@dataclass
class Agent:
    name: str = "code-repair-agent"
    memory: Memory = field(default_factory=Memory)
    skills: dict[str, SkillFn] = field(default_factory=dict)

    def register(self, name: str, fn: SkillFn) -> None:
        if not name or " " in name:
            raise ValueError("技能名不能为空或含空格")
        self.skills[name] = fn

    def register_all(self, mapping: dict[str, SkillFn]) -> None:
        for name, fn in mapping.items():
            self.register(name, fn)

    def run(self, command: str) -> str:
        """指令格式：`<技能名>: <参数>`。不认识的指令原样回显并记入记忆。"""
        text = (command or "").strip()
        if ":" in text:
            name, _, argument = text.partition(":")
            name = name.strip()
            fn = self.skills.get(name)
            if fn is not None:
                self.memory.add("user", text)
                try:
                    output = fn(argument.strip())
                except PermissionError as exc:
                    output = f"拒绝执行：{exc}"
                self.memory.add("assistant", output)
                return output

        self.memory.add("user", text)
        return f"未识别指令：{text}"

    def available(self) -> list[str]:
        return sorted(self.skills)
