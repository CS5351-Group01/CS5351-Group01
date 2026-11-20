# C 角色与边界

WEEK1_START
本文件在 Week 1 创建，日期为真实当前日期。

# C role and scope

## 职责

输入侧：需求解析与会话状态

对应课程原始模块：原 B1 需求解析/分类 + 原 B2 Session/State

## 负责的文件

- `course_evidence/C/**`
- `tests/roles/c/**`
- `course_tools/c/**`

## 边界

- 只改本角色 `paths` 内的文件
- Week 1–4 只提交 `course_evidence/C/**`，不改生产代码
- `main.py` 如属共享，只改 `main_functions` 里声明过的方法
- 需要动别人的东西时，先提给对方，不直接改
