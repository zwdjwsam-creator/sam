# ZHANGWEI｜Gemma4 本地两窗口 HUB 通知器：独立安装与真实闭环验收
task_id: LOCAL_AI_TWO_WINDOW_HUB_NOTIFIER_PILOT_20261021_1913
target: ZHANGWEI
status: NEW
previous_completed: LOCAL_AI_INSTALL_GEMMA4_12B_QWEN3_14B_ZHANGWEI_20261021
scope: TWO_FIXED_NOTIFICATIONS_ONLY
safety: NO_BLACKBOX_BUSINESS_WRITES; NO_GITHUB_TOKEN_REGEN; NO_EXTRABILLING
period_sec: 180
goal: 12h+ monitoring capability (long-run PASS only after actual evidence)

## 当前已查收/验收
已读 inbox/LOCAL_AI_INSTALL_GEMMA4_12B_QWEN3_14B_ZHANGWEI_20261021/REPORT.md 和 STATUS.json：
Ollama 0.40.7；Gemma4 12B vision PASS；Qwen3 14B text PASS；
Ollama=D:\LOCAL_AI\Ollama，models=D:\LOCAL_AI\Models，Watchdog=D:\LOCAL_AI\Watchdog。
安装无需重复。Gemma 的合成截图识别 PASS 不等于能实际操作 Cursor/ChatGPT GUI。
之前另有看门狗方案，以本条用户最终收窄的两项通知为准；勿建立通用复杂监工、勿擅装更多模型。
当前 BLACKBOX 复查原窗口截止 2026-10-21 17:09+08，已过期。此工单**不能**被解释为续跑已过期的 BLACKBOX 业务授权；只部署独立通知器，不中断现有业务。

## 最终只实现两句固定通知
1. 一旦检测到 **Cursor 本地 Agent 有新的实际已提交 HUB 结果**（inbox 文件新 path+sha 或正式完成事件），确保已登录 Cursor 内嵌 ChatGPT 原会话《接管迁移核验》可见且可输入，发：
「Cursor 有新结果已上传 HUB，请查收 inbox。结果：<可信报告链接>。请审阅并将后续任务发布至 outbox/reviews。」
2. 一旦检测到 **GPT 在 HUB outbox/reviews 发布了未领取的新指令/复核**，向正确的 Cursor 本地 Agent 会话发：
「GPT 已在 HUB 发布新的任务或复核，请查收 outbox/reviews，按既有授权范围处理。任务：<任务ID+链接>。」
不是复制几千字的自由内容，不要把“请查收”通知当成新的任务触发回复，防回声死循环。
正常扫描期间不打扰 Cursor；没有新事件就不发通知；每条事件最多成功发送一次。不能因为 3 分钟轮询就每轮自动调用高级模型。

## 实现路线（优先既有系统、最小而可靠）
A. 在 D:\LOCAL_AI\Watchdog 建单实例轻量调度器、持久化队列及送达日志，按 180 秒检查；用已有 GitHub 身份会话、HUB 既有收件手段，无新token；通过 path+blob SHA+direction+task_id 识别事件。历史事件预加载为 seen，首轮不得把老报告刷屏。
B. 优先 Windows UI Automation 读取/定位 Cursor Agent 和内嵌 ChatGPT 的真实可访问控件、滚动聊天区域到底部、检测回答是否完毕、选择目标输入框、输入/提交后回读验证。Gemma4 vision 只在 UIA 不能识别且截图确有必要时进行截图状态辅助判断；模型不直接执行任意 shell/click，动作由受约束控制器执行。先只读探测，记录两个目标窗口可访问性。
C. 内嵌 Browser 可用则可复用 Cursor 官方 Browser；若 cursor-ide-browser Server not found，不许创建另一个没有登录的 ChatGPT 浏览器 profile，不取 cookie。可对 UIA 进行**可验证**的受控操作；若两路径都不可访问，状态 BLOCKED_GUI，HUB 后台仍运行，不能假装“已通知”。
D. 程序须区别 GPT 正在生成/已完成、Cursor Running/Idle/Blocked。滚动时先将正确内嵌 GPT 聊天面板滚到底，再确认最新消息；禁止拿未完成的流式输出当完成。Ctrl+V/Enter 不等于发送成功，要在正确会话看到回显或可靠回执。
E. 稳定性：Windows 计划任务独立于单次 Cursor Agent 聊天，设置 Ignorenew/互斥防双实例，GPU 使用按需加载、一轮结束及时 unload。唤醒/锁屏下 GUI 操作有限制，真实反馈。

## 验收优先级
1. 只读定位两个真实窗口/当前会话、识别底部状态和输入框；截图/元素记录**脱敏**，不上传个人聊天全文。
2. 只用一次独立测试 ID 验证 Cursor->GPT 固定通知实际到达原会话；用另一新测试 ID 验证 GPT/HUB->Cursor 固定通知真实到达原会话；各有发送前后证据。若两个会话任一个不能安全定位，不执行盲发，清楚报告 BLOCKED。
3. 连续4次180秒调度测试，不重发、不回声、不打断现有 Worker。需确认至少一轮没有新消息时保持静默。
4. 12小时目标须以后有完整日志才能标 LONG_RUN_12H=PASS，不能用12分钟冒充。

## 回报
将真实验收报告发回 HUB：
agents/chatgpt/inbox/LOCAL_AI_TWO_WINDOW_HUB_NOTIFIER_PILOT_20261021_1913/REPORT.md
附 STATUS.json：
WINDOWS_FOUND; GPT_CHAT_IDENTIFIED; CURSOR_AGENT_IDENTIFIED; GPT_SCROLL_TO_BOTTOM; GEMMA_VISION_CALL; CURSOR_TO_GPT_DELIVERED; GPT_TO_CURSOR_DELIVERED; POLL_4_CYCLES; NO_DUPLICATES; NO_ECHO; BACKGROUND_ALIVE; LONG_RUN_12H; BLOCKERS; NO_BLACKBOX_MUTATION。
可行部分立即部署，困难明确报实际接口和阻塞，禁止凭模型自述写 PASS。
