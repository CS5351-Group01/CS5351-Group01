# Week 12 — 真模型实验报告

## 1. 实验环境
- 模型：deepseek-chat (OpenAICompatClient)
- API 接口：https://api.deepseek.com/v1
- 测试用例数：5 个

## 2. 真模型实验结果

| 用例名 | 结果 | 轮数 | 耗时 (s) | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| broken_project | PASS | 1 | 2.94 | 第 1 轮修复通过 |
| empty_input | PASS | 1 | 1.75 | 第 1 轮修复通过 |
| name_error | PASS | 1 | 1.55 | 第 1 轮修复通过 |
| off_by_one | PASS | 1 | 2.03 | 第 1 轮修复通过 |
| syntax_error | PASS | 1 | 1.93 | 第 1 轮修复通过 |

**汇总：通过率 5/5 (100%)，平均轮数 1.0 轮。**

## 3. 运行命令与输出
命令：.\.venv\Scripts\python.exe -m eval.run_experiments
输出：
客户端：OpenAICompatClient (model=deepseek-chat)

用例                 结果    轮数    耗时    说明
------------------------------------------------------------
broken_project       PASS    1       2.94    第 1 轮修复通过
empty_input          PASS    1       1.75    第 1 轮修复通过
name_error           PASS    1       1.55    第 1 轮修复通过
off_by_one           PASS    1       2.03    第 1 轮修复通过
syntax_error         PASS    1       1.93    第 1 轮修复通过
------------------------------------------------------------
通过 5/5

## 结果
X_WEEK12_DAY4: PASS