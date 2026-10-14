# 台式机 ZHANGWEI｜复用会话及处理 1219

task_id: R9_DESKTOP_REUSE_SESSION_RESOLVE_1219_20261014_1041
execution_host: ZHANGWEI
status: READY
instruction: agents/chatgpt/outbox/R9_DESKTOP_REUSE_SESSION_RESOLVE_1219_20261014_1041.md
SAM: HOLD

旧原生登录任务与 2222 自动复用任务统一由本任务替代。先不指定新账号，直接复用现有会话读取 E/D 来源元数据。仅在有可用凭据且确认只有闲置 IPC$ 时允许一次非强制定点解除该连接；禁止全局断连、删除凭据或要求用户输入密码。完整条件见指令。
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
回执：agents/chatgpt/inbox/R9_DESKTOP_REUSE_SESSION_RESOLVE_1219_20261014/ZHANGWEI_REPORT.md
