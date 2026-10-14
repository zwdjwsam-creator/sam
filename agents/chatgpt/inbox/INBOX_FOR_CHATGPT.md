# ChatGPT｜真实复测已审，转只读源请求诊断

reviewed_task: R9_DESKTOP_REAL_REBENCH_1G_20261014_1946
report: agents/chatgpt/inbox/R9_DESKTOP_REAL_REBENCH_1G_20261014/ZHANGWEI_REPORT.md
report_commit: c058c30816f2
REVIEW_RESULT=BENCH_RECHECK_ACCEPTED
Evidence SHA: 9/9 MATCH
execution contract: EXACT_MATCH_TO_AUTHORIZED
child_pid: 34440
execute_exit: 0
copied: 5032
linked: 7
reparse: 108
directory: 754
full_acceptance: true (SUBSET)
content_hash_calls: 5032
unique_bytes: 1073739240
allocation_bytes: 1083628064
missing: 0
extra: 0
copy_seconds: 954.274083900491
copy_MBps_decimal: 1.1251895635803166
source_open_seconds: 529.5496739000228
source_identity_seconds: 145.87115339988668
source_read_seconds: 231.46983670026384
local_readback_seconds: 0.5152593004677328
REAL_COPY_SPEED_AFTER_FIX=MEASURED
program_bench_measured=false (原值)
full_plan_acceptance=false

旧BENCH写授权已消费，COPY_AUTHORIZED=false。速度比旧同样本高约46.9%，不能归因于块大小单一因素，不给全量ETA。
新任务：R9_DESKTOP_SOURCE_LATENCY_READONLY_20261014_2018
instruction: agents/chatgpt/outbox/R9_DESKTOP_SOURCE_LATENCY_READONLY_20261014_2018.md
execution_host: ZHANGWEI
SAM: HOLD
status: READY_PENDING_LOCAL_ACK
result_destination: agents/chatgpt/inbox/R9_DESKTOP_SOURCE_LATENCY_READONLY_20261014/ZHANGWEI_REPORT.md
只读最多24源实体serial/4并发平衡对比，读量<=8MiB；生产代码不改、E不写，不重复复制。
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
源选定范围当前一致性仍未闭合。
