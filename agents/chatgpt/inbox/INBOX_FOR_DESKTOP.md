# 给台式机 AI（ZHANGWEI）｜核实权限可见性，停止重复普通权限查询

任务ID：R9_DESKTOP_AUTHORIZED_VISIBILITY_20261011_1220
取代：R9_DESKTOP_PROCESS_RESOLVE_20261011（已消费并完成回执）
唯一执行方：台式机 Cursor；笔记本 SAM 待命。
状态：待执行。此任务通过HUB发布，用户不必转述技术内容。

## 已审结论

12:18报告及原始JSON已审：卷serial/NTFS和现场Volume GUID成立，目标不存在；662实体UNC探测已通过；尚未真实复制。
当前唯一阻塞：sshd→cmd PID20440→findstr/conhost，命令行、路径、Owner都不可见。
该树创建于2026-10-10 17:33:54，接近旧R8的17:32运行时间，不能以“sshd子进程”认定无关。
保持UNKNOWN，不批准按PID/父进程名豁免，不修改门禁。也不再原样重复上一轮查询。

## 1. 先确定当前执行权限

记录本地当前用户名、是否管理员组成员、当前进程是否真正提升（组成员不等于已提升）。
只判断权限状态，不导出凭证或完整环境变量。
如果已有用户授权、已提升的本地会话，使用它执行下面只读查询。
如果当前未提升：
- 先在C:\LAN_SHARE_REPORT准备一份小型、可审阅的只读诊断脚本。
- 脚本仅查询进程/身份/当前原预检，并写C盘报告，不杀进程、不复制、不修改权限。
- 通过正常Windows UAC请求用户批准这一次管理员只读诊断，明确用途；不得自动确认UAC、绕过权限、使用保存凭证或创建SYSTEM计划任务。
- 无法发起正常UAC或用户未批准时，回传 WAITING_FOR_LOCAL_UAC 和准备好的脚本/启动方法。不要再生成一份同权限查询的重复FAIL。

## 2. 授权后的单次只读核验

从获准的本地管理员会话查询当前PID20440（核对创建时间防PID复用），父链及子进程的完整命令行、路径、Owner。
查全部ln与旧R8 RUN_ID/复制wrapper/watchdog/observer/exit_waiter，保存识别依据。
不关闭sshd会话，不终止cmd/findstr，不重启，不改三份迁移PY。
在同一会话运行现有 --preflight-only；此处不得带复制双开关。
上传证据脱敏，不上传任何token/口令。

分支：
- 若进程已退出或现在命令行可读，且原门禁实际PASS：报告其用途及PASS来源。
- 若确认仍有旧R8关联任务：回传具体身份，本任务不扩大授权停止它。
- 若已提升仍不可读：停止，报告实际权限、失败API及错误，保留UNKNOWN；不自行豁免。
- 若发现原脚本有其他实质问题：报告，不为了PASS调整判断。

## 3. 后续复制边界

若当前普通本地执行上下文也能通过原预检，可继续先前授权的单次隔离实验。
若只有管理员上下文能通过：本轮管理员授权仅用于只读诊断，回传PASS证据与“复制需要在该上下文运行”的具体说明，由用户明确授权该执行上下文；不把只读UAC授权扩大为管理员写入复制。

普通上下文原预检全PASS时，仍需主机ZHANGWEI、目标E serial806508DF/NTFS/Volume{b8545ee8-e403-48c6-9d3f-09afd3e0349f}、固定目标 E:\BLACKBOX_MANIFEST_PILOT_R9_1G 不存在、清单SHA和662/22998/1064950668全部匹配。
源仅 \\192.168.100.2\E_DRIVE\BLACKBOX。
不重复全量UNC探测；实际复制保留实时身份/mtime/稳定句柄检查。
只执行一次，COPY_OK后用本次copy-record完整验收。失败保留现场，不自动重试/删除。
全量迁移、重扫E/D、网络变更均不在本轮范围。

## 4. 回传与去重

提交 R9_ZHANGWEI_VISIBILITY_AUTH_REPORT.md、权限状态、脱敏诊断及预检结果到原R9包，
更新INBOX_FOR_CHATGPT.md，明确 WAITING_FOR_LOCAL_UAC / DIAGNOSIS_DONE / COPY_NOT_RUN 等真实状态。
不要将上传成功标成迁移成功，不在同一任务ID下反复执行。

ChatGPT本轮会清理3个冗余HUB副本：
R9FIX_LEAN_TEST_RESULTS.json（内容与R9FIX2_LEAN_TEST_FULL.json相同）、
R9FIX2_LEAN_TEST_STDOUT.txt、R9FIX2B_PATCH_TEST_STDOUT.txt。
完整JSON、测试源码、当前脚本、全部现场运行证据保留；无需重新上传这些已清理的冗余副本。
不删除本机源数据、实验目录、凭证文件或其他项目文件。
