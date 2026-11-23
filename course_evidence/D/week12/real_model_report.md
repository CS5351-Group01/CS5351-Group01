# Week 12 — 真模型实验报告

## 1. 实验环境
- 模型：deepseek-chat
- API 接口：https://api.deepseek.com/v1
- 测试用例数：5 个

## 2. 假模型 vs 真模型结果对照

| 用例名 | 假模型结果 | 真模型结果 | 真模型轮数 | 耗时 (s) | 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| broken_project | PASS | PASS | 1 | 2.06 | 第 1 轮修复通过 |
| empty_input | PASS | PASS | 1 | 1.27 | 第 1 轮修复通过 |
| name_error | PASS | PASS | 1 | 1.74 | 第 1 轮修复通过 |
| off_by_one | PASS | PASS | 1 | 1.14 | 第 1 轮修复通过 |
| syntax_error | PASS | PASS | 1 | 2.01 | 第 1 轮修复通过 |

**汇总：通过率 5/5 (100%)，平均轮数 1.0 轮，总耗时约 8.22 秒。**

## 3. 现象观察与反思
- 虽然是真模型，但表现和假模型一样完美（5/5 且 1 轮过）。这说明当前 examples 下的 5 个用例（缺冒号、拼写错、少加号等）属于非常经典的浅层语法/逻辑错误。
- DeepSeek 的代码理解能力很强，结合我们优质的 Prompt 提示词，能够一次性精准定位并修复。
- 能跑出真实的 100% 修复率非常令人振奋。但在未来的答辩/扩展中，我们可以考虑加入更复杂的跨文件调用或业务逻辑错误，来测试真模型的极限。

## 4. 运行命令与输出

### 4.1 真模型评估命令
命令：.\.venv\Scripts\python.exe -m eval.run_experiments
输出：
用例                 结果    轮数    耗时    说明
------------------------------------------------------------
broken_project       PASS    1       2.06    第 1 轮修复通过
empty_input          PASS    1       1.27    第 1 轮修复通过
name_error           PASS    1       1.74    第 1 轮修复通过
off_by_one           PASS    1       1.14    第 1 轮修复通过
syntax_error         PASS    1       2.01    第 1 轮修复通过
------------------------------------------------------------
通过 5/5

### 4.2 本地回归测试（连跑 3 次验证稳定性）
命令：1..3 | ForEach-Object { .\.venv\Scripts\python.exe -m pytest tests/roles/d -q }
输出：
19 passed, 1 warning in 4.49s
19 passed, 1 warning in 4.39s
19 passed, 1 warning in 4.42s

## 结果
X_WEEK12_DAY4: PASS