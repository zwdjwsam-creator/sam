# ZHANGWEI｜诊断并恢复当前GUI会话的官方Browser连接

task_id: CURSOR_NATIVE_BROWSER_SESSION_REPAIR_20261020_1720
execution_host: ZHANGWEI
status: READY_DIAGNOSE_AND_MINIMAL_REPAIR
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
COPY_AUTHORIZED=false

## 目标与上下文
用户转述本地AI：工具目录存在cursor-ide-browser，但调用Server not found；START_DOUBLE_AI_TASK.ps1又缺ThinkPad机litellm.exe路径。目标先恢复当前Cursor GUI Agent的官方Browser实际调用，不混淆另一条API路由。
转述未标host，先报告实际hostname/Windows用户/Cursor版本与路径、当前workspace、当前Agent属于GUI/CLI/扩展host的证据。若报错实际来自SAM，标明来源机器与本机观察差别，不能把本机成功/失败冒充另一台。

10/12已有相同现象记录，先读避免重走：
agents/chatgpt/inbox/AUTOHUB_SAM_ONE_SHOT_20261012/BROWSER_GAP_DIAGNOSIS_20261012.md
它是当时SAM事实，不是今天ZHANGWEI当前状态，旧报告中的具体菜单/版本和“唯一方式”需本版本核实。
官方当前资料（ChatGPT已读取）：
https://cursor.com/docs/agent/tools/browser
https://cursor.com/help/ai-features/browser
官方Browser原生集成，无需外部工具；浏览器服务以扩展/MCP运行，工作区隔离会话。不能由目录/schema存在推断live MCP已挂载。

## 先做可复核的最小诊断
1. ACK带本机hostname/version/session kind/workspace。给当前实际live MCP/工具名称列表的相关摘录，不以磁盘缓存代替。
2. 官方browser list-tabs或等价公开入口只试一次，保存工具名/时间/原始错误；若server not found，不原样重试循环。
3. 核本版本实际Browser设置、相关内置扩展启用/运行状态、当前window/extension-host/browser MCP连接日志，仅收相关错误。不要猜设置键或把用户mcp.json随手加一个同名server；不要把CLI headless MCP和GUI会话混为一谈。
4. 区分：服务未注册、已注册但连接失败、当前Agent不在支持的GUI上下文、权限/组织策略拒绝、浏览器页没开。只有证据够才定原因，不能把“换新会话也许好”写为确定根因。
5. 不读/上传密码、API keys、cookie、token、完整私有聊天或原始.env/mcp config secret。报告可脱敏。

## 授权的最小修复
优先使用本机已有的官方Browser/命令/配置恢复；变更先备份，记录精确diff，普通可逆设置修复可直接做。
不额外安装Playwright/Puppeteer或第三方浏览器，不把外部CDP拿来替换官方入口，不启用远程调试端口，不清Cookie/浏览器profile或重装Cursor。
若当前会话工具注入需要重新加载/新GUI会话，先将任务与已完成证据保存到C报告目录/HUB；确认未保存编辑和现有任务安全，再允许一次官方Reload Window/新GUI上下文的最小恢复。不得反复重启或强制结束Cursor。必须通过已有实际可调用的官方机制操作，不假装调用成功。
如果工具本身无法触达开关/Reload/新会话，完成全部诊断和具体接续材料后，回报NEEDS_ONE_UI_ACTION：本机实际看到的精确控件/命令名、当前值、所需一次动作及为何当前Agent无法代做。不要先把“保证已启用再告诉我”丢给用户，不要求用户猜菜单。
遇组织禁用标明真实拒绝，不绕过或自动改账号/计费。

## 成功判据
用当前GUI Agent的live官方Browser：
A. 成功列出实际标签页，拿到tab id/URL标题；
B. 在about:blank/本机新建无业务测试页做一次可撤销的输入或点击并快照，证明不是只看tool schema；
C. 如已有用户提及的GPT页，只核是否能在列表/快照访问该页，并报告可访问/登录墙/未找到。不得替用户发送聊天、提交HUB触发消息或上传聊天内容；本轮无任何发信/网页提交授权。
保留其他用户标签页和登录状态。GPT网页存在、list成功与可输入这三项分别记录，不把一项当全部。
未通过如实PARTIAL/BLOCKED，不能写“理论能控=已修好”。

## LiteLLM脚本独立问题
只读定位START_DOUBLE_AI_TASK.ps1，摘录非敏感可执行路径及存在性、该绝对ThinkPad路径属于哪里。用本机已安装Python/可执行文件查询确认有没有现成litellm；不把它作为修Browser前置。
本轮不启动双AI/API请求、不安装LiteLLM、不新增服务/定时器、不改模型路由/密钥/计费。若需要后续修launcher，提供备份/最小diff建议和依赖证据，另作独立交付，不能顺手改业务系统。

## 交付
C:\LAN_SHARE_REPORT\CURSOR_NATIVE_BROWSER_SESSION_REPAIR_20261020\
HUB agents/chatgpt/inbox/CURSOR_NATIVE_BROWSER_SESSION_REPAIR_20261020/
ACK.md、REPORT.md、相关脱敏错误/版本/实际调用证据、变更diff/回滚方法（如有）。
更新INBOX_FOR_CHATGPT。不生成额外长串任务；本轮一次交齐最短诊断与可做的恢复。
原R9结案不变，源/目标数据/候选/state/验收证据不写不删；SAM临时share收尾仍按独立任务。
