# ZHANGWEI 报告

task_id: R9_DESKTOP_FIX_PREFETCH_LOOKAHEAD_ORDER_20261014_2049
execution_host: ZHANGWEI
SAM: HOLD
status: HOLD_PENDING_LOOKAHEAD_REVIEW

LOOKAHEAD_READONLY=true
ORDER_PRESERVED=true
TIMING_SCOPE_CORRECT=true
REAL_CONCURRENT_COPY_SPEED=NOT_RUN
full_plan_acceptance=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 修复

有界窗口现在只做只读分类。分类只看状态和目标是否存在，不调用 `_finish_entity`、不提交、不做硬链接。窗口按原顺序保留 DONE、可恢复 INTENT 和新实体，上限 4。轮到该实体时才按原来的串行逻辑校验、恢复和补 alias。DONE 和可恢复 INTENT 不预开源。

`entity_phase_wall_seconds` 从实体消费前计到预取清理完。`copy_seconds` 在 workers=4 时只含句柄就绪后的复制调用，不含预取打开、第一次身份和 take 等待。worker 秒数总和不是墙钟。三者不相加。不能把新的 copy_seconds 和旧的 954.274084 当成同一口径。下次真实吞吐要用实体阶段墙钟或完整执行墙钟，并和旧的 974.838884 进程内总时长或 979.066619 启动器墙钟比。

新 code_digest `a1ce1ae5e2d0490d6b6c415917200f7c84bb502d9befb397a38fe974e43e5bfd`。
子集仍是 `514a3466554bbac540701e345a37e484284a446ae972e8b456a1d107f6fd59a2`，没有重选样本。
`E:\R9_FORMAL_PREFETCH_BENCH_20261014` 仍不存在。

## 测试

隔离测试 10 项，连同正式链和阶段计时共 17 项通过。日志 TESTS.log。
混合序列的后端事件是先 commit 新实体 0，再 hardlink DONE 实体 1 的 alias。
前面的源身份失败后，后面的 DONE alias 没有创建，后面的 INTENT 仍是 INTENT。句柄打开数和关闭数相等。
B/C 中断也会收回未消费句柄。实体阶段墙钟覆盖了首次打开等待，并且大于 copy_seconds。
未授权真实后端 source_open_calls=NOT_RUN，Win32 write_calls=0。

## 未授权合同

`PREFETCH_CONTRACT.json`，workers=4，copy_authorized=false。run_id `R9_DESKTOP_FIX_PREFETCH_LOOKAHEAD_ORDER_20261014_2049_BENCH`。
dry-run 子进程 35952，退出 0。plan_audit.ok=true，write_calls=0，gate_open=false。
execute 子进程 14100，退出 3。REFUSED_BEFORE_WRITE，write_calls=0，source_open_calls=NOT_RUN。
这两次 claim 已占用。审批前的单次命令是：

`python C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014\launch_formal_once.py execute <新的授权合同路径>`

本轮没有授权复制。源选定范围和冻结计划的当前一致性还没有闭合。等待审核。
