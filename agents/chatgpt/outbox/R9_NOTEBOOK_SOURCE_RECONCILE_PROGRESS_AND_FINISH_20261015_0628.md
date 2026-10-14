# SAM｜刷新进度，完成现有来源核对

followup_id: R9_NOTEBOOK_SOURCE_RECONCILE_PROGRESS_AND_FINISH_20261015_0628
task_id: R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014_2312
execution_host: SAM
ZHANGWEI: HOLD
这是2312原任务的补充，不新开一轮扫描、不重建基线、不改变复制授权。
原指令: agents/chatgpt/outbox/R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014_2312.md

## 本次查收

06:28查看HUB，最后报告仍是02:35：基线已核SHA/size/quick_check通过，paths_enumerated=1965812、dirs_done=35063、queue_pending=60709、dirs_error=0，ADDED=51、SIZE_MISMATCH=141。这是过程中间值，不是最终缺失/变化清单。
收件箱记录reconcile_pid=20796，summary pid=22336，ACK pid=34236。可能是不同启动/父子进程，仅凭不同不能认定故障。FILE_SHA256还是较早报告的大小/哈希，不能据它核验当前报告。

## 立即处理同一个现有任务

1. 只读检查实际进程及命令行、父子关系、最新日志时间、数据库/队列持久化状态，确定真实scanner PID。先向HUB更新一次当前状态、观察时间及与02:35相比的进度，不要等扫描结束才回报。不要只回“RUNNING”而没有最新计数/日志时间。
2. 若仍运行并有进展：让原进程继续，不杀、不重启、不复制启动。报告当前路径/目录数、队列、速度观察区间、C剩余空间、日志位置和已用时。仅有真实进度才估剩余时间；路径比例不等于耗时比例。后续约每30分钟或阶段结束时更新小型进度，不能让上传阻塞主扫描。
3. 若已结束：直接完成原任务的全范围比对、删除/变化/新增统计及原指令要求的总结，不重复扫描。若仅扫描结束但比对仍在跑，明确阶段及PID。
4. 若进程已退出/无进展/空间不足：报告证据与退出原因，保留现场。仅在现有程序已支持可靠恢复、队列和目录提交语义可核实且不存在另一个活跃实例时，从同一checkpoint恢复；不要清空数据库、重新全扫或无限重试。否则报告具体阻塞等待审核。
5. 错误为0必须说明覆盖范围；只有队列空且所选全部根覆盖、无未处理错误才可报SOURCE_ENUMERATION_COMPLETE=true。真实delta照实保留，不强行让旧计划匹配。141条大小差异先给少量类型/路径样本，确认是普通文件实际变化还是目录/reparse字段口径，不能直接一概叫内容损坏。
6. 回传现有source_reconcile_r1.py、reparse_nofollow_r1.py及必要本轮适配小脚本（或仓库可直接读取的准确commit/path），不能只有Windows本地路径。上传是为审核现有实现，不要求另开发新框架/新测试链。
7. 完成后再生成与实际上传版本一致的FILE_SHA256.json，数据库大文件留本机C。过程报告不因旧hash清单不匹配就停扫描。

回传继续用原目录：
agents/chatgpt/inbox/R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014/
更新SAM_REPORT.md、SOURCE_RECONCILE_SUMMARY.json和INBOX_FOR_CHATGPT.md，并在NOTEBOOK邮箱准确标记RUNNING/COMPLETE/BLOCKED，勿让领取状态长期仍为READY。本补充不覆盖原范围、no-follow、身份归一及历史内容未证实等约束。

只允许SAM C元数据读写和来源E/D本机只读核对。不要新增测速/复制试验，不改变来源/共享/会话，不要求密码，不写桌面E。
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false

台式机ZHANGWEI仍无执行任务，保留交接共享待命。SAM完成这次来源核对后停止，交HUB做最终计划更新与放行审核。
