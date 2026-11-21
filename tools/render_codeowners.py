#!/usr/bin/env python3
"""从 roles.json 生成 .github/CODEOWNERS。

CODEOWNERS 只负责「通知谁来 review」，不负责拦住越权改动 —— 那是
check_pr_ownership.py + CI 的活。两者都从 roles.json 出来，所以不会各说各话。

  python tools/render_codeowners.py            # 写入 .github/CODEOWNERS
  python tools/render_codeowners.py --stdout   # 只打印
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLACEHOLDER_PREFIX = "PUT-"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 CODEOWNERS")
    parser.add_argument("--roles", default="roles.json")
    parser.add_argument("--out", default=".github/CODEOWNERS")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    roles_path = Path(args.roles)
    if not roles_path.exists():
        print(f"找不到 {roles_path}", file=sys.stderr)
        return 2
    data = json.loads(roles_path.read_text(encoding="utf-8"))

    leader = (data.get("leader") or {}).get("github") or ""
    leader_ok = leader and not leader.startswith(PLACEHOLDER_PREFIX)

    lines = [
        "# 由 tools/render_codeowners.py 从 roles.json 生成，不要手改。",
        "# 这里只做 review 路由；真正的越权拦截在 CI 的 Check ownership。",
        "",
    ]

    if leader_ok:
        for pattern in (data.get("leader") or {}).get("reserved") or []:
            lines.append(f"{pattern} @{leader}")
        lines.append("")
    else:
        lines.append("# TODO: 在 roles.json 的 leader.github 填上组长账号后重新生成")
        lines.append("")

    for role in data.get("roles") or []:
        owner = role.get("github") or ""
        ok = owner and not owner.startswith(PLACEHOLDER_PREFIX)
        if not ok:
            # 用户名没填就别输出 `@role-x` 这种假 handle，
            # GitHub 会判定 CODEOWNERS 有错并挂一条黄条。整段注释掉更干净。
            lines.append(f"# TODO: 角色 {role['id']}（{role.get('title', '')}）还没填 github，"
                         f"下面几行先注释掉，填好后重新生成")
            for pattern in role.get("paths") or []:
                lines.append(f"# {pattern}")
            lines.append("")
            continue
        lines.append(f"# {role['id']} — {role.get('title', '')}")
        for pattern in role.get("paths") or []:
            lines.append(f"{pattern} @{owner}")
        lines.append("")

    text = "\n".join(lines).rstrip() + "\n"
    if args.stdout:
        sys.stdout.write(text)
        return 0

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"已写入 {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
