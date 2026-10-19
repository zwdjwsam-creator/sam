# ZHANGWEI｜17904启动回执已核，维持当前实例并补准确状态

task_id: R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037
followup_id: R9_RESUME_STARTED_REVIEW_20261019_2050
execution_host: ZHANGWEI
status: EXISTING_INSTANCE_ONLY
pid: 17904
expected_start_time: 2026-10-19T20:47:10.4043508+08:00
COPY_AUTHORIZED=true
FULL_COPY_AUTHORIZED=true
FULL_MIGRATION=true
full_plan_acceptance=false

已核e639491 STARTED.json及main PRESTART_CHECK.json。实际argv、code digest27af138391d66219ebc6d03609cec6933aecfce3aacba48c215d5de9f14b2551、1938 run/state、合同SHA ea8ad53f4ea8c6ef9ef3d9116951a38df3f7ab53705cc5cfffe18ee6301d3e23、目标2694002743及physical UniqueId均一致。旧32636/15872不在，四个近限final/temp均不存在，启动前state计数/绑定一致。
确认是已启动一次；尚无first_new_entity_copied证据，尚未完成。当前运行事实来自本机回执，并非ChatGPT直接探测Windows。

## 维持当前实例
不要停止、重启、挂调试器、改代码、改合同/参数/并发，不能因stdout/stderr为空就重启。原单次授权已经使用，没有第二次启动额度。
经代码复核，r9_formal_executor.main先等待execute_contract返回，再print最终JSON；正常执行可能长时间无stdout。这不能单独证明失败/卡住，也不能结合CPU增长就认定具体处于预检/复制哪阶段。
保留所有原state/源/目标及临时共享；本followup只允许C报告写入与轻量只读观察，不改正在运行的业务程序。

## 补一个不扰动运行的当前快照
回原2037目录CURRENT_STATUS.json（含observed_at）：
- 同一PID的CreationDate/argv与20:47:10启动一致，进程存活/退出状态，CPU累计，能直接取得的进程I/O计数及日志长度；取不到写NOT_OBSERVED，不编数。
- 精确排除检查命令自身，仅核实际python执行器、对应run/合同，回传本目标无第二复制实例。不要用命令行全文含r9字符串的任意powershell当复制进程。
- phase没有直接证据时写RUNNING_PHASE_UNCONFIRMED；没有首个新实体证据时first_new_entity_copied仍false，不能用网络活动/CPU当复制证据。
- 可用短timeout只读SQLite按固定主键查四个实体的stage，不要COUNT/SUM全800万行、不扫全目标、不长时间保持读事务。如库忙/锁则回NOT_OBSERVED，不中断迁移。
  entity:2387166462|844424930324628
  entity:2387166462|844424930324634
  entity:2387166462|844424930324640
  entity:2387166462|844424930324643
  将实际phase/现有sha/dest identity字段作为新实体已完成的证据；之前prestart四者final/temp均不存在，所以首次出现对应DONE可以区分旧进度。
- 如观察到新增DONE，首次回FIRST_NEW_ENTITY.json注明item_key、source volume/fileid、实际state DONE证据；不要为了上报而重复全内容hash。若只是旧DONE重hash或重建目录过程据实区分，不给无依据ETA。

PRESTART_CHECK.json当前ok=false，matching_processes仅为PID17060的检查powershell命令；STARTED.precheck_note解释后续另查没有python复制实例。保留原文件不篡改，在PRESTART_CHECK_CORRECTION.json记录误匹配原因、实际二次查询证据（如有原记录则引用原记录；没有历史记录不能补造，只报当前精确扫描及事实范围）。不为这项文档更正重做6GB plan核验或重启。
更新INBOX_FOR_CHATGPT为当前2037启动/运行状态，清除1950等待审核的过期摘要；附STARTED和最新快照路径。

## 后续沿用原2037交付
当前快照完成后继续现有运行，无需下一条“继续”。
有首个新增实体/正式退出/错误/独立FULL验收结果时按原任务回报。进程退出只记录真实exit_code及现有日志/状态，不自动重启、不删temp、不修数。
若无日志但进程仍活，不能自行判完成或故障；后续必要诊断限轻量只读证据。独立验收full_plan_acceptance=true前一律不称完成。
SAM保持R9LP_RO可用，本机不做源文件修改/共享清理或重启。
