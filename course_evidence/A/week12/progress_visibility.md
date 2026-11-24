# Week 12 — 让「第几轮」看得见

## 改了什么

- `app/services/task_runner.py` — commit `993787d`
  - `run_repair_task` 开跑先写 `status="running"`、`iterations=0`、`message="准备修复（最多 3 轮）…"`。
  - 每一轮开始时写一次库：`iterations=当前轮`，`message="第 N/M 轮：…"`（第 2 轮起是「上一轮未通过，重新生成…」）。
  - 实现方式：用 `_ProgressClient` 包住 `llm.client.default_client()`，`repair_source` 每轮固定调用一次 `client.complete()`，包装层在调用前写库。**没有改 `llm/`**（D 的目录），也没有把轮次逻辑复制一份到 app 层。
- `tests/roles/a/test_task_progress.py` — 2 个测试（新增）— commit `993787d`
  - `test_iterations_increase_while_task_is_running`：直接查 DB，第 1 轮卡住时读到 `iterations=1`，放行后第 2 轮读到 `2`。
  - `test_api_shows_progress_before_repair_finishes`：任务跑完前用 `GET /tasks/{id}` 就能读到 `status=running`、`iterations=1`。
- 前端没有改（E 的目录）：`frontend/index.html` 本来就每 1 秒轮询 `/tasks/{id}` 并显示 `iterations` 和 `message`，后端逐轮写库后状态栏自动能看到变化。
- 顺带说明：`repair_source` 原来默认 `FakeLLM()`，生产里即使配了 `LLM_API_KEY` 也一直用假模型；改成 `default_client()` 后恢复「有 key 用真模型、没 key 退化假模型」的语义。

## 实际跑了什么

同步 main（普通 merge，结果是 fast-forward）：

```powershell
git fetch origin
git switch course/a
git merge origin/main --no-edit
git push origin course/a
```

```text
Updating f2b7a0c..26eeaae
Fast-forward
 .github/CODEOWNERS                                 |  48 +++---
 .gitignore                                         |   5 +
 app/routers/tasks.py                               |  30 ++++
 app/services/storage.py                            |  12 +-
 course_evidence/C/week11/role_report.md            | 163 +++++++++++++++++++++
 course_evidence/E/week11/01-repair-success.png     | Bin 0 -> 28996 bytes
 .../E/week11/02-upload-file-details.png            | Bin 0 -> 30092 bytes
 course_evidence/E/week11/role_report.md            | 105 +++++++++++++
 docs/PR_OWNERSHIP.md                               |  14 ++
 frontend/index.html                                | 146 +++++++++++++++++-
 roles.json                                         |  12 +-
 sandbox/runner.py                                  |  36 ++++-
 sandbox/workspace.py                               |   9 +-
 tests/conftest.py                                  |  29 ++++
 tests/roles/a/test_auth_boundaries.py              |  20 ++-
 tests/roles/a/test_task_original.py                |  67 +++++++++
 tests/roles/c/test_sandbox_isolation.py            | 152 +++++++++++++++++++
 tools/check_pr_ownership.py                        |  14 ++
 tools/test_check_pr_ownership.py                   |   6 +
 19 files changed, 818 insertions(+), 50 deletions(-)
 create mode 100644 course_evidence/C/week11/role_report.md
 create mode 100644 course_evidence/E/week11/01-repair-success.png
 create mode 100644 course_evidence/E/week11/02-upload-file-details.png
 create mode 100644 course_evidence/E/week11/role_report.md
 create mode 100644 tests/roles/a/test_task_original.py
 create mode 100644 tests/roles/c/test_sandbox_isolation.py
To ssh://ssh.github.com:443/CS5351-Group01/CS5351-Group01.git
   f2b7a0c..26eeaae  course/a -> course/a
```

角色测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/roles/a -q
```

```text
.........................                                                [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 1 warning in 8.63s
```

全量测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

```text
........................................................................ [ 93%]
.....                                                                    [100%]
============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  D:\coding\CS5351-Group01\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
77 passed, 1 warning in 18.85s
```

新增的两个测试连跑 3 次：

```powershell
1..3 | ForEach-Object { .\.venv\Scripts\python.exe -m pytest tests/roles/a/test_task_progress.py -q --no-header }
```

```text
..                                                                       [100%]
2 passed, 1 warning in 1.46s
..                                                                       [100%]
2 passed, 1 warning in 1.44s
..                                                                       [100%]
2 passed, 1 warning in 1.39s
```

端到端验证（真实服务，不是 TestClient）：

```powershell
.\.venv\Scripts\python.exe run.py --port 8123
# 另开一个进程：注册 → 上传 raise RuntimeError("boom") 的 boom.py → 每 0.15s 轮询 /tasks/{id}
```

```text
create: 201 pending 0
iterations=0 status=pending message=None
iterations=1 status=running message=第 1/3 轮：正在生成修复…
iterations=2 status=running message=第 2/3 轮：上一轮未通过，重新生成…
iterations=3 status=running message=第 3/3 轮：上一轮未通过，重新生成…
iterations=3 status=failed message=3 轮内未能修复
```

## 结果

A_WEEK12_RESULT: PASS

## 卡在哪

无。
