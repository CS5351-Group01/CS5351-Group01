# 网页版多轮对话代码修复代理

一个在浏览器里用的自动改代码工具：上传一份有 bug 的 Python 文件，
系统把它放进沙箱、调大模型生成修复、跑测试验证，不通过就带着失败信息再修一轮。

```text
上传 → 生成修复 → 沙箱应用 → 跑测试 → 通过？→ 交付
                    ↑                    ↓ 否
                    └──── 失败信息回灌 ───┘
```

## 架构

```text
frontend/    浏览器里那一页（上传、状态轮询、结果显示）
    ↓ HTTP
app/         FastAPI：注册登录、JWT、文件存储、任务调度
    ↓ 后台任务
llm/         闭环修复：拼 prompt、调模型、解析回复、多轮重试
    ↓ 调用
sandbox/     把项目复制到临时目录，跑 pytest，跑完删掉
    ↓ 依赖
agent/       技能（ls/read/grep/write）、记忆、补丁落盘
```

四条边界很清楚：**前端只说话，后端只调度，llm 只决策，sandbox 只执行**。
`agent/` 是前三者共用的小工具层。

## 六个人怎么分

| 角色 | 负责 | 目录 |
|---|---|---|
| **A** | 接口、认证、数据、任务调度 | `app/**` |
| **B** | Agent 核心：技能、记忆、补丁 | `agent/**` |
| **C** | 沙箱与测试执行 | `sandbox/**` |
| **D** | LLM 集成：客户端、Prompt、闭环 | `llm/**` |
| **E** | 前端：上传、对话、结果可视化 | `frontend/**` |
| **F** | 评估与实验：数据集、批量跑、指标 | `eval/**` |

**目录即归属**，没有共享文件。组长独占 `docs/`、`tools/`、`.github/`、
`examples/`、`tests/conftest.py`、`requirements.txt`、`run.py`。

规则写在 `roles.json` 里，CI 每个 PR 自动查，见 `docs/PR_OWNERSHIP.md`。

## 跑起来

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

python run.py
```

打开 <http://127.0.0.1:8000>，注册一个账号，传一个 `.py` 文件。

**没有模型 key 也能跑**：系统会退化成假模型（`llm/client.py` 里的 `FakeLLM`），
它只会修示例项目里那两个预置 bug，用来跑通流程。

要接真模型：

```bash
set LLM_API_KEY=sk-xxx
set LLM_BASE_URL=https://api.deepseek.com/v1
set LLM_MODEL=deepseek-chat
```

## 跑测试

```bash
python -m pytest tests -q                     # 全部
python -m pytest tests/roles/a -q             # 只跑 A 的
python -m eval.run_experiments                # 闭环实验，输出对照表
```

## 示例项目

`examples/broken_project/` 是一个故意写坏的小模块（`add` 返回减法、`last_item` 越界）。
它是全组的公共靶子：C 拿它测沙箱，D 拿它测闭环，F 拿它做实验。

因为好几个角色都要用，所以**它归组长管**，别人不要改——改坏了同时影响三个人的测试。

## 每周节奏

| 阶段 | 周 | 每个人干什么 |
|---|---|---|
| 摸清边界 | 1–4 | 只写 `course_evidence/<角色>/weekNN/*.md`，不动代码 |
| Sprint 1 | 5 | 每个角色一个可执行测试 + 第一次 PR |
| Sprint 2 | 6–9 | 补边界/失败路径测试，或做真实改进 |
| Sprint 3 | 10–13 | 第二轮改进、回归、答辩材料、最终 PR |

每一周都要有一个**不是 Markdown** 的产物。写了 `PASS` 就必须能敲命令复现，
没跑过的写 `NOT_RUN`。
