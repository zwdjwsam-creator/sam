# RUNBOOK

工作目录：`C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013`

样本生成（只读计划，不写 E）：

```
python -m r9_capability_pilot build-sample --out C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\CAPABILITY_SAMPLE.json
```

当前合同 `pilot_write_authorized=false`。四个场景都先 dry-run。把 `NORMAL` 换成 `A`、`B`、`C` 即另外三套。

```
python -m r9_capability_pilot dry-run --scenario NORMAL --sample C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\CAPABILITY_SAMPLE.json --contract C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json
```

将来的真实授权才把 dry-run 换成 execute，并且每个场景只用自己的 run 和 `C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\state\<SCENARIO>.sqlite`。NORMAL 先完整跑，再原样重跑。A/B/C 先在受控故障点停下，再用同一 run 恢复。本轮不要执行这些真实写入。

不要再次执行 1232 的旧合同，也不要删除 `E:\R9_POSTFORMAT_PILOT_20261014`。

代码 digest `5299ae4491b1e33bd787c8df8cd58faae2f1cd4e32630f487aa5a2e1fa02b32a`。样本 SHA256 `96c42610d94f02a99aacee62b5ad3aa0ae14c1afdfc1a1102bfbcf0b9e23dc10`。
