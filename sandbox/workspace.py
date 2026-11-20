"""沙箱工作区：把待修复的项目复制到临时目录，跑完自动清理。

原则：**永远不在原始目录里改代码**。所有试错都在副本上进行。
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

IGNORE = shutil.ignore_patterns(
    ".git", "__pycache__", ".pytest_cache", ".venv", "node_modules",
    "*.pyc", "*.pyo", "app.db", "*.db",
)

MAX_FILES = 5_000
MAX_TOTAL_BYTES = 50_000_000


class SandboxError(RuntimeError):
    """沙箱准备失败。"""


class SandboxWorkspace:
    """`with SandboxWorkspace(src) as ws:` —— 退出时自动删掉副本。"""

    def __init__(self, source: Path | str | None = None) -> None:
        self.source = Path(source) if source else None
        self._root: Path | None = None

    # ------------------------------------------------------------ 生命周期

    def __enter__(self) -> "SandboxWorkspace":
        self._root = Path(tempfile.mkdtemp(prefix="codefix-"))
        if self.source is not None:
            self._copy_in(self.source)
        return self

    def __exit__(self, *exc_info) -> None:
        if self._root and self._root.exists():
            shutil.rmtree(self._root, ignore_errors=True)

    def _copy_in(self, source: Path) -> None:
        if not source.exists():
            raise SandboxError(f"源目录不存在：{source}")
        if source.is_file():
            shutil.copy2(source, self.root / source.name)
            return

        count = 0
        total = 0
        for item in source.rglob("*"):
            if not item.is_file():
                continue
            if item.name in {"app.db"} or "__pycache__" in item.parts:
                continue
            count += 1
            total += item.stat().st_size
            if count > MAX_FILES:
                raise SandboxError(f"文件数超过上限 {MAX_FILES}")
            if total > MAX_TOTAL_BYTES:
                raise SandboxError(f"总体积超过上限 {MAX_TOTAL_BYTES} 字节")

        # 用 copytree 一次拷完，再清掉忽略项
        for child in source.iterdir():
            if child.name in {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}:
                continue
            target = self.root / child.name
            if child.is_dir():
                shutil.copytree(child, target, ignore=IGNORE, dirs_exist_ok=True)
            else:
                shutil.copy2(child, target)

    # ------------------------------------------------------------ 访问

    @property
    def root(self) -> Path:
        if self._root is None:
            raise SandboxError("沙箱还没进入（用 with 语句）")
        return self._root

    def path(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve()
        if self.root not in candidate.parents and candidate != self.root:
            raise SandboxError(f"路径越界：{relative}")
        return candidate

    def read(self, relative: str) -> str:
        return self.path(relative).read_text(encoding="utf-8", errors="replace")

    def write(self, relative: str, content: str) -> None:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
