# E 角色与边界

WEEK1_START
本文件在 Week 1 创建，日期为真实当前日期。

# E role and scope

## 职责

沙箱与 JavaScript 检查

对应课程原始模块：原 D1：Sandbox / JavaScript Checker

## 负责的文件

- `skills/CodeAgent/scripts/codeagent_sandbox.py`
- `skills/CodeAgent/scripts/codeagent_js_checker.js`
- `skills/CodeAgent/scripts/package.json`
- `course_evidence/E/**`
- `tests/roles/e/**`
- `course_tools/e/**`

## 边界

- 只改本角色 `paths` 内的文件
- Week 1–4 只提交 `course_evidence/E/**`，不改生产代码
- `main.py` 如属共享，只改 `main_functions` 里声明过的方法
- 需要动别人的东西时，先提给对方，不直接改
