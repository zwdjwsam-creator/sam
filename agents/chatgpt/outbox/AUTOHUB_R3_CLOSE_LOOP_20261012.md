# AUTOHUB R3 — 补齐双机通信闭环与真实自动化证明

task_id: AUTOHUB_R3_CLOSE_LOOP_20261012
target: BOTH
primary: ZHANGWEI
secondary: SAM
scope: COMMUNICATION_ONLY
status: NEW
copy_authorized: false
full_migration: false
r9_migration_state: HOLD

## ChatGPT 对 R2 的证据审核（2026-10-12）
1. SAM 报告 NOTEBOOK_AUTO_RECEIVE=VERIFIED_POWERSHELL_RECEIVER，计划任务一分钟/Ready，但**开机后自动启动未证明**。本机自测PING收到ACK。
2. ZHANGWEI 报告 DESKTOP_AUTO_RECEIVE=VERIFIED_POWERSHELL_RECEIVER，SAM→ZHANGWEI 的 PING `PING_SAM_TO_ZHANGWEI_20261011T234504Z` 已ACK。
3. ZHANGWEI 已发布 `PING_ZHANGWEI_TO_SAM_20261011T235542Z`，但截至本次核验仓库仍**缺 SAM 的对应ACK**；不得称双向闭环PASS。
4. 桌面收件脚本 `autohub_r2_comm_receiver_zhangwei.ps1` 只写本地 receiver_out ACK 和 processed；**脚本本身没有上传GitHub**。既有ACK虽已上传，必须证明其上传是自动的、而非Agent/人工二次动作。
5. 两机 CURSOR_AGENT_AUTO_WAKE 均未证明；CHATGPT_WEB_AUTOMATION 未测，WORK_PR_EVENT_TRIGGER 未验证。
6. R9仍HOLD，1GiB样本及BLACKBOX数据不得改动。

## 本轮唯一工作目标
以现有HUB、PowerShell、Windows任务计划、现有Git鉴权，做最小补修，证实两台主机在无人工催促的前提下可自动执行**安全测试消息**的获取→本地ACK→上传HUB→对端收到，明确Cursor Agent自动唤醒仍有无阻碍。
避免更换工具、部署新模型、增加服务端、重复执行以前的测试。

## A. 先完成缺失反向ACK（优先SAM）
- 只读取现有 `agents/chatgpt/inbox/AUTOHUB_R2_RESULTS_20261012/PING_ZHANGWEI_TO_SAM_20261011T235542Z.json`。
- 核查SAM任务计划是否真已自动运行：最近/下次时间、上次退出码、日志、receiver_state、心跳，不把状态 Ready 当作已在自动运行。
- 如果PING尚未ACK，修正SAM本机接收/上传流程，再由定时任务处理这个**同一既有PING**；不得新建测试PING来掩盖旧ACK缺失。
- 仅限scope COMMUNICATION_TEST；ACK必须引用完全相同ping_id/nonce、target=ZHANGWEI，记录生成/上传时间、GitHub提交SHA、是否由计划任务触发。
- 若已存在ACK但未被索引发现，核对路径及ID后报告，不重复上传。

## B. 真正的全链路自动完成（双机）
- 分别核验/补齐：收件脚本读取消息 → 生成本地ACK → **自动提交HUB** → 对端自动检测ACK 的所有环节。
- 必须每个环节都有时间戳/日志/执行进程与运行者证据，证明用户和Cursor聊天窗口未参与该次收发。
- 保留task_id/ping_id去重、目录分离、幂等提交；ACK已存在就校验其内容并视为完成，不覆盖、更不重复执行。
- 原台式机脚本递归搜索C盘以定位token不是适宜长期方式：复用已有受控凭证路径指针或Git凭证助手；不输出或上传token，不把token路径作为公开报告。GitHub仓库是PUBLIC。
- 如果不能证明已实现自动push，应标 `AUTO_ACK_UPLOAD=false`，并说明最少的缺口；不要将本地生成ACK冒充已发送。

## C. 轻量确认Cursor Agent可被后台唤醒
- 两台机器各核实其实际Cursor版本及CLI是否具有**非交互Agent执行**能力；`cursor.cmd` 编辑器启动器不等于Agent CLI。
- 无正式可用接口就如实标 `CURSOR_AGENT_AUTO_WAKE=UNSUPPORTED_OR_UNPROVEN`，本轮不以网页鼠标模拟替代CLI、不绕开登录/授权。
- 如官方CLI已实际可用，仅在隔离C盘对一条无害文本检验一次启动与完成证明，不授权执行任意HUB文本。

## D. 避免冲突与中断
- 与旧 R2 COMM_TEST receiver 保持兼容，不对R2已完成ACK重复执行；R3文件是本轮人工/Agent协调指令，不自动作为PowerShell任意命令执行。
- 勿将INBOX_FOR_CHATGPT里的R9 HOLD误识别成自动化任务，也勿覆盖历史R9日志。
- 单次修补+验收完成即退出Agent会话；安全通信receiver可以继续每分钟运行，但只接受scope COMMUNICATION_TEST。
- 若当前无法从本机自动启动对方Agent，用现有已授权共享/消息链路传达R3；如须各自第一次手动唤醒，准确回报FIRST_BOOTSTRAP_REQUIRED，不假装自动。
- 暂不做ChatGPT网页自动控制/Work PR事件的持续部署；它们待双机ACK验证后单独验证，不再混入通信缺口。

## 交付（严格实测，不编造）
在台式机 C:\LAN_SHARE_REPORT\AUTOHUB_R3_DESKTOP\ 与笔记本 C:\LAN_SHARE_REPORT\AUTOHUB_R3_NOTEBOOK\ 写报告；仅将脱敏摘要和测试ACK提交新HUB目录 `agents/chatgpt/inbox/AUTOHUB_R3_RESULTS_20261012/`，文件独立命名。
报告至少列：
R2_ZHANGWEI_TO_SAM_ACK
R2_SAM_TO_ZHANGWEI_ACK
DESKTOP_RECEIVER_SCHEDULED_RUN_PROOF
NOTEBOOK_RECEIVER_SCHEDULED_RUN_PROOF
DESKTOP_AUTO_ACK_UPLOAD
NOTEBOOK_AUTO_ACK_UPLOAD
TWO_WAY_UNATTENDED_COMM_TEST
DESKTOP_CURSOR_AGENT_AUTO_WAKE
NOTEBOOK_CURSOR_AGENT_AUTO_WAKE
CHATGPT_AUTO_WAKE (NOT_TESTED)
PENDING_MANUAL_ACTION
R9_HOLD_UNCHANGED
COPY_AUTHORIZED=false

## 不可逾越的边界
仅C盘通信状态与脱敏HUB文件；笔记本E/D、台式机E/F BLACKBOX业务文件严格不动。
禁止复制/格式化/删除业务数据、恢复P7、访问交易账户、改动其他安全设置、上传密钥或敏感日志、启动付费API或无限网页自动化。
不执行正式迁移；无效或缺失状态必须报告BLOCKED，不擅自升级范围。
