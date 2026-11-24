# Week 12 · C（沙箱）：失败原因 failure_reason()

Date: 2026-11-24（Day 5）
Commit: `f907ebc`（代码）、`820a1cf`（本记录）

组长这一轮的要求是「超了标记 failed **并说明原因**」。
前一份记录（`resource_limits.md`）解决的是「刹得住」，这一份解决的是「刹住之后说得出为什么」。

## 为什么需要它

`RunResult` 原来有两个出口，都不适合直接写进前端/数据库的 `message` 字段：

| 出口 | 问题 |
|---|---|
| `summary`（property） | 超时只会返回「超时」两个字，说不出是单次超时还是总预算耗尽 |
| `as_feedback()` | 给模型看的，带一大段 pytest 输出，直接显示给用户太长 |

结果就是：任务失败了，但 `task.message` 要么是空的，要么是一整坨 traceback。

## 改了什么

| 文件 | 说明 | commit |
|---|---|---|
| `sandbox/runner.py` | `RunResult` 新增 `failure_reason()` 方法 | `f907ebc` |
| `tests/roles/c/test_sandbox_isolation.py` | 新增 2 条测试 | `f907ebc` |

一行就能用：

```python
from sandbox.limits import TimeBudget
from sandbox.runner import run_pytest

budget = TimeBudget(120)
result = run_pytest(ws.root, timeout=60, budget=budget)

if not result.passed:
    task.message = result.failure_reason()   # 例：总时间预算 120s 已用完，任务中止
    task.status  = "failed"
```

## 行为表

| 情况 | `failure_reason()` 返回 |
|---|---|
| 通过 | `""`（空字符串，前端不会显示一条空错误） |
| 超时 / 预算耗尽 | `stderr` 里的原因，例如「总时间预算 120s 已用完，任务中止」 |
| 测试失败 | pytest 的结论行，例如「1 failed, 2 passed in 0.12s」 |

## 新增的 2 条测试

| 测试 | 验什么 |
|---|---|
| `test_failure_reason_explains_budget_exhaustion` | 预算耗尽时返回的原因里必须同时出现「预算」和「中止」 |
| `test_failure_reason_is_empty_when_passed` | 通过的任务必须返回空字符串，避免前端显示空错误 |

## 实际跑了什么

同步并合并 main（会产生 merge commit，属于正常）：

```text
PS D:\Projects\SE_project\CS5351-Group01> git fetch origin
   dc733d0..0d3ed95  course/a  -> origin/course/a
   26eeaae..59ae66c  main      -> origin/main
PS D:\Projects\SE_project\CS5351-Group01> git merge origin/main
Merge made by the 'ort' strategy.
 ... 10 files changed, 389 insertions(+), 21 deletions(-)
```

本层连跑 3 次：

```text
PS D:\Projects\SE_project\CS5351-Group01> 1..3 | ForEach-Object { .\.venv\Scripts\python.exe -m pytest tests/roles/c -q }
===== 第 1 次 =====
27 passed in 8.55s
===== 第 2 次 =====
27 passed in 8.66s
===== 第 3 次 =====
27 passed in 8.55s
```

全量回归（合并前）：

```text
PS D:\Projects\SE_project\CS5351-Group01> .\.venv\Scripts\python.exe -m pytest tests -q
98 passed, 1 warning in 33.12s
```

PR #17 合并进 main 之后，重新在最新 main 上复跑（2026-11-25）：

```text
PS D:\Projects\SE_project\CS5351-Group01> .\.venv\Scripts\python.exe -m pytest tests/roles/c -q
27 passed in 10.16s

PS D:\Projects\SE_project\CS5351-Group01> .\.venv\Scripts\python.exe -m pytest tests -q
115 passed, 1 warning in 66.92s
```

## 结果

```text
C_WEEK12_DAY5: PASS
```

- 本层用例：27 个（Day 4 的 25 + 今天 2），连跑 3 次全绿
- 合并 main 后全量：115 passed
- 提交：`f907ebc`

## 对接说明（给 A / D）

C 这层**只提供原语，不改任务状态**。要让它真正生效，task_runner 里需要两步：

1. 把 `TimeBudget` 传进 `run_pytest`（不传就没有总预算，只有单次 timeout）；
2. `result.timed_out` 为真时，把任务标成 `failed` 并把 `failure_reason()` 写入 `message`。

如果只做第 1 步不做第 2 步，任务会在预算耗尽后被中止，但状态仍停留在 running —— 前端会一直转圈。
