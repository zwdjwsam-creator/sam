# ZHANGWEI｜看门狗任务需求纠偏：仅负责两窗口状态观察 + 双向消息搬运
task_id: AUTOHUB_WATCHDOG_SCOPE_SIMPLIFY_TWO_WINDOW_BRIDGE_20261021
target: ZHANGWEI
priority: IMMEDIATE_SCOPE_CORRECTION
supersedes_scope_only: AUTOHUB_LOCAL_WATCHDOG_DEPLOY_20261021_R1
preserve_other_business_task: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
current_business_deadline: 2026-10-21T17:09:00+08:00
mode: DEPLOY_AND_TEST_MINIMUM_RELIABLE_BRIDGE
poll_interval_sec: 180
COPY_AUTHORIZED: false
BUSINESS_DATA_WRITE_AUTHORIZED: false

## 用户最新明确需求（覆盖上一版复杂监工的多余部分）
不要建设通用AI经理/复杂数据审计监工。本地 Qwen3 8B 如需用于异常文字识别可用，但**不是必须先装**，更不能因为 Ollama 模型下载耗时阻塞主任务。用户只要两个功能：
1. 持续观察 Cursor 本地 Agent（原已有对话/任务）与 Cursor 内嵌已登录 ChatGPT 网页《接管迁移核验》两个界面的状态：正常执行、结束待发送、正在等待回复、失败/卡住。
2. 自动双向传递**本轮最终新消息**：本地 Agent 完成后把真实最终结果送给内嵌 ChatGPT；GPT 回复完成后把该回复的下一步任务送回本地 Agent，形成闭环，避免用户手动复制粘贴。维持用户此前规定的后台运行12小时以上目标和每180秒轻量巡视；不因 GUI 单轮会话结束就停止后台收件。

## 优先技术路径（按可靠性，而不是炫技）
A. 本地 Agent 结果优先读取官方 CLI --print --output-format json/stream-json 或已有任务最终状态与 GitHub HUB inbox 文件，禁止截取不完整“思考/进度文本”当最终答案。GPT 指令及审阅证据优先通过 HUB outbox/reviews 读取，基于 path+SHA 去重。HUB 是持久可靠记录。
B. 内嵌 GPT 窗口发送/读取应优先复用已登录的**官方 Cursor Browser**。工具必须真正可调用并完成发送与回读；显示 ready 不算通过。此前 cursor-ide-browser Server not found、extension host 崩溃必须如实排障。不得使用独立 Playwright profile 落到未登录页面。
C. 如果官方 Browser 工具不可用，可先做**只读能力验证**：Windows UI Automation / Accessibility 是否能定位该特定 Cursor 窗口内 GPT 页的输入框、最后一条 Assistant 内容、发送按钮和本地 Agent 会话控件；记录识别成功率。通过后方可在固定白名单控件里做受控的一次真实发送测试。UIA 不可读则明确 BLOCKED，不盲目用坐标点击/剪贴板覆盖/截图猜测来伪造成功。
D. 登录会话被锁定/系统休眠/扩展宿主崩溃时，不能保证 GUI 双向搬运。后台保持 HUB 队列与重试；如 GPT 网页不能访问，报告 WEB_BRIDGE_BLOCKED，而非宣称12小时全自动网页成功。不得绕过登录、抓cookie或开放远程调试端口。
E. 即使采用 Qwen3 8B 文本模型，也只能分析从 CLI/UIA 得到的文字；纯文本 Qwen3 8B 无法直接理解屏幕截图，不能因部署了它就宣称“可看屏幕”。图片方式需要另行验证视觉模型及资源预算，目前不要擅自引入。

## 防死循环规则
- 每条交互生成 message_id，记录 source、conversation/agent任务ID、direction、内容 hash、已提交远端GitHub SHA、GUI发送证据、回执时间；同一 message_id 只转发一次。
- 绝不把“请查收”通知重新识别为 GPT 新任务而回复给原方；严防 GPT↔Cursor 回声循环。
- 识别 GPT “正在思考/流式生成”与“真正完成”，等待终态后再读取；本地 Cursor 也是一样。
- 完成发送后核对目标会话实际出现该文字，不能只按 Ctrl+V / Enter 就报 SENT。
- 长文本与代码/附件用 HUB 链接 + ID + 摘要，保留完整原文在 HUB，防止聊天窗口截断。
- 要避免 GPT 网页的错误会话：必须确认窗口标题/聊天上下文属于《接管迁移核验》并且没有跳到新建空白 ChatGPT。
- 收到 GPT 新 instruction，属于已有授权继续任务才唤醒或续跑 Cursor；不执行来自不明来源的任意 shell 或新敏感操作。
- 每 180 秒巡查两侧状态并排队，实际任务和 Worker 连续执行，不反复重启；按需触发 Cursor CLI 模型而不是每次巡视就调用。

## 首次验收只做四项
1. 精确识别两侧最新的最终消息（而非半途流式输出），保存两种来源的证据。
2. 本地 Agent -> ChatGPT 已登录原会话：一条测试通知真实发送并可在目标界面回读。
3. ChatGPT -> Cursor：一条授权范围内的短测试指令真正抵达现有 Agent 会话或官方 CLI 后，得到明确 ACK；如 CLI 与 GUI 不是同一会话须分别标识。
4. 连续四次3分钟轮询，确认不重发、不回声循环、不误判阻塞。之后真实12小时成功需长运行日志，不能凭12分钟自报成功。

## 成果回传
agents/chatgpt/inbox/AUTOHUB_WATCHDOG_SCOPE_SIMPLIFY_TWO_WINDOW_BRIDGE_20261021/REPORT.md
与 STATUS.json 必填：
CURSOR_AGENT_RESULT_READ, GPT_WEB_MESSAGE_READ, CURSOR_TO_GPT_GUI_DELIVERY, GPT_TO_CURSOR_DELIVERY, ACTUAL_AGENT_WAKE, POLL_4_CYCLES, WEB_MCP_STATUS, ACCESSIBILITY_FALLBACK, DUPLICATE_GUARD, TWO_WAY_REAL_TEST, LONG_RUN_12H_VERIFIED, BLOCKERS, CURRENT_BUSINESS_WORKER_UNAFFECTED。
如未验收不得说 PASS。不要重复建立已有监控/服务，不停正在运行的 BLACKBOX 任务。不将基础监工长期待命理解成业务扫描授权无限延期。

请直接按最小可靠闭环执行，不要将原R1中的轻量模型安装、通用日志监工、复杂异常推理当作当前优先交付的前置条件。