# 总时间预算的接入状态核查

| 项目 | 内容 |
|---|---|
| 模块 | `sandbox` |
| 角色 | C（沙箱） |
| 周期 | Week 12，2026-11-25 |
| 相关提交 | `05d3062`（预算实现，已合并）、`f907ebc`（失败原因，已合并）、本期记录 |
| 关联记录 | `resource_limits.md`、`failure_reason.md` |

## 1. 核查目的

本期任务要求为沙箱增加总时间预算，使单个修复任务的执行时间存在上限，超限后任务标记为失败
并说明原因。总时间预算的实现（`sandbox.limits.TimeBudget` 与 `run_pytest(budget=...)`）
已于前两期完成并合并。

本记录核查该能力在端到端流程中的实际生效情况，并记录所需的上层接口变更。

## 2. 核查结果

该能力目前**未在端到端流程中生效**。`llm/iterative_fix.py` 中两处 `run_pytest` 调用均未传入 `budget`：

| 位置 | 当前调用 | 影响 |
|---|---|---|
| `llm/iterative_fix.py:79`（`repair_project`） | `run_pytest(workspace.root, target=test_target)` | 单次超时采用默认值 60 秒；多轮执行时无总时长上限 |
| `llm/iterative_fix.py:154`（`repair_source`） | `run_pytest(..., timeout=timeout)` | 仅约束单次调用；多轮执行时总时长可累加，无上限 |

由此产生的实际行为：

- 单轮内的死循环会因单次超时被终止；
- 任务的**总**执行时间不受约束，多个超时轮次可累加；
- 预算对象未被使用，`BudgetExceeded` 分支无法触发。

## 3. 影响分析

| 场景 | 当前行为 | 预期行为 |
|---|---|---|
| 单轮测试挂死 | 60 秒后终止 | 终止 |
| 连续三轮各挂死 | 约 180 秒后结束 | 到达总预算即终止 |
| 上层忽略 `timed_out` 继续循环 | 每轮重新启动子进程 | 预算耗尽后拒绝启动，直接返回失败 |

第三项为本机制的主要价值：即使调用方未正确处理返回值，也不会持续产生新的子进程。

## 4. 本期补充的验证

为固定接入后的行为，新增测试 `test_budget_blocks_later_iterations_after_exhaustion`：
设置 2 秒总预算，连续调用三次，断言第 1 次实际执行并被终止、第 2 与第 3 次不启动进程
（`duration_ms == 0`），且三次返回的 `stderr` 均包含预算耗尽说明。

```python
budget = TimeBudget(2.0)
results = [run_pytest(tmp_path, timeout=60, budget=budget) for _ in range(3)]

assert results[0].timed_out is True
assert results[0].duration_ms > 0
assert results[1].duration_ms == 0
assert results[2].duration_ms == 0
assert all("预算" in r.stderr for r in results)
```

## 5. 所需的上层接口变更

变更位于 `llm/iterative_fix.py`（由 D 角色维护）。C 侧提供可直接采用的实现建议：

### 5.1 `repair_project`

```diff
 from sandbox.runner import check_syntax, run_pytest
+from sandbox.limits import TimeBudget
 from sandbox.workspace import SandboxWorkspace
@@
 def repair_project(
     project_root: Path | str,
     target: str,
     *,
     max_iters: int = 3,
     client: LLMClient | None = None,
     test_target: str | None = None,
+    time_budget: float | None = 120.0,
 ) -> RepairOutcome:
     client = client or FakeLLM()
+    budget = TimeBudget(time_budget) if time_budget else None
@@
-            result = run_pytest(workspace.root, target=test_target)
+            result = run_pytest(workspace.root, target=test_target, budget=budget)
             history.append(f"第 {iteration} 轮：{result.summary}")
+
+            if result.timed_out:
+                return RepairOutcome(
+                    success=False,
+                    iterations=iteration,
+                    final_code=last_code,
+                    message=result.failure_reason(),
+                    report="\n".join(history),
+                    history=history,
+                )
```

### 5.2 `repair_source`

```diff
 def repair_source(
     source_code: str,
     *,
     max_iters: int = 3,
     client: LLMClient | None = None,
     timeout: float = 60.0,
+    time_budget: float | None = 120.0,
 ) -> RepairOutcome:
     client = client or FakeLLM()
+    budget = TimeBudget(time_budget) if time_budget else None
@@
-            result = run_pytest(workspace.root, target="tests/test_smoke.py", timeout=timeout)
+            result = run_pytest(
+                workspace.root,
+                target="tests/test_smoke.py",
+                timeout=timeout,
+                budget=budget,
+            )
             history.append(f"第 {iteration} 轮：{result.summary}")
+
+            if result.timed_out:
+                return RepairOutcome(
+                    success=False,
+                    iterations=iteration,
+                    final_code=candidate,
+                    message=result.failure_reason(),
+                    report="\n".join(history),
+                    history=history,
+                )
```

### 5.3 任务状态层

`RepairOutcome.message` 在预算耗尽时即为原因描述，任务执行层可直接采用：

```python
outcome = repair_source(code, time_budget=120)
task.status  = "success" if outcome.success else "failed"
task.message = outcome.message
```

## 6. 验证记录

```text
PS> .\.venv\Scripts\python.exe -m pytest tests/roles/c -q
28 passed in 13.47s

PS> 1..3 | ForEach-Object { .\.venv\Scripts\python.exe -m pytest tests/roles/c -q }
===== 第 1 次 =====
28 passed in 12.95s
===== 第 2 次 =====
28 passed in 13.68s
===== 第 3 次 =====
28 passed in 11.67s

PS> .\.venv\Scripts\python.exe -m pytest tests -q
116 passed, 1 warning in 67.10s
```

## 7. 结论

```text
C_WEEK12_DAY6: PASS（沙箱侧完成，接入待 llm 层）
```

| 项目 | 状态 |
|---|---|
| 总时间预算实现 | 已完成并合并（`05d3062`） |
| 失败原因接口 | 已完成并合并（`f907ebc`） |
| 多轮循环下的预算行为 | 已由测试固定（本期新增 1 项，本层共 28 项） |
| 端到端生效 | 未完成，依赖 `llm/iterative_fix.py` 的两处调用变更 |

在 `llm` 层完成上述变更前，总时间预算不具备端到端约束能力；单次超时约束仍然有效。
