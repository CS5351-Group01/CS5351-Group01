# Day 4 - B Agent 新增 find 技能

胡慧妍

## 改了什么

- `agent/skills.py`：新增 `find` 技能，支持按 glob 模式（如 `*.py`）查找文件，支持 `in <子路径>` 限定范围，最多返回 100 条结果，拦截路径越界。
- `agent/skills.py`：在 `Skills` 类的 `registry` 中注册 `find`。
- `tests/roles/b/test_skill_boundaries.py`：新增 4 个 find 测试（正常找到、找不到、模式不合法、越界拦截）。
- commit 短SHA：1e42833

## 实际跑了什么
```cmd
E:\gcg\Software_Engineering\CS5351-Group01>powershell -Command "1..3 | ForEach-Object { Write-Host \"--- 第 \$_ 次 ---\"; .\.venv\Scripts\python.exe -m pytest tests/roles/b -q }"
--- 第 \1 次 ---
.................................                                            [100%]
33 passed in 0.28s
--- 第 \2 次 ---
.................................                                            [100%]
33 passed in 0.21s
--- 第 \3 次 ---
.................................                                            [100%]
33 passed in 0.25s
```

## 结果
X_WEEK12_DAY4: PASS