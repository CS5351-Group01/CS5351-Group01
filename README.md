# 六人组开局骨架

给「6 人 + 周记录 + 最后要交工程证据」这类课程项目用。核心只有一件事：

> **让"谁改了谁的文件"变成机器能判的事。**

组长最大的成本不是写代码，是每周调解"你为什么动我的文件"。

---

## 里面有什么

```text
roles.json                          唯一配置点：谁管哪些路径、哪些方法
.github/CODEOWNERS                  由生成器产出，不要手改
.github/workflows/pr-ownership.yml  CI：每个 PR 自动查越权
tools/check_pr_ownership.py         校验器本体（路径 glob + AST 方法级）
tools/test_check_pr_ownership.py    校验器的回归测试（12 条）
tools/list_main_methods.py          列出 main.py 里可归属的方法
tools/render_codeowners.py          从 roles.json 生成 CODEOWNERS
tools/init_week01.py                生成 6 份 Week 1 角色文件
docs/SETUP.md                       开组清单，按顺序做
docs/PR_OWNERSHIP.md                规则说明 + 事故记录表
templates/role_week.md              成员每周证据模板
templates/team_week.md              组长每周证据模板
course_evidence/{A..F}/week01/      六份角色边界文件（已生成）
course_evidence/team/week01/        团队分工说明
```

---

## 六个人怎么分

课程原定八个模块，合并成六个：

| 角色 | 职责 | 合并自 |
|---|---|---|
| **A** | 接入与配置 | 原 A1 |
| **B** | 主流程与集成 | 原 A2 |
| **C** | 输入侧：需求解析 + 会话状态 | 原 B1 + B2 |
| **D** | 现场与交付：调试快照 + 打包 | 原 C1 + C2 |
| **E** | 沙箱 + JavaScript 检查 | 原 D1 |
| **F** | 安全 + 质量 + 测试 | 原 D2 |

A 和 B 都碰 `main.py`，所以它们不按文件分、按**方法**分——
这正是 `main_functions` 那套 AST 校验存在的理由。

分得不均想调？改 `roles.json`，跑一次 `python tools/render_codeowners.py` 就行。

---

## 怎么用

**装好之后（见 `docs/SETUP.md`）**，日常只有两条命令：

```bash
# 提交前自查，和 CI 同一套逻辑
python tools/check_pr_ownership.py --base origin/main --head HEAD --branch course/a

# 改完 roles.json 重新生成 CODEOWNERS
python tools/render_codeowners.py
```

开 PR 后等 `Check ownership` 变绿。

---

## 为什么要这么麻烦

因为「每人只改自己的东西」这句话，靠开会讲是不算数的。

没装这套东西的组，典型走势是：

```text
Week 1–4   大家都很客气
Week 5     第一个人发现要改别人的文件才能跑通 → 改了
Week 6     第二个人也开始改 → 没人知道边界在哪了
Week 7     组长开始每周看 diff → 看不过来
Week 9+    冲突频发，全组时间花在扯皮上
```

装上之后，越权在 PR 阶段就红了，**而且报错直接告诉你是谁的东西**：

```text
所有权检查失败：

  - course_evidence/team/week01/evil.md 是组长的保留路径（`course_evidence/team/**`），成员分支不能改。
  - main.py::<module-level> 改到了模块级代码（import / 常量 / 顶层语句），任何角色都不拥有。

OWNERSHIP CHECK FAIL changed=2 violations=2
```

---

## 三条纪律

1. **组长一个人 Admin，其余全部 Write。**
   给了 Admin，谁都能关掉 branch protection、直推 main，前面全白搭。

2. **规则只有 `roles.json` 一个来源。**
   要加公共目录、要改归属，开 PR 改这个文件，别私下 `git add -f`。

3. **每周必须有一个非纯文档产物。**
   测试、脚本、配置、源码改动之一。四周全是 Markdown 是不合格的——
   而证据里写了 `PASS` 的，必须真的能敲命令复现。

---

## 验收

```bash
python tools/test_check_pr_ownership.py
```

应该看到 `12/12 通过`。

然后按 `docs/SETUP.md` 第 8 步，**故意开一个越权 PR 看它是不是红的**。
两个方向都验过，这套东西才算真的生效。
