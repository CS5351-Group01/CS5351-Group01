# 开组清单（6 人版）

按顺序做，别跳。第 8 步是验收，不做等于没装。

---

## 0. 先确认项目源在哪

这套骨架假设项目是 **CodeAgent（AstrBot 插件）**，路径按它的目录结构写。

如果你们组拿到的是别的起始代码：

- 改 `roles.json` 里每个角色的 `paths` 就行，别改脚本
- 改完跑 `python tools/render_codeowners.py` 重新生成 CODEOWNERS

**先确认你们有起始源码再往下做**——没有源码，整个所有权规则没有对象。

---

## 1. 建 Organization（不是个人仓库）

GitHub 网页 → 右上角头像 → **New organization** → Free 计划。

为什么必须用 org：

- 个人仓库的协作者权限只有 Read / Write / Admin 三档，混着用会乱
- org 才有 Team 概念，成员进出不用逐个仓库改
- 课程结束后仓库移交/归档更干净

---

## 2. 建空仓库

```text
名字：CS5351-<你们组号>
可见性：Private（先 Private，别一上来就 public）
初始化：不要勾 README / .gitignore / license
```

**空仓库**——第一条 commit 由组长自己写，这样 `main` 的历史从第一天就干净。

---

## 3. 配权限（这条最容易漏，也最要命）

```text
Settings → Collaborators and teams
  你（组长）：Admin
  其余 5 人：Write
```

**别给所有人 Admin。** 给了 Admin 就等于谁都能：

- 关掉 branch protection
- 直接 push 到 main
- 删掉那个 required check

那前面所有规则都退化成君子协定。

---

## 4. 保护 main

```text
Settings → Branches → Add branch ruleset (或 classic protection)
分支：main
✅ Require a pull request before merging
      Required approvals: 1
✅ Require status checks to pass before merging
      → 先跑一次 CI 让它出现，再选 "Check ownership"
✅ Do not allow bypassing the above settings
❌ Allow force pushes
❌ Allow deletions
```

---

## 5. 把骨架放进去

把这套文件拉进本地空仓库，然后：

```bash
git checkout -b ops/scaffold
```

要放的：

```text
roles.json
.github/CODEOWNERS            ← 先跑生成器，别手写
.github/workflows/pr-ownership.yml
docs/PR_OWNERSHIP.md
docs/SETUP.md
tools/check_pr_ownership.py
tools/list_main_methods.py
tools/render_codeowners.py
templates/
course_evidence/team/week01/ownership.md
```

```bash
git add -A
git commit -m "chore: bootstrap team ownership guard"
git push -u origin ops/scaffold
```

开 PR `ops/scaffold -> main`，合并。

---

## 6. 填 roles.json（唯一的配置点）

三件事：

**① 组长账号**

```json
"leader": { "github": "你的GitHub用户名", ... }
```

**② 六个人的账号**

每个角色一个 `github` 字段。对上号之后，`ops/*` 分支就只认组长、`course/<角色>` 只认本人。

**③ `main.py` 的方法归属**

先把源码放进来，然后：

```bash
python tools/list_main_methods.py main.py
```

输出类似：

```text
main.py 可单独归属的符号（14 个）：
  _get_config
  _prepare_node_dependencies
  CodeAgentPlugin.initialize
  CodeAgentPlugin.handle_message
  ...
```

把配置/环境类的丢给 A 的 `main_functions`，编排类的丢给 B 的。**一个方法只能出现在一个角色里**，
重复了 CI 会直接报「配置有歧义」。

改完：

```bash
python tools/render_codeowners.py
git add roles.json .github/CODEOWNERS
git commit -m "chore: assign roles and main.py symbols"
```

---

## 7. 建六条分支

```bash
for r in a b c d e f; do
  git branch "course/$r" origin/main
  git push -u origin "course/$r"
done
```

每个人：

```bash
git fetch origin --prune
git switch course/<自己的角色>
```

---

## 8. 验收：故意开一个越权 PR

**不做这步就等于没装。** 让 A 在自己的分支上加一行改 `course_evidence/B/**` 的文件，
开 PR，看 `Check ownership` 是不是**红的**。

红了 → 装上去了。
绿了 → 你的 CI 没跑，或者 `roles.json` 路径写错了，回去查第 4 步的 required status check。

然后再开一个正常的 PR 确认它是**绿的**。两个方向都验过，这套东西才算生效。

验证完把那个测试 PR 关掉，别合并。

---

## 每周节奏

| 时间 | 谁做 | 产出 |
|---|---|---|
| 每周开头 | 组长 | `course_evidence/team/weekNN/*.md`，一句话说清本周目标 |
| 周内 | 每人 | 自己的 `course_evidence/<角色>/weekNN/*.md` + 至少一个可执行产物 |
| 周内 | 每人 | 推 `course/<角色>`，**不用**每周开 PR，攒到 Sprint 末 |
| Week 5 / 9 / 13 | 每人 | 开 PR → 过 CI → 组长合并 |
| 合并后 | 每人 | `git merge --ff-only origin/main` 拉平自己的分支 |

**每个 Sprint 每人至少一个非纯文档产物**：测试、脚本、配置、源码改动之一。
四周全是 Markdown 是不合格的。

---

## 出事了怎么办

| 症状 | 处理 |
|---|---|
| CI 红了说自己改到别人的文件 | 切出去，别再提交；不要改名绕过 |
| 两个人改了 `main.py` 同一个方法 | 停，组长定谁改，另一个回退 |
| 有人直推了 main | 立刻 revert，然后在 `docs/PR_OWNERSHIP.md` 事故表里记一条 |
| 有人要加公共目录 | 带理由开 PR 改 `roles.json`，别私下 `git add -f` |
| 冲突解不了 | 停下来问，**不要** `git checkout --ours/--theirs` 蒙过去 |

---

## 一个提醒

这套东西的价值不在文件本身，在**第 8 步那个红叉**。

它红了，团队就知道边界是真的；它绿了（或者根本没装），所有人都会觉得规则只是组长说说而已，
然后 Week 6 开始继续扯皮。
