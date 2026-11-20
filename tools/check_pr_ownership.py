#!/usr/bin/env python3
"""PR 文件所有权校验。

设计目标：让「谁改了谁的文件」变成机器能判的事，而不是靠组长肉眼看 diff。

规则来自 roles.json：
  - role.paths        每个角色允许改的路径（glob，** 跨目录）
  - role.main_functions  共享模块里允许改的函数/方法名（按 AST 比对，不看行号）
  - leader.reserved   只有组长能动的路径

只读 git 对象，不执行被检查分支里的任何代码。

用法（CI 与本地一致）：
  python tools/check_pr_ownership.py --base <sha> --head <ref> --branch course/a --author alice
  python tools/check_pr_ownership.py --base origin/main --head HEAD --branch course/a

退出码：0 = 通过；1 = 有违规；2 = 配置或环境错误。
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PLACEHOLDER_PREFIX = "PUT-"


# --------------------------------------------------------------------------
# glob
# --------------------------------------------------------------------------

def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """把 glob 转正则。支持 ** （跨目录）、* （段内）、? （单字符）。"""
    out: list[str] = []
    i, n = 0, len(pattern)
    while i < n:
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def path_matches(path: str, pattern: str) -> bool:
    return bool(glob_to_regex(pattern).match(path))


# --------------------------------------------------------------------------
# 配置
# --------------------------------------------------------------------------

@dataclass
class Role:
    id: str
    title: str
    github: str | None
    paths: list[str]
    main_functions: list[str]

    @property
    def configured_owner(self) -> bool:
        return bool(self.github) and not self.github.startswith(PLACEHOLDER_PREFIX)


@dataclass
class Rules:
    leader_github: str | None
    reserved: list[str]
    shared_modules: list[str]
    roles: list[Role]

    def role_by_id(self, rid: str) -> Role | None:
        for r in self.roles:
            if r.id.casefold() == rid.casefold():
                return r
        return None

    def role_for_path(self, path: str) -> list[Role]:
        return [r for r in self.roles if any(path_matches(path, p) for p in r.paths)]

    def role_for_symbol(self, symbol: str) -> list[Role]:
        return [r for r in self.roles if symbol in r.main_functions]


def load_rules(path: Path) -> Rules:
    data = json.loads(path.read_text(encoding="utf-8"))
    leader = data.get("leader") or {}
    leader_github = leader.get("github")
    if leader_github and leader_github.startswith(PLACEHOLDER_PREFIX):
        leader_github = None
    roles = []
    for item in data.get("roles") or []:
        gh = item.get("github")
        if gh and gh.startswith(PLACEHOLDER_PREFIX):
            gh = None
        roles.append(
            Role(
                id=str(item["id"]),
                title=str(item.get("title", "")),
                github=gh,
                paths=list(item.get("paths") or []),
                main_functions=list(item.get("main_functions") or []),
            )
        )
    if not roles:
        raise SystemExit("roles.json 里没有任何角色")
    shared = list(data.get("shared_modules") or ["main.py"])
    return Rules(
        leader_github=leader_github,
        reserved=list(leader.get("reserved") or []),
        shared_modules=shared,
        roles=roles,
    )


# --------------------------------------------------------------------------
# git
# --------------------------------------------------------------------------

def git(*args: str, cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 失败：{proc.stderr.strip()}")
    return proc.stdout


def changed_paths(base: str, head: str, cwd: Path) -> list[tuple[str, str]]:
    """返回 [(status, path)]。--no-renames 让重命名表现为 删+增，避免绕过路径规则。"""
    raw = git("diff", "--name-status", "--no-renames", base, head, cwd=cwd)
    result = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0][:1]
        if len(parts) >= 2:
            result.append((status, parts[-1].replace("\\", "/")))
    return result


def file_at(rev: str, path: str, cwd: Path) -> str | None:
    """读取某个 revision 下的文件内容。

    用 utf-8-sig 解码：Windows 上编辑器存出来的 BOM 会被吃掉，
    否则 ast.parse 会报 “invalid non-printable character U+FEFF”。
    """
    proc = subprocess.run(
        ["git", "show", f"{rev}:{path}"], cwd=str(cwd), capture_output=True, text=True,
        encoding="utf-8-sig", errors="replace",
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


# --------------------------------------------------------------------------
# AST 符号
# --------------------------------------------------------------------------

MODULE_LEVEL = "<module-level>"


def module_symbols(source: str) -> dict[str, str]:
    """把模块拆成 {符号名: AST 文本}。

    符号名：顶层函数 `f`；类方法 `Cls.m`；模块级其余部分（import、常量、类骨架）
    统一记作 `<module-level>`。

    按名字逐个比对，所以函数顺序变化、增删无关函数都不会互相污染。
    """
    if not source.strip():
        return {}
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise SystemExit(f"解析失败：{exc}") from exc

    symbols: dict[str, str] = {}
    module_level: list[ast.AST] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols[node.name] = ast.dump(node, include_attributes=False)
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols[f"{node.name}.{sub.name}"] = ast.dump(sub, include_attributes=False)
            module_level.append(_class_shell(node))
        else:
            module_level.append(node)

    if module_level:
        symbols[MODULE_LEVEL] = "|".join(
            ast.dump(n, include_attributes=False) for n in module_level
        )
    return symbols


def _class_shell(node: ast.ClassDef) -> ast.AST:
    """只保留类的骨架（基类、装饰器、非方法成员），方法体单独按方法名归属。"""
    keep = [n for n in node.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return ast.ClassDef(
        name=node.name,
        bases=node.bases,
        keywords=node.keywords,
        body=keep,
        decorator_list=node.decorator_list,
    )


def changed_symbols(base_src: str | None, head_src: str | None) -> list[str]:
    before = module_symbols(base_src or "")
    after = module_symbols(head_src or "")
    names = set(before) | set(after)
    return sorted(n for n in names if before.get(n) != after.get(n))


# --------------------------------------------------------------------------
# 判定
# --------------------------------------------------------------------------

def role_of_branch(branch: str) -> str | None:
    m = re.fullmatch(r"course/([A-Za-z0-9]+)", branch or "")
    return m.group(1) if m else None


def check(
    rules: Rules,
    changes: list[tuple[str, str]],
    branch: str,
    author: str | None,
    cwd: Path,
    base: str,
    head: str,
) -> tuple[list[str], list[str]]:
    violations: list[str] = []
    warnings: list[str] = []

    branch_role_id = role_of_branch(branch)
    is_ops = (branch or "").startswith("ops/")
    is_main = (branch or "") in ("main", "refs/heads/main")

    if not (branch_role_id or is_ops or is_main):
        violations.append(
            f"分支名不合规：`{branch}`。只允许 `course/<角色>`、`ops/<用途>` 或 `main`。"
        )
        return violations, warnings

    if (is_ops or is_main) and rules.leader_github and author and author != rules.leader_github:
        violations.append(
            f"`{branch}` 只能由组长（{rules.leader_github}）推送，当前提交人：{author}。"
        )

    branch_role = rules.role_by_id(branch_role_id) if branch_role_id else None
    if branch_role_id and branch_role is None:
        violations.append(
            f"分支 `{branch}` 对应的角色不存在。现有角色：{', '.join(r.id for r in rules.roles)}。"
        )
        return violations, warnings

    if branch_role and not branch_role.configured_owner:
        warnings.append(f"角色 {branch_role.id} 还没在 roles.json 里填 github，跳过提交人核对。")

    # 组长分支（main / ops/*）：只核对提交人，不限制路径。
    # 组长是集成者，合并冲突、搭骨架、改公共夹具都要靠他。
    privileged = is_main or is_ops

    for status, path in changes:
        if path in rules.shared_modules:
            if privileged:
                continue
            level = "新增" if status == "A" else "删除" if status == "D" else "修改"
            violations_symbols: list[str] = []
            symbols = changed_symbols(file_at(base, path, cwd), file_at(head, path, cwd))
            if not symbols:
                warnings.append(f"{path} 有{level}但没解析出符号变化，可能只改了空白/注释。")
                continue
            for symbol in symbols:
                owners = rules.role_for_symbol(symbol)
                label = f"{path}::{symbol}"
                if symbol == MODULE_LEVEL:
                    violations_symbols.append(
                        f"{label} 改到了模块级代码（import / 常量 / 顶层语句），任何角色都不拥有。"
                    )
                elif not owners:
                    violations_symbols.append(f"{label} 不属于任何角色。")
                elif len(owners) > 1:
                    violations_symbols.append(
                        f"{label} 被多个角色同时声明：{', '.join(o.id for o in owners)}，配置有歧义。"
                    )
                elif branch_role and owners[0].id != branch_role.id:
                    violations_symbols.append(
                        f"{label} 属于角色 {owners[0].id}（{owners[0].title}），"
                        f"当前分支是 {branch_role.id}。"
                    )
            violations.extend(violations_symbols)
            continue

        reserved_hit = [p for p in rules.reserved if path_matches(path, p)]
        if reserved_hit and not privileged:
            violations.append(
                f"{path} 是组长的保留路径（`{reserved_hit[0]}`），成员分支不能改。"
            )
            continue

        if privileged:
            continue

        owners = rules.role_for_path(path)
        if not owners:
            violations.append(f"{path} 不属于任何角色（未声明路径）。")
            continue
        if len(owners) > 1:
            violations.append(
                f"{path} 同时命中多个角色：{', '.join(o.id for o in owners)}，roles.json 需要收紧。"
            )
            continue
        owner = owners[0]
        if branch_role is None:
            violations.append(f"{path} 属于角色 {owner.id}，但 `{branch}` 不是角色分支。")
        elif owner.id != branch_role.id:
            violations.append(
                f"{path} 属于角色 {owner.id}（{owner.title}），当前分支是 {branch_role.id}。"
            )

    return violations, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PR 文件所有权校验")
    parser.add_argument("--base", required=True, help="基线 revision，例如 origin/main 或 PR base SHA")
    parser.add_argument("--head", required=True, help="待检查 revision，例如 HEAD 或 PR head ref")
    parser.add_argument("--branch", required=True, help="PR 的源分支名")
    parser.add_argument("--author", default=None, help="PR 提交人 GitHub 登录名")
    parser.add_argument("--roles", default=None, help="roles.json 路径，默认仓库根目录")
    parser.add_argument("--repo-root", default=".", help="仓库根目录")
    parser.add_argument("--list", action="store_true", help="只打印当前规则，不做检查")
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve()
    roles_path = Path(args.roles) if args.roles else root / "roles.json"
    if not roles_path.exists():
        print(f"找不到规则文件：{roles_path}", file=sys.stderr)
        return 2
    rules = load_rules(roles_path)

    if args.list:
        print(f"保留路径（组长）：{', '.join(rules.reserved) or '无'}")
        print(f"共享模块（按方法归属）：{', '.join(rules.shared_modules)}")
        for r in rules.roles:
            print(f"\n{r.id}  {r.title}")
            for p in r.paths:
                print(f"    {p}")
            if r.main_functions:
                print(f"    main.py 方法：{', '.join(r.main_functions)}")
        return 0

    changes = changed_paths(args.base, args.head, root)
    violations, warnings = check(rules, changes, args.branch, args.author, root, args.base, args.head)

    for w in warnings:
        print(f"note: {w}")

    if violations:
        print("\n所有权检查失败：\n")
        for v in violations:
            print(f"  - {v}")
        print(f"\nOWNERSHIP CHECK FAIL changed={len(changes)} violations={len(violations)}")
        return 1

    role_label = role_of_branch(args.branch) or args.branch
    print(f"OWNERSHIP CHECK PASS role={role_label} changed={len(changes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
