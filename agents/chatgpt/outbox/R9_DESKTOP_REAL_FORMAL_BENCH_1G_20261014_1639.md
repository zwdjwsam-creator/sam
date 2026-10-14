# 统一正式入口的一次代表性实盘测速

task_id: R9_DESKTOP_REAL_FORMAL_BENCH_1G_20261014_1639
execution_host: ZHANGWEI
SAM: HOLD
status: READY
COPY_AUTHORIZED: true (BENCH_SCOPE_ONLY)
PILOT_WRITE_AUTHORIZED: true (THIS_TASK_ONLY)
FULL_MIGRATION: false
IMPLEMENTATION_READY: false

## 审核与授权
1616修复包24份文本/代码/清单SHA独立核对一致，代码digest 0ce471dd661789558754d92f0c1af0aca249a50146bbfa152dc470d621095cd6一致。4项统一入口/目录闭合测试独立通过（Linux禁止真API，仅C状态路径条件便携适配）。
真实二进制subset没有由ChatGPT直接读取，SHA/计数为本机manifest/闭合审计；执行前仍需实际文件SHA和写前审计通过。
新子集：5032实体、5039文件路径、754目录、108链接；missing_target/missing_ancestor/link_as_dir均0。本次只测BENCH，不放行FULL，不能拿本次局部验收说全计划通过。

新授权合同：agents/chatgpt/outbox/R9_DESKTOP_REAL_FORMAL_BENCH_1G_20261014_1639/BENCH_AUTHORIZATION_CONTRACT.json
代码工作目录 C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013。
只用已审实际r9_formal_executor dry-run/execute ->生产链，不改代码、重建样本或另写复制程序。

## 输入与唯一目标
子集 C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014\subset\BENCH_SUBSET.sqlite
SHA 20843e97b90557b947823c9ecbe01679876c3d56be18fe31e1d36952c1381b6a
唯一内容1073739240字节，硬上限1073741824（1GiB），不可扩容。
源冻结plan SHA 94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba。
写入只允许 E:\R9_FORMAL_PILOT_1G_20261014\BLACKBOX、\BLACKBOX_ENGINES与该公共父，所有文件/目录/link按冻结子集；实体提交所用临时文件仅在各代表路径旁按同目录 .partial 规范处理。不得写正式 E:\BLACKBOX/BLACKBOX_ENGINES或旧试验根。
源UNC不变，目标卷D86AEE82/3630886530，NTFS，物理UniqueId eui.E8238FA6BF530001001B448B42E694AE。
新状态 C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_FORMAL_BENCH_1G_20261014\state\bench.sqlite，run由新合同绑定。

## 一次执行
1. 确认本任务/旧任务没有正在执行的同类复制子进程；仅一个AI/启动者领取本任务。保留所有旧试验目录，不运行旧合同。保持现有未提升ZHANGWEI\Admin与SMB会话，不找密码/登录/断IPC$。
2. 初始 E:\R9_FORMAL_PILOT_1G_20261014 和新state应不存在；若存在未知对象/状态，STOP，不清理/覆盖。实际code摘要、source plan和新subset SHA、无非空WAL、目录闭合审计及现场目标绑定必须都匹配。
3. 将新合同原样保存 C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_FORMAL_BENCH_1G_20261014\BENCH_AUTHORIZATION_CONTRACT.json，不修改true/预算/root/run。
4. 沿用已审 launch_formal_once.py，独占领取/子PID/全文不覆盖日志，不自动重试。启动器自身TASK/日志前缀仍是1616旧label，按本新合同SHA、实际child argv和新run_id归属本任务，不为改label修改运行程序。
   先运行一次：
   python C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014\launch_formal_once.py dry-run C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_FORMAL_BENCH_1G_20261014\BENCH_AUTHORIZATION_CONTRACT.json
   需要实际gate_open=true、plan_audit.ok=true、scope=BENCH、write_calls=0；exit0本身不是充分通过条件。
5. 干跑通过后只运行一次：
   python C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014\launch_formal_once.py execute C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_FORMAL_BENCH_1G_20261014\BENCH_AUTHORIZATION_CONTRACT.json
   要求真实WindowsBackend/Win32，不能isolated_chain或注入虚拟backend/probe。
6. 捕获真实子PID与起止UTC/+08、完整stdout/stderr、退出码和日志SHA。若工具调用超时/断开，先查原子PID与领取日志，不再启动。允许原子进程继续其已授权任务，进度通过只读日志/状态观察。
7. 成功exit0且reason=ACCEPTED_SUBSET、acceptance.full_acceptance=true，实体/alias/dir/link计数与子集一致；预计copied_count5032、linked_count7、reparse_count108。state及目标身份/大小/内容哈希/AllocationSize去重符合验收，no-follow精确覆盖，无partial。
   FULL计划验收应仍false。如果首轮计数全0、验收false、源变/短读、目标未知或任何非预期错误，STOP保留现场；不恢复重跑、不删目录/换run/改码，本任务无第二execute授权。
8. 完成后只读查询两目标根没有越界写入，旧目录仍保持；不要“搬到正式目录”或直接继续FULL。

## 速度报告
输出 BENCH_RESULT.json 与说明，记录:
- 总墙钟（启动者计时含绑定/预检）以及runner执行总时间；
- 目录seconds、实体复制seconds/唯一bytes、aliases/link次数及seconds；
- 独立验收seconds、实际hash读bytes/次数、峰值工作集（取不到标UNKNOWN）；
- 实测2.5Gbps链路与route，MB/s按10^6、MiB/s按2^20分开；
- 5032实体平均大小、真正唯一AllocationSize与逻辑路径bytes。
程序可能始终把bench_measured字段写false；以真实已完成/日志/计时证据派生本轮bench_measured=true，并注明源字段不变，不能假称已改程序。
启动时6GB来源plan SHA等固定预检成本不按每1GiB复制重复外推。全量365007198749内容bytes、1223721实体、8715067文件路径、233660目录、4825links仅现有冻结plan口径。分实体复制/大量alias/验收估算，样本仅7个alias无法支撑精确全量alias费时；明确估计的条件、未确认源范围与误差，不编精确小时数。

## 交付与停止
agents/chatgpt/inbox/R9_DESKTOP_REAL_FORMAL_BENCH_1G_20261014/
ZHANGWEI_REPORT.md、BENCH_RESULT.json、真实PID/完整dry-run/execute日志与SHA、合同SHA、目标统计与状态摘要、PERFORMANCE_NOTE.md。
完成HOLD_PENDING_BENCH_REVIEW，供审核后准备正式范围/源一致性核对与正式开工；不新增微型试验或全量授权。
COPY_AUTHORIZED=true (ONLY_THIS_BENCH)
PILOT_WRITE_AUTHORIZED=true (SINGLE_EXECUTE)
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
执行电脑=ZHANGWEI；SAM=HOLD。更新INBOX_FOR_CHATGPT.md。
