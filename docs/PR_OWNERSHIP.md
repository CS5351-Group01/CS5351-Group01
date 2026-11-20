# PR 文件所有权规则

一句话：**每人只在自己的目录里改，然后 PR 到 `main`。**
越权由 CI 拦，不靠组长肉眼审 diff。

## 谁能改什么

规则只有一个来源：仓库根目录的 `roles.json`。

| 归属 | 路径 |
|---|---|
| **组长独占** | `course_evidence/team/**`、`docs/**`、`tools/**`、`.github/**`、`examples/**`、`tests/conftest.py`、`README.md`、`requirements.txt`、`run.py`、`roles.json` |
| **A** 后端 | `app/**`、`tests/roles/a/**` |
| **B** Agent 核心 | `agent/**`、`tests/roles/b/**` |
| **C** 沙箱 | `sandbox/**`、`tests/roles/c/**` |
| **D** LLM 集成 | `llm/**`、`tests/roles/d/**` |
| **E** 前端 | `frontend/**`、`tests/roles/e/**` |
| **F** 评估 | `eval/**`、`tests/roles/f/**` |

每个角色还拥有自己的 `course_evidence/<角色>/**`。
完整清单以 `roles.json` 为准，这张表只是给人看的。

## 为什么按目录分

这套骨架是**一层一个目录**：`app` / `agent` / `sandbox` / `llm` / `frontend` / `eval`，
六个角色正好一人一层，天然不重叠。

对比一下另一种分法——按文件分（`main.py` 归谁、`utils.py` 归谁）：
那种分法一旦两个人要改同一个文件，就得靠方法级归属、行级冲突来兜，成本高得多。
**能按目录分就别按文件分。**

## 组长分支的特殊待遇

`main` 和 `ops/*` 只核对提交人，**不限制路径**。

原因：组长是集成者，合并冲突、搭骨架、改公共夹具都得靠他。
代价是理论上组长能绕过规则——所以第 1 条纪律是「只有组长是 Admin」。

## 分支与 PR

```
course/<角色>  ->  main     成员
ops/<用途>     ->  main     只有组长
```

PR 必须等 `Check ownership` 变绿。它红了怎么办：

1. 看日志里列出的越权文件 —— 每条都带着「属于谁」；
2. 把不属于你的改动切出去，或者退给对方；
3. **不要**靠重命名、直推 main、或临时改 CI 绕过。

## 这个 check 到底看了什么

- `git diff --name-status --no-renames` 拿改动路径 —— 重命名按「删 + 增」处理，改名绕不过去
- 路径逐条比对 `roles.json` 的 glob
- 只读 git 对象，**不执行 PR 里的任何代码**
- CI 用 `pull_request_target`，checkout 的是 base 版本，PR 的 head 只作为数据 fetch 进来

本地可以预检，和 CI 同一套逻辑：

```bash
python tools/check_pr_ownership.py --base origin/main --head HEAD --branch course/a
```

## 规矩是怎么来的（别删，这是给后来人看的）

> 每出一次所有权事故，就在这里加一行。否则半年后没人知道某条例外为什么存在。

| 日期 | 事故 | 补的规则 |
|---|---|---|
| — | 建组 | 初始规则：按目录分六个角色 |
| — | 组长 ops 分支被自己的规则挡住（无法集成） | `main` / `ops/*` 改为只核对提交人，不限路径 |
