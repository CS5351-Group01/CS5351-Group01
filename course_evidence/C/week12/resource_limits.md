# Day 4 · C（沙箱）—— 给沙箱加刹车

任务要求「三个里选两个，做扎实」。我做的是 **① 总时间预算** 和 **② 输出上限**，
并把 **③ 文件数 / 体积上限** 的测试覆盖也补上了（那条上限原本存在但没有任何测试守着）。

## 改了什么

| 文件 | 说明 | commit |
|---|---|---|
| `sandbox/limits.py` | **新增**：`TimeBudget`（总时间预算）、`BudgetExceeded`、`truncate_output`（带标记的截断）、`MAX_OUTPUT`、`TRUNCATION_MARKER` | `05d3062` |
| `sandbox/runner.py` | `run_pytest(..., budget=...)` 接预算；`RunResult` 新增 `truncated` 字段；stdout/stderr 截断时打标记 | `05d3062` |
| `sandbox/__init__.py` | 导出 `TimeBudget` / `BudgetExceeded` / `truncate_output` / `MAX_OUTPUT`，方便 D 那层直接 import | `05d3062` |
| `tests/roles/c/test_sandbox_isolation.py` | 新增 6 条测试（下节逐条说明） | `05d3062` |

只动了 `sandbox/**` 和 `tests/roles/c/**`，没碰别人的目录。

### ① 总时间预算

之前的问题：`run_pytest` 的 `timeout` 是**单次**上限。一个修复任务要跑 3 轮，
每轮都卡到 60 秒的话，整个任务最长能拖 3 分钟，而且没有「总预算」的概念。

现在给修复任务一个总预算，每次跑只拿走 `min(单次 timeout, 剩余预算)`：

```python
from sandbox.limits import TimeBudget
from sandbox.runner import run_pytest

budget = TimeBudget(120)                 # 整个任务最多 120 秒
for i in range(max_iters):
    result = run_pytest(ws.root, timeout=60, budget=budget)
    if result.timed_out:                 # 预算见底 → 直接中止
        break
```

关键行为：

- `TimeBudget.clamp(timeout)` 把单次 timeout 压到剩余预算之内 —— 死循环跑满预算就断；
- 预算已经见底时，**不再启动新的子进程**，直接返回 `RunResult(passed=False, timed_out=True)`，
  避免「明明没时间了还起一个进程」；
- 超时信息里区分两种情况：单次超时写「pytest 超过 N 秒未结束」，预算耗尽写「总时间预算 Ns 已用完，任务中止」；
- 计时用 `time.monotonic()`，不受系统时钟调整影响。

### ② 输出上限（带标记）

之前是 `proc.stdout[-MAX_OUTPUT:]` —— **静默截断**。上层拿到一份少了开头的输出，
完全不知道它被截过，日志和评估数据都会失真。

现在统一走 `truncate_output()`：保尾部（pytest 的结论行在最后）、在开头插一行
`…[输出已截断]…`，并且 `RunResult.truncated` 会变成 `True`，供上层显式判断。

`as_feedback()`（喂给模型的那段文本）也走同一个函数，所以模型也能看到「这里不完整」。

### ③ 文件数 / 体积上限（补测试）

`MAX_FILES = 5000`、`MAX_TOTAL_BYTES = 50MB` 两条上限原本就写在 `workspace.py` 里，
但没有任何测试覆盖。今天用 `monkeypatch` 把常量压到很小，验证它们真的会抛 `SandboxError`。

## 新增的 6 条测试

| 测试 | 验什么 |
|---|---|
| `test_spin_loop_is_aborted_by_budget` | 沙箱里放 `while True: pass`，`TimeBudget(1.5)` + `timeout=60` → 必须 8 秒内被掐断，`timed_out=True`，stderr 含「预算」 |
| `test_expired_budget_never_starts_a_process` | 预算 0.2s、先睡 0.35s → 直接判失败，`duration_ms == 0`（证明没起进程） |
| `test_huge_output_is_truncated_with_marker` | 造一份 20 万字符的失败输出 → `truncated=True`、长度 ≤ `MAX_OUTPUT`、含「已截断」、**尾部 `1 failed` 仍在** |
| `test_truncate_output_keeps_short_text_intact` | 不超限时原文返回，不误报截断 |
| `test_file_count_limit_raises` | 3 个文件 + `MAX_FILES=2` → `SandboxError` |
| `test_total_bytes_limit_raises` | 128 字节 + `MAX_TOTAL_BYTES=100` → `SandboxError` |

## 实际跑了什么

同步 main（今天要求用普通 merge，不用 `--ff-only`）：

```text
PS D:\Projects\SE_project\CS5351-Group01> git fetch origin
   e5bd1ed..26eeaae  main       -> origin/main
   ...
PS D:\Projects\SE_project\CS5351-Group01> git switch course/c
Already on 'course/c'
PS D:\Projects\SE_project\CS5351-Group01> git merge origin/main
Updating f4f2503..26eeaae
Fast-forward
 ... 16 files changed, 827 insertions(+), 36 deletions(-)
```

> 说明：我上一轮的提交已经在 `main` 里（PR #12），所以这次是 fast-forward 而不是 merge commit。
> 没有用 `--ff-only`，也没有冲突。

本层连跑 3 次：

```text
PS D:\Projects\SE_project\CS5351-Group01> 1..3 | ForEach-Object { .\.venv\Scripts\python.exe -m pytest tests/roles/c -q }
===== 第 1 次 =====
25 passed in 8.96s
===== 第 2 次 =====
25 passed in 9.30s
===== 第 3 次 =====
25 passed in 8.70s
```

全量回归：

```text
PS D:\Projects\SE_project\CS5351-Group01> .\.venv\Scripts\python.exe -m pytest tests -q
81 passed, 1 warning in 40.47s
```

## 结果

```text
C_WEEK12_DAY4: PASS
```

- 本层用例：25 个（Day 3 的 19 + 今天 6），连跑 3 次全绿
- 跳过：0，失败：0
- 选做：① 总时间预算 ✅ ② 输出上限 ✅（③ 顺带补了测试）

## 局限（写清楚，别夸大）

1. **预算只覆盖 `run_pytest` 的时间**。模型 API 的往返时间不在里面，D 那层要自己把
   `TimeBudget` 传进来、并在 `result.timed_out` 时把任务标记成 failed 才算真正「中止」。
2. **只杀直接子进程**。`subprocess.run(timeout=...)` 在 Windows 上是 `TerminateProcess`，
   如果 pytest 自己再拉起孙进程，那些不会被回收（当前用例集不会，但这是个真实的边界）。
3. **输出上限按字符数算，不是字节数**。中文内容时实际占用会更大。
4. 预算的粒度是「每次 `run_pytest`」，不是「每秒检查一次」——所以最坏情况是
   「剩余预算 0.1s 但本次调用刚好在 0.1s 内结束」，不会立刻中止。
