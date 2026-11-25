# Week 11 — 沙箱（C）工作总结

## 改了什么

| 文件 | 说明 | commit |
|---|---|---|
| `tests/roles/c/test_sandbox_isolation.py` | 新增 5 项隔离边界测试（越界项参数化为 3 例，共 7 个用例） | `1a5df8c` |

变更范围限于 `tests/roles/c/`，未修改 `examples/`、`tests/conftest.py`、`docs/`、`requirements.txt`。

任务要求的 5 项中，第 1~4 项在既有 `tests/roles/c/test_sandbox.py` 中已有覆盖，第 5 项（空目录建沙箱）为新增。
本文件采用加强版断言，覆盖范围如下：

1. 超时：除断言 `timed_out is True` 外，另断言 `exit_code == -1` 且 `duration_ms` 落在 900~5000 ms，
   用于确认子进程在 1 秒预算附近被终止，而非等待 `sleep` 执行结束。
2. 清理：在 `with` 块内部主动抛出异常，退出后沙箱目录必须已被删除，覆盖异常路径的清理逻辑。
3. 原件：同时比较内容与 `st_mtime_ns`，用于识别「内容一致但源文件被重写」的情况。
4. 越界：参数化 3 例，分别为 `../outside.txt`、`../../../etc/passwd` 与绝对路径 `C:/Windows/win.ini`。
5. 空目录：建出的沙箱必须存在、不等于源目录，且内部为空。

## 实际跑了什么

主机：Windows / Python 3.12.9（`.venv`）

```text
PS D:\Projects\SE_project\CS5351-Group01> .\.venv\Scripts\python.exe -m pytest tests/roles/c -q
...............                                                          [100%]
15 passed in 4.72s
```

全量回归：

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

- 执行用例：本层 15 项（既有 8 项 + 新增 7 项）
- 跳过：0
- 失败：0

## 卡在哪

1. **分支基线滞后（已解决）**：`course/c` 停留于 `9d9aae1`（PR #3），落后 `origin/main` 8 个提交，
   缺少 `scripts/setup.ps1` 与 `examples/` 下 5 个用例，且 `sandbox/workspace.py` 不含
   `b32e2d5` 的 `resolve()` 修复。执行 `git merge --ff-only origin/main` 后恢复，`setup.ps1` 输出 `48 passed`。
2. **公共文件中的资源清理问题（未修改，属负责人维护范围）**：`tests/conftest.py` 中
   `_TMP_DIR = Path(tempfile.mkdtemp(prefix="codefix-tests-"))` 创建临时目录后未做清理，
   每次测试运行遗留一个 `codefix-tests-*` 目录。建议增加 `atexit.register(shutil.rmtree, _TMP_DIR, True)`。
3. `pytest` 的 `tmp_path` 基线目录在仓库根目录产生 `pytest-of-ZHONG/`（未提交）。
   建议将 `pytest-of-*/` 与 `codefix-tests-*/` 加入 `.gitignore`（该文件由负责人维护，未修改）。

## 局限

- 上述测试验证的是**目录级隔离**（不修改源目录、路径不可越界），不构成安全隔离。
  沙箱内代码仍以当前用户权限运行，可读取 `%USERPROFILE%\.ssh`，亦可访问网络。
  实现进程级隔离需引入权限降级、Windows Job Object 限额或容器化，当前版本不具备这些能力。
- 超时断言的上界 5000 ms 为异机运行预留的余量，非精确值。

---

## Day 3 改了什么

| 文件 | 说明 | commit |
|---|---|---|
| `tests/roles/c/test_sandbox_isolation.py` | 新增 4 项边界测试：源目录不存在、`run_pytest` 传入不存在的目录、`check_syntax` 处理语法错误文件、两个沙箱互不干扰 | `288b84a` |
| `sandbox/workspace.py` | 修复缺陷 1：`__enter__` 中 `_copy_in` 抛出异常时清理已创建的临时目录 | `288b84a` |
| `sandbox/runner.py` | 修复缺陷 2：`run_pytest` / `check_syntax` 捕获 `OSError`，返回 `passed=False`，不再向调用方抛出异常 | `288b84a` |

### 发现的两个缺陷

**缺陷 1：进入失败的沙箱遗留临时目录。**
`SandboxWorkspace("不存在的路径")` 执行时，`__enter__` 首先通过 `mkdtemp` 创建目录，
随后 `_copy_in` 抛出 `SandboxError`；由于 `__enter__` 抛出异常时 `__exit__` 不会被调用，
该 `codefix-xxxx` 目录将长期保留。测试中断言 `not created[0].exists()` 失败，现象可稳定复现。
处理方式：在 `__enter__` 中捕获异常，调用 `shutil.rmtree` 清理后重新抛出。

**缺陷 2：`run_pytest` 对不存在的 cwd 抛出 `NotADirectoryError [WinError 267]`。**
`subprocess.run(cwd=...)` 启动失败时抛出 `OSError`，原实现仅捕获 `TimeoutExpired`，异常直接传递给调用方。
在完整流程中，若用户上传目录在执行期间被删除，整个修复任务将返回 500，而非按单轮失败处理。
处理方式：捕获 `OSError` 并返回 `RunResult(passed=False, exit_code=-1, stderr=...)`；`check_syntax` 同步处理。

上述两处均位于 `sandbox/**`，属本角色维护范围，未修改其它角色的文件。

## Day 3 实际跑了什么

同步 `main`：

```text
PS D:\Projects\SE_project\CS5351-Group01> git fetch origin
   9d9aae1..ec5854e  course/d          -> origin/course/d
   ...
PS D:\Projects\SE_project\CS5351-Group01> git merge --ff-only origin/main
Already up to date.
```

修复前先执行一次，用于确认当前行为：

```text
PS D:\Projects\SE_project\CS5351-Group01> .\.venv\Scripts\python.exe -m pytest tests/roles/c -q
...
E                                    NotADirectoryError: [WinError 267] 目录名称无效。
D:\Program Files\Miniconda3\Lib\subprocess.py:1540: NotADirectoryError
=========================== short test summary info ===========================
FAILED tests/roles/c/test_sandbox_isolation.py::test_missing_source_raises_and_leaves_no_temp_dir
FAILED tests/roles/c/test_sandbox_isolation.py::test_run_pytest_on_missing_dir_returns_failed
2 failed, 17 passed in 4.93s
```

修复后连续执行三次：

```text
PS D:\Projects\SE_project\CS5351-Group01> 1..3 | ForEach-Object { .\.venv\Scripts\python.exe -m pytest tests/roles/c -q }
===== 第 1 次 =====
19 passed in 4.06s
===== 第 2 次 =====
19 passed in 4.46s
===== 第 3 次 =====
19 passed in 4.03s
```

全量回归：

```text
PS D:\Projects\SE_project\CS5351-Group01> .\.venv\Scripts\python.exe -m pytest tests -q
59 passed, 1 warning in 17.10s
```

## Day 3 结果

```text
C_WEEK11_DAY3: PASS
```

- 本层用例：19 项（原有 15 项 + Day 3 新增 4 项），连续三次通过
- 跳过：0
- 失败：0
- 发现缺陷：2 项，均已修复并纳入回归（`288b84a`）
- 遗留事项（公共文件，未修改）：`tests/conftest.py` 每次运行仍在仓库根目录遗留一个 `codefix-tests-*`，
  本地已清理；建议在 `.gitignore` 中补充 `pytest-of-*/` 与 `codefix-tests-*/`。
