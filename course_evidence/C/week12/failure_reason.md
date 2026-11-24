# 失败原因接口：RunResult.failure_reason()

| 项目 | 内容 |
|---|---|
| 模块 | `sandbox` |
| 角色 | C（沙箱） |
| 周期 | Week 12，2026-11-24 |
| 相关提交 | `f907ebc`（实现）、`820a1cf`（记录） |
| 关联记录 | `resource_limits.md`、`budget_wiring.md` |

## 1. 背景

任务被中止后，需要向用户说明中止原因。`RunResult` 原先提供两个出口，均不适用于任务消息字段：

| 出口 | 不适用原因 |
|---|---|
| `summary`（属性） | 超时情况下仅返回「超时」，无法区分单次超时与总预算耗尽 |
| `as_feedback()` | 面向上层模型，包含完整 pytest 输出，长度不适于直接展示 |

其结果是任务失败时 `message` 字段为空，或包含未经裁剪的诊断文本。

## 2. 实现内容

| 文件 | 变更 | 提交 |
|---|---|---|
| `sandbox/runner.py` | `RunResult` 新增 `failure_reason()` 方法 | `f907ebc` |
| `tests/roles/c/test_sandbox_isolation.py` | 新增 2 项测试 | `f907ebc` |

调用方式：

```python
from sandbox.limits import TimeBudget
from sandbox.runner import run_pytest

budget = TimeBudget(120)
result = run_pytest(ws.root, timeout=60, budget=budget)

if not result.passed:
    task.message = result.failure_reason()   # 例：总时间预算 120s 已用完，任务中止
    task.status  = "failed"
```

返回约定：

| 情况 | 返回值 |
|---|---|
| 任务通过 | 空字符串（避免前端展示空错误） |
| 超时 / 预算耗尽 | `stderr` 中的原因描述 |
| 测试未通过 | pytest 的结论行 |

## 3. 测试覆盖

| 测试 | 验证内容 |
|---|---|
| `test_failure_reason_explains_budget_exhaustion` | 预算耗尽时返回值同时包含「预算」与「中止」 |
| `test_failure_reason_is_empty_when_passed` | 通过的任务返回空字符串 |

## 4. 验证记录

环境同步（产生合并提交，属预期结果）：

```text
PS> git fetch origin
   dc733d0..0d3ed95  course/a  -> origin/course/a
   26eeaae..59ae66c  main      -> origin/main
PS> git merge origin/main
Merge made by the 'ort' strategy.
 ... 10 files changed, 389 insertions(+), 21 deletions(-)
```

本层测试连续执行三次：

```text
PS> 1..3 | ForEach-Object { .\.venv\Scripts\python.exe -m pytest tests/roles/c -q }
===== 第 1 次 =====
27 passed in 8.55s
===== 第 2 次 =====
27 passed in 8.66s
===== 第 3 次 =====
27 passed in 8.55s
```

全量回归（合并前）：

```text
PS> .\.venv\Scripts\python.exe -m pytest tests -q
98 passed, 1 warning in 33.12s
```

在最新 `main`（PR #17 合并后）复验，2026-11-25：

```text
PS> .\.venv\Scripts\python.exe -m pytest tests/roles/c -q
27 passed in 10.16s

PS> .\.venv\Scripts\python.exe -m pytest tests -q
115 passed, 1 warning in 66.92s
```

## 5. 结论

```text
C_WEEK12_DAY5: PASS
```

- 本层用例 27 项（Day 4 的 25 项 + 本期 2 项），连续三次通过
- 合并至 `main` 后的全量结果：115 项通过
- 实现提交：`f907ebc`

## 6. 调用约定

本模块仅提供失败原因的描述能力，不负责修改任务状态。端到端生效需满足两项条件：

1. 调用 `run_pytest` 时传入 `TimeBudget` 实例；
2. `result.timed_out` 为真时，由任务执行层将任务状态置为 `failed`，并写入 `failure_reason()`。

仅满足条件 1 时，任务会在预算耗尽后中止，但状态仍停留在 `running`。
