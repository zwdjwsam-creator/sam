# AUTOHUB R6 — Agent 无人唤醒：CLI 安装审批闸门与本地浏览器衔接验证

task_id: AUTOHUB_R6_CLI_APPROVAL_GATE_20261012
target: ZHANGWEI
scope: PREPARE_ONLY_UNTIL_OWNER_APPROVES
status: PENDING_OWNER_APPROVAL_FOR_INSTALL
r9: HOLD
copy_authorized: false
full_migration: false
notebook: SAM_STANDBY_NO_NEW_TASK

## ChatGPT 对R4B、R5的实证审核（已完成，不要重跑）
1. R4B `agents/chatgpt/inbox/AUTOHUB_R4_GPT_BRIDGE_20261012/LOCAL_TASK_COMPLETED.md` 显示：台式机由Windows计划任务完成固定白名单C盘MARKER，第二次运行PASS，任务已Disabled；这是PowerShell执行，不是Cursor Agent自动唤醒。
2. R5 `agents/chatgpt/inbox/AUTOHUB_R5_RESULTS_20261012/ZHANGWEI_REPORT.md` 显示：当前本机Cursor版本3.24.12，`cursor.cmd`为编辑器命令；本机无独立 `agent` / `cursor-agent`；CLI_HEADLESS_TEST=BLOCKED；R5固定C盘MARKER通过PowerShell计划任务执行，执行后Disabled。
3. R2/R3双机HUB收发及R4 Cursor Browser GUI `browser_fill`、`browser_click` → ChatGPT → GitHub ACK → Cursor再次领取的**人工启动Agent会话内通信**已通过；无需重复PING/ACK/浏览器发送。
4. 待解决：无需用户手动开启Agent聊天的真正Agent启动，并验证**后台Agent能否实际使用已登录Cursor GUI Browser Tab**。独立CLI成功并不能自动证明GUI Browser可用。
5. R9迁移仍HOLD、未授权复制。与本任务绝对隔离。

## R6执行范围：先核验授权条件，不擅自安装
- Cursor官方文档 `https://cursor.com/docs/cli/overview` 和 `https://prod.cursor.com/docs/cli/installation` 说明 Windows PowerShell可安装独立的Cursor Agent CLI，命令行入口为 `agent`，支持脚本/非交互使用。
- 台式机Cursor核对**当前登录账号的CLI使用权限、收费或用量风险、安装范围、安全签名核验方案、是否需要浏览器重新登录/额外权限**，交付一个对用户清晰的一次性安装审批请求；不得读写或上传账号凭证。
- 可**只读**核查官方 CLI 文档、下载地址真实性、Windows支持情况、机器现有已安装组件。**不得**在用户未明确批准前执行 `irm ... | iex`、安装软件、下载后运行、登录新的服务、开启任何收费自动运行、开管理员服务、改网络入站规则、修改全局权限。
- 在未批准安装的情况下，仍可研究现有GUI Cursor的浏览器能力与后台调度是否有官方可用桥梁（只读），列出 `BACKGROUND_CLI_TO_GUI_BROWSER_TAB` 的证据/不确定性。禁止把技术猜想当已验证。
- 避免借安装CLI绕过ChatGPT登录和浏览器确认。不能在无人值守时自动解锁Windows/通过验证码/跳过产品审批。
- 不创建新的永久定时任务或无限测试循环。

## 明确审批后的下一轮（本轮**禁止提前执行**）
只有用户之后明确批准，ChatGPT再发布附有授权引用的新task_id，才可：
1. 官方、可核验来源安装最小范围的CLI并用现有Cursor账户认证。
2. 安装后先以C盘固定目录做一次无害 `agent -p` 运行；验证真实agent执行与退出码、实际模型调用、费用/配额反馈。
3. 单独验证CLI可否操作**已登录的Cursor Browser Tab**，不许把对C盘的无害文件操作PASS冒充ChatGPT网页桥接PASS。
4. 若CLI不支持Browser Tab，提出最短的本机浏览器自动化替代方案并再次审批；禁止扩大工具权限/安装MCP/下载不明插件。
5. 所有额外安装和运行用户都可中止，要求可恢复/停机安全。

## 交付
新建脱敏文件 `agents/chatgpt/inbox/AUTOHUB_R6_RESULTS_20261012/ZHANGWEI_PREFLIGHT.md`（只有实际新结论再发），记录：
- OFFICIAL_WINDOWS_AGENT_CLI_DOC_CONFIRMED
- INSTALL_AUTHORIZATION_STATUS=PENDING_OWNER
- ACCOUNT_CLI_ELIGIBILITY / USAGE_CHARGES_KNOWN
- HEADLESS_CLI_BROWSER_TAB_BRIDGE_STATUS
- ONE_TIME_PERMISSION_REQUEST
- ANY_RUNNING_AUTOMATION_CREATED=false
- R9_HOLD_UNCHANGED=true
若已知道R5结论且无其他新证据，不要做重复盘点刷日志；维持待批准并停止。
