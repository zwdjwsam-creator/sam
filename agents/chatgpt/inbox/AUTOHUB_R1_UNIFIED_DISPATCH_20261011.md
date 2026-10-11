# AUTOHUB R1 | 双机自动执行统一启动令

任务ID: AUTOHUB_R1_UNIFIED_20261011
总协调: ZHANGWEI（台式机Cursor）
参与端: SAM（笔记本Cursor）
唯一人工入口: 本文件。此前两份分工任务仅作技术附件；先查状态防重复。
附件:
- agents/chatgpt/inbox/AUTOHUB_R1_20261011_DESKTOP_ZHANGWEI.md
- agents/chatgpt/inbox/AUTOHUB_R1_20261011_NOTEBOOK_SAM.md

## 用户真实目标
不是人工让两台Cursor去GitHub看消息，也不是每次手动告诉ChatGPT去看报告。
两台Windows机器应各自能自动发现自己负责的HUB新任务、启动Cursor可用的非交互执行途径、完成无害任务并发布结果；无需每轮人工提示。
要区分「收到任务文件」「系统自动执行」「ChatGPT被自动唤醒」三种状态，不能混为一谈。

## 立即进行（本轮仅测试通信）
1. 台式机先检查本机和笔记本目前有没有常驻监听器/计划任务/Cursor CLI；如已有可用组件直接复用。不重复安装、不更改BLACKBOX迁移状态。
2. 台式机经已授权的SMB/现有双机渠道将笔记本子任务及必要的C盘轻量收件程序安全部署到SAM；若无法远程启动（以前WinRM可能未启用），不要偷偷开新管理口或强行远程执行，明确标明首次手动启动缺口与最短命令。
3. 两台电脑各自配置一个最小收件器（现有Git/PowerShell/Windows任务计划程序优先），约60秒检查自己目标的HUB测试信件，去重并维护本机C盘状态。Windows开机后能否自动启动要实测，不能仅写配置即判通过。
4. 只允许 scope=COMMUNICATION_TEST + target=SAM/ ZHANGWEI + 唯一task_id 的无害PING/ACK任务自动执行；所有R8/R9、源数据和正式迁移任务禁止自动执行。
5. 通过实际运行证明：台式机向HUB上传SAM PING → 笔记本无需人工操作自动收信和回复 → 台式机自动收到；随后SAM发ZHANGWEI PING → 台式机自动收信并回复。各方向仅测试一次，消息文件用独立名字，不能造成自循环。
6. 评估Cursor CLI能否在这两台实际Windows中被后台唤醒；仅PowerShell自收ACK不等同于Cursor Agent能自动执行。若CLI不可用，要明确报告「自动收件可用、Agent唤醒尚不可用」。
7. 台式机另行只做一次无害浏览器能力检查：现有Cursor Browser能否打开ChatGPT、找到输入框、输入无害测试标记并识别回复；不要模拟批量ChatGPT交互、绕过人工审批/登录验证，不上传cookie/token。
8. 查验用户当前ChatGPT Work环境里是否实际配置了GitHub PR事件触发功能；不可直接检查则UNVERIFIED，不声称已经能自动唤醒此聊天。若可用仅给最小实验，不创建未经审核的永久PR触发。
9. 把两机结果汇总到一份C盘报告及单独HUB文件。交接给ChatGPT审核，下一步是否开启正式双机自动执行须单独授权。

## 边界
当前HUB是公开仓库：只放无害脱敏消息，禁止token/会话/业务数据/个人私密日志。
不部署本地大模型、不启用付费OpenAI API、不新建HuggingFace、不修改管理员安全配置。
不动笔记本E/D、台式机E/F任何BLACKBOX业务文件，不复制/删除/格式化，不恢复P7。
不覆盖现有R9任务/测试数据，禁止自动执行旧邮箱里未处理的任务。
任何真实文件写入、全量迁移、实盘操作仍需独立授权。
测试后停止Agent循环；可以保留已明确批准且只接受COMMUNICATION_TEST的安全收件器。

## 汇报（台式机负责统一提交）
C:\LAN_SHARE_REPORT\AUTOHUB_R1_UNIFIED\REPORT.md
HUB独立新报告文件
字段：
- DESKTOP_RECEIVER_INSTALLED / NOTEBOOK_RECEIVER_INSTALLED
- DESKTOP_AUTOSTART_TESTED / NOTEBOOK_AUTOSTART_TESTED
- TWO_WAY_PING_ACK_AUTOMATIC
- CURSOR_CLI_AGENT_WAKE_TESTED
- CHATGPT_BROWSER_PING_TESTED
- WORK_GITHUB_EVENT_AVAILABLE
- FIRST_BOOTSTRAP_MANUAL_ACTION_REQUIRED
- FUTURE_HUMAN_INTERVENTION_PER_CYCLE
- R9_UNTOUCHED
- REMAINING_BLOCKERS

如果未实测，写UNKNOWN/NOT_TESTED；禁止编造全自动通过。
