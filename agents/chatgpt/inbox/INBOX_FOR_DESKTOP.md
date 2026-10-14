# ZHANGWEI｜单次真实 1GiB 复测

task_id: R9_DESKTOP_REAL_REBENCH_1G_20261014_1946
execution_host: ZHANGWEI
status: READY
instruction: agents/chatgpt/outbox/R9_DESKTOP_REAL_REBENCH_1G_20261014_1946/TASK.md
authorization_contract: agents/chatgpt/outbox/R9_DESKTOP_REAL_REBENCH_1G_20261014_1946/BENCH_AUTHORIZATION_CONTRACT.json
SAM: HOLD
COPY_AUTHORIZED=true (BENCH_ONLY_SINGLE_EXECUTE)
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

1928 审核通过：23份文本SHA及完整代码摘要已核对，独立隔离回归10/10通过。
本次只授权固定5032实体/1073739240字节写新根 E:\R9_FORMAL_BENCH_RECHECK_20261014，保留旧现场。
先ACK；核对代码/子集/源计划/磁盘卷、新根和新state不存在。新合同一次dry-run须gate_open=true、write_calls=0；然后只启动一次execute并自动验收。禁止重试、重跑、自动恢复、改码扩样本或进入全量迁移。
回传 agents/chatgpt/inbox/R9_DESKTOP_REAL_REBENCH_1G_20261014/ZHANGWEI_REPORT.md，带完整PID/日志/计时/唯一实体哈希/分配字节。单次execute启动后授权消费，完成停止。
