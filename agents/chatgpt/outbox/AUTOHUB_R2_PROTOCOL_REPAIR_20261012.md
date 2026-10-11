# AUTOHUB R2 — 修复双机HUB消息路由并实测自动收发

task_id: AUTOHUB_R2_PROTOCOL_REPAIR_20261012
target: BOTH
primary: ZHANGWEI (desktop Cursor)
secondary: SAM (notebook Cursor)
scope: COMMUNICATION_ONLY
r9_migration_state: HOLD
copy_authorized: false
full_migration: false
source_write_authorized: false
status: NEW
supersedes: AUTOHUB_R1_UNIFIED_20261011 (未完成的自动通信测试，不取代R9业务状态)

## 已查到的现场
- GitHub仓库 zwdjwsam-creator/sam 可读写，是 PUBLIC 仓库。
- 2026-10-12北京时间07:36左右，ZHANGWEI上传了 CURSOR_HUB_POLL_20261011T233614Z 收信报告。
- 报告确认其本地脚本 `外部大脑信箱_fetch_outbox.py` 尝试读 `agents/chatgpt/outbox`，但目录当时不存在；同时报 `agents/cursor/inbox` 不存在。
- 此前AUTOHUB R1指令只放在 `agents/chatgpt/inbox`，因此没有被该脚本认作GPT->Cursor新任务。
- 旧权威指针仍指向R9 HOLD；脚本报告未执行AUTOHUB R1，也没有进行复制。
- 今次已新建此 `agents/chatgpt/outbox` 指令；还应检查 `agents/cursor/inbox` 路由兼容性。不要把旧HOLD状态理解为允许复制。

## 严格工作边界
本任务只涉及本机C盘通信脚本/报告和GitHub无害PING/ACK文件。
不得操作笔记本E/D任何业务文件，不得碰台式机E/F BLACKBOX数据、运行研究/行情写入、恢复P7、格式化、删除、复制1GiB/整库或修复R9。
旧R9的HOLD与COPY_AUTHORIZED=false保持不变；本轮通信测试不得覆盖R9原始报告或旧审批闸门。
不改管理员防护、账号安全配置，不开WinRM/SSH新管理端口，不上传凭证/token/cookie；当前GitHub仓库为公开仓库。
无需Hugging Face、本地大模型或付费OpenAI API。
不得重演失败的文件/SQLite全盘扫描。

## 阶段A：先核对实际收信机制
1. ZHANGWEI和SAM分别对本机现有Git/HUB同步、 `外部大脑信箱_fetch_outbox.py`、Cursor CLI/Agent可调用性、收件目录配置、Windows计划任务/后台监听状态进行定点只读检查。
2. 统一唯一权威路径：GPT发给Cursor的任务在 `agents/chatgpt/outbox`，按目标机器和独立task_id领取；Cursor回给GPT的报告放 `agents/chatgpt/inbox` 独立新文件。
3. 若旧脚本实际要求 `agents/cursor/inbox`，应作为兼容别名/指针读取到同一任务对象；不得因此使同一task_id执行两次。检查HUB里同名任务是否已处理；R1旧指令不自动补跑。
4. 原来的 `agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md` 是Cursor->GPT回报入口，不能被用作新的GPT->Cursor执行授权； `INBOX_FOR_DESKTOP.md`、`INBOX_FOR_NOTEBOOK.md` 可以作为备用可读指针。
5. 每条任务必须检查 `task_id`、`target`、`scope`、`status`；绝不因为仓库新增普通文件就执行里面的脚本或旧业务指令。按本机固定身份匹配目标，未知身份失败。
6. 保持本机C盘last_processed/状态账本，处理时先声明领取状态、失败/断网允许重试但不可重复执行同一任务；不得两端同时写同一GitHub文件，禁止force-push。
7. 如果SAM暂时不能由台式机安全远程启动，则台式机仍完成自己的部分、给出笔记本一次性的最短启动方式；不得声称两机已自动执行。

## 阶段B：安全双向自动PING/ACK
1. 仅允许 `scope=COMMUNICATION_TEST` 的新测试消息被监听器自动消费，不允许本任务扩展为自动执行任意Cursor指令。
2. ZHANGWEI发布含task_id与target=SAM的无害PING；由SAM后台收件器（而非用户手动点击Cursor）读取、落本地去重账本并回传ACK。
3. SAM再发布含task_id与target=ZHANGWEI的无害PING；由ZHANGWEI后台收件器自动ACK。
4. 双向各只测试一次；记录 GitHub SHA、触发/检测/ACK时间、是否需要人工操作、后台进程/任务计划信息、重试是否幂等。
5. 单纯PowerShell读文件并回ACK仅证明「收件器自动化」，不能当成「Cursor Agent自动唤醒」。
6. 再尝试一项无害的正式Cursor CLI/Agent自动唤醒测试，必须实际由后台启动且获得Agent执行证明；若产品/系统不支持则报告阻塞，不绕过权限提示。

## 阶段C：ChatGPT端触发器现实核验（仅验证，不长期运行）
1. 台式机可用Cursor Browser对已登录的ChatGPT进行至多一次无害测试，验证是否能检测已登录页面、输入唯一测试字符串、等待回复完成；有验证码、登录、动作审批即停止请求用户审批，不私自绕过。
2. 检查当前账号是否实际有ChatGPT Work GitHub PR事件自动触发入口，未在账户内证明就写UNVERIFIED。不能以一般文档存在作为账户已开通的证据。
3. 当前对话无法只靠一个GitHub commit自行被唤醒；必须明确区分这一限制和Cursor是否自动收信。
4. 浏览器自动化测试不得在用户真实BLACKBOX工作聊天里擅自下发业务任务，不得启动无限网页循环。

## 阶段D：报告与交接
本地台式机: `C:\LAN_SHARE_REPORT\AUTOHUB_R2_DESKTOP\REPORT.md`
本地笔记本: `C:\LAN_SHARE_REPORT\AUTOHUB_R2_NOTEBOOK\REPORT.md`
双方各在 `agents/chatgpt/inbox/AUTOHUB_R2_RESULTS_20261012/` 下上传唯一命名的脱敏报告、状态JSON；未能自动生成目录时上传唯一文件到inbox。
更新INBOX_FOR_CHATGPT.md为新R2报告入口需仅在真实回执完成之后进行，不用假的PASS覆盖R9 HOLD。
报告至少提供:
- ROUTE_MATCHED
- DESKTOP_WATCHER_AUTOSTART / NOTEBOOK_WATCHER_AUTOSTART
- DESKTOP_AUTO_RECEIVE / NOTEBOOK_AUTO_RECEIVE
- TWO_WAY_PING_ACK (每方向时间/证据)
- CURSOR_AGENT_AUTO_WAKE (与纯脚本收件分开)
- CHATGPT_WEB_AUTOMATION / WORK_PR_EVENT_TRIGGER (VERIFIED/UNVERIFIED)
- STILL_NEEDS_HUMAN_STEP
- R9_HOLD_UNCHANGED
- FAILED_CHECKS / NEXT_SAFE_ACTION
未测=NOT_TESTED，不冒充PASS。
任务完成后终止本轮Agent自循环，只保留本次获准、严格只认COMMUNICATION_TEST的安全收件器。
