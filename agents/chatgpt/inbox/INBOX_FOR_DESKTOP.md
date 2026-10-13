# ZHANGWEI 台式机｜正式计划批次、恢复与全计划验收

task_id: R9_DESKTOP_BATCH_RESUME_ACCEPTANCE_20261013_1852
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
instruction: agents/chatgpt/outbox/R9_DESKTOP_BATCH_RESUME_ACCEPTANCE_20261013_1852.md
supersedes: R9_DESKTOP_PRODUCTION_CHAIN_REWORK_20261013_1842

仍由台式机执行，SAM=HOLD。
上一轮 PARTIAL 如实；ChatGPT 独立复跑非空 fixture reader->runner->WindowsBackend 虚拟链 PASS。
下一步补正式 plan schema 的 reader（测试目前自造 source_path/dest_path 列）、真正可观察目录/硬链接/重解析及真实 observer、三种中断恢复、绑定全计划验收。
独立复现 hardlink 后 alias=MISSING；真实 Win32Syscalls 无 observe；真实 published schema reader 报 source_path 列不存在。详细指令含修复与验证要求。
同时隔离 SIMULATED_CHAIN 与真实 Win32 后端，两个 preparation 场景写入 syscall=0。
IMPLEMENTATION_READY=false
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
不格式化、不真实复制/链接试验、不在 E 写入；用户未来本人格式化 E 后才进入真实试验。
回执：agents/chatgpt/inbox/R9_DESKTOP_BATCH_RESUME_ACCEPTANCE_20261013/ZHANGWEI_REPORT.md
