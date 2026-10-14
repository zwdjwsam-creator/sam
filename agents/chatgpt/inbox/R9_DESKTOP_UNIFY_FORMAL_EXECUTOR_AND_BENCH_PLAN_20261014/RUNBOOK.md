# 三条命令

工作目录：`C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013`

启动器对同一合同字节只领取一次，不自动重试。当前两份合同都是 `copy_authorized=false`。

## 1. 干跑

```text
python C:\LAN_SHARE_REPORT\R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014\launch_formal_once.py dry-run C:\LAN_SHARE_REPORT\R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014\FALSE_AUTHORIZATION_CONTRACT.json
```

已跑。子进程 9428，退出 0，目标写入 0。合同 SHA 前缀 `ac1e943a4361` 已领取，再跑同一文件会返回 `CLAIM_EXISTS`。

## 2. 代表性试跑

```text
python C:\LAN_SHARE_REPORT\R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014\launch_formal_once.py execute C:\LAN_SHARE_REPORT\R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014\FALSE_AUTHORIZATION_CONTRACT.json
```

已跑。子进程 21628，退出 3，`REFUSED_BEFORE_WRITE`，目标写入 0。审核通过后，应由新合同把同一子集 SHA `b99af9b71abb6261e63320a37209287f68b513e2e2267ef8f694687c997ffd50` 和上限 1073739240 标成允许写入。命令仍是这个启动器和 `execute`，不能另写一套复制程序，也不能只在命令行改一个字节数。

## 3. 将来正式启动

```text
python C:\LAN_SHARE_REPORT\R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014\launch_formal_once.py execute C:\LAN_SHARE_REPORT\R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014\FORMAL_NOT_AUTHORIZED.json
```

这份合同的范围是 FULL，计划 SHA 必须是 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`，目标根是 `E:\BLACKBOX` 与 `E:\BLACKBOX_ENGINES`。当前 `copy_authorized=false` 且 `full_migration=false`，执行会在写入前拒绝。本轮没有跑这条命令。

## 重建子集

```text
python -m r9_formal_executor build-subset --plan C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite --out-dir C:\LAN_SHARE_REPORT\R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014\subset
```

生成器就是 `r9_formal_chain.build_subset`。它只写 C: 上的子集库，不创建 E: 目录。
