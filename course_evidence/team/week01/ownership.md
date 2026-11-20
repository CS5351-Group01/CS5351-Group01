# 角色分工

六人小组，每个角色一条 `course/<角色>` 分支。

| 角色 | 职责 | 分支 | 负责文件 |
|---|---|---|---|
| A | 接入与配置 | `course/a` | `metadata.yaml`、`_conf_schema.json`、`pyproject.toml`、`.astrbot-plugin/`、`main.py` 的配置读取与依赖准备方法 |
| B | 主流程与集成 | `course/b` | `main.py` 的主流程编排方法、`SKILL.md` |
| C | 输入侧：需求解析与会话状态 | `course/c` | `course_tools/c/`、`tests/roles/c/` |
| D | 现场与交付：调试快照与打包 | `course/d` | `codeagent_packager.py`、`tests/roles/d/` |
| E | 沙箱与 JavaScript 检查 | `course/e` | `codeagent_sandbox.py`、`codeagent_js_checker.js`、`package.json` |
| F | 安全、质量与测试 | `course/f` | `codeagent_security.py`、`tests/roles/f/` |

组长：`course_evidence/team/**`、`docs/**`、`tools/**`、`.github/**`。

## 为什么是六个角色

课程原定八个模块，六个人要合。合并的两处：

- **C** = 需求解析/分类 + Session/State
  —— 都在「输入进来之后怎么理解、怎么记住」这条线上，接口天然相邻，合起来反而少一次跨人协调。

- **D** = Debug/Snapshot/Rollback + Packager/Delivery
  —— 都在「把现场抓住、再交出去」这条线上，快照和打包共用同一套产物结构。

**A 和 B 没合成一个**，因为 `main.py` 的配置层和编排层是两组独立方法，
合并会让一个人同时改两处共享代码，正好是冲突高发区。分开后可以用方法级归属精确拦。

## 边界纪律

- 只改自己 `paths` 里的文件；`main.py` 只改 `main_functions` 里列出的方法
- Week 1–4 只提交自己 `course_evidence/<角色>/**`，**不动生产代码**
- 发现要改别人的东西 → 开 PR 改 `roles.json`，或者直接提给对方
- 冲突解不了就停下来问，不自动 `--ours` / `--theirs`
