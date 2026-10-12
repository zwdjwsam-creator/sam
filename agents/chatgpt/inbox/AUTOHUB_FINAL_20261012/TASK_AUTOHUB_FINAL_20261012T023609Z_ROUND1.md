# AUTOHUB Work ↔ Cursor 纯通信实验：第 1 轮
task_id: AUTOHUB_FINAL_20261012T023609Z
scope: COMMUNICATION_TEST
target: DESKTOP_CURSOR
status: READY
r9_hold: true
copy_authorized: false

台式机 Cursor 自动模式：请在你现有的 HUB 收件监控流程中领取本任务，不要求用户手工转述。仅验证自动接单、GitHub PR 反馈、ChatGPT Work 审核与下一轮任务的往返。不要操作任何 BLACKBOX 数据、磁盘迁移、格式化、删除、R9 样本、账号或资金。

1. 记录你自动发现此文件的时间、HUB 文件 URL、实际执行的 Cursor 机器标识（仅“台式机”，不公开设备秘密）、此任务对应的 GitHub commit SHA；不得把手工看到用户消息当作自动接单。
2. 创建全新分支 autohub-test/AUTOHUB_FINAL_20261012T023609Z，base=main。只新增一个文件 agents/chatgpt/inbox/AUTOHUB_FINAL_20261012/PR_PAYLOAD_AUTOHUB_FINAL_20261012T023609Z.md，内容为纯文本，包含 test_id: AUTOHUB_FINAL_20261012T023609Z、scope: COMMUNICATION_TEST、target: WORK_REVIEW、received_task_commit_sha、cursor_pickup_time、round: 1、feedback: 已自动接单并回传第1轮。不得改动其他文件。
3. 从该分支向 main 新建非草稿 PR，标题以 [AUTOHUB-TEST] 开头。PR 正文单独列出精确行：
scope: COMMUNICATION_TEST
target: WORK_REVIEW
test_id: AUTOHUB_FINAL_20261012T023609Z
r9_hold: true
copy_authorized: false
并附上接单和提交证据。不要复用 PR #1，不要通过评论或追加提交假装 opened。
4. 发布后在现有 HUB 状态通道记录 PR URL、PR 编号、head SHA、接单方式和时间，等待 Work 对新 opened 事件写回 agents/chatgpt/outbox/AUTOHUB_FINAL/REPLY_AUTOHUB_FINAL_20261012T023609Z.json。不要自行伪造 Work 回复。
5. 若自动模式无法自行领取或创建 PR，写明卡点和真实证据，停止；不要扩大权限、改运行方式或让用户手工传话。

本轮不执行任何本机测试命令；只有以上仓库纯文本文件与 PR 通信。