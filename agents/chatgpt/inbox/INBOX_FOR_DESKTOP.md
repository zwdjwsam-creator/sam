# ZHANGWEI台式机｜冻结绑定补漏及1326只读诊断

task_id: R9_DESKTOP_FREEZE_BINDING_AND_SMB_DIAG_20261013_2035
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
instruction: agents/chatgpt/outbox/R9_DESKTOP_FREEZE_BINDING_AND_SMB_DIAG_20261013_2035.md
supersedes: R9_DESKTOP_BIND_SOURCE_FACTS_AND_FINAL_PREP_20261013_2016
SAM: HOLD

有后续任务，仍台式机执行。
40项单测独立复跑通过；27个已上传清单文件SHA/大小匹配，4个清单条目缺上传待补。
新增精确反例：WAL中已提交mtime变更被只hash main文件漏掉，旧摘要及full_acceptance仍通过；修改common底层模块也不改变当前code_digest。
本轮强制真实冻结条件及全部运行模块绑定；修D_DRIVE不应依赖D$；使测试fixture可移植并补齐包。
1326只读诊断当前Windows身份、已有相关SMB会话/凭据目标元数据及既有日志；不重试登录、不读明文、不改账号/凭据/共享/网络。
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
仍准备期，不格式化、不复制、不实盘写链接、不在E写入。
回执：agents/chatgpt/inbox/R9_DESKTOP_FREEZE_BINDING_AND_SMB_DIAG_20261013/ZHANGWEI_REPORT.md
