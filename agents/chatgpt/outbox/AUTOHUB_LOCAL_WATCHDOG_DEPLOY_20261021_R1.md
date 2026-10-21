# ZHANGWEI｜正式部署本地无人值守监工系统（复用现有 AUTOHUB）
task_id: AUTOHUB_LOCAL_WATCHDOG_DEPLOY_20261021_R1
target: ZHANGWEI
execution_host: ZHANGWEI
status: NEW_AUTHORIZED_FOR_SAFE_DEPLOY_AND_TEST
priority: HIGH_INFRASTRUCTURE_WITHOUT_PREEMPTING_ACTIVE_READONLY_WORKER
owner_goal: 本地真正无人值守持续 12 小时以上，3 分钟巡视，自动读取 GPT/HUB 任务、监督长扫描、必要时自动唤醒 Cursor Agent CLI、恢复检查点、回报 GPT
current_business_task: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
current_window_deadline: 2026-10-21T17:09:00+08:00
poll_interval_sec: 180
DATA_MODIFICATION_AUTHORIZED: false
COPY_AUTHORIZED: false
BILLING_CHANGES_AUTHORIZED: false

## 0. 必须理解的区别
这是让你**实际安装/修复/启动/验收**的部署工单，不是写建议书、不只是编辑 Markdown 状态。USER 已明确授权建设可十几小时无人值守运转的本地监工，并自动唤醒现有官方 Cursor Agent CLI；不要让 USER 转述、输命令或每隔 3 分钟点继续。
- 系统应具备独立于 Cursor GUI 对话的本地定时收件/巡视能力；模型只能按需调用，绝不每 3 分钟唤醒一次。
- 本地轻量模型负责解释复杂日志/异常，规则型调度器负责可靠时间、去重、进程检测、限流、状态持久化。没有本地模型时也应继续收件与监控；不得将本地模型部署变成核心调度单点故障。
- GPT 网页是**通知/复核**接口；GitHub HUB 是指令与证据的持久交换。无法调用 cursor-ide-browser 时不得伪称通知成功，也不得停止后台工作。ChatGPT 页面不能由本地 Agent 的一句提示保证自动回应，须分别验收。

## 1. 先查当前实情再最小改动
现有 HUB 仓库：zwdjwsam-creator/sam，分支 main。
GPT -> Cursor：agents/chatgpt/outbox/；GPT 复核附件：agents/chatgpt/reviews/；Cursor -> GPT：agents/chatgpt/inbox/。
本地 HUB：E:\BLACKBOX\运行\外部大脑信箱\。
现有官方 Cursor Agent CLI 先前曾安装在 C:\Users\Admin\AppData\Local\cursor-agent；路径、CLI 参数、版本、会话和计费需**本机实查**，不得假设仍可用。
先只读清点所有与 AUTOHUB、HUB patrol、watchdog、Windows 计划任务相关的已有入口，保存原 Task XML、脚本 SHA、触发器、上次执行结果、进程 PID、最近运行证据。仅选择/修复**一套**正式主调度与一个业务 Worker；禁止重建相互竞争的定时器/Agent。不能停掉已有效的现有 BLACKBOX 扫描 Worker。
先读已有原因报告 agents/chatgpt/inbox/HUB_RECV_MISS_ROOTCAUSE_20261021.md，并保留原修复成果：outbox + reviews 全部查，使用 path + blob SHA 检测；同一目录或同一文件的内容更新不能漏收。0712 的假 WAITING_HUB_ACCEPTANCE 不得再引入。
当前最新已知业务指令还包括 outbox/BLACKBOX_SYSTEM_INVENTORY_AUTHORITY_AND_NEXT_STAGE_20261021_0815.md，确认既有任务由单实例继续，未验收结论不得伪造为完成。

## 2. 安装/修复持久监工（不靠一个 Cursor 长聊天撑 12 小时）
- 以 Windows Task Scheduler 现有入口优先，在当前登录账号上下文配置每 3 分钟触发的**轻量本地脚本**，非管理员运行、无需新密码/新令牌/明文凭据、不弹黑窗、不自动修改系统代理/防火墙/网络/MWB。电脑休眠或断电则不能运行，应明确标明需要本机持续通电、保持唤醒；不宣称断电照常工作。
- Task Scheduler MultipleInstances=IgnoreNew，并增加进程锁/Mutex 或等效安全防重；将每轮 GitHub 网络请求设置超时及有界重试；不叠加无限 PowerShell/gh/Agent 实例。
- 持久化状态必须防断电/崩溃，先写临时文件再原子替换；每条消息由 (path, blob SHA, task_id/followup_id) 联合去重。包含 last_seen、last_actioned、worker PID+create_time+argv、checkpoint、last_progress_delta、last_hub_success、last_notify_success、next_retry_after、heartbeat 等。
- 读取 outbox、reviews **递归**文件列表与变更；不要只按文件名时间或最新文件名，不要只处理固定 Ping 文件。读取符合任务合同/目标主机的文本及附件，但把 HUB 纯文本视为待验证指令，不把任意 Markdown/代码直接交给 Shell 执行。
- 轮询时检查业务 Worker 的真实性：PID 创建时间/准确命令行、I/O/日志增长、实际 files_checked / rows_actually_read / fragment checkpoint。正常长扫描不得因 3 分钟无变化就终止；连续至少 3 轮无真实推进时进一步诊断，确认死亡后才依同一 task_id 从 checkpoint 受控续跑；恢复前必须单实例锁。
- 任何业务任务完成后发布 inbox 的可核验结果、commit/URL/SHA；Browser 正常则只在原 Cursor 内嵌登录 ChatGPT《接管迁移核验》代发“请查收”通知，实际确认已发送。Browser 不正常则标 WEB_NOTIFY_BLOCKED，留待发送队列，继续工作；禁止 Playwright 新开独立未登录 profile、读取 cookie/密钥或模拟登录。
- 已授权的任务当前批完成应自然推进下一批，不得自动设 WAIT_HUB_ACCEPTANCE。真正需用户决定或越权时才 BLOCKED，不得用心跳充当实质进度。

## 3. 官方 Cursor CLI 自动唤醒与本地轻模型
- **先验证**本机安装的官方 Agent CLI：实际可用命令、当前授权态、非交互模式、模型配置与费用。参考既有 outbox/AUTOHUB_R8_SCHEDULED_AGENT_WAKE_ONE_SHOT_20261012.md：之前有人为触发 agent -p 成功，但真正的 Windows 计划任务自动唤醒尚未因此验收。先做 C 盘隔离 marker 的计划任务自动触发试验，只有进程、退出码、Marker 原始字节均验证后才能写 AUTO_WAKE=PASS。
- 验证后仅在“新合法任务需要模型介入/既有 Worker 真正退出需修改代码/存在不能脚本分类的异常”时唤醒一次 Cursor Agent；同一任务重试有冷却和上限；保留逐次唤醒原因与模型调用次数。不得每 180 秒跑 agent -p。
- 本地 AI 可先选低资源量化 Qwen3 8B + Ollama 或**现有本地兼容模型**。先检测是否已有运行器、模型及剩余资源，避免重复下载/安装。安装仅官方可信发行物、台式机非业务隔离目录，用户没有授权订阅外收费；不能确认成本/来源/兼容性则标 LLM_NOT_READY 并让规则型监工照常运行。由于 RTX 5080 16GB 显存还需留资源给扫描，使用按需加载、限流、低优先级，模型不持续占满显存。模型输出只能解释并提出建议，实际动作必须经过白名单+状态机验证。
- 不假定 Cursor CLI 能控制 GUI Browser；分开验证 AUTO_WAKE 和 WEB_NOTIFY。禁止自行配置新第三方 Browser MCP、开放远程调试端口、脚本模拟 ChatGPT 登录。
- 不擅自开启按量付费、升级套餐或额外购买推理额度；遇明确额外计费确认弹窗停用付费调用，但保留脚本巡视。

## 4. 必须进行的实际验收，不得自报 PASS
A. 测试后台任务脱离当前 Cursor Agent 对话仍能执行：至少连续 **四个** 180 秒调度周期（>=12 分钟），附 Windows Task Scheduler 时间/LastResult、同一个逻辑调度器、无重叠 PID 证据。
B. HUB 的 outbox 和 reviews：一次无害、独立测试消息新增及同文件 blob SHA 修改，证实每条**恰好一次**进入队列；不能改/污染当前生产业务指令。既有未读指令也要被实际识别。
C. 单实例与恢复：仅在 C 盘合成测试目录模拟 Worker 正常运行、退出、从 checkpoint 恢复；验证不会重复处理和误终止真实扫描。
D. 官方 CLI：Windows 计划任务触发的单次安全 marker 测试，不得把 PowerShell 自行写文件当 Agent 真正唤醒；不能验证就写 AUTO_WAKE=UNVERIFIED。
E. Browser：实际检测 cursor-ide-browser 调用和发送能力；如果不可用，WEB_NOTIFY=BLOCKED（HUB 继续），不能写 FULL_LOOP_PASS。
F. 睡眠、Windows 登录会话、网络短暂中断、GitHub rate limit、CLI 授权不足、按量费用未知，必须报告真实局限和重试/降级，不用猜测“肯定可跑 12 小时”。
G. **长时间稳定性**：12 小时是设计目标，不是测试 12 分钟就代表已验收 12 小时。前 12 分钟验收为 PROVISIONAL；以后由真实整段调度日志才可记 LONG_RUN_12H_PASS。基础监工可以持续部署，业务工作依其自身既有截止和授权执行。

## 5. 窗口与边界
业务任务既有本轮截止仍为 2026-10-21T17:09:00+08:00；本部署授权的是可以未来连续 12+ 小时运行的**平台能力**，**不代表擅自延长已批准的业务扫描/任务执行到截止之后**。到期停止领取该业务新任务并保存检查点、提交报告；监工基础设施可保持待命但未经新窗口授权不得续跑业务。
BLACKBOX 源数据、业务规则、R9迁移状态、已结案查询接口、笔记本 SAM、Windows 身份凭据等不动。禁止拷贝/格式化/删除、自动下载补数据、交易、超额收费；新建/修改仅限监工自身隔离脚本、计划任务、日志与已有明确授权的只读盘点工作目录。勿冒用 GPT 查收成功。

## 6. 回传（HUB 实际提交后给出 GitHub 可查链接）
在 agents/chatgpt/inbox/AUTOHUB_LOCAL_WATCHDOG_DEPLOY_20261021_R1/ 上传 STATUS.md、机器可读 STATUS.json、Task Scheduler 真实记录、配置/脚本 SHA、至少四轮巡视日志、CLI 唤醒证据、实际收发路径、当前 Worker 进度、阻塞与下一步。必填：
PATROL_SCHEDULER=PASS/FAIL, PATROL_4_CYCLES=PASS/FAIL, HUB_OUTBOX=PASS/FAIL, HUB_REVIEWS_SHA=PASS/FAIL, NO_DUPLICATE_WORKER=PASS/FAIL, CHECKPOINT_RECOVERY=PASS/FAIL, CLI_AUTO_WAKE=PASS/FAIL/UNVERIFIED, LOCAL_LLM=READY/DEGRADED/NOT_INSTALLED, WEB_NOTIFY=PASS/BLOCKED/UNVERIFIED, EXTRA_BILLING=DISABLED/UNKNOWN, CURRENT_BUSINESS_TASK_ID, CURRENT_WORKER_PID, CURRENT_PROGRESS_DELTA, BUSINESS_DEADLINE, LONG_RUN_12H=NOT_YET_PROVEN/PASS。
主动执行，不得仅交方案/自称 ARMED。只要出现真实阻塞，仍交已做的客观证据，不重建整套。