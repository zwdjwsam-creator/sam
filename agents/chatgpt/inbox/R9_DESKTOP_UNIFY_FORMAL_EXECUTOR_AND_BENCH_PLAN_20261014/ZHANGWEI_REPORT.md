# ZHANGWEI 报告

task_id: R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014_1518
execution_host: ZHANGWEI
SAM: HOLD
status: HOLD_PENDING_CODE_REVIEW

COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
bench_measured=false
full_plan_acceptance=false

## 结论

统一入口已经接在 `r9_formal_executor.py` 的 `dry-run` / `execute`。实际复制、恢复和验收走现有 `production_run`、`WindowsBackend` 和 `full_acceptance`。本轮合同 `copy_authorized=false`，台式机执行在首次目标写入前拒绝。没有创建 `E:\R9_FORMAL_PILOT_1G_20261014`，也没有创建 `E:\BLACKBOX`。

隔离测试里，同一条 `execute` 命令在授权的内存后端上进入了 runner 和验收：1 个实体、1 个别名，首次 `content_hash_calls=1`，重跑 `copied_count=0` 且验收仍通过。这不是 E 盘试跑，也不能当成全计划通过。

## 本机命令结果

合同 SHA256 前缀 `ac1e943a4361`。

- dry-run：子进程 9428，退出 0。`write_calls=0`，`would_write=false`，`gate_open=false`，计划审计通过，5032 个实体，唯一内容 1073739240 字节。
- execute：子进程 21628，退出 3。原因 `REFUSED_BEFORE_WRITE`，`write_calls=0`。
- 日志：`logs\R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014_1518_dry-run_ac1e943a4361.log` 与同名 execute 日志。
- 启动器对同一合同文件只领取一次，不自动重试。

到 `192.168.100.2` 的本机路由在 ifIndex 11，状态 Up，协商速率 **2.5 Gbps**。下一跳为空，表示直连。2.5 Gbps 不是 2.5 GB/s。按位换算的理论上限约 312.5 MB/s，只说明链路规格，不是迁移耗时。本轮没有做代表性复制，所以没有速度和 ETA。

## 代码

运行代码仍在 `C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013`。`code_digest=9b5ae88dd66b550d3e73eaabb2366c8682a2ffadd33e6b207e974d03fc950a22`。

`execute` 会检查主机、冻结源计划 SHA、目标卷 `3630886530` / `D86AEE82`、磁盘 `eui.E8238FA6BF530001001B448B42E694AE`、NTFS、合同字节上限与子集 SHA、状态库必须在 C:。FULL 范围还必须是冻结计划 SHA `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`，不能用子集冒充全计划。

旧的 `copy` 子命令仍然无条件拒绝，包括传入两个 true 标志。它不是正式入口。`SIMULATED_CHAIN` 不能配到 Win32 后端。

元数据观察默认不计算内容 SHA。唯一实体在复制流、临时目标和最终验收时各做显式哈希；别名只核对同卷 file id、大小和文件类型。计划里没有 mtime 时，正式阶段用本次源句柄读到的时间，记为 `OBSERVED_THIS_RUN`，不编造历史值。源变化、短读、未知目标和验收失败按所在阶段停止，不写成“全部在写入前拒绝”。

## 子集

`subset\BENCH_SUBSET.sqlite`
SHA256 `b99af9b71abb6261e63320a37209287f68b513e2e2267ef8f694687c997ffd50`
唯一内容 1073739240 字节，上限 1073741824，按预算停止。
5032 个实体，5039 条文件路径，1023 个目录，3715 条链接。
路径逻辑字节 1073740486。按唯一身份去重的分配字节 1073736777。
E 卷实体 5031，D 卷实体 1。没有丢弃实体。

类别：普通文件 1、小文件 200、多别名 1（path_count=8）、中文长路径 1（243 字符）、D 来源 1、1–8MiB 中等文件 1、按 file_id 填充 4819、为闭合链接补入 8。

链接：3715 条目标不超过 16 个文件路径且缺口字节放得进预算，已纳入。382 条目标更大，排除。728 条缺口超出剩余预算，排除。没有为了闭合去复制整份 release。纳入的 junction tag 为 2684354563，目标是本机 `E:\R9_FORMAL_PILOT_1G_20261014` 下的目录，不是 UNC，也不是 D: 盘符。

拟定目标，尚未创建：

- `E:\R9_FORMAL_PILOT_1G_20261014\BLACKBOX`
- `E:\R9_FORMAL_PILOT_1G_20261014\BLACKBOX_ENGINES`

## 测试

`test_r9_formal_chain` 3 项通过：授权子集走完整链并重跑、未授权/错盘/坏摘要/超预算/越界不写、空计划和部分验收失败、SIMULATED 不能走 Win32、FULL 不能用非冻结计划 SHA。

`test_r9_formal_executor`、`test_r9_close`、`test_r9_strict`、`test_r9_scheduler`、`test_r9_copy_body`、`test_r9_bounded_pilot` 通过。

`test_r9_capability_pilot` 有一项失败：它断言 `E:\R9_CAPABILITY_PILOT_20261014\NORMAL` 不存在。该目录是先前 1345 实跑留下的，本轮按要求保留，没有删除，也没有重跑。

## 仍未放行

正式范围、源在冻结计划之后是否变化、以及现场写入条件都还没核完。见 `SCOPE_GAPS.md`。下一轮只应发一次代表性试跑；通过后再准备正式迁移。
