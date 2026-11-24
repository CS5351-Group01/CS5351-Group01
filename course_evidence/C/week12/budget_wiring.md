# Week 12 · C（沙箱）：总时间预算的接线核查

Date: 2026-11-25（Day 6）
相关提交：`05d3062`（预算本体，已合并）、`f907ebc`（failure_reason，已合并）、本记录

组长这轮给 C 的原话是：**「一个修复任务最多跑 N 秒，超了标记 failed 并说明原因」**。

预算本体（`sandbox/limits.py` 的 `TimeBudget` + `run_pytest(budget=...)`）在前两天已经做完并合并了。
今天补的是**它到底有没有接上**——结论是：**闸造好了，但调用链上还没有人拉闸。**

## 核查结果：目前不生效

`llm/iterative_fix.py` 里有两处调用 `run_pytest`，**都没有传 `budget`**：

| 位置 | 代码 | 后果 |
|---|---|---|
| `llm/iterative_fix.py:79`（`repair_project`，项目级修复） | `run_pytest(workspace.root, target=test_target)` | 连 `timeout` 都用默认 60s；3 轮最长 180s，**没有总上限** |
| `llm/iterative_fix.py:154`（`repair_source`，单文件修复） | `run_pytest(..., timeout=timeout)` | 只有单次上限，**没有总上限**；一轮死循环最多卡 60s，但 N 轮可以累加 |

也就是说：死循环**单轮**会被 60s 的 `timeout` 掐断，但「整个任务最多 N 秒」这条闸目前没起作用——
预算对象被造出来了，没人把它传进去。

> 为什么 C 不自己改：`roles.json` 里 `llm/**` 归 D。CI 的 `Check ownership` 会拦越权提交，
> 改了就红，所以只能由 D 来接线。C 这边提供的是**一行就能接上的接口**。

## C 侧今天补的测试（循环级行为）

既然接线在 D 那边，C 至少要把「接上之后是什么行为」用测试钉死，避免 D 接错或后人改坏。

新增 `test_budget_blocks_later_iterations_after_exhaustion`：

```python
budget = TimeBudget(2.0)
results = [run_pytest(tmp_path, timeout=60, budget=budget) for _ in range(3)]

assert results[0].timed_out is True      # 第 1 轮真跑了，被预算掐断
assert results[0].duration_ms > 0
assert results[1].duration_ms == 0       # 第 2、3 轮：预算已耗尽，不再起进程
assert results[2].duration_ms == 0
assert all("预算" in r.stderr for r in results)
```

**它证明的是一件比单次超时更重要的事**：即使上层忘了看 `timed_out`、傻乎乎地继续循环，
也不会再拉起新的 pytest 进程。这就是「防止一段死循环拖死服务」的最后一层保险。

## 给 D 的接线 patch（两条，直接可贴）

### ① `repair_project`（项目级，主要路径）

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
+                    message=result.failure_reason(),   # 「总时间预算 120s 已用完，任务中止」
+                    report="\n".join(history),
+                    history=history,
+                )
```

### ② `repair_source`（单文件路径）

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
+                workspace.root, target="tests/test_smoke.py",
+                timeout=timeout, budget=budget,
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

### 给 A 的一行（任务状态侧）

`repair_*` 返回的 `RepairOutcome.message` 在预算耗尽时就是那句「总时间预算 120s 已用完，任务中止」，
task_runner 里直接：

```python
outcome = repair_source(code, time_budget=120)
task.status  = "success" if outcome.success else "failed"
task.message = outcome.message
```

这样「标记 failed 并说明原因」才真的落到用户看得见的那一层。

## 实际跑了什么

```text
PS D:\Projects\SE_project\CS5351-Group01> .\.venv\Scripts\python.exe -m pytest tests/roles/c -q
28 passed in 13.47s

PS D:\Projects\SE_project\CS5351-Group01> 1..3 | ForEach-Object { .\.venv\Scripts\python.exe -m pytest tests/roles/c -q }
===== 第 1 次 =====
28 passed in 12.95s
===== 第 2 次 =====
28 passed in 13.68s
===== 第 3 次 =====
28 passed in 11.67s

PS D:\Projects\SE_project\CS5351-Group01> .\.venv\Scripts\python.exe -m pytest tests -q
116 passed, 1 warning in 67.10s
```

## 结果

```text
C_WEEK12_DAY6: PASS（C 侧完成，接线待 D）
```

- 预算本体：已完成并合并（`05d3062`）
- 失败原因：已完成并合并（`f907ebc`）
- 循环级行为：已用测试钉死（本次新增 1 条，本层共 28 条）
- **未完成的部分（不归 C）**：`llm/iterative_fix.py` 的两处 `run_pytest` 调用需要传 `budget`。
  在 D 接线之前，这条闸**实际不生效**——写在这里，避免答辩时被问「你们说有限时，在哪生效」答不上来。
