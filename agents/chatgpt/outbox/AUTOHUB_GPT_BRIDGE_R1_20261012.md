# AUTOHUB GPT BRIDGE R1 — 优先打通本地AI ↔ 网页版ChatGPT ↔ HUB 自动闭环

task_id: AUTOHUB_GPT_BRIDGE_R1_20261012
target: ZHANGWEI
coordinator: DESKTOP_CURSOR
scope: HARMLESS_GPT_BRIDGE_TEST
status: NEW
R9_HOLD: true
COPY_AUTHORIZED: false

## 最高优先级 — 用户真实需求
停止把笔记本/台式机互发PING/ACK或R9迁移验证当成当前主线。本轮唯一目标是让本地Cursor/自动化代理代替用户完成：
本地Cursor上传测试结果到GitHub HUB → 自动操作已登录ChatGPT网页发送「请查看HUB最新测试报告」 → ChatGPT读取、审核并写回HUB → 本地代理识别回复已发布 → 自动将新测试任务交给Cursor。全程只做一轮无害验证，勿无限循环。
无需HuggingFace、无需部署本地大模型、暂不调用收费OpenAI API。
旧AUTOHUB R2/R3通信脚本仅作可复用组件，不必继续以PING ACK为验收终点。R9迁移状态继续HOLD，禁止实际拷贝/修改BLACKBOX业务数据。

## 台式机ZHANGWEI的具体步骤
1. 盘点现有Cursor版本、Browser工具（浏览器操作/截图/可用的CDP/扩展/MCP）、Windows当前已登录ChatGPT网页版会话、浏览器授权限制、现有GitHub HUB登录/写入功能。只核查可操作能力，不读取/保存/上传Cookie、密码、令牌。
2. 以本地C盘测试目录及HUB唯一新文件创建无害测试报告，内容仅包括 task_id=GPT_BRIDGE_TEST_20261012_01 和一行「PING_FROM_LOCAL_CURSOR」。使用当前HUB，勿上传真实业务数据。
3. 本地代理尝试通过**已授权的正常浏览器交互**打开或定位当前ChatGPT对话，自动输入并发送如下无害中文提示：
   「这是AUTOHUB GPT_BRIDGE_TEST_20261012_01。请直接查看GitHub仓库 zwdjwsam-creator/sam 下本轮GPT桥测试报告，读取task_id，并在 agents/chatgpt/outbox/ 下新建 GPT_BRIDGE_REPLY_20261012_01.md，内容仅写 task_id、ACK_FROM_CHATGPT 和下一条无害测试动作。不要操作BLACKBOX数据。」
   注：这条提示必须作为网页对话发送；单纯写进HUB不算成功。
   如浏览器无法连接已有真实ChatGPT标签、无法可靠自动点击、出现确认/登录/验证码/安全检查，必须停止该分支并明确阻塞。不得绕过批准；不要向未知网站输入内容。
4. 通过只读轮询HUB验证GPT是否真正新建对应回复文件；**文件存在且内容task_id匹配**才算GPT回复成功。仅从网页读到“好的”不算HUB任务写回完成。
5. 如果回信存在，让本机通信收件器（非用户手动通知）检测并把测试动作交给Cursor可用的正式Agent启动途径：如已安装并认证的Cursor Agent CLI、官方Background Agent、已有可信本地进程机制。若只支持Cursor GUI聊天/需要人工点击，准确记录「HUB自动收信PASS，Cursor Agent自动唤醒BLOCKED」，禁止把cursor.cmd启动编辑器算Agent自动执行。
6. 检查可否在正常已授权浏览器中检测ChatGPT答复完成及会话失效，验证一次即可；禁止持久网页刷屏、无限自调用或以本地PowerShell假冒GPT回复。
7. 若Cursor自带Browser工具只能由人工发起Agent会话，不具备非交互调度，评估在现有电脑上以普通UI自动化/脚本操作网页的可行性及其授权和稳定性，但不要安装额外软件或绕过安全措施。对无法实现的自动唤醒环节明确列出最小条件。
8. 可顺带只读检查ChatGPT Work GitHub PR触发器当前账户是否实际可用，但**本轮不切Work、不配置PR自动化、不引入API**。别再分散注意力。

## 验收：严格以端到端实测为准
A. LOCAL_REPORT_TO_HUB: 无害报告已在GitHub提交（有URL）。
B. LOCAL_AI_SENDS_CHATGPT_WEB_PROMPT: 是本地代理实际在已登录网页中发出，无需用户键盘转述。
C. CHATGPT_READS_HUB: ChatGPT在网页对话中检查指定报告。
D. CHATGPT_WRITES_HUB_REPLY: HUB产生GPT回复文件，task_id匹配。
E. LOCAL_AGENT_AUTO_RECEIVES: 本地收件器无需用户提醒检测该文件。
F. CURSOR_AGENT_AUTO_EXECUTES_TEST: Cursor真正由可验证机制自动领取并执行无害测试任务。
只有A-F均有实际证据且用户不必每轮操作，才能标 END_TO_END_PASS。否则列出阻塞环节，不能把设计图当作验收。
此处发送GPT网页消息只允许本轮一次测试；如果生成回复后操作本地Cursor需要首次批准，标记并停止，不擅自升级权限。

## 安全与交付
- 只写本机C盘无害测试文件与GitHub专用新文件；公开HUB禁止密钥、token、私人信息、BLACKBOX业务文件/内容、敏感日志。
- 笔记本E/D和台式机E/F BLACKBOX数据严格不动，R9 HOLD，COPY_AUTHORIZED=false，FULL_MIGRATION=false。
- 不允许格式化、复制、移动、删除业务数据、不恢复P7、不访问交易账户、不改Windows安全策略。
- 不覆盖旧R2/R3报告，不再优先开发双机互发PING功能。
- 结果写 C:\LAN_SHARE_REPORT\AUTOHUB_GPT_BRIDGE_R1\REPORT.md，并在 agents/chatgpt/inbox/ 下上传独立脱敏报告。
- 报告写A-F逐项PASS/BLOCKED/NOT_TESTED；浏览器实际动作、是否ChatGPT同一对话、卡点、所需一次性人工授权、下一最小步骤。
完成单次试验即停止；用户目标是代替人转述，不是持续出报告。
