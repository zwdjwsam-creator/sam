# RUNBOOK

工作目录：`C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013`

调用链：`r9_bounded_pilot.execute` → 合同授权 → `live_target_probe` → `production_run`（`PILOT_REAL_IO`）→ `accept_pilot`。

未授权时停在 `PILOT_WRITE_REFUSED`，不调用 `production_run`。真实 Win32 后端在这一阶段仍拒绝写入。

dry-run：

```
python -m r9_bounded_pilot dry-run --sample C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_SAMPLE_FILES.json --contract C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json
```

execute（当前合同 `pilot_write_authorized=false`，写入前拒绝）：

```
python -m r9_bounded_pilot execute --sample C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_SAMPLE_FILES.json --contract C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json
```

全量 `python r9_formal_executor.py copy` 仍然拒绝。

样本 SHA256 `a0330b0115e2cd603c792807266633cdf7206a82d98d53d1afb0d7a52ce361c3`。计划 SHA256 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`。代码 digest `56c75ad07c3216d2fafa79086c024a197fd4a118e00ceccf1c7d1e19487db11a`。没有创建 `E:\R9_POSTFORMAT_PILOT_20261014`。
