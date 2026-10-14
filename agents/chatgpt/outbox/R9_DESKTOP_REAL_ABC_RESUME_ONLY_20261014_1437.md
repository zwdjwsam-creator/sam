# 仅补做 A/B/C 的实盘恢复试验；NORMAL保留

task_id: R9_DESKTOP_REAL_ABC_RESUME_ONLY_20261014_1437
execution_host: ZHANGWEI
SAM: HOLD
status: READY
PILOT_WRITE_AUTHORIZED: true
COPY_AUTHORIZED: false
FULL_MIGRATION: false

## 只读排查审核
1417包的报告、EXECUTION_TIMELINE.json、STATE_BINDING_READONLY.json、REAL_CAPABILITY_RESULT.json已读取。三个目标文件SHA与state SHA一致，两alias同内容，目标3身份不同，分配65536一致。CURRENT_TARGET_VERIFIED=true。
首次创建者/计数没有留存证据：FIRST_CREATION_PROVENANCE=UNKNOWN、FIRST_EXECUTION_COUNTS=UNKNOWN、FIRST_EXECUTION_PROVEN=false，保留这些结论，不继续为了找copy3而追查、清空或重跑NORMAL。
NORMAL对象/验收证据可以作为当前junction/长路径实物结果，不能改写成已记录首次create3。
A/B/C根和旧状态均不存在，可继续尚未做的恢复试验。本任务不恢复1345旧合同；旧合同保持撤销。

## 限定授权
合同 agents/chatgpt/outbox/R9_DESKTOP_REAL_ABC_RESUME_ONLY_20261014_1437/PILOT_EXECUTION_CONTRACT.json，只含A/B/C，NORMAL授权条目缺席。代码必须仍为已审1313模块digest 58e5765a8270a97e9b7cbbefa1178c6c873816419810ea51839f31baa30e3a59，样本SHA 96c42610d94f02a99aacee62b5ad3aa0ae14c1afdfc1a1102bfbcf0b9e23dc10，代码不修改、不换样本。
每场景3实体57498唯一字节、5普通文件路径（含2目标夹具alias）、2junction、24普通目录（共享公共父）；3场景共172494内容字节。只在 E:\R9_CAPABILITY_PILOT_20261014\A、\B、\C及既存公共父按计划操作，不能修改NORMAL或旧1232目录。不全量、不再格式化。
任务合同保存 C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_ABC_RESUME_ONLY_20261014\PILOT_EXECUTION_CONTRACT.json；新run与状态按合同，不能复用旧run。

## 启动记录与防重复（C上最简保护，不改生产模块）
1. 回ACK并指定仅一个本地执行者。先查本任务/旧1345是否有相关execute进程；若已有正在执行，不开第二个。保持现有未提升ZHANGWEI\Admin、SMB会话，不查密码/重登录/断IPC$。
2. 每条命令按 task+scenario+phase(FAULT/RESUME) 创建唯一C领取记录，用文件exclusive create（Python open(...,"x")或等价CreateNew），写UTC/+08开始时刻、launcher PID和精确argv。已存在即拒绝重复启动，不能删除领取记录绕过。FAULT/RESUME分别6记录，允许指定故障后的另一phase恢复，不把它误当重复故障。
3. 用同一个C上启动流程仅创建一个子进程，记录子PID与开始/结束时间，stdout/stderr全文写各自唯一日志（exclusive create，不覆盖、不只取最后工具输出块）。并记录exit和日志SHA；如果工具调用中断/超时，先查实际PID和已有日志，不能自动再次启动。可写最小C启动器，但不能改已审核生产模块/摘要或开放任意新目标。
4. 初始每场景根和新state必须不存在。场景A/B/C按顺序逐个完成；公共父/NORMAL已经存在是预期，不删。源身份/卷/大小、本次句柄mtime及目标新卷/物理ID仍由真实执行器检查；不注入假OS/backend。
5. 恢复前只读确认刚才退出原因是对应INTERRUPT_X且阶段证据匹配，并引用同一子PID日志，不仅凭exit3继续。缺预期输出/状态、输出如首次全0、发现未知对象或正在运行进程则停止，不补造计数。

## 命令（在 C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013）
共同参数：
--sample C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\CAPABILITY_SAMPLE.json
--contract C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_ABC_RESUME_ONLY_20261014\PILOT_EXECUTION_CONTRACT.json

先对A/B/C各dry-run一次，authorized=true、写入0。然后以下每行后加共同参数：
python -m r9_capability_pilot execute --scenario A --fault A
只允许INTERRUPT_A退出3；第一已提交实体INTENT含fileid/卷/SHA/size，导出只读stage证据。
python -m r9_capability_pilot execute --scenario A
同run恢复resumed_entities=1、copy2/link2/reparse2、acceptance=true。已提交第一实体不能重抄，其余2实体按计划补齐。

python -m r9_capability_pilot execute --scenario B --fault B
只允许INTERRUPT_B退出3；3entity DONE、第一alias DONE、第二缺，导出stage证据。
python -m r9_capability_pilot execute --scenario B
copy0/link1/reparse2，acceptance=true。

python -m r9_capability_pilot execute --scenario C --fault C
只允许INTERRUPT_C退出3；3entity DONE、第一alias已创建INTENT、第二缺，导出stage证据。
python -m r9_capability_pilot execute --scenario C
copy0/resumed_links1/link1/reparse2，acceptance=true。

共6条execute，不正常加跑、不循环重试、不重新跑NORMAL，不回收状态/目录。非预期错误/验收false/日志丢失即STOP保留现场，等待HUB审核。

## 回执与停止
agents/chatgpt/inbox/R9_DESKTOP_REAL_ABC_RESUME_ONLY_20261014/
ZHANGWEI_REPORT.md、REAL_ABC_RESULT.json、6条命令领取/PID/全文stdout/stderr/exit时间线及SHA、每个故障后与恢复后的持久状态摘要、本任务合同hash。可上传C启动器供复核，不上传payload/密码。
每场景3唯一实体身份/SHA/size/AllocationSize、2alias同实体、2junctiontag/映射目标与follow打开验证、长路径长度364、无partial。记录实际结果，目录API调用未采集不得报0。
NORMAL仅引用1417已有证据，FIRST_EXECUTION_PROVEN仍false，不将本轮ABC结果补写成NORMAL首次证据。
完成HOLD_PENDING_REAL_IO_REVIEW；真实A/B/C通过仅证明这些受控故障点，不等于所有断电/中途temp恢复通过。
PILOT_WRITE_AUTHORIZED=true (THIS_TASK_ABC_ONLY)
COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
执行电脑=ZHANGWEI；SAM=HOLD。更新INBOX_FOR_CHATGPT.md。
