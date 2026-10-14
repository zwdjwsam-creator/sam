# RUNBOOK

工作目录：`C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013`

当前合同 `pilot_write_authorized=false`。下面的 execute 在这个合同下会在写入前拒绝。真实四场景授权之后，才把 dry-run 换成 execute。

dry-run：

```
python -m r9_capability_pilot dry-run --scenario NORMAL --sample C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\CAPABILITY_SAMPLE.json --contract C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json
```

把 `NORMAL` 换成 `A`、`B` 或 `C` 即另外三套。目录按父到子创建。公共根和场景根都在清单里。

受控故障只允许同名场景，本轮不在这台机器上真的中断进程：

```
python -m r9_capability_pilot execute --scenario A --fault A --sample C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\CAPABILITY_SAMPLE.json --contract C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json
```

`B`、`C` 同样把场景和 `--fault` 写成同一个字母。`NORMAL --fault A` 会被拒绝。

恢复使用同一合同、同一 run、同一状态，去掉 `--fault`：

```
python -m r9_capability_pilot execute --scenario A --sample C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\CAPABILITY_SAMPLE.json --contract C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json
```

状态文件分别是 `C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\state\A.sqlite`，以及 `B`、`C`、`NORMAL`。execute 成功时打印 `acceptance=true`；失败打印 reasons 并返回非 0。

不要再次执行 1232，也不要删除 `E:\R9_POSTFORMAT_PILOT_20261014`。

代码 digest `58e5765a8270a97e9b7cbbefa1178c6c873816419810ea51839f31baa30e3a59`。样本 SHA256 `96c42610d94f02a99aacee62b5ad3aa0ae14c1afdfc1a1102bfbcf0b9e23dc10`。
