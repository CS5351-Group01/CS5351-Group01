# 现场演示脚本

演示只有 **5 分钟**，目标只有一个：**让人看到一段坏代码被自动修好，且不是编的。**

---

## 演示前 30 分钟

```powershell
cd CS5351-Group01
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# ① 先确认代码本身没问题
python -m pytest tests -q
#   期望：35 passed 以上

# ② 再确认闭环能跑（不联网，用假模型）
python -m eval.run_experiments
#   期望：5 个用例全 PASS，每个 1 轮

# ③ 起服务
python run.py
#   保持这个窗口开着
```

浏览器打开 <http://127.0.0.1:8000>，**先注册一个账号跑一遍**，确认能走完全流程。
演示时不要第一次就现场注册。

---

## 演示流程（5 分钟）

### 1. 开场（30 秒）

> 「我们的项目是一个网页版的代码修复代理。
> 用户在浏览器上传一段有 bug 的代码，系统会在沙箱里自动修改、跑测试验证，
> 不通过就把失败信息回喂给模型再修一轮，直到测试通过。」

### 2. 先展示「它是坏的」（40 秒）

打开终端的 `examples/broken_project`，跑一次：

```powershell
python -m pytest examples/broken_project -q
```

```text
2 failed, 1 passed
FAILED tests/test_calc.py::test_add - assert -1 == 5
FAILED tests/test_calc.py::test_last_item - IndexError: list index out of range
```

> 「这就是我们要修的东西。`add(2,3)` 返回了 -1。」

### 3. 走网页（2 分钟）

1. 登录
2. 上传 `examples/broken_project/calc.py`
3. 点「开始修复」
4. 状态从 `pending` → `running` → `success`
5. 结果区显示修好的完整代码

**讲解要点**（一边等一边说）：

> 「注意它没有直接改原文件。系统把项目复制到临时目录，在副本上试错，
> 跑完就删掉。原文件一个字节都没动——这是沙箱层的承诺。」

### 4. 展示「不是碰运气」（1 分钟）

切回终端：

```powershell
python -m eval.run_experiments
```

```text
用例              结果    轮数    耗时    说明
broken_project    PASS    1      0.78    第 1 轮修复通过
empty_input       PASS    1      0.74    第 1 轮修复通过
name_error        PASS    1      0.80    第 1 轮修复通过
off_by_one        PASS    1      0.75    第 1 轮修复通过
syntax_error      PASS    1      0.76    第 1 轮修复通过
通过 5/5
```

> 「五个不同类型的 bug：语法错、名字拼错、循环少一步、空列表除零、越界。
> 每一个都真的跑过测试才算通过。」

### 5. 收尾（30 秒）

> 「整个系统的边界很清楚：前端只负责说话，后端只负责调度，
> LLM 层只负责决策，沙箱只负责执行。六个人一人一层，
> CI 会自动拦住越权改动。」

---

## 一定要说的一句

> 「为了让演示可复现，我们现在用的是内置的假模型，它只会修这几个预置的 bug。
> 接真模型只要设三个环境变量，代码一行不用改。」

**主动说出局限，比被人问出来强。**

---

## 现场翻车预案

| 情况 | 怎么办 |
|---|---|
| 网页打不开 | 直接演示命令行：`python -m eval.run_experiments` |
| 后端报错 | 切终端跑 `python -m pytest tests -q`，用测试结果顶上 |
| 上传卡住 | 说「后台任务在跑」，同时切到终端展示实验 |
| 模型超时 | 换成假模型：不设 `LLM_API_KEY` 就是假模型 |
| 完全跑不起来 | 播事先录的 60 秒录屏（**提前录好**） |

**提前录一个 60 秒的备用录屏。** 这是唯一不会翻车的保险。

---

## 演示前检查单

```text
□ python -m pytest tests -q      全绿
□ python -m eval.run_experiments 5/5 PASS
□ 浏览器能打开 127.0.0.1:8000
□ 账号已经注册好
□ 还有一个能同时传的文件在手边
□ 备用录屏已录并试播过
□ 终端字号调大（后排看得见）
```
