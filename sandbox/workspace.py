"""沙箱工作区：把待修复的项目复制到临时目录，跑完自动清理。

原则：**永远不在原始目录里改代码**。所有试错都在副本上进行。
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

IGNORE = shutil.ignore_patterns(
    ".git", "__pycache__", ".pytest_cache", ".venv", "node_modules",
    "*.pyc", "*.pyo", "app.db", "*.db",
)

MAX_FILES = 5_000
MAX_TOTAL_BYTES = 50_000_000


def is_within(root: Path, candidate: Path) -> bool:
    """candidate 是否在 root 里面。

    两个路径都应已 resolve()。仍然再兜一层：
    Windows 下大小写不敏感，而 Path 比较是敏感的，直接用 relative_to
    在极端情况下会误判，所以补一次 normcase 前缀比较。
    """
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        pass
    root_s = os.path.normcase(str(root)).rstrip("\\/")
    cand_s = os.path.normcase(str(candidate))
    return cand_s == root_s or cand_s.startswith(root_s + os.sep)


class SandboxError(RuntimeError):
    """沙箱准备失败。"""


class SandboxWorkspace:
    """`with SandboxWorkspace(src) as ws:` —— 退出时自动删掉副本。"""

    def __init__(self, source: Path | str | None = None) -> None:
        # 立刻 resolve：TEMP 里可能带 Windows 8.3 短名（如 ADMINI~1），
        # 不展开的话后续和 resolve 过的路径比对会永远失败。
        self.source = Path(source).resolve() if source else None
        self._root: Path | None = None

    # ------------------------------------------------------------ 生命周期

    def __enter__(self) -> "SandboxWorkspace":
        self._root = Path(tempfile.mkdtemp(prefix="codefix-")).resolve()
        if self.source is not None:
            # 进入失败（源目录不存在、超过体积上限…）时 __exit__ 不会被调用，
            # 这里必须自己把已经建出来的临时目录删掉，否则每失败一次泄漏一个。
            try:
                self._copy_in(self.source)
            except BaseException:
                shutil.rmtree(self._root, ignore_errors=True)
                self._root = None
                raise
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
        root = self.root
        candidate = (root / relative).resolve()
        if not is_within(root, candidate):
            raise SandboxError(f"路径越界：{relative}")
        return candidate

    def read(self, relative: str) -> str:
        return self.path(relative).read_text(encoding="utf-8", errors="replace")

    def write(self, relative: str, content: str) -> None:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
