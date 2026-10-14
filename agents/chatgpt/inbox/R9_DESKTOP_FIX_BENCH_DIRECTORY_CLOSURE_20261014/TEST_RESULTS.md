# 测试

- `python -m unittest test_r9_directory_closure test_r9_formal_chain test_r9_close test_r9_strict`：15 项通过。
- 空目录 junction 的目标来自 `directory_chain`，执行后可观察为目录。删掉目标目录时预检为 `LINK_CLOSURE`，验收含 `DANGLING_TARGET`。
- 没有删除 `E:\R9_CAPABILITY_PILOT_20261014\NORMAL`。`test_r9_capability_pilot` 里“该目录不存在”的旧断言因此仍会失败，这不是本轮要修的迁移逻辑。
