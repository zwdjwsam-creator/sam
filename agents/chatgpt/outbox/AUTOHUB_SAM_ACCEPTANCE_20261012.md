# SAM 笔记本：一次完整通信闭环验收
task_id: AUTOHUB_SAM_ACCEPTANCE_20261012
test_id: AUTOHUB_SAM_ACCEPT_20261012T034000Z
target: SAM
scope: COMMUNICATION_AUTOMATION
status: READY
r9_hold: true
copy_authorized: false

用户授权：人工通知本机 Cursor 读取本任务一次。之后仅通过现有计划任务、GitHub 和 Work 往返完成验收，停止本轮试验。台式机部署及收件入口不改。

1. 复用 SAM 已安装 CLI、AUTOHUB_SAM_NOTEBOOK_POLLER 和既有接收器，不重新安装、不重复部署。工作仅在 C:\LAN_SHARE_REPORT\AUTOHUB_SAM_ONE_SHOT\ 内现有通信子目录及本仓库的本轮纯文本路径。按旧门禁重新核验；不增加豁免、不绕过登录或计费。
2. 先只读确认按需计费是否 DISABLED。确认后允许本轮最多一次真实 Agent 唤醒；UNKNOWN 或 ENABLED 时不调用模型，继续固定脚本通信并标记 AGENT_WAKE_BLOCKED。不能启用额外付费，不能把脚本执行报为 Agent。
3. 将对应 allowlisted JSON 接入现有 watcher，一次人工准备后，下一次正常 Windows 计划任务轮询自动领取新 ID并执行固定 marker。不得人工运行测试执行器冒充计划任务领取。账本按 test_id 与任务 SHA去重；状态不明不重复启动模型。
4. 领取后在 main 上传 ACK_AUTOHUB_SAM_ACCEPT_20261012T034000Z.json 和 PRE_WORK_REPORT.md 到 agents/chatgpt/inbox/AUTOHUB_SAM_ACCEPT_20261012/。记录真实 task commit SHA、计划任务触发时间/LastTaskResult、marker hash、Agent PID/exit或阻塞原因、一次人工启动与后续转述次数、费用检查结果。脱敏，不公开账号标识或凭据。报告和 ACK 必须在创建 PR 前实际存在并取得提交 SHA。
5. 创建同仓库新分支 autohub-sam/AUTOHUB_SAM_ACCEPT_20261012T034000Z 向 main 提交非草稿 PR；标题以 [AUTOHUB-SAM] 开头。PR 变更恰好一个新增纯文本：
agents/chatgpt/inbox/AUTOHUB_SAM_ACCEPT_20261012/PR_PAYLOAD_AUTOHUB_SAM_ACCEPT_20261012T034000Z.md
PR body 与 payload 必须匹配以下精确字段：
test_id: AUTOHUB_SAM_ACCEPT_20261012T034000Z
scope: COMMUNICATION_AUTOMATION
target: WORK_REVIEW
host: SAM
r9_hold: true
copy_authorized: false
另含 received_task_commit_sha、ack_commit_sha、report_commit_sha、cursor_pickup_time、agent_wake_status及反馈。不要复用旧 PR；不以评论或追加提交冒充 opened。payload 不含代码或命令。
6. PR 发布后由本机接收器自动等待并领取
agents/chatgpt/outbox/AUTOHUB_SAM_ACCEPT_20261012/REPLY_AUTOHUB_SAM_ACCEPT_20261012T034000Z.json
只接受 schema=AUTOHUB_SAM_REPLY_V1、from=CHATGPT_WORK、target=SAM、test_id及PR/head SHA匹配的回执；核验其真实 GitHub commit SHA。不得伪造回执。最多等15分钟；超时上传 PARTIAL并停止，不创建另一个PR。
7. 自动上传 FINAL_ACK_AUTOHUB_SAM_ACCEPT_20261012T034000Z.json、SAM_FINAL_REPORT.md、STATUS.json到本轮inbox目录，并更新 INBOX_FOR_CHATGPT.md 和 INBOX_FOR_NOTEBOOK.md。记录回执SHA、自动领取时间、去重结果。真实Agent、计划任务自动领取、Work事件回执及本机自动读回均有证据才标 FULL_LOOP_PASS；仅脚本链通过标 SCRIPT_WORK_LOOP_PASS / AGENT_BLOCKED，证据缺失标 PARTIAL。不用已打开的聊天网页代替 Work 事件证明。
8. 回传最终结果即 STOP；本轮只建一个新验收PR、最多一次模型调用，不再测试、不自动转入其他任务。轻量监听可待命未来明确授权任务。本次无任何业务操作授权，R9持续HOLD、copy_authorized=false。