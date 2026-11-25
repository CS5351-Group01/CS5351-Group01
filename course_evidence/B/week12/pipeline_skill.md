# Day 5 - B Agent 管道调度支持

胡慧妍

## 改了什么

- `agent/core.py`：重构 `run` 方法，支持 `|` 分割的多条指令。采用递归调用，分离管道逻辑和单条指令逻辑。
- `tests/roles/b/test_pipeline.py`：新增 3 个管道测试（正常管道、包含未知指令、记忆记录）。
- commit短SHA：dca5b38

## 实际跑了什么
```cmd
E:\gcg\Software_Engineering\CS5351-Group01>powershell -Command "1..3 | ForEach-Object { Write-Host \"--- 第 \$_ 次 ---\"; .\.venv\Scripts\python.exe -m pytest tests/roles/b -q }"
--- 第 \1 次 ---
....................................                                         [100%]
36 passed in 0.31s
--- 第 \2 次 ---
....................................                                         [100%]
36 passed in 0.25s
--- 第 \3 次 ---
....................................                                         [100%]
```

## 结果
X_WEEK12_DAY5: PASS