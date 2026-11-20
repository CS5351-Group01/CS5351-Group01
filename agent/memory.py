"""多轮对话的短期记忆。

只存最近的若干轮，避免 prompt 无限膨胀。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class Turn:
    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class Memory:
    limit: int = 20
    turns: deque[Turn] = field(default_factory=deque)

    def add(self, role: str, content: str) -> None:
        self.turns.append(Turn(role=role, content=content))
        while len(self.turns) > self.limit:
            self.turns.popleft()

    def recent(self, n: int = 5) -> list[Turn]:
        if n <= 0:
            return []
        return list(self.turns)[-n:]

    def as_text(self, n: int = 5) -> str:
        return "\n".join(f"[{t.role}] {t.content}" for t in self.recent(n))

    def clear(self) -> None:
        self.turns.clear()
