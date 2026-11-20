"""Agent 的技能集：ls / read / grep / write。

每条技能都是「相对工作区根目录」的操作，并且强制不许跳出根目录。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

MAX_READ_BYTES = 200_000
MAX_LIST_ENTRIES = 200
MAX_GREP_HITS = 50

_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules"}


def resolve_within(root: Path, relative: str) -> Path:
    """把相对路径解析到 root 下；试图越界直接抛异常。"""
    root = Path(root).resolve()
    candidate = (root / (relative or ".")).resolve()
    if candidate != root and root not in candidate.parents:
        raise PermissionError(f"路径越界：{relative}")
    return candidate


@dataclass
class Workspace:
    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, relative: str) -> Path:
        return resolve_within(self.root, relative)

    # ---------------------------------------------------------- 技能实现

    def ls(self, relative: str = ".") -> str:
        target = self.path(relative)
        if not target.exists():
            return f"不存在：{relative}"
        if target.is_file():
            return target.name

        entries: list[str] = []
        for child in sorted(target.iterdir()):
            if child.name in _SKIP_DIRS:
                continue
            entries.append(child.name + ("/" if child.is_dir() else ""))
            if len(entries) >= MAX_LIST_ENTRIES:
                entries.append("...")
                break
        return "\n".join(entries) or "（空目录）"

    def read(self, relative: str) -> str:
        target = self.path(relative)
        if not target.is_file():
            return f"不是文件：{relative}"
        data = target.read_bytes()
        if len(data) > MAX_READ_BYTES:
            return f"文件过大（{len(data)} 字节），超过 {MAX_READ_BYTES} 上限"
        return data.decode("utf-8", errors="replace")

    def grep(self, argument: str) -> str:
        """参数格式：`<关键词>` 或 `<关键词> in <子路径>`。

        用 ` in ` 分隔而不是空格，因为关键词本身经常带空格
        （比如 `return 42`），按空格切会把关键词切碎。
        """
        text = argument.strip()
        if not text:
            return "用法：grep <关键词> [in <子路径>]"
        if " in " in text:
            keyword, _, sub = text.partition(" in ")
            sub = sub.strip() or "."
        else:
            keyword, sub = text, "."
        base = self.path(sub)
        if not base.exists():
            return f"路径不存在：{sub}"

        files = [base] if base.is_file() else [
            p for p in base.rglob("*")
            if p.is_file() and not (_SKIP_DIRS & set(p.parts))
        ]

        hits: list[str] = []
        for file in files:
            try:
                lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for number, line in enumerate(lines, start=1):
                if keyword in line:
                    # 统一用正斜杠：Windows 下 relative_to 会给出反斜杠，
                    # 直接拼进输出会让结果在不同平台不一致
                    rel = file.relative_to(self.root).as_posix()
                    hits.append(f"{rel}:{number}: {line.strip()[:200]}")
                    if len(hits) >= MAX_GREP_HITS:
                        return "\n".join(hits) + "\n...（截断）"
        return "\n".join(hits) or f"没找到：{keyword}"

    def write(self, argument: str) -> str:
        """参数格式：`<相对路径>\n<内容>`"""
        relative, _, content = argument.partition("\n")
        relative = relative.strip()
        if not relative:
            return "用法：write <相对路径>\\n<内容>"
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"已写入 {relative}（{len(content)} 字符）"


@dataclass
class Skills:
    """把 Workspace 的方法包成「名字 -> 可调用」，供 Agent 注册。"""

    workspace: Workspace
    registry: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.registry = {
            "ls": self.workspace.ls,
            "read": self.workspace.read,
            "grep": self.workspace.grep,
            "write": self.workspace.write,
        }
