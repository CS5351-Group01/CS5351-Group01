# A 的 REPORT.md 文稿

> 以下正文可直接替换 `docs/REPORT.md` 对应小节；第 8 节是追加一条。
> 替换后请顺手把 5.3 的 `115 passed` 改成 `123 passed`。

---

## 2.2 四层边界

| 层 | 只做什么 | 不做什么 |
|---|---|---|
| `frontend` | 发请求、渲染结果 | 不做业务判断 |
| `app` | 鉴权、存储、派任务 | 不碰模型，不碰沙箱 |
| `llm` | 问什么、怎么解析、要不要重试 | 不直接读写文件、不跑进程 |
| `sandbox` | 复制、跑、清理 | 不知道什么叫"修复" |
| `agent` | 对工作区做原子操作 | 不知道什么叫"一轮" |

为什么这样分：每层只有一个变化理由，出问题能定位到层；六个人各占一个目录，才能并行改而不互相踩。

反面例子：如果 `SandboxWorkspace` 直接在原目录上改，模型写出一份半截文件（比如 `return a -`）后 pytest 超时，原文件已经被覆盖，下一轮只能拿这份坏代码继续修，用户上传的原始版本也没了。
`tests/roles/c/test_sandbox_isolation.py::test_source_file_untouched_including_mtime` 就是锁这条的：在沙箱里改 `calc.py`，原文件的内容和 mtime 都不许变。

---

## 4.2 为什么设 `max_iters`

模型一直改不对时，循环必须有硬上限：`app/services/task_runner.py` 里 `MAX_REPAIR_ITERS = 3`，`llm/iterative_fix.py` 的 `repair_source(max_iters=3)` 到第 3 轮直接返回 `RepairOutcome(success=False, message="3 轮内未能修复")`，任务落 `failed`，每轮失败摘要留在 `report` 里。

为什么是 3：每轮 = 1 次模型调用 + 1 次 pytest（真模型实测单轮 1.5~3 秒，见 6.2），3 轮上限约 5~10 秒，用户还能等；再往上加，失败信息大多重复，收益递减。`max_iters` 是参数，测试和实验可以覆盖（比如进度测试用 2 轮），默认值只服务线上任务。

---

## 第 8 节（追加一条）

- **A（Jy1372099）**：最难的是让 `task_runner` 在不改 D 的 `llm/` 代码的前提下拿到轮次——最后用 `_ProgressClient` 把 `client.complete()` 包了一层，才知道现在是第几轮。

---

## 备注：报告里需要同步的数字

- 5.3 实际输出：`123 passed`（当前写的是 115）
- 5.1 各角色测试数合计也以实际跑出来的为准
