# A 角色与边界

WEEK1_START
本文件在 Week 1 创建，日期为真实当前日期。

# A role and scope

## 职责

接入与配置

对应课程原始模块：原 A1：元数据 / 配置 / 环境

## 负责的文件

- `metadata.yaml`
- `_conf_schema.json`
- `pyproject.toml`
- `LICENSE`
- `.astrbot-plugin/**`
- `course_evidence/A/**`
- `tests/roles/a/**`

## 边界

- 只改本角色 `paths` 内的文件
- Week 1–4 只提交 `course_evidence/A/**`，不改生产代码
- `main.py` 如属共享，只改 `main_functions` 里声明过的方法
- 需要动别人的东西时，先提给对方，不直接改
