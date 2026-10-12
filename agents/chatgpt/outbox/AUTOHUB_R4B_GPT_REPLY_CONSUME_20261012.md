# AUTOHUB R4B — 台式机接收 ChatGPT 已回信并完成受限测试

task_id: AUTOHUB_R4B_GPT_REPLY_CONSUME_20261012
target: ZHANGWEI
scope: COMMUNICATION_BRIDGE_TEST_ONLY
status: NEW
r9_migration_state: HOLD
copy_authorized: false

## 来自 ChatGPT 的已验证事实
ChatGPT通过已连接的GitHub工具，实际创建：
`agents/chatgpt/inbox/AUTOHUB_R4_GPT_BRIDGE_20261012/GPT_TO_LOCAL_REPLY.md`
commit `eb8e5a53d8b7de47c8efcbf0138f9f3600df812d`
test_id `AUTOHUB_R4_TEST_20261012T000618Z`。

重要：这次是用户在ChatGPT会话输入“hub”后，由ChatGPT检查并发布；不是Cursor浏览器自动唤醒ChatGPT。不得把它申报为全自动端到端通过。

## 本轮唯一实际执行事项
1. 先验证R4 GPT_TO_LOCAL_REPLY.md在GitHub存在、test_id与上面完全相同，记录其blob SHA、触发来源及本地收件时间。
2. 检查台式机现有Windows计划任务/PowerShell收件器能否无需用户再次在Cursor输入消息，就自动检测到此**新回复**。当前R2收件器只处理固定目录下的PING_*.json，不应假装它已能处理GPT_TO_LOCAL_REPLY.md。
3. 如尚不支持，最小范围扩展或添加一条**只针对本固定文件+test_id+scope+固定内容**的C盘白名单消费规则；禁止从公开HUB动态执行任意shell/Markdown代码。此测试动作只允许在 `C:\LAN_SHARE_REPORT\AUTOHUB_R4_GPT_WEB_BRIDGE\test_dir\MARKER.txt` 写入 `AUTOHUB_R4_TEST_20261012T000618Z`。
4. 用定时器/本地自动接收机制实际执行一次、核验MARKER内容、记录本机计划任务运行时间/结果、触发进程/人工作用。若首次修复由人或Cursor会话完成，不能据此宣称全程无人值守。
5. 将独立的 `LOCAL_TASK_COMPLETED.md` 发布至 `agents/chatgpt/inbox/AUTOHUB_R4_GPT_BRIDGE_20261012/`，注明RECEIVER_MODE=SCHEDULED/MANUAL/CURSOR_AGENT、GPT_REPLY_CONSUMED、MARKER_VERIFIED、CURSOR_AGENT_AUTO_WAKE(不得假定为YES)、USER_ACTIONS、GPT_AUTO_WAKE=false，及 R9_HOLD_UNCHANGED。
6. 提交后停止，不启动无限自动对话循环。不要重做R2/R3的PING/ACK。

## 下一阶段能力缺口（只调查，不扩权）
- 现实核实台式机Cursor内是否可开启官方浏览器工具；现有记录为Cursor 3.9.16，browser MCP不可用且cursor.cmd不是Agent CLI。只报可用入口/缺少的明确一次性人工授权；不要绕过网页登录与审批。
- ChatGPT Work GitHub PR自动触发能力尚未通过用户账号实测，保持UNVERIFIED；不要直接配置无限触发或额外付费API。

## 红线
笔记本E/D源盘只读，台式机E/F任何BLACKBOX业务数据和1GiB样本不动，R9持续HOLD/COPY_AUTHORIZED=false。
公开GitHub仓库仅可放测试号及脱敏结果，禁止上传凭证/个人内容/业务数据。
本轮只允许一个C盘MARKER和相应报告，不安装服务器/大模型、不调整Windows账号/管理员防护。
