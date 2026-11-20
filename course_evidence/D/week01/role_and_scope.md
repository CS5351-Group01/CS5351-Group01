# D 角色与边界

WEEK1_START
本文件在 Week 1 创建，日期为真实当前日期。

# D role and scope

## 职责

现场与交付：调试快照与打包

对应课程原始模块：原 C1 Debug/Snapshot/Rollback + 原 C2 Packager/Delivery

## 负责的文件

- `skills/CodeAgent/scripts/codeagent_packager.py`
- `course_evidence/D/**`
- `tests/roles/d/**`
- `course_tools/d/**`

## 边界

- 只改本角色 `paths` 内的文件
- Week 1–4 只提交 `course_evidence/D/**`，不改生产代码
- `main.py` 如属共享，只改 `main_functions` 里声明过的方法
- 需要动别人的东西时，先提给对方，不直接改
