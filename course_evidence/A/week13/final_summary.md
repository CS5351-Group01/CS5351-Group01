# Week 13 — A 后端：收尾与报告证据

日期：2026-11-25

## 交付

| 项 | 位置 / 结果 |
|---|---|
| 后端全层 | `app/`（认证、上传白名单、任务归属、原文件接口、轮次进度） |
| 已合并 PR | #19（Week 12 轮次进度），merge commit `2e49bba` |
| 本层测试 | `tests/roles/a/` → 25 passed |
| 全量测试 | `tests/` → 123 passed |

## 报告 2.2 的证据（沙箱不能直接改原目录）

反面场景：如果沙箱直接在原目录上改代码，模型输出一份半截文件后 pytest 超时，
原文件已经被覆盖，下一轮只能基于坏代码继续修，用户上传的原始版本也不可恢复。

现在由 `sandbox/workspace.py` 复制到临时目录（`_copy_in`），`__exit__` 时删除；
C 的测试把「原文件一个字节都不动」锁死了。实际跑：

```text
.\.venv\Scripts\python.exe -m pytest "tests/roles/c/test_sandbox_isolation.py::test_source_file_untouched_including_mtime" -q
1 passed in 0.02s
```

## 报告 4.2 的证据（max_iters 为什么是 3）

- `app/services/task_runner.py:16`：`MAX_REPAIR_ITERS = 3`
- `llm/iterative_fix.py`：`repair_source(..., max_iters=3)`，第 3 轮仍失败时返回
  `success=False`、`message="3 轮内未能修复"`，任务状态落 `failed`，每轮摘要留在 `report`
- 每轮 = 1 次模型调用 + 1 次 pytest；真模型单轮实测 1.5~3 秒（报告 6.2），3 轮约 5~10 秒
- `max_iters` 是参数，测试/实验可覆盖（进度测试就用 2 轮）

## 最难的一件事

```text
A | Jy1372099 | 后端全层
最难的一件事：最难的是让 task_runner 在不改 D 的 llm/ 代码的前提下拿到轮次——最后用 _ProgressClient 把 client.complete() 包了一层，才知道现在是第几轮。
```

## 实际跑的命令与输出

```text
.\.venv\Scripts\python.exe -m pytest tests/roles/a -q
25 passed, 1 warning in 8.67s

.\.venv\Scripts\python.exe -m pytest tests -q
123 passed, 1 warning in 31.54s
```
