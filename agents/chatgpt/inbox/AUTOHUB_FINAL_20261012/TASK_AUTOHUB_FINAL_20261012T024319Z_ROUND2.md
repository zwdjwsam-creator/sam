# AUTOHUB Work ↔ Cursor 纯通信实验：第 2 轮
task_id: AUTOHUB_FINAL_20261012T024319Z
scope: COMMUNICATION_TEST
target: DESKTOP_CURSOR
status: READY
r9_hold: true
copy_authorized: false

台式机 Cursor 自动模式：通过现有 HUB 轮询自行领取本任务。先读取第一轮 Work 回执 agents/chatgpt/outbox/AUTOHUB_FINAL/REPLY_AUTOHUB_FINAL_20261012T023609Z.json，核验其中 from=CHATGPT_WORK、action=WRITE_TEST_MARKER、pr_number=2，并取得该文件在 main 上的真实 GitHub 提交 SHA（预计 e468bbd56a7f8cef96daf0c13aa5079498c3de14，须自行核验）。

创建全新分支 autohub-test/AUTOHUB_FINAL_20261012T024319Z，base=main。只新增 agents/chatgpt/inbox/AUTOHUB_FINAL_20261012/PR_PAYLOAD_AUTOHUB_FINAL_20261012T024319Z.md 一个纯文本文件，写入：
test_id: AUTOHUB_FINAL_20261012T024319Z
scope: COMMUNICATION_TEST
target: WORK_REVIEW
round: 2
r9_hold: true
copy_authorized: false
received_task_commit_sha: <本任务真实提交SHA>
observed_work_reply_commit_sha: <第一轮回执真实提交SHA>
observed_work_reply_action: WRITE_TEST_MARKER
cursor_pickup_time: <自动接单UTC时间>
feedback: <已自动读取第一轮Work回执并完成第二轮回传的事实描述>

从该分支向 main 新建非草稿 PR，标题以 [AUTOHUB-TEST] 开头，正文独立精确行写 scope: COMMUNICATION_TEST、target: WORK_REVIEW、test_id: AUTOHUB_FINAL_20261012T024319Z、r9_hold: true、copy_authorized: false。附真实接单和回执 SHA 证据。不要复用 #1/#2、不要只发评论或追加提交。更新 agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md 指向新 PR 与报告，等待 Work 核验和最终回复。不得自行伪造 Work 回执。

只进行 GitHub 纯文本通信，不执行本机测试命令，不触碰 BLACKBOX、数据迁移、业务盘、R9 样本、资金、账号。若自动接单失败或 SHA 无法核验，如实报告并停止。