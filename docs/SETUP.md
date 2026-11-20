# 开组清单（6 人版）

按顺序做，别跳。第 6 步是验收，不做等于没装。

---

## 1. 六个人对号入座

先定谁是谁，再填 `roles.json`：

| 角色 | 负责 | 目录 | GitHub |
|---|---|---|---|
| A | 后端 | `app/` | ? |
| B | Agent 核心 | `agent/` | ? |
| C | 沙箱 | `sandbox/` | ? |
| D | LLM 集成 | `llm/` | ? |
| E | 前端 | `frontend/` | ? |
| F | 评估 | `eval/` | ? |

---

## 2. 填 `roles.json`

打开仓库根目录的 `roles.json`，把七个 `PUT-GITHUB-NAME` 换成真的用户名
（`leader` 一个 + 六个角色各一个）。

```bash
python tools/render_codeowners.py     # 重新生成 .github/CODEOWNERS
```

**成功标志**：文件里搜不到 `PUT-` 了。

---

## 3. 配权限

```text
Settings → Collaborators and teams
  你（组长）：Admin
  其余 5 人：Write
```

**别给所有人 Admin。** 给了 Admin 就能关掉第 4 步的保护、能直推 main、能改 CI 配置，
前面所有规则都退化成君子协定。

---

## 4. 开分支保护

```text
Settings → Rulesets → 你的 "main" → Edit
```

| 项目 | 设成 |
|---|---|
| Enforcement status | **Active** |
| Target branches | Include default branch |
| Require a pull request before merging | ☑ Required approvals: **0** |
| Require status checks to pass | ☑ 选 `Check ownership` |
| Block force pushes | ☑ |
| Restrict deletions | ☑ |
| Bypass list | **空** |

> **Required approvals 填 0**：GitHub 不允许你批准自己的 PR，
> 队友还没接受邀请时填 1 会让你连自己的 PR 都合并不了。
> 等大家都能 review 了再改回 1。

---

## 5. 建六条分支

```powershell
git checkout main
git pull
foreach ($r in 'a','b','c','d','e','f') {
  git branch "course/$r" origin/main
  git push -u origin "course/$r"
}
```

每人：

```powershell
git fetch origin --prune
git switch course/<自己的字母>
```

---

## 6. 验收：两个方向都要验

**① 越权必须是红的**

让 A 往 `agent/` 里塞一个文件，开 PR，`Check ownership` 应该失败，并写明：

```text
agent/skills.py 属于角色 B（Agent 核心：技能、记忆、补丁），当前分支是 A。
```

**② 正常必须是绿的**

A 往自己的 `app/` 里改一个文件，开 PR，应该绿。

两个方向都验过，这套东西才算生效。验完把测试 PR 关掉，别合并。

---

## 7. 每人先跑一遍本地环境

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests -q
```

**成功标志**：`35 passed`。

跑不通就别开始写代码——环境问题拖到 Sprint 中间会很难受。

---

## 8. 然后进 Week 1

六个人各自写 `course_evidence/<角色>/week01/role_and_scope.md`（已经生成好了，补两句就行）。

**Week 1–4 不改任何生产代码。** 这四周唯一的产出是「我知道我管哪几行」。

---

## 每周节奏

| 时间 | 谁 | 产出 |
|---|---|---|
| 周一 | 组长 | `course_evidence/team/weekNN/*.md`，一句话说清本周目标 |
| 周内 | 每人 | 自己的 `course_evidence/<角色>/weekNN/*.md` |
| 周内 | 每人 | 至少一个可执行产物（测试/脚本/改动） |
| Week 5 / 9 / 13 | 每人 | 开 PR → 过 CI → 组长合并 |
| 合并后 | 每人 | `git merge --ff-only origin/main` 拉平分支 |

---

## 出事了怎么办

| 症状 | 处理 |
|---|---|
| CI 红，说改到别人的文件 | 切出去，别改名绕过 |
| 两个人要改同一处 | 停，组长定谁改 —— 但按目录分本来不该发生 |
| 有人直推了 main | 立刻 revert，在 `docs/PR_OWNERSHIP.md` 事故表记一行 |
| 有人要改 `examples/` | 不行，那是公共靶子，归组长 |
| 冲突解不了 | 停下来问，**不要** `--ours` / `--theirs` |
