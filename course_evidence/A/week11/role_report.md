# Week 11 — 我做了什么

## 改了什么

- `tests/roles/a/test_auth_boundaries.py`（新增，6 个边界测试）— commit `ac192a4`
- `course_evidence/A/week11/role_report.md`（本文件，新增）
- 说明：`course/a` 原本停在旧骨架 `9d9aae1`，没有 `scripts/setup.ps1`、`examples/` 等文件；已先 fast-forward 到 `origin/main`（`e5bd1ed`）再写测试。没有改 `app/` 等任何归属别人的文件。

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

## 结果

A_WEEK11_RESULT: PASS

## 卡在哪

无。

唯一需要处理的是 `course/a` 落后 main 8 个提交、连 `scripts/setup.ps1` 都没有，所以先做了 fast-forward 再跑环境。
