# ZHANGWEI｜单次真实源预取1GiB试跑

task_id: R9_DESKTOP_REAL_PREFETCH_BENCH_1G_20261014_2102
execution_host: ZHANGWEI
status: READY
instruction: agents/chatgpt/outbox/R9_DESKTOP_REAL_PREFETCH_BENCH_1G_20261014_2102/TASK.md
authorization_contract: agents/chatgpt/outbox/R9_DESKTOP_REAL_PREFETCH_BENCH_1G_20261014_2102/BENCH_AUTHORIZATION_CONTRACT.json
SAM: HOLD
COPY_AUTHORIZED=true (BENCH_ONLY_SINGLE_EXECUTE)
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

2049已审：22份SHA/15模块digest一致，独立隔离20/20通过；混合恢复顺序和等待墙钟已修复。
授权固定5032实体/1073739240字节写新根E:\R9_FORMAL_PREFETCH_BENCH_20261014，source_prefetch_workers=4，源句柄总峰值<=4，顺序复制/提交/校验不变。
先ACK，核对代码/计划/目标绑定及root/state不存在。新合同一次dry-run通过后只启动一次execute，完整保存PID/claim/输出；失败不重试/恢复，完成停止。所有旧授权不复用、旧现场保留。
真实速度按entity阶段/完整执行墙钟算；不得用排除了预取的copy_seconds高估速度。
回传 agents/chatgpt/inbox/R9_DESKTOP_REAL_PREFETCH_BENCH_1G_20261014/ZHANGWEI_REPORT.md。单次execute首次启动即消费BENCH许可，全量未授权。
