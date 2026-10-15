# 正式迁移启动令｜ZHANGWEI立即执行，不再等待用户确认

authorization_id: R9_FULL_COPY_START_AUTH_20261015_1155
task_id: R9_POSTFORMAT_BIND_AND_START_ZHANGWEI_20261015_1117
execution_host: ZHANGWEI
SAM: HOLD_SOURCE_UNCHANGED
status: READY_EXECUTE_NOW
COPY_AUTHORIZED=true
FULL_COPY_AUTHORIZED=true
FULL_MIGRATION_AUTHORIZED=true
FORMAT_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
full_plan_acceptance=false

## 授权及技术审核已完成
用户11:15要求格式化后开启正式迁移，11:17:07明确“格式化完毕，E盘清空，可以直接安排任务”。无需再询问用户。
已读取POSTFORMAT_VOLUME/CHECKS/HASHES/实际chain/新合同。
独立字节比对证明相对已审核版本唯一变化为EXPECTED_VOLUME 3630886530→2694002743。
实际chain SHA256=8d5e158190ab06773391d9f7ea056841634ee4355c55d5588a0e4538d7b7a30e。
15模块原始字节独立重算digest=096da3327fc4da0f17799fca347f68117df2a886f0a92376a2feaa8cdfc72626。
直接加载该实际新源码在隔离环境测试：新卷正确盘放行、copy=false拒绝、旧卷拒绝、错误物理盘拒绝，4/4通过。仅Linux Path.drive系统差异作边界适配，禁止原生I/O，不宣称真实E写入复测。其余逻辑与此前23项通过版本相同。
现场新卷NTFS A0933837 / 2694002743，物理盘仍eui.E8238FA6BF530001001B448B42E694AE，容量4000769372160、可用4000538427392字节，E两个目标根不存在。来源E/D同上下文已恢复。现场状态仍须由正式入口在首次写入前验证。

## 精确执行合同
下载本次已授权合同，原样存本机：
repo: agents/chatgpt/outbox/R9_FULL_COPY_START_AUTH_20261015_1155/FULL_EXECUTION_CONTRACT_AUTHORIZED.json
local: C:\LAN_SHARE_REPORT\R9_POSTFORMAT_BIND_AND_START_ZHANGWEI_20261015\FULL_EXECUTION_CONTRACT_AUTHORIZED.json
不再沿用copy=false的POSTFORMAT/PENDING合同。
run_id=R9_POSTFORMAT_BIND_AND_START_ZHANGWEI_20261015_1117
state=C:\LAN_SHARE_REPORT\R9_POSTFORMAT_BIND_AND_START_ZHANGWEI_20261015\state\full_1117.sqlite
plan SHA=53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d
code digest=096da3327fc4da0f17799fca347f68117df2a886f0a92376a2feaa8cdfc72626
target volume=2694002743
target physical disk=eui.E8238FA6BF530001001B448B42E694AE
dest roots=E:\BLACKBOX、E:\BLACKBOX_ENGINES
source=.2 E_DRIVE\BLACKBOX与冻结计划D_DRIVE条目，来源卷2387166462/3187598165
max_unique_bytes=365004696055
workers=1

## 立即执行
1. 先上传EXECUTION_ACK.md，指明本authorization_id及领取时间。确认没有同run实际执行进程，防止重复启动；已有则接续报告，不另起。只检查本任务进程/锁，不批量结束Python。
2. 保持已审核代码及独立1117 state，不复用旧0800/试验DONE；下载准确授权合同，不改新卷/清单/digest/预算。正式入口完成自身必需plan/code/卷/物理盘/结构检查，不绕过；不用再独立运行重复完整预检或全源扫描，不新增BENCH/开发轮次。
3. 在已能读来源的同一普通用户登录会话中，从C工作目录启动一次：
python C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\r9_formal_executor.py execute --contract C:\LAN_SHARE_REPORT\R9_POSTFORMAT_BIND_AND_START_ZHANGWEI_20261015\FULL_EXECUTION_CONTRACT_AUTHORIZED.json
使用实际已可运行Python入口，不因命令别名不可用改代码。stdout/stderr完整留C，保持原退出码，不覆盖同次日志。可用本机现有安全后台方式，避免终端超时误判并重复启动；不得借此创建权限绕过/新增无限轮询器。
4. 启动后立即上传STARTED.json：PID、真实开始时间、无秘密命令/合同路径、日志路径、run/state、观察到的进程状态。启动慢或入口正审6GB也据实标PRECHECK_RUNNING，不等有复制计数才回报，不把“已启动进程”称首文件已复制。
5. 进度从现有日志和只读state提取，首次实际目标创建/实体复制后更新。首次10分钟内给一份阶段进度，之后每30分钟或阶段切换/错误回传；不得为进度全盘扫描来源/目标。目录阶段可能copy=0，应区分建目录/实体/链接/验收，不把无stdout等同挂起。无需改执行器为实现新仪表盘。
6. 按实体唯一复制、保留硬链接、按本地映射创建junction，140异常按AS_IS_MIGRATE_MARKED；不展开链接、不临时改worker/重写执行器、不删除来源、不格式化、不覆盖不匹配既有对象。
7. 任何身份/清单/code/物理盘/新卷不符、源变化、I/O错误、验收失败都停并保存日志/state，不能自动删目录、重置state、重建候选或自行扩大修复。会话断开只报告，已复制证据保留，不猜密码。
8. 正式完成由既有完整验收返回；报告真实实体/硬链接/junction计数、唯一复制字节、逻辑路径字节与实际分配/空闲变化分别列、错误及验收结果。full_plan_acceptance仅在完整实际验收后可true，不以授权合同的full_migration=true宣称已经完成。

## 回传
agents/chatgpt/inbox/R9_POSTFORMAT_BIND_AND_START_ZHANGWEI_20261015/
EXECUTION_ACK.md、STARTED.json、PROGRESS.json、最终ZHANGWEI_EXECUTION_REPORT.md及既有验收输出引用。
更新INBOX_FOR_CHATGPT为实际STARTED/PRECHECK_RUNNING/COPY_RUNNING/STOPPED/COMPLETED。
SAM保持来源不动、无需另领任务。当前是正式启动令，不是继续准备任务。执行一次并交启动回执。
