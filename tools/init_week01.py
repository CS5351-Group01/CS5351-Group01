#!/usr/bin/env python3
"""从 roles.json 生成每个角色的 Week 1 证据骨架。

  python tools/init_week01.py            # 写文件
  python tools/init_week01.py --dry-run  # 只打印

已存在的文件不会被覆盖。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TEMPLATE = """# {id} 角色与边界

WEEK1_START
本文件在 Week 1 创建，日期为真实当前日期。

# {id} role and scope

## 职责

{title}

{legacy_line}

## 负责的文件

{paths}

## 边界

- 只改本角色 `paths` 内的文件
- Week 1–4 只提交 `course_evidence/{id}/**`，不改生产代码
- `main.py` 如属共享，只改 `main_functions` 里声明过的方法
- 需要动别人的东西时，先提给对方，不直接改
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 Week 1 角色文件")
    parser.add_argument("--roles", default="roles.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data = json.loads(Path(args.roles).read_text(encoding="utf-8"))
    written = 0
    for role in data.get("roles") or []:
        rid = role["id"]
        legacy = role.get("legacy")
        body = TEMPLATE.format(
            id=rid,
            title=role.get("title", ""),
            legacy_line=f"对应课程原始模块：{legacy}" if legacy else "",
            paths="\n".join(f"- `{p}`" for p in role.get("paths") or []),
        )
        target = Path(f"course_evidence/{rid}/week01/role_and_scope.md")
        if args.dry_run:
            print(f"--- {target} ---\n{body}")
            continue
        if target.exists():
            print(f"skip（已存在）{target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        print(f"written {target}")
        written += 1

    if not args.dry_run:
        print(f"\n共写入 {written} 个文件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
