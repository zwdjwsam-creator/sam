# ZHANGWEI｜E工作区完成一轮实际对接
task_id: CURSOR_BLACKBOX_E_DOCKING_HANDSHAKE_20261020_1824
execution_host: ZHANGWEI
workspace: E:\BLACKBOX
status: READY
supersedes_active_instruction: CURSOR_BLACKBOX_E_SESSION_REVIEW_20261020_1814
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
COPY_AUTHORIZED=false

## 本轮目标
用户已要求接收18:18状态并下达下一步自动对接任务。此任务替代当前1814补证流程，1814暂停、不执行。E工作区/历史/HUB已通过；LiteLLM先不动。
18:18报告是“官方Browser曾PASS后间歇失败”，不能提前称稳定恢复。现在只完成一次 E Agent → HUB → 当前GPT网页的交接，不再重做设置诊断或要求用户重新打开E窗口。

## 执行
1. 从当前E GUI Agent读取本任务；核hostname=ZHANGWEI、workspace=E:\BLACKBOX。若不符仅报告，不能用D旧会话冒充。
2. 使用已有本机HUB认证，在以下目录写ACK.json并通过Contents API读回，核任务号与内容一致：
agents/chatgpt/inbox/CURSOR_BLACKBOX_E_DOCKING_HANDSHAKE_20261020_1824/
ACK记录task_id、实际观察时间（+08:00）、host/workspace、历史与HUB沿用证据、1814=HOLD、LiteLLM=UNCHANGED、网页发送前状态。不得上传token/凭据或聊天全文。
3. 当前GUI会话官方cursor-ide-browser做一次live tabs调用。有工具schema不能当成功。若Server not found/超时，不重复同样调用，不reload、不改设置：写RESULT.json标BROWSER_UNAVAILABLE_HUB_ONLY，更新INBOX_FOR_CHATGPT指向结果，本轮结束。HUB已经可用，不把文件通道失败与Browser掉线混淆。
4. live可用时，仅核现有目标GPT会话：
https://chatgpt.com/g/g-p-6acaf94bf878819186ea89f1b8050ab9-shu-ju-qian-xi/c/6acaddec-e988-83e9-8062-ac6e621a09a2
标题曾为“接管迁移核验”；以会话URL为准，不仅凭标题选择。复用现有标签；如无匹配页，可以官方Browser打开此精确URL一次。遇登录墙/无composer/页面不符，写明确结果并停止，不改账号或新建其他聊天。
5. 具备官方Browser真实页面访问和composer时，将RESULT.json先写为READY_TO_NOTIFY，更新INBOX_FOR_CHATGPT，读回确认后，向上述会话仅发送以下一条消息（本任务明确授权该次网页提交；不向其他人/其他会话发送）：

【E工作区对接回合1/1】任务 CURSOR_BLACKBOX_E_DOCKING_HANDSHAKE_20261020_1824。ZHANGWEI 当前 E:\BLACKBOX 已领取，HUB回执已写入并读回；1814暂停，LiteLLM未动。请查收 https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/CURSOR_BLACKBOX_E_DOCKING_HANDSHAKE_20261020_1824 并作对接验收。

只发送一次。若提交结果不明，不再点击/重发，RESULT记SEND_UNCONFIRMED。发送成功需看到该消息成为页面已发送记录，保存必要的脱敏证据，不导出既有聊天。
6. 提交后将RESULT更新为WEB_MESSAGE_SENT或实际失败/不明状态；更新INBOX_FOR_CHATGPT并读回。若网页发送后任务被GPT回复打断，先补完本轮RESULT；收到本任务以外新明确指令前不自启下一回合。

## 状态与边界
RESULT至少有task_id、observed_at、host、workspace、hub_write/readback、browser_live、target_conversation_matched、composer_observed、send_attempt_count、send_outcome、error（若有）、1814_hold、litellm_unchanged。
ACK/HUB读回成功、Browser可见、网页发送成功、GPT已回执四项分开；最后一项只能在实际收到本轮GPT回复后标通过。暂未收到记PENDING_GPT_ACK，不能自行宣布闭环全部成功。
本轮是一次有限对接，不安装定时器/常驻服务，不循环刷网页或反复发送“HUB”，不调用LiteLLM/API，不启动迁移/verify-existing，不动R9业务或冻结证据。保留已有工作区历史和D回退。
后续本地任务通过INBOX_FOR_DESKTOP最新明确指令领取；task_id已完成的不重复执行。HUB文件fallback不等于ChatGPT已被自动唤醒，如本轮Browser失败，如实停在HUB_ONLY。
