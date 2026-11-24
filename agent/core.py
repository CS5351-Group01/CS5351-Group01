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
        """支持单条指令或使用 `|` 分割的多条管道指令。"""
        text = (command or "").strip()
        if not text:
            self.memory.add("user", text)
            return "未识别指令：空指令"

        # 如果包含管道符，拆分成多条指令执行
        if "|" in text:
            parts = [p.strip() for p in text.split("|")]
            outputs = []
            for part in parts:
                # 递归调用自身，执行单条指令，底层逻辑无需修改
                outputs.append(self.run(part))
            # 用换行符把结果拼起来返回
            return "\n".join(outputs)

        # --- 下面是原有的单条指令逻辑，保持不变 ---
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
