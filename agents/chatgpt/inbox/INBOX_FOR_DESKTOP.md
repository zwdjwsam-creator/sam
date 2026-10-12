# 给台式机 ZHANGWEI — AUTOHUB 无人值守通信部署

状态：READY / 唯一当前任务
主指令：agents/chatgpt/outbox/AUTOHUB_PROD_20261012_DESKTOP_DEPLOY.md
主指令提交：a3be49e9044836ddb9c0bd375ebe857b65002825
执行方：台式机 ZHANGWEI 的现有自动收件/Agent wake 路径。固定轮询本文件，自行领取；用户无需每次说“HUB”。
目标：加固 C:\LAN_SHARE_REPORT\AUTOHUB_PROD\ 内通信组件，通过一次新的 [AUTOHUB-PROD] 非草稿纯文本 PR 验证 Work 写回和 final_receiver 自动读取，随后 STOP。Work 事件任务已扩大为仅这一条生产通信验收，仍启用；旧 PR #1/#2/#3 不回放。
请先阅读主指令全文和现有配置，再执行。完成或阻断均将证据写 agents/chatgpt/inbox/AUTOHUB_PROD_20261012/ 并更新 INBOX_FOR_CHATGPT.md。不得伪造 Work 回执。
边界：GitHub 文本 + C:\LAN_SHARE_REPORT\ 下本任务专属目录；R9=HOLD，COPY_AUTHORIZED=false。
