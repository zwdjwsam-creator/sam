# ZHANGWEI｜修真实枚举接口，只读重验BENCH

task_id: R9_DESKTOP_FIX_ENUM_AND_REVERIFY_BENCH_READONLY_20261014_1748
execution_host: ZHANGWEI
status: READY
instruction: agents/chatgpt/outbox/R9_DESKTOP_FIX_ENUM_AND_REVERIFY_BENCH_READONLY_20261014_1748.md
SAM: HOLD

1639单次execute已审：copy5032/link7/reparse108完成，missing0/extra0，accept hash0失败；真实_find_children只返path/type，验收未逐child补metadata，已独立复现。旧单次写授权已消费，不再execute、不删现场。
本轮只修验收/元数据，测试names-only真接口形状；用原run/state/旧copy-code绑定+新verifier摘要只读重验现有1GiB目标，不改run_bind或伪造digest，不放松copy闸门。可以有限只读诊断0.766MB/s，不新复制/测速，不关闭安全软件。
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
回执：agents/chatgpt/inbox/R9_DESKTOP_FIX_ENUM_AND_REVERIFY_BENCH_READONLY_20261014/ZHANGWEI_REPORT.md
