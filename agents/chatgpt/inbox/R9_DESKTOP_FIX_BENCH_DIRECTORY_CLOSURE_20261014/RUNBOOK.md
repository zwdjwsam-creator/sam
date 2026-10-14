# 命令

工作目录：`C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013`

当前合同 `copy_authorized=false`。启动器对同一合同字节只领取一次。

## 干跑

```text
python C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014\launch_formal_once.py dry-run C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014\FALSE_AUTHORIZATION_CONTRACT.json
```

已跑。子进程 14044，退出 0，写入 0。合同前缀 `96fb1474191c`。

## 代表性试跑

```text
python C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014\launch_formal_once.py execute C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014\FALSE_AUTHORIZATION_CONTRACT.json
```

已跑。子进程 4344，退出 3，`REFUSED_BEFORE_WRITE`。审核通过后，新合同必须绑定子集 SHA `20843e97b90557b947823c9ecbe01679876c3d56be18fe31e1d36952c1381b6a` 和上限 1073739240。仍用这个启动器和 `execute`。

## 将来正式启动

正式合同还没有发布。范围必须是 FULL，计划 SHA `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`，目标根 `E:\BLACKBOX` 与 `E:\BLACKBOX_ENGINES`，并且 `copy_authorized` 与 `full_migration` 都为 true。本轮没有正式启动。

## 重建子集

```text
python -m r9_formal_executor build-subset --plan C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite --out-dir C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014\subset
```
