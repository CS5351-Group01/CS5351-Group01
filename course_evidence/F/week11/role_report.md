# Week 11 — 我做了什么（F 评估）

角色：F 评估与实验
分支：`course/f`
日期：2026-11-22

## 改了什么

- `course_evidence/F/week11/role_report.md`（本文件，新增）
- **没有改任何代码**。本周 F 的任务是先把现有实验跑通、把数字记下来，确认评估链路可用，
  再谈加指标。

## 实际跑了什么

先同步到最新 main，再跑：

```powershell
git fetch origin --prune
git merge --ff-only origin/main
```

```text
Already up to date.
```

### 1. 全量测试

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

```text
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
48 passed, 1 warning in 19.53s
```

### 2. 批量修复实验（表格）

```powershell
.\.venv\Scripts\python.exe -m eval.run_experiments
```

```text
用例                      结果      轮数    耗时      说明
----------------------------------------------------------------------
broken_project          PASS    1     1.11    第 1 轮修复通过
empty_input             PASS    1     1.08    第 1 轮修复通过
name_error              PASS    1     1.11    第 1 轮修复通过
off_by_one              PASS    1     1.18    第 1 轮修复通过
syntax_error            PASS    1     1.07    第 1 轮修复通过
----------------------------------------------------------------------
通过 5/5
```

### 3. 同一批实验的 JSON 输出（给后面画图用）

```powershell
.\.venv\Scripts\python.exe -m eval.run_experiments --json
```

```json
[
  { "case": "broken_project", "success": true, "iterations": 1, "duration_s": 1.06, "message": "第 1 轮修复通过" },
  { "case": "empty_input",    "success": true, "iterations": 1, "duration_s": 1.04, "message": "第 1 轮修复通过" },
  { "case": "name_error",     "success": true, "iterations": 1, "duration_s": 1.10, "message": "第 1 轮修复通过" },
  { "case": "off_by_one",     "success": true, "iterations": 1, "duration_s": 1.17, "message": "第 1 轮修复通过" },
  { "case": "syntax_error",   "success": true, "iterations": 1, "duration_s": 1.02, "message": "第 1 轮修复通过" }
]
```

## 结果

```text
F_WEEK11_RESULT: PASS
```

### 用例覆盖的 bug 类型

| 用例 | 类型 | 现象 |
|---|---|---|
| `syntax_error` | 语法错 | 缺冒号，整个文件无法编译 |
| `name_error` | 名字错 | 函数名拼错，运行时 NameError |
| `off_by_one` | 逻辑错 | 循环少走一步，漏掉最后一个元素 |
| `empty_input` | 边界 | 空列表触发除零 |
| `broken_project` | 逻辑错 + 越界 | 两个 bug 同时存在 |

## 重要局限（别让答辩时被人问住）

**5/5 全部 1 轮通过，这个数字目前不能用来证明"模型很强"。**

原因：

1. 现在跑的是内置假模型 `FakeLLM`，它的修法表（`llm/client.py` 的 `DEMO_FIXES`）
   本来就是照着这 5 个用例写的——**等于用答案考答案**。
2. 因此"平均 1.1 轮、100% 通过率"只能说明**闭环管路是通的**，
   不能说明修复能力。
3. 真实模型下的对比实验**尚未执行**（缺 API key），记为 `NOT_RUN`。

```text
REAL_MODEL_EXPERIMENT: NOT_RUN
```

这个局限必须写进报告，否则第 13 周演示时会被当场问倒。

## 下一步（Week 12 计划）

想把评估从"能跑"做到"能出结论"，需要补三块：

1. **换真模型跑同一批用例**，和假模型做对照，看真实通过率和平均轮数。
2. **加一批"假模型修不了"的用例**（比如需要跨多行的重构、需要理解上下文的改动），
   用来区分模型强弱——只有区分度，指标才有意义。
3. **补几个指标**：
   - 每轮耗时分布（不只是总分）
   - 首次修复率 vs 最终修复率（差多少轮才救回来）
   - 用例代码行数 / 复杂度 与 修复成功率 的相关性
   - 失败用例的失败原因归类（语法 / 运行时 / 断言 / 超时）
