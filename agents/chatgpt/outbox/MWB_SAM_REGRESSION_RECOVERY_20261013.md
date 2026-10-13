# SAM 笔记本 — MWB 功能回归调查与最小恢复（最高优先级）

task_id: MWB_SAM_REGRESSION_RECOVERY_20261013
target: SAM（笔记本 Cursor）
priority: ONLY_NOW
status: READY
scope: POWERTOYS_MOUSE_WITHOUT_BORDERS_REGRESSION
R9: HOLD
COPY_AUTHORIZED: false

## 用户亲自观察到的时间顺序（优先于旧端口测试）
1. 在之前任务执行期间，**SAM 笔记本自己的鼠标可以在笔记本与台式机两个屏幕之间来回跨屏**（当时 USER_OBSERVED_SUCCESS）。
2. **ZHANGWEI 台式机自己的鼠标可以跨到笔记本，但不能从笔记本跨回台式机**（当时 USER_OBSERVED_PARTIAL，不是双向完全通过）。
3. 用户明确反馈：**笔记本端口修复任务结束后，原来能用的跨屏功能反而不行了**（CURRENT_REGRESSION_USER_REPORTED，具体哪些方向现时不能动尚无复测）。请不要说“之前双向均完全PASS”，也不要只凭旧15100探针断言配对彻底失败。

## 已知最近SAM改动，必须作差异审计
读取 `agents/chatgpt/inbox/MWB_SAM_INBOUND_15100_FIX_20261013/SAM_REPORT.md` 并核对本机 C盘证据/备份：
- 加入入站Windows防火墙规则 `BLACKBOX_MWB_SAM_INBOUND_100_2_FROM_100_1`，限制 `.1→.2 TCP 15100/15101`，有线网卡Public。
- MWB配置 `ValidateRemoteMachineIP: true → false`（官方 MWB settings，备份后原子写）。这个是值得优先检查的应用配置变化，但**时间相关≠根因已证实**。
- MWB Name2IP现为 `sam:192.168.100.2,ZHANGWEI:192.168.100.1`，同时存在WLAN侧 `192.168.0.62→192.168.0.136:15101` 会话。两台电脑PowerToys版本 SAM=0.100.0.0, ZHANGWEI=0.100.2.0（按最新真实数据复核）。
- 此前发生过 settings.json 被锁后写空、已备份恢复；尤其避免并发写/覆盖密钥。
- 台式机当前另有 `MWB_ZHANGWEI_RETEST_20261013` **暂缓**，避免双端同步改动。

## 唯一优先目标：恢复曾经成立的用户实际功能
A. 先冻结现状并只读取证：笔记本MWB进程/监听端口/时间戳、PowerToys运行状态、官方UI设备顺序与联机状态、最近MWB错误日志/网络会话；从本机C盘历史报告备份提取本轮更改前后**非密钥**配置差异。完整本机备份可以私有存放，但任何报告、GitHub HUB、终端输出均不得含Security Key或配置全文、剪贴板内容。
B. 对照任务执行前用户亲测有效期间与本次修复后的日志时间，确认是否进程重启、端口/防火墙/应用设置变化造成行为改变；明确记录“证据支持”和“仅是假设”的层级。特别检查真正MWB应用会话是否仍优先走WLAN 192.168.0.x、应用层机器矩阵方向与屏幕边界配置，不必强行要求有线15100时刻PASS。
C. 若确有适当本机**备份证明** `ValidateRemoteMachineIP` 原来为true、当前为false，在记录当前值后，允许**仅对该单一MWB设置执行可逆恢复到上一次已知值**（优先官方GUI，需程序退出/锁释放并原子修改才能安全更新；不能整个覆盖旧settings以免损失最新密钥/屏幕布局），必要的单次MWB应用重载需先评估，不影响其他Windows业务。恢复后观察最新应用握手/非敏感连接日志；若尚无因果依据，先只读报告，不要为追求改变而修改。
D. **不自动移除已加的窄范围防火墙规则**；防火墙“允许”规则一般不会单独解释失去跨屏，须有具体测试证据才考虑停用此规则。每次只改变一个配置点，前后保留状态和回滚操作记录。严禁为测试全局关闭防火墙、改IP/路由/DNS/网卡/WiFi/SMB。
E. **不重置Security Key、不解除配对、不重装PowerToys、不升级版本、不启用UseService、不修改台式机设置**；不要在无法自动证明时“修”第二个猜测。不能因 `LISTENING` `ping` `Test-NetConnection` PASS而宣告MWB功能恢复。
F. 自动完成只读检查/经证据支持的单一可逆修复后，在 SAM Cursor 界面简要请用户进行**一次实际复验**：SAM物理鼠标 笔记本→台式机→笔记本；台式机物理鼠标 台式机→笔记本→台式机。将两方向分别标 USER_TEST_PENDING 直到用户实际反馈。键盘跨机用记事本是下一步；本轮先解决鼠标回归，不增加更多配置动作。
G. 若本机恢复未奏效，报告最小根因候选/证伪测试与下一步建议，停止等待GPT复核；不要循环重启或多Agent同时变更。

## 业务保护与报告
- 笔记本业务盘E/D、台式机D/E/F不写不改，QMT/BLACKBOX/SMB数据传输线路不动。R9=HOLD，COPY_AUTHORIZED=false。
- 私有证据（可能含凭据的完整原始配置）保存在笔记本C盘受限目录，不复制到公开HUB。
- C盘报告：`C:\LAN_SHARE_REPORT\MWB_SAM_REGRESSION_RECOVERY_20261013\REPORT.md`
- GitHub HUB 无密钥总结：`agents/chatgpt/inbox/MWB_SAM_REGRESSION_RECOVERY_20261013/SAM_REPORT.md`
- 写明 `PRE_TASK_SAM_MOUSE_BIDIRECTIONAL=USER_OBSERVED_PASS`、`PRE_TASK_DESKTOP_MOUSE_RETURN=USER_OBSERVED_FAIL`、`CURRENT_POST_TASK_REGRESSION=USER_REPORTED`、`CHANGED_FIELDS`、`CAUSE_CONFIDENCE`、`REPAIR_ACTION`、`CURRENT_PROCESS_TCP`、`CURRENT_APP_SESSION`、`SAM_MOUSE_NOW`、`DESKTOP_MOUSE_NOW`、`SECRET_EXPOSED=false`、`R9_HOLD=true`。
