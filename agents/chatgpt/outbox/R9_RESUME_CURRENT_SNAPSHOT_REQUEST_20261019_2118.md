# ZHANGWEI｜HUB状态已过时，现在补一次当前快照

task_id: R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037
followup_id: R9_RESUME_CURRENT_SNAPSHOT_REQUEST_20261019_2118
execution_host: ZHANGWEI
status: READONLY_SNAPSHOT_REQUESTED
START_AGAIN_AUTHORIZED=false

用户21:18查收HUB，最新CURRENT_STATUS仍为20:53:20。现在领取后立即做一次轻量只读当前快照，不把旧快照当当前状态，不重启/停止/改代码或合同、不新增复制进程。原2037授权只对原实例继续运行有效。

1. 先核PID17904的创建时间/argv：必须仍是20:47:10实例。若PID已复用，不能当原迁移进程。
2. 当前观察时间、alive、CPU累计、进程I/O读写累计、日志字节数、精确python执行器列表/无第二实例。和20:53旧值CPU368.28125、read18497482536、write3317760比较可用增量；这些是进程I/O，不得换算为迁移完成比例。
3. 仍只用短timeout只读查询四个已指定entity主键；不COUNT/SUM800万行，不全源扫描，不长时间保持数据库读事务。锁忙写NOT_OBSERVED。若有DONE，报告该行sha/目标身份及首次新增完成证据；若无行，仅说明这4个没有stage行，不推断全部其他文件情况。
4. 阶段没有直接证据仍RUNNING_PHASE_UNCONFIRMED，不根据CPU/空stdout/磁盘活动推断具体阶段。入口结束才print汇总，空stdout本身不是故障。
5. 如果原进程已退出，读取既有stdout/stderr/父级退出记录，回传实际exit_code和错误。取不到exit_code就明确UNKNOWN，不虚构；不得自动启动第二次、删temp、改state或代码。
6. 原2037目录更新CURRENT_STATUS.json，留存20:53历史（可另存快照）；更新INBOX_FOR_CHATGPT并上传。没有新DONE/退出/验收也要据实交这一份当前快照，不只ACK后继续等。
7. 继续沿用原2037的首个新增实体/退出/最终独立验收回报要求，不为本次查状态添加后台任务/服务/定时器。SAM保持原只读共享。
