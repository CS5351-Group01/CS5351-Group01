#!/usr/bin/env python3
"""列出某个 Python 文件里可以被单独归属的符号，用来填 roles.json 的 main_functions。

  python tools/list_main_methods.py main.py
  python tools/list_main_methods.py main.py --rev origin/main
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_pr_ownership import MODULE_LEVEL, module_symbols  # noqa: E402


def read_file(path: str, rev: str | None) -> str:
    if rev:
        proc = subprocess.run(
            ["git", "show", f"{rev}:{path}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            raise SystemExit(f"读不到 {rev}:{path}：{proc.stderr.strip()}")
        return proc.stdout
    return Path(path).read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="列出可归属的符号")
    parser.add_argument("path", help="Python 文件路径，例如 main.py")
    parser.add_argument("--rev", default=None, help="从某个 git revision 读，例如 origin/main")
    args = parser.parse_args()

    symbols = module_symbols(read_file(args.path, args.rev))
    funcs = [s for s in symbols if s != MODULE_LEVEL]

    if not funcs:
        print(f"{args.path} 里没有顶层函数或类方法。")
    else:
        print(f"{args.path} 可单独归属的符号（{len(funcs)} 个）：\n")
        for name in funcs:
            print(f"  {name}")

    if MODULE_LEVEL in symbols:
        print(
            f"\n另有一段「模块级代码」（import / 常量 / 类骨架），"
            f"任何改动都会记作 {MODULE_LEVEL}，默认不属于任何角色。"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
