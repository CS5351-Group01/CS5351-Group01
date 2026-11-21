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