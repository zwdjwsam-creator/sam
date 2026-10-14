# RUNBOOK

工作目录：`C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013`

本轮 dry-run，不写 E：

```
python -m r9_bounded_pilot dry-run --sample C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_SAMPLE_FILES.json --contract C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json
```

将来单独授权后的 execute。当前合同 `pilot_write_authorized=false`，这条命令会在任何目标写入前拒绝：

```
python -m r9_bounded_pilot execute --sample C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_SAMPLE_FILES.json --contract C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json
```

全量入口保持拒绝：

```
python r9_formal_executor.py copy --copy-authorized --format-done
```

样本来自只读计划，生成器是 `r9_bounded_pilot.build_sample`。原计划 SHA256 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`。样本 SHA256 `b92519954ae7f83f15b873865aeb73220d7d0ef00ba81eaf58965c05be37572d`。代码 digest `53485b5eb64fb2c8f0d823cc5dd26ec8a2ae500ddfc18a349e63a75a530593d6`。

目标只允许 `E:\R9_POSTFORMAT_PILOT_20261014`，新卷 `D86AEE82`，磁盘 `eui.E8238FA6BF530001001B448B42E694AE`。本轮没有创建该目录。
