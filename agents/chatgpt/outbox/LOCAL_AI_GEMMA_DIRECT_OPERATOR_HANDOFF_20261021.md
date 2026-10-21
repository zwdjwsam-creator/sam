# 用户最新指令｜本地模型接管双窗口通讯，不再让 Cursor Agent 执行日常通知
task_id: LOCAL_AI_GEMMA_DIRECT_OPERATOR_HANDOFF_20261021
target_host: ZHANGWEI
priority: ROLE_CORRECTION
supersedes_runtime_role_of: LOCAL_AI_TWO_WINDOW_HUB_NOTIFIER_PILOT_20261021_1913
scope: LOCAL_MODEL_RUNS_NOTIFICATIONS_NOT_CURSOR_AGENT
NO_BLACKBOX_BUSINESS_WRITE: true
NO_EXTRA_BILLING: true

## 用户明确的最终运行架构
- **Gemma 4 12B 是值守智能体**：自主读取已提供的 UIA 结构化状态与必要窗口截图，判断 GPT 内嵌网页或 Cursor Agent 的最新状态、是否应滚动/等待/发出固定通知。
- **Windows UI Automation / 受限控制脚本是它的手脚**：提供允许动作 screenshot, inspect, scroll_chat_bottom, focus_known_composer, type_fixed_notice, send, verify_delivery；执行前必须核对真实目标窗口/输入控件，严禁在错误窗口盲发。
- **Qwen3 14B 仅可作为本地文字辅助模型**，按需调用，非必须。
- **Windows 独立常驻调度器**执行3分钟巡视和事件队列，不依赖 Cursor Agent 会话继续运行；Gemma 由 Ollama 本地 HTTP API 按事件唤醒，不能仅在 Cursor 里提示“运行模型”。
- Cursor Agent 仅在一次性部署/调试/修复控制器时使用；验收之后日常观察、滚动、切换窗口、双向通知由 D:\LOCAL_AI\Watchdog 的本地运行时自行完成。禁止用定时唤醒 Cursor 远端付费模型冒充本地 AI 监工。
- GPT-6 只对 HUB 文件做业务审阅与发布，不承诺网页自行响应；本地 AI 的职责严格限于两个方向的固定“请查收 HUB”通知。不能让本地模型自行修改 BLACKBOX 或任意运行从 HUB 获取的 Shell 命令。

## 当前真实故障必须先解决
已核对实际报告 inbox/LOCAL_AI_TWO_WINDOW_HUB_NOTIFIER_PILOT_20261021_1913/REPORT.md：
- Cursor->GPT 仅有 UIA tree echo，**尚不能把文本存在控件树作为最终 SEND 验收**，需在真实会话消息历史看到已提交消息，发送前后两段不同证据。
- GPT->Cursor 为 FAIL：当前 UIA 找到的是 ChatGPT Work 输入框而非 Cursor Agent 输入框；测试通知出现过乱码（UTF-8/Windows编码链及错误 URL 尾部标点）。**禁止在未能唯一定位本地 Agent composer 时执行任何发送**。
- Browser MCP cursor-ide-browser Server not found；不能以此假定已恢复，也不得使用新 Playwright 登录态或读取 cookie。
- 前一个测试只有4次20秒、非正式180秒独立后台调度，也未验证12小时；不得以短测试代替长期稳定性。
- 两款模型此前已安装验证：Ollama D:\LOCAL_AI\Ollama，Models D:\LOCAL_AI\Models，Gemma4 tag gemma4:12b-it-q4_K_M，Qwen3 tag qwen3:14b-q4_K_M。不要重新下载安装。

## 一次性部署步骤（Cursor仅作为安装工程师）
1. 检查 D:\LOCAL_AI\Watchdog\hub_two_window_notifier_1913 中现有代码、定时器、UIA树、编码和送达证据；复用现有逻辑，不重复建第二套调度器。检查 Ollama 的本地 Gemma4 vision API 实际可被自己的控制器调用。
2. 制作/修复一个独立进程的 **Local AI Operator**：调用本地 Ollama Gemma4，输入脱敏 UIA 层级+按需截图，输出严格结构化允许动作；程序先验证目标窗口，再按白名单执行；运行后回读实际结果；模型输出不得变成自由任意点击、运行 shell 或敏感文件操作。
3. 两侧输入框定位必须以可重复的窗口/会话身份+控件条件为准。Cursor GUI Agent 的输入框无法唯一识别时立刻标 BLOCKED_G2C，可保留 HUB 通知队列，但不得将消息发送到 GPT 输入框。优先修复 UIA 和窗口识别，而非追求换更大的模型。
4. 中文统一 UTF-8：脚本源码、持久化、窗口发送、剪贴板/ValuePattern、日志和 GitHub URL 解析逐跳核验；Windows 控件经 Unicode API 发送，不能产生“GPT 宸插湪...”乱码；URL 独立字段不拼入中文句号。
5. 固定通知只允许两句：C2G「Cursor 已有新结果，请 GPT 查收 HUB inbox：<URL>」；G2C「GPT 已有新任务，请 Cursor 查收 HUB outbox/reviews：<URL>」。每次通知只引用由 GitHub 验证存在的具体文件；path+blob SHA+direction+message ID 去重，禁止回声循环。
6. GPT 网页未自动下滑时，Gemma可建议 SCROLL_BOTTOM，由控制器先识别正确聊天滚动区域再执行，截图并检查最新回复是否生成完毕；绝不抓取未完成的流式片段用于转发。
7. 利用 Windows Task Scheduler 或现有已启动调度器，保持独立于 Cursor Agent 的后台三分钟轮询/状态机；Cursor Agent 单轮结束后不影响。仅有新事件或状态模糊时调用 Gemma，按需卸载节约 RTX5080显存。Windows锁屏/休眠/GUI不可见时暂停 GUI 投递而不是盲发；HUB 队列继续保存。
8. 本次**只部署两窗口通知器**，不续跑之前已到期 BLACKBOX 业务盘点，不动 E:\BLACKBOX 原数据、文件、规则、R9 状态、登录密钥/付费配置。

## 必须实测后交付
A. 单独运行本地 Gemma4 API 决策，保存模型输入摘要与结构化输出证据（脱敏）；不能只在 Cursor Agent 内完成文字演示。
B. 用两个新独立 PILOT ID 各测试一次 C2G 和 G2C；对方实际目标会话可见**已发送的消息**，有真实送达证据；没找到 Cursor 输入框则G2C=BLOCKED，不能宣称 PASS。
C. 连续至少4轮真正180秒独立调度，证明不依赖当前 Cursor 聊天轮次、零重复、零回声；记录Windows计划任务历史、运行日志。十二小时可运行性必须之后用真实12h日志证明。
D. 尽量在测试安全检查点结束后，让 Cursor Agent 退出一次，验证独立运行时仍可巡检/调用本地Gemma，而无需 Cursor Agent 发新命令；不能因 GUI Agent关闭而冒充其界面还可投递。

## 回执
agents/chatgpt/inbox/LOCAL_AI_GEMMA_DIRECT_OPERATOR_HANDOFF_20261021/REPORT.md 与 STATUS.json，至少填：
LOCAL_GEMMA_API_RUN, OPERATOR_OUTSIDE_CURSOR_AGENT, CURSOR_WINDOW_LOCATED, GPT_WEB_WINDOW_LOCATED, GPT_SCROLL_VERIFIED, CURSOR_TO_GPT_DELIVERED, GPT_TO_CURSOR_DELIVERED, UTF8_END_TO_END, POLL_4x180S, NO_DUPLICATES, NO_ECHO, GUI_UNLOCK_REQUIREMENT, CURSOR_AGENT_INDEPENDENCE, LONG_RUN_12H, BLOCKERS。
未亲自实测标 UNVERIFIED/FAIL；确认本地程序独立运行并完成双向送达后才标 END_TO_END_PASS。
