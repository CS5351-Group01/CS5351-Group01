## 这个 PR 做了什么

<!-- 一句话说清。不要写「优化」「完善」这种话。 -->

## 自查

- [ ] 我只改了自己角色目录下的文件（`app/` `agent/` `sandbox/` `llm/` `frontend/` `eval/`）
- [ ] 我没改 `examples/`、`tests/conftest.py`、`requirements.txt` 这些公共文件
- [ ] 本地跑过 `python tools/check_pr_ownership.py` 并且是绿的
- [ ] 我这一层的测试单独跑是全绿的：`python -m pytest tests/roles/<我的字母> -q`
- [ ] 所有写了 `PASS` 的地方都有真实命令和真实输出
- [ ] 没跑的东西写了 `NOT_RUN`

## 证据

- 对应周：Week <NN>
- 证据文件：`course_evidence/<角色>/week<NN>/`
- 实际执行的命令：

```text

```

## 给组长看的话

<!-- 有阻塞、有分歧、有需要拍板的地方写在这里。没有就写「无」。 -->
