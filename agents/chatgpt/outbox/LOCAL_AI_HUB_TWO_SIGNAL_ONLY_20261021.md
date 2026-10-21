# ZHANGWEI｜最终需求：本地 Gemma 仅负责双向 HUB 两字通知
task_id: LOCAL_AI_HUB_TWO_SIGNAL_ONLY_20261021
target: ZHANGWEI
priority: OWNER_LATEST_REQUIREMENT_SUPERSEDES_PREVIOUS_WATCHDOG_SCOPE
status: READY_FOR_IMPLEMENTATION_AND_TEST
poll_interval_sec: 180
LOCAL_WORKDIR: D:\LOCAL_AI\Watchdog
CURSOR_WORKSPACE: E:\BLACKBOX

## 唯一功能：两个方向只发 ASCII "HUB"
1. GitHub HUB 的 GPT 发件箱 agents/chatgpt/outbox/ 或 reviews/ 出现新且未通知的正式任务/复核：在 Cursor BLACKBOX 工作区原来的本地 Agent 对话输入并真正发送 HUB。
2. GitHub HUB 的 Cursor 发件箱 agents/chatgpt/inbox/ 出现新且未通知的真实业务结果/进度报告：在 Cursor 内嵌已登录 ChatGPT《接管迁移核验》原会话输入并真正发送 HUB。
不转述完整内容、不附 URL、不总结、不判断业务数据质量。相应 Agent 或 GPT 收到 HUB 后，自行读取 GitHub 并处理。没有新消息就保持静默。
必须忽略 PILOT/测试、CLAIM/ACK、心跳、自动通知本身的报告、收件日志，否则将 HUB 通知形成无限回声。每个方向的新增事件按 path+blob SHA/任务ID 去重，可把同期多个新文件合并成一次 HUB。

## 谁来做
已安装的 Gemma 4 12B/Ollama 是本地窗口识别辅助；Windows 独立轻量进程负责每 180 秒读 GitHub 和可靠触发窗口输入。Gemma 不需要读取任务长文、不改代码、不处理 BLACKBOX。不用 Cursor 远程模型每三分钟当监工；Cursor Agent 只用于一次性安装/修复最小本地程序。
复用 D:\LOCAL_AI\Watchdog\hub_two_window_notifier_1913，禁止重新安装模型、另建多个有冲突的监控服务。
视觉模型可以帮助识别正确窗口，但执行器必须单独验证目标会话和唯一输入框；找不到则保留通知队列，标记 BLOCKED，绝不盲发。旧报告曾把 Cursor 本地 Agent 的目标框误识别为 ChatGPT Work，GPT->Cursor 通道 FAIL，必须首先解决这一精确故障。
正式投递内容必须严格等于 ASCII HUB，这样无需传输中文或 URL，避免乱码；成功标准是正确目标会话出现实际已提交的消息，不是输入框文本回显、剪贴板或模型自述。无法使用 Browser MCP 时可以尝试已有 UIA 控制；不能擅自创建新登录浏览器或提取凭据。
Cursor GUI 关闭、Windows 锁屏/休眠、Ollama 不可用时可能无法操作窗口；后台应保留未送达队列，等待恢复。不能宣称绝对保证12小时 GUI 通讯。

## 验收
先只在安全测试模式下创建两个唯一测试事件，分别证明 GPT HUB->Cursor Agent 的 HUB 确实发送到正确本地对话、Cursor HUB->内嵌 GPT 的 HUB 确实发送到正确网页对话；确认不会发错窗口。生产正常模式必须忽略这些测试事件。
做至少4轮间隔真实180秒的独立后台巡视：无新消息时不发、同一事件不重发、无需 Cursor Agent 聊天窗口持续运行。使用实际超过12小时日志才能宣称长期稳定。
业务范围边界：不得写入 BLACKBOX 业务数据、修改 R9、重启旧业务盘点或更改认证/收费设置。

## 回报
agents/chatgpt/inbox/LOCAL_AI_HUB_TWO_SIGNAL_ONLY_20261021/REPORT.md 和 STATUS.json。
报告两方向投递真实证据、模型是否调用、目标输入框验证、计划任务实际启动、四次180秒巡视、去重、阻塞和12小时状态。没有核验不得写PASS。
用户最新要求取代此前多功能监工、长篇消息转发、复杂自动修复等冗余要求。请最小修改现有程序完成真正双向测试。
