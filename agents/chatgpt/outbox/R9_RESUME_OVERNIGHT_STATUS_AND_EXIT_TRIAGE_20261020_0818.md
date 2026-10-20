# ZHANGWEI｜今早实际状态核查，不能继续引用昨晚21:21

task_id: R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037
followup_id: R9_RESUME_OVERNIGHT_STATUS_AND_EXIT_TRIAGE_20261020_0818
execution_host: ZHANGWEI
status: PRIORITY_CURRENT_STATUS_AND_EXIT_TRIAGE
START_AGAIN_AUTHORIZED=false

用户10月20日08:18问现在情况。HUB仍停10月19日21:21:42，近11小时没有新进度/退出/验收回执。立即先ACK本followup，再执行当前只读核查并上传真实结果；不要只ACK后停下，也不要引用旧alive当当前alive。
本命令是核查和必要的只读退出诊断，不是停止/重启令，不改代码、合同、run_bind，不删目标/temp，不新建空state。原一次启动额度已经使用。

## 1. 先确定原迁移实例存亡
原PID17904，creation_time2026-10-19T20:47:10+08:00，Python312执行批准code下r9_formal_executor.py execute --contract ...2037\FULL_RESUME_CONTRACT.json。
现在查询准确创建时间、argv、进程是否还在/是否PID复用、精确无第二实例，记录observed_at。
若仍为原实例，记录当前CPU/进程I/O/日志长度及相对21:21旧CPU1885.484375、read151867337103、write23064808043的增量。这些不是复制比例。
不得因为长时间没回执就停止或重启；CPU/I/O也不能替代成功证据。

## 2. 读取已有运行结果/状态
读取原2037 execute.stdout.log / execute.stderr.log及现有父级退出记录。stdout若有最终JSON，上传完整结构（不含业务payload/秘密）；日志很大时先尾部定位结果，不无界上传。
入口返回后才输出汇总，所以仍空不能单独推定故障。
原进程已退出就必须报告实际退出结果；没有exit_code记录写UNKNOWN，不能补造0或把alive=false当完成。full_plan_acceptance必须来自真实独立验收结果。
保持原stdout/stderr、state和旧run不变，不用重新execute获得退出码。

## 3. 当前进度证据
对现存full_1938.sqlite采用mode=ro、短timeout、短事务，禁止开启写连接或checkpoint。
必查四个主键：
entity:2387166462|844424930324628
entity:2387166462|844424930324634
entity:2387166462|844424930324640
entity:2387166462|844424930324643
回传phase/sha/目标file_id/volume/size等现有stage证据。四个仍无行，仅说明四个无行，不能概括所有剩余实体。
为了避免一再只回“阶段未知”，如state表有通常SQLite rowid，可用ORDER BY rowid DESC LIMIT 8取最后写入的少量记录（主键排序不能表示写入先后）。该表put_stage会DELETE/INSERT，因此这可辅助判断最后记录写入到dir/entity/alias/reparse哪类；不能把“最后写入种类”直接冒充当前执行阶段。表无rowid则据实说明，不改schema。
运行中不GROUP BY/COUNT全800万行、不扫全源或全目标，不长持读锁。若锁忙回NOT_OBSERVED，不干预进程。必要时可用已存在的轻量只读打开文件观察确认是在读plan/state/目标，不能安装调试器/挂接/注入。
若进程已经退出，允许在无人写入state时做一次分类计数/unique entity logical_size汇总，给与旧停点1083975/348928107919的实际增量；这是新的终止状态核查，不是每次轮询重复全库。别把alias逻辑重复字节计作实体迁移字节。

## 4. 按证据分支处理
- 仍运行：给今早时间戳、准确存活/活动证据、实际stage证据和可直接确认的阶段；无法确认阶段可以写UNKNOWN，但不能省略今早观察。继续现有实例，无需再领“继续”。
- 已停止且失败：只读定位首个实际错误/阶段/文件身份/路径API长度、最终日志/exit_code/已保留DONE；交EXIT_REPORT.md，停止等待技术处理，不自动第二次启动。
- 已停止且自称成功：交最终JSON及独立验收报告路径、full_plan_acceptance/预算/实体/alias/dir/reparse验证结果。没有验收不称完成，不临时再执行一个写任务补结果。

## 5. HUB交付（现在完成一次）
agents/chatgpt/inbox/R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037/
ACK_20261020_0818.md、CURRENT_STATUS_20261020_MORNING.json、更新CURRENT_STATUS.json（保存昨晚历史）、如有则EXIT_REPORT.md/FINAL_RESULT.json/验收报告。
更新INBOX_FOR_CHATGPT为今早真实状态和新观察时间，不保留昨晚21:21摘要当最新。
如本地观察/上传本身失败，给确切阻塞，不仅回复“等待”。
SAM暂保持只读来源共享；未经本任务外清理令不删除share、不修改源数据。
