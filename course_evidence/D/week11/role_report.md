# Week 11 — 我做了什么

## 改了什么
- 新增文件：`tests/roles/d/test_llm_boundaries.py` （覆盖了模型无代码块、连续失败、空输入、Prompt 拼装、DEMO 编译、调用次数等 6 个边界测试）
- 修改文件：`tests/roles/d/test_iterative_fix.py` （添加了 monkeypatch 修复底层沙箱 Windows 路径 Bug，并修复了 Protocol 继承错误）
- 新增报告：`course_evidence/d/week11/role_report.md`

## 实际跑了什么
命令：`.\.venv\Scripts\python.exe -m pytest tests/roles/d -q`
输出：11 passed in 8.99s

## 结果
X_WEEK11_RESULT: PASS

## 卡在哪
C 模块的 `sandbox/workspace.py` 存在 Windows 路径解析 Bug（`self.root` 未 `.resolve()`），导致正常文件被误判越界。我已在 D 模块的两个测试文件中使用 `monkeypatch` 绕过该 Bug，并已反馈给 C 组。

## Day 3 改了什么
- 修改文件：`tests/roles/d/test_llm_boundaries.py`（新增 4 个边界测试：max_iters=0、多代码块提取、空代码块防御、空修法表异常处理）。
- 修复了测试 `test_demo_fixes_compile` 中由于假模型代码带缩进或冒号导致的编译报错问题。

## Day 3 实际跑了什么
命令：`1..3 | ForEach-Object { .\.venv\Scripts\python.exe -m pytest tests/roles/d -q }`
输出：
（三次结果均为：`19 passed, 1 warning`）
19 passed, 1 warning in 9.90s
19 passed, 1 warning in 9.70s
19 passed, 1 warning in 10.40s

## Day 3 结果
X_WEEK11_DAY3: BUG_FOUND
（说明：已测出 `test_empty_code_block` 场景下，系统提取到空代码块时，会将目标文件直接清空成 `\n`，且因为空文件无语法错误，系统会误报 `success=True`。建议在 `iterative_fix.py` 中增加空字符串判空拦截。）