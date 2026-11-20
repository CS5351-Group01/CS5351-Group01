#!/usr/bin/env python3
"""check_pr_ownership.py 的回归测试。

在一个临时 git 仓库里造出每一种越权场景，逐条确认校验器的结论。
装好骨架之后跑这个，全绿才算规则真的生效：

  python tools/test_check_pr_ownership.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_pr_ownership.py"

ROLES = {
    "version": 1,
    "leader": {
        "github": "lead",
        "reserved": ["course_evidence/team/**", "README.md", "tools/**"],
    },
    "shared_modules": ["main.py"],
    "roles": [
        {
            "id": "A",
            "title": "接入与配置",
            "github": "alice",
            "paths": ["metadata.yaml", "course_evidence/A/**", "tests/roles/a/**"],
            "main_functions": ["_get_config"],
        },
        {
            "id": "B",
            "title": "主流程",
            "github": "bob",
            "paths": ["course_evidence/B/**", "tests/roles/b/**"],
            "main_functions": ["handle_message"],
        },
    ],
}

MAIN_PY = """import os

TIMEOUT = 30


def _get_config(name):
    return os.environ.get(name)


def handle_message(msg):
    return msg.strip()
"""

MAIN_PY_B_CHANGE = MAIN_PY.replace(
    "    return msg.strip()", "    return msg.strip().lower()"
)
MAIN_PY_A_CHANGE = MAIN_PY.replace(
    "    return os.environ.get(name)", "    return os.environ.get(name) or None"
)
MAIN_PY_IMPORT = "import sys\n" + MAIN_PY


def sh(cwd: Path, *args: str) -> str:
    proc = subprocess.run(list(args), cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"{args} 失败：{proc.stderr}\n{proc.stdout}")
    return proc.stdout


def git(cwd: Path, *args: str) -> str:
    return sh(cwd, "git", *args)


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(root: Path, branch: str, author: str, base: str = "main") -> tuple[int, str]:
    proc = subprocess.run(
        [
            sys.executable, str(CHECKER),
            "--base", base, "--head", "HEAD",
            "--branch", branch, "--author", author,
            "--repo-root", str(root),
        ],
        cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def reset_branch(root: Path, branch: str) -> None:
    git(root, "checkout", "-q", "-B", branch, "main")
    git(root, "reset", "-q", "--hard", "main")


def commit(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", message)


CASES: list[tuple[str, str, str, str, int]] = []


def case(name: str, branch: str, author: str, expect: int):
    def deco(fn):
        CASES.append((name, branch, author, fn, expect))
        return fn
    return deco


@case("A 改自己的证据", "course/a", "alice", 0)
def _(root: Path) -> None:
    write(root, "course_evidence/A/week01/role_and_scope.md", "# A\n\n## 职责\n\n接入与配置\n")
    commit(root, "docs(a): w1")


@case("A 改 B 的证据", "course/a", "alice", 1)
def _(root: Path) -> None:
    write(root, "course_evidence/B/week01/role_and_scope.md", "# B\n\n被别人动了\n")
    commit(root, "docs(a): 越权")


@case("A 改组长保留路径", "course/a", "alice", 1)
def _(root: Path) -> None:
    write(root, "README.md", "# 改标题\n")
    commit(root, "docs(a): 越权")


@case("A 改没人认领的文件", "course/a", "alice", 1)
def _(root: Path) -> None:
    write(root, "random_note.txt", "hi\n")
    commit(root, "chore: 野文件")


@case("B 改自己拥有的 main.py 方法", "course/b", "bob", 0)
def _(root: Path) -> None:
    write(root, "main.py", MAIN_PY_B_CHANGE)
    commit(root, "feat(b): 改编排")


@case("A 改 B 拥有的 main.py 方法", "course/a", "alice", 1)
def _(root: Path) -> None:
    write(root, "main.py", MAIN_PY_B_CHANGE)
    commit(root, "feat(a): 抢改")


@case("A 改自己拥有的 main.py 方法", "course/a", "alice", 0)
def _(root: Path) -> None:
    write(root, "main.py", MAIN_PY_A_CHANGE)
    commit(root, "feat(a): 改配置")


@case("改 main.py 模块级代码（import）", "course/a", "alice", 1)
def _(root: Path) -> None:
    write(root, "main.py", MAIN_PY_IMPORT)
    commit(root, "chore(a): 加 import")


@case("把 B 的文件改名挪到 A 目录", "course/a", "alice", 1)
def _(root: Path) -> None:
    git(root, "rm", "-q", "course_evidence/B/secret.md")
    write(root, "course_evidence/A/secret.md", "x\n")
    commit(root, "docs(a): 改名搬家")


@case("分支名不是已知角色", "course/g", "george", 1)
def _(root: Path) -> None:
    write(root, "course_evidence/A/week01/x.md", "x\n")
    commit(root, "docs(g): 野分支")


@case("组长用 ops 分支改保留路径", "ops/scaffold", "lead", 0)
def _(root: Path) -> None:
    write(root, "README.md", "# 组长改\n")
    commit(root, "chore: scaffold")


@case("非组长用 ops 分支", "ops/scaffold", "alice", 1)
def _(root: Path) -> None:
    write(root, "README.md", "# 冒名\n")
    commit(root, "chore: 冒名")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        git(root, "init", "-q", "-b", "main")
        (root / "roles.json").write_text(json.dumps(ROLES, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
        write(root, "main.py", MAIN_PY)
        write(root, "course_evidence/A/week01/role_and_scope.md", "# A\n")
        write(root, "course_evidence/B/week01/role_and_scope.md", "# B\n")
        write(root, "course_evidence/B/secret.md", "x\n")
        commit(root, "chore: init fixture")

        failures = []
        for name, branch, author, fn, expect in CASES:
            reset_branch(root, branch)
            fn(root)
            code, out = check(root, branch, author)
            ok = code == expect
            mark = "PASS" if ok else "FAIL"
            print(f"[{mark}] {name}  (期望 exit={expect} 实际 exit={code})")
            if not ok:
                failures.append((name, expect, code, out))

        print(f"\n{len(CASES) - len(failures)}/{len(CASES)} 通过")
        for name, expect, code, out in failures:
            print(f"\n--- {name} 期望 {expect} 实际 {code} ---")
            print(out)
        return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
