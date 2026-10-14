# ZHANGWEI｜只修代表子集目录闭合

task_id: R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014_1616
execution_host: ZHANGWEI
status: READY
instruction: agents/chatgpt/outbox/R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014_1616.md
SAM: HOLD

统一入口3项测试独立通过，运行模块hash/code摘要一致，接通链保留。审核复现build_subset：空目录junction被纳入，但target目录本身不在paths（只加其parent），可能悬空；缺完整父链审计。仅修这一实际缺口，先只读统计现有3715链接target/祖先缺口，不假定全部有错。
C上补target与父链、生成器/写前审计/验收目标存在检查，重建同一<=1GiB子集及更新SHA/false合同。不新建框架、不加场景、不新写E。
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
回执：agents/chatgpt/inbox/R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014/ZHANGWEI_REPORT.md
