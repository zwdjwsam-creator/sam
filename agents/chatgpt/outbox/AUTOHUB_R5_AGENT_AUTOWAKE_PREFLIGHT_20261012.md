# AUTOHUB R5 — Cursor Agent 无人值守唤醒可行性核验（仅安全实验）

task_id: AUTOHUB_R5_AGENT_AUTOWAKE_PREFLIGHT_20261012
target: ZHANGWEI
scope: AUTOWAKE_CAPABILITY_AND_C_ONLY_TEST
status: NEW
r9_migration_state: HOLD
copy_authorized: false
full_migration: false

## 经ChatGPT核验的R4基线
已在GitHub确认 `agents/chatgpt/inbox/AUTOHUB_R4_GPT_BRIDGE_20261012/CURSOR_CONSUME_GPT_ACK_LATEST.md` 及最新 `ONE_CYCLE_RESULT.md`：
- 先前Cursor Agent会话经内置 Browser 进行了 browser_lock、browser_fill、browser_click，成功将 R4 test_id 发进 ChatGPT 网页；
- ChatGPT 通过连接GitHub写入提交 `7b4462033dc8`；
- ZHANGWEI 的后续 Agent 会话自动读取ACK并提交 `809e963`；
- 通信往返PASS；**Agent后台自动唤醒未证明**（先前用户开启/继续了Agent对话）；
- `LOCAL_HARMLESS_TASK_EXECUTED=NOT_RUN`；不得将通信成功等同于端到端任务执行或完全无人值守。
本轮不要重做R2-R4的已成功PING/ACK/Browser消息发送。

## 一、优先核查官方 Cursor Agent CLI，区别编辑器启动器
1. 在ZHANGWEI本机只读核查 `agent` 命令、`cursor-agent`、实际安装位置、版本与签名/供应商；此前 `cursor.cmd` 仅是编辑器入口，不能由此推断独立CLI不存在。
2. 官方Cursor文档 `https://cursor.com/docs/cli/overview` 描述Windows PowerShell安装及非交互 `agent -p` 模式；仅作为能力候选，必须本机验证Windows版本、认证、是否可用、是否包含Browser工具。
3. 如果**已经安装并已登录**官方 Agent CLI：只准使用固定C盘隔离工作目录，运行一次非交互只读/写测试文本任务，禁止把公开GitHub任意文本直接接入可执行shell；记录启动方式、退出码、响应、实际文件校验、模型/调用费用提示、人工确认次数。
4. 如果未安装CLI或缺少认证/Browser能力：精确记录BLOCKED和最短用户审批步骤；**未经额外授权不得安装新软件、执行远程安装脚本、产生额外收费、重配全局Cursor权限**。
5. 验证 `agent -p` 可以后台执行普通任务，不意味着可控制**当前Cursor GUI的Browser Tab**或当前ChatGPT登录会话；两项必须分别独立验证。

## 二、本机Windows计划任务闭环：仅C盘白名单动作
1. 复用现有AUTOHUB_R2通信监听器；为本轮新task_id配置**显式固定白名单**，且只允许在 `C:\LAN_SHARE_REPORT\AUTOHUB_R5_AUTOWAKE\` 下创建一次 `MARKER.txt`，内容仅为 `AUTOHUB_R5_AGENT_AUTOWAKE_PREFLIGHT_20261012`。其他目录、其他消息、旧R9任务一律不得执行。
2. 实际证明：计划任务/非交互Agent（如可用）读取预先指定的安全测试令 → 启动Agent → 创建MARKER → 校验内容 → 提交脱敏完成回执到GitHub。所有步骤需时间/进程/退出码/trace，不能把单纯PowerShell执行写入MARKER称为Agent已自动执行。
3. 如CLI不可用，可单独测试PowerShell固定白名单创建MARKER，标记 `SCRIPT_UNATTENDED_PASS` 且 `CURSOR_AGENT_WAKE=BLOCKED`，不得把它冒充AI Agent自动唤起。
4. 不创建永久运行无限循环；若有新计划任务，测试后禁用/停用（保留记录），原有仅针对COMMUNICATION_TEST的已授权收件器不受影响。
5. 后台无交互运行需要人类点审批、解锁桌面、浏览器工具无权限、Windows无用户会话等必须明确写出，不能尝试绕开安全检查。

## 三、替代方案，只评估不启用
1. 核实本机Cursor账号中官方Cursor Automations功能是否存在、是否能使用GitHub PUSH/PR或计划事件唤起云Agent。官方文档: `https://cursor.com/docs/cloud-agent/automations`。
2. 必须明确云端Agent通常在隔离环境中执行，不等于自动控制本地ZHANGWEI或SAM的Windows盘符，更不等于使用本地已登录的ChatGPT GUI会话；可能有独立云Agent用量费用。
3. 只报告本账号可用性、开通条件、实际费用/授权闸门；不创建持续自动化、不部署云环境、不调用收费服务。

## 四、下阶段建议与汇报
- 台式机本地 C 盘 `C:\LAN_SHARE_REPORT\AUTOHUB_R5_AUTOWAKE\REPORT.md`。
- HUB 发布独立新文件 `agents/chatgpt/inbox/AUTOHUB_R5_RESULTS_20261012/ZHANGWEI_REPORT.md` 和状态JSON（真实结果才写PASS）。
- 核心字段：CURSOR_OFFICIAL_AGENT_CLI_INSTALLED / CLI_HEADLESS_TEST / AGENT_WAKE_BY_TASK_SCHEDULER / AGENT_BROWSER_HEADLESS_AVAILABLE / MARKER_VERIFIED / POWERSHELL_FALLBACK_ONLY / AUTOMATIONS_AVAILABLE / EXTRA_BILLING_PERMISSION_NEEDED / USER_MANUAL_STEPS / R9_HOLD_UNCHANGED。
- 请提出**一条**最少额外动作、最少额外付费的可靠路线，不要让用户二选多套复杂方案。
- 如果自动唤醒依然阻塞，请停在明确的最小授权请求上；不得宣称整个系统无人值守。

## 不可逾越的安全边界
- 笔记本 SAM E/D源数据、台式机E/F BLACKBOX业务及1GiB样本均不能修改；R9持续HOLD / COPY_AUTHORIZED=false。
- HUB当前是公开仓库，禁止上传凭证、私密日志、业务数据、ChatGPT cookie/登录态或用户聊天原文。
- 无实际数据迁移、格式化、删除、全库复制、账户更改、权限绕过、API计费调用、HuggingFace、本地大模型部署。
- 如果检测到R5已被消费，不重复执行。此指令是实验，不构成自动执行未来任意HUB任务的通用授权。
