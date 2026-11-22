# Week 11 — 我做了什么

## 改了什么

- `tests/roles/a/test_auth_boundaries.py`（6 个边界测试）— commit `ac192a4`；签名篡改假绿修复 — commit `4d3422b`；新增 4 个边界测试 — commit `0d9e3f8`
- `course_evidence/A/week11/role_report.md`（本文件，新增并更新）
- 发现（`0d9e3f8` 实测）：
  - `.exe` 上传当前返回 201：后端没有扩展名白名单，用 `test_exe_extension_current_behavior` 锁定现状，等以后加白名单再改预期。
  - 越权查任务没有暴露 bug：B 读 A 的任务返回 404，`app/routers/tasks.py` 里已经有 `task.owner_id != current.id` 的判断，所以没有改 `app/`。
- 同步 main：`git fetch origin` + `git merge --ff-only origin/main` → `Already up to date.`（`origin/main` = `e5bd1ed`）。
- 说明：`course/a` 原本停在旧骨架 `9d9aae1`，没有 `scripts/setup.ps1`、`examples/` 等文件；前一轮已 fast-forward 到 `origin/main` 再写测试。没有改 `app/` 等任何归属别人的文件。

## 实际跑了什么

```powershell
cd D:\coding\CS5351-Group01
git fetch origin --prune
git merge --ff-only origin/main
```

```text
Updating 9d9aae1..e5bd1ed
Fast-forward
 ...（26 files changed，输出略）
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

```text
仓库目录: D:\coding\CS5351-Group01
1/4 Python: Python 3.14.6
2/4 虚拟环境已存在，跳过创建
3/4 安装依赖…
4/4 跑测试…

................................................                         [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
48 passed, 1 warning in 8.46s

环境好了。以后跑测试用这条：
  .\.venv\Scripts\python.exe -m pytest tests -q
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/roles/a -q
```

```text
.............                                                            [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
13 passed, 1 warning in 1.94s
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

```text
......................................................                   [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
54 passed, 1 warning in 9.11s
```

修掉签名用例的假绿后，连跑 5 次：

```powershell
1..5 | % { .\.venv\Scripts\python.exe -m pytest tests/roles/a -q }
```

```text
.............                                                            [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
13 passed, 1 warning in 2.10s
.............                                                            [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
13 passed, 1 warning in 1.66s
.............                                                            [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
13 passed, 1 warning in 1.63s
.............                                                            [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
13 passed, 1 warning in 1.65s
.............                                                            [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
13 passed, 1 warning in 1.66s
```

补 4 个测试后（今天，先同步 main）：

```powershell
git fetch origin --prune
git merge --ff-only origin/main
```

```text
From ssh://ssh.github.com:443/CS5351-Group01/CS5351-Group01
   9d9aae1..1245c27  course/b          -> origin/course/b
   9d9aae1..1d93135  course/c          -> origin/course/c
   9d9aae1..df3f904  course/d          -> origin/course/d
   9d9aae1..5060a01  course/e          -> origin/course/e
   9d9aae1..33e60eb  course/f          -> origin/course/f
 * [new branch]      ops/roles-fill    -> origin/ops/roles-fill
 * [new branch]      ops/task-original -> origin/ops/task-original
Already up to date.
```

```powershell
1..5 | ForEach-Object { .\.venv\Scripts\python.exe -m pytest tests/roles/a -q }
```

```text
.................                                                        [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
17 passed, 1 warning in 4.09s
.................                                                        [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
17 passed, 1 warning in 4.04s
.................                                                        [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
17 passed, 1 warning in 4.28s
.................                                                        [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
17 passed, 1 warning in 4.22s
.................                                                        [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
17 passed, 1 warning in 4.14s
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

```text
..........................................................               [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
58 passed, 1 warning in 13.30s
```

## 结果

A_WEEK11_RESULT: PASS

## 卡在哪

无。

唯一需要处理的是 `course/a` 落后 main 8 个提交、连 `scripts/setup.ps1` 都没有，所以先做了 fast-forward 再跑环境。

已知缺口：`.exe` 上传目前不拦（测试锁定现状），本轮没要求修；越权查任务实测已正确，无 bug 可修。
