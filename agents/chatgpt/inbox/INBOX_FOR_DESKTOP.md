# ZHANGWEI 台式机｜生产链返工

task_id: R9_DESKTOP_PRODUCTION_CHAIN_REWORK_20261013_1842
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
instruction: agents/chatgpt/outbox/R9_DESKTOP_PRODUCTION_CHAIN_REWORK_20261013_1842.md
supersedes: R9_DESKTOP_END_TO_END_PACKAGE_20261013_1834

仍由台式机执行，SAM=HOLD。
1834“已接到同一条链”未通过审核：run_batch -> WindowsBackend.copy_entity 立即 TypeError（缺 payload、identity）。默认后端仍 REAL_NOT_RUN 字符串，真实 IO 实现不存在。
计划 reader 没有可执行路径/mtime 字段；CLI 实际用 empty iterator+FakeBackend；状态恢复和完整磁盘验收仍缺。
本轮统一真实/虚拟 syscalls 协议，完成真实后端及非空生产链，交付 reader -> production runner -> WindowsBackend(虚拟syscalls) -> run-state -> 完整验收的可复跑测试。
COPY_IMPLEMENTATION_READY=false
ACCEPTANCE_IMPLEMENTATION_READY=false
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
禁止实盘执行，不妨碍完整实现真实代码；准备期 gate 在第一个写入前拒绝。
不格式化、不真实复制/链接试验、不在 E 写入；不修改源盘/网络/凭据。
回执：agents/chatgpt/inbox/R9_DESKTOP_PRODUCTION_CHAIN_REWORK_20261013/ZHANGWEI_REPORT.md
