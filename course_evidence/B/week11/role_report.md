# Week 11 — 我做了什么

胡慧妍

## 改了什么
- 新建了 `tests/roles/b/test_skill_boundaries.py`，补充了 7 个边界测试（ls/read 异常处理、路径穿越拦截、grep 子目录定位、Memory 淘汰机制、未闭合代码块解析）。
- commit SHA: 20d4367

## 实际跑了什么
```cmd
E:\gcg\Software_Engineering\CS5351-Group01>git branch
* course/b
  main

E:\gcg\Software_Engineering\CS5351-Group01>.\.venv\Scripts\python.exe -m pytest tests/roles/b -q
.........................                                  [100%]
25 passed in 0.19s
```

## 结果
B_WEEK11_RESULT: PASS

## 卡在哪
无