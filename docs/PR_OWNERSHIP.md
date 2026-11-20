# PR 文件所有权规则

一句话：**每人只在 `course/<角色>` 分支上改自己的东西，然后 PR 到 `main`。**
越权由 CI 拦，不靠组长肉眼审 diff。

## 谁能改什么

规则只有一个来源：仓库根目录的 `roles.json`。

| 归属 | 路径 |
|---|---|
| 组长独占 | `course_evidence/team/**`、`docs/**`、`tools/**`、`.github/**`、`README.md`、`roles.json` |
| 角色 A — 接入与配置 | 元数据、配置 schema、打包元数据、i18n、`course_evidence/A/**`、`tests/roles/a/**` |
| 角色 B — 主流程与集成 | `main.py` 的编排方法、`SKILL.md`、`course_evidence/B/**` |
| 角色 C — 输入侧 | `course_evidence/C/**`、`tests/roles/c/**`、`course_tools/c/**` |
| 角色 D — 现场与交付 | `codeagent_packager.py`、`course_evidence/D/**`、`tests/roles/d/**` |
| 角色 E — 沙箱与 JS 检查 | `codeagent_sandbox.py`、`codeagent_js_checker.js`、`package.json`、`course_evidence/E/**` |
| 角色 F — 安全与质量 | `codeagent_security.py`、`course_evidence/F/**`、`tests/roles/f/**` |

完整清单以 `roles.json` 为准，这张表只是给人看的。

## 共享文件怎么分

`main.py` 是共享的，按**方法**归属，不按文件归属：

- A 拥有配置读取、Node.js 准备那几组方法
- B 拥有主流程编排那几组方法
- 方法名写进 `roles.json` 的 `main_functions`

不知道有哪些方法时：

```bash
python tools/list_main_methods.py main.py
```

改到 `<module-level>`（import、模块级常量、类骨架）会被判失败 —— 那属于「结构改动」，
要么组长自己改，要么在 `roles.json` 里显式写清归谁。

## 分支与 PR

```
course/<角色>  ->  main     成员
ops/<用途>     ->  main     只有组长
```

PR 必须等 `Check ownership` 这个 check 变绿。它红了怎么办：

1. 看日志里列出的越权文件 —— 逐条都带着「属于谁」；
2. 把不属于你的改动切出去（`git restore --staged` / 拆分支），或者退回给你的队友；
3. **不要**靠重命名、直接推 main、或临时改 CI 绕过。

## 这个 check 到底看了什么

- `git diff --name-status --no-renames` 拿改动路径 —— 重命名按「删 + 增」处理，改名绕不过去
- 路径逐条比对 `roles.json` 的 glob
- `main.py` 走 AST 比对，按函数/方法名看谁变了，不看行号
- 只读 git 对象，**不执行 PR 里的任何代码**

本地可以precheck，和 CI 同一套逻辑：

```bash
python tools/check_pr_ownership.py --base origin/main --head HEAD --branch course/a
```

## 规矩是怎么来的（别删，这是给后来人看的）

> 这里记录每一次所有权事故，以及为它补的规则。
> 新组可以留空，但**出了事故就写一条**——否则半年后没人知道某条例外为什么存在。

| 日期 | 事故 | 补的规则 |
|---|---|---|
| — | 建组 | 初始规则 |
