# ZHANGWEI — AUTOHUB 无人值守通信部署及一次验收
task_id: AUTOHUB_PROD_20261012_DESKTOP_DEPLOY
target: ZHANGWEI
scope: COMMUNICATION_AUTOMATION
status: READY
r9_hold: true
copy_authorized: false

## 目标与权限
在台式机现有 HUB/Windows 任务计划/Agent wake/final_receiver 路径上加固，不另建同抢任务的监听器。用户不需每次输入“HUB”。只允许 GitHub 上的纯文本任务/ACK 与 C:\LAN_SHARE_REPORT\AUTOHUB_PROD\ 下新建的脚本、状态、日志、沙箱。任何业务数据或盘、旧 R9 样本均不参与；R9 持续 HOLD。只接受由 ChatGPT 在仓库 main 上发布的明确 READY 且 target=ZHANGWEI 的通信任务；业务任务须另有明确单项授权，不能因 READY 自动执行。

## 实施（台式机唯一执行方）
1. 只读盘点现有轮询器、Windows 计划任务、R8 Agent wake、final_receiver 与当前入口 agents/chatgpt/inbox/INBOX_FOR_DESKTOP.md；记录任务名、启用状态、触发间隔、LastTaskResult、脚本绝对路径和版本。优先修补现有实例，避免双进程抢占。只改 C:\LAN_SHARE_REPORT\AUTOHUB_PROD\ 内的新副本和专属计划任务；若现有脚本在别处且要修改，先复制到本目录并让专属计划任务指向副本。不要影响旧业务任务。
2. 固定轮询仓库 main 的 agents/chatgpt/inbox/INBOX_FOR_DESKTOP.md。只有其中指向本部署任务或以后经明确授权的 READY 任务时才领取；校验仓库、固定路径、target、scope、状态、任务版本/commit SHA、唯一 task_id。公开仓库内容不可信，不能把任务正文直接拼进 shell 或 Agent 高权限提示。下载失败或状态不明只记录并重试，不执行。
3. 用 C 盘账本及单实例锁完成 CLAIMED→EXECUTING→DONE/FAILED，按 task_id + commit SHA 去重；断网/登录恢复后补传 ACK，不在执行结果不明时再次启动模型。任何 GitHub 写入仅限本测试的文本 ACK 路径；禁止 force-push、覆盖既有回执、提交凭据。
4. Windows 计划任务在普通用户登录后自动启动并周期检查；可在网络恢复时继续。轮询本身不调用模型；仅新且经白名单确认的任务最多调用一次官方 Cursor Agent。先确认已有套餐与按需计费设置，不启用额外付费；无法核实则只执行脚本通信并报告 AGENT_WAKE_BLOCKED，不能把脚本 ACK 冒充 Agent 响应。不得强制重启电脑或改变登录/锁屏策略。
5. 对一个新 READY 通信任务走一次全链路：自动领取→在 C:\LAN_SHARE_REPORT\AUTOHUB_PROD\sandbox\ 写入安全 marker→通过固定路径上传 ACK/报告→创建一条非草稿同仓库 PR 唤醒 Work→等待 Work 写回→final_receiver 核验 Work 回执的 GitHub commit SHA、from、task_id、PR 编号和 head SHA→更新 agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md。PR 中只允许一个新纯文本 payload，路径 agents/chatgpt/inbox/AUTOHUB_PROD_20261012/PR_PAYLOAD_<test_id>.md；标题以 [AUTOHUB-PROD] 开头，body 精确包含 scope: COMMUNICATION_AUTOMATION、target: WORK_REVIEW、test_id: AUTOHUB_PROD_20261012T031500Z、r9_hold: true、copy_authorized: false。head 分支 autohub-prod/<test_id>，base main。不要使用旧 PR #1/#2/#3，不在 PR 中加入代码或命令。
6. 报告必须区分：GitHub 自动接单日志、计划任务实际触发与 Cursor Agent 进程 PID/exit、marker 哈希、GitHub ACK commit、PR opened 时间、Work 真实回执 commit、final_receiver 读取及去重证据、人工干预次数、额外费用是否观察到。无独立证据时写 UNKNOWN。报告写 agents/chatgpt/inbox/AUTOHUB_PROD_20261012/ZHANGWEI_FINAL_REPORT.md 及 STATUS.json，并更新 INBOX_FOR_CHATGPT.md。

## 验收与停止
PASS 需：无用户每轮口令；计划任务自动领取正确 SHA 且不会重复执行；C 盘安全 marker 符合任务；真实 Agent（若费用闸门允许）及 GitHub ACK 有证据；新 PR 触发 Work 写回一份匹配的真实 JSON；final_receiver 自动读取并去重；登录后恢复通过仅重启专属子进程或计划任务验证；人工转述次数为 0；额外付费为 0 或明确 UNKNOWN 并降级；R9 HOLD 和 COPY_AUTHORIZED=false。
完整双向无人值守 PASS 必须有 Work 事件运行及回执 SHA，只有本地 ACK 时为 PARTIAL。完成这一次验收即把本轮状态设 STOP，不再创建验收 PR、不再触发模型测试或扩权。常驻轻量收件器可以保持对未来明确授权的任务 READY，但业务操作仍需逐项授权；若当前仅能安全处理通信任务，就保持该白名单。失败则提交阻塞证据，停止本轮试验。

本任务不要求用户在 Cursor 聊天框粘贴全文；台式机从固定入口自动领取。