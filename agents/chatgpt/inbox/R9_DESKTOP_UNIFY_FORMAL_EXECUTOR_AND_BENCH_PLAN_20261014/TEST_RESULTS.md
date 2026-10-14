# 测试

工作目录 `C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013`。

- `python -m unittest test_r9_formal_chain`：3 项通过。
- `test_r9_formal_executor`、`test_r9_close`、`test_r9_strict`、`test_r9_scheduler`、`test_r9_copy_body`、`test_r9_bounded_pilot`：通过。
- `test_r9_capability_pilot`：`test_refusals_and_false_contract_do_not_write` 失败，因为它断言 `E:\R9_CAPABILITY_PILOT_20261014\NORMAL` 不存在。该目录来自已保留的 1345 实跑。本轮没有删除，也没有重跑。

隔离链的首次验收 `content_hash_calls=1`（1 个实体加 1 个别名）。重跑 `copied_count=0`、`linked_count=0`，进程内累计 `hash_calls=3`（首次验收、恢复时核对代表文件、第二次验收），没有按别名再读一遍内容。

本机 false 合同：dry-run 退出 0，execute 退出 3。都没有 E: 写入。
