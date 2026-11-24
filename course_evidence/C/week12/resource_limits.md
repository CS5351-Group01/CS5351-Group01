# 沙箱资源限制：总时间预算与输出截断

| 项目 | 内容 |
|---|---|
| 模块 | `sandbox` |
| 角色 | C（沙箱） |
| 周期 | Week 12，2026-11-24 |
| 相关提交 | `05d3062`（实现）、`cd25d0d`（记录） |
| 关联记录 | `failure_reason.md`、`budget_wiring.md` |

## 1. 背景

沙箱工作区（`sandbox.workspace`）解决了「试错过程污染原始目录」与「路径越界」两类问题，
但不限制单次修复任务的资源消耗，存在两项风险：

1. **执行时间不可控。** `run_pytest` 原先仅提供单次调用超时。修复循环通常执行多轮，
   若每轮均触及超时，任务总耗时随轮数线性增长；若被测代码进入死循环，执行单元将被长期占用。
2. **输出规模不可控。** `stdout` / `stderr` 原先按 `[-MAX_OUTPUT:]` 截取，属于静默截断，
   调用方无法判断输出是否完整。

本期任务要求从三项候选中选取两项实现。选定项为总时间预算与输出上限，
并补充文件数 / 体积上限的测试覆盖（该上限此前已存在，但无测试保护）。

## 2. 实现内容

| 文件 | 变更 | 提交 |
|---|---|---|
| `sandbox/limits.py` | 新增 `TimeBudget`、`BudgetExceeded`、`truncate_output`、`MAX_OUTPUT`、`TRUNCATION_MARKER` | `05d3062` |
| `sandbox/runner.py` | `run_pytest` 新增 `budget` 参数；`RunResult` 新增 `truncated` 字段；输出截断时写入标记 | `05d3062` |
| `sandbox/__init__.py` | 导出上述对象，供上层模块引用 | `05d3062` |
| `tests/roles/c/test_sandbox_isolation.py` | 新增 6 项测试 | `05d3062` |

变更范围限于 `sandbox/**` 与 `tests/roles/c/**`。

### 2.1 总时间预算

`TimeBudget` 以 `time.monotonic()` 计时，向调用方提供剩余预算与耗尽状态；
`run_pytest` 在每次调用时取 `min(单次 timeout, 剩余预算)`。

```python
from sandbox.limits import TimeBudget
from sandbox.runner import run_pytest

budget = TimeBudget(120)                 # 任务总预算 120 秒
for _ in range(max_iters):
    result = run_pytest(ws.root, timeout=60, budget=budget)
    if result.timed_out:                 # 预算耗尽，终止任务
        break
```

行为约定：

| 条件 | 行为 |
|---|---|
| 预算充足 | 单次超时取 `min(timeout, remaining)` |
| 单次执行超出剩余预算 | 终止子进程，返回 `timed_out=True`，`stderr` 记录「总时间预算 Ns 已用完，任务中止」 |
| 预算已耗尽 | 不再启动子进程，直接返回失败结果，`duration_ms` 为 0 |
| 仅发生单次超时（未传预算） | `stderr` 记录「pytest 超过 N 秒未结束」 |

### 2.2 输出上限

`truncate_output()` 保留输出尾部（pytest 的结论行位于末尾），在开头插入标记行
`…[输出已截断]…`，并通过 `RunResult.truncated` 向调用方暴露截断状态。
`RunResult.as_feedback()`（用于构造模型输入）采用同一函数，使模型同样能够识别输出不完整。

### 2.3 文件数 / 体积上限

`MAX_FILES`（5000）与 `MAX_TOTAL_BYTES`（50 MB）为既有约束，本期补充测试覆盖：
通过 `monkeypatch` 收缩阈值，验证超限时抛出 `SandboxError`。

## 3. 测试覆盖

| 测试 | 验证内容 |
|---|---|
| `test_spin_loop_is_aborted_by_budget` | 死循环在预算（1.5 秒）内被终止，且总耗时不超过 8 秒 |
| `test_expired_budget_never_starts_a_process` | 预算耗尽后不再启动子进程（`duration_ms == 0`） |
| `test_huge_output_is_truncated_with_marker` | 超长输出被截断、带标记，且尾部结论行保留 |
| `test_truncate_output_keeps_short_text_intact` | 未超限时不截断、不误报 |
| `test_file_count_limit_raises` | 文件数超限抛出 `SandboxError` |
| `test_total_bytes_limit_raises` | 总体积超限抛出 `SandboxError` |

## 4. 验证记录

环境同步（普通合并）：

```text
PS> git fetch origin
   e5bd1ed..26eeaae  main -> origin/main
PS> git merge origin/main
Updating f4f2503..26eeaae
Fast-forward
```

本层测试连续执行三次：

```text
PS> 1..3 | ForEach-Object { .\.venv\Scripts\python.exe -m pytest tests/roles/c -q }
===== 第 1 次 =====
25 passed in 8.96s
===== 第 2 次 =====
25 passed in 9.30s
===== 第 3 次 =====
25 passed in 8.70s
```

全量回归：

```text
PS> .\.venv\Scripts\python.exe -m pytest tests -q
81 passed, 1 warning in 40.47s
```

## 5. 结论

```text
C_WEEK12_DAY4: PASS
```

- 本层用例 25 项（Day 3 的 19 项 + 本期 6 项），连续三次通过
- 跳过 0 项，失败 0 项
- 合并至 `main` 后（含 `failure_reason` 的 2 项），本层共 27 项

## 6. 已知限制

1. 预算仅覆盖 `run_pytest` 的执行时间，模型调用的往返耗时不在其内。
   完整生效需由 `llm` 层在调用处传入 `TimeBudget`，并在 `timed_out` 时更新任务状态。
2. 子进程终止方式为 `TerminateProcess`，仅作用于直接子进程；
   若被执行的测试另行派生进程，其生命周期不受本机制管理。
3. 输出上限按字符数计量，非字节数；包含多字节字符时实际占用更大。
4. 预算粒度为「每次 `run_pytest` 调用」，非实时检查。

## 7. 后续工作

预算在端到端流程中的接入状态与所需接口变更，见 `budget_wiring.md`。
