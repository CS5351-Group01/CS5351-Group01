# Week 11 — 沙箱（C）我做了什么

## 改了什么

| 文件 | 说明 | commit |
|---|---|---|
| `tests/roles/c/test_sandbox_isolation.py` | 新增 5 条隔离边界测试（其中越界为参数化 3 例，共 7 个用例） | `1a5df8c` |

只动了 `tests/roles/c/`，没有碰 `examples/`、`tests/conftest.py`、`docs/`、`requirements.txt`。

被要求的 5 条里，第 1~4 条在既有 `tests/roles/c/test_sandbox.py` 中已有覆盖，第 5 条（空目录建沙箱）是新增。
所以本文件写的是**加强版断言**，不是重复抄写：

1. 超时 —— 不只断言 `timed_out is True`，还断言 `exit_code == -1` 且 `duration_ms` 落在 900~5000ms，
   证明子进程是在 1 秒预算附近被真正掐断的，而不是等 `sleep` 自己跑完才返回。
2. 清理 —— 在 `with` 块**内部主动抛异常**，退出后沙箱目录必须已消失（覆盖异常路径的清理）。
3. 原件 —— 不只比较内容，还比较 `st_mtime_ns`，防止「内容一样但源文件被重写过」的假阴性。
4. 越界 —— 参数化 3 例：`../outside.txt`、`../../../etc/passwd`、绝对路径 `C:/Windows/win.ini`。
5. 空目录 —— 建出来的沙箱必须存在、必须不等于源目录、且内部为空。

## 实际跑了什么

主机：Windows / Python 3.12.9（`.venv`）

```text
PS D:\Projects\SE_project\CS5351-Group01> .\.venv\Scripts\python.exe -m pytest tests/roles/c -q
...............                                                          [100%]
15 passed in 4.72s
```

全量回归（确认没有影响其它角色）：

```text
PS D:\Projects\SE_project\CS5351-Group01> .\.venv\Scripts\python.exe -m pytest tests -q
.......................................................                  [100%]
=============================== warnings summary ===============================
tests/roles/a/test_auth_api.py::test_health
  .venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
55 passed, 1 warning in 23.83s
```

环境确认（`scripts/setup.ps1`，合并 `origin/main` 之后）：

```text
4/4 跑测试…
48 passed, 1 warning in 20.44s
环境好了。以后跑测试用这条：
  .\.venv\Scripts\python.exe -m pytest tests -q
```

## 结果

```text
C_WEEK11_RESULT: PASS
```

- 跑了几个用例：本层 15 个（既有 8 + 新增 7）
- 跳过几个、为什么：0
- 失败几个：0

## 卡在哪

1. **分支基线是旧的（已解决）**：`course/c` 停在 `9d9aae1`（PR#3），落后 `origin/main` 8 个提交，
   上面没有 `scripts/setup.ps1`、没有 `examples/` 下 5 个用例，且 `sandbox/workspace.py` 缺
   `b32e2d5` 的 `resolve()` 修复。执行 `git merge --ff-only origin/main` 后恢复，
   `setup.ps1` 输出 `48 passed`。
2. **待组长处理的技术债（未修改，属组长文件）**：`tests/conftest.py` 顶部
   `_TMP_DIR = Path(tempfile.mkdtemp(prefix="codefix-tests-"))` 建了临时目录但从不清理，
   每跑一次测试就遗留一个 `codefix-tests-*` 目录。建议加 `atexit.register(shutil.rmtree, _TMP_DIR, True)`。
3. `pytest` 的 `tmp_path` 基线目录在仓库根留下了 `pytest-of-ZHONG/`（未提交）。
   建议把 `pytest-of-*/` 和 `codefix-tests-*/` 加进 `.gitignore`（`.gitignore` 属组长，未改）。

## 局限

- 这些测试验证的是**目录级隔离**（改不坏原目录、路径出不去），不是**安全隔离**。
  沙箱里的代码仍然以当前用户权限运行，可以读 `%USERPROFILE%\.ssh`、可以联网。
  要真正隔离需要 subprocess 降权 / Windows Job Object 限额 / 容器化，本层当前不具备。
- 超时断言的上界 5000ms 是为慢机器留的余量，不是精确值。
