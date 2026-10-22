# ZHANGWEI｜用户要求加速：一轮完成自动对接安装，不再逐探针等查收
task_id: LOCAL_AI_AUTODOCK_FIX_FIRST_ZHANGWEI_20261021_2008
followup_id: LOCAL_AI_AUTODOCK_FINISH_NOW_ZHANGWEI_20261022_1145
execution_host: ZHANGWEI
priority: OWNER_SPEED_UP_FINISH_DEPLOYMENT
status: FINISH_IMPLEMENTATION_AND_INSTALL_IN_ONE_RUN
sole_execution_entry: this_instruction
DATA_ORGANIZATION: PAUSED_PENDING_AUTODOCK_TECH_ACCEPTANCE
NO_BLACKBOX_BUSINESS_WRITES: true
completion_package: agents/chatgpt/reviews/LOCAL_AI_AUTODOCK_FINISH_PACKAGE_20261022_1145

最新HUB仍停昨晚20:44。当前已能真实点击GPT框、键入HUB；Agent那条排队标志后来消失，但没有可归因送达记录。计划任务仍QUEUE_ONLY。不得说已经自动运行。
用户要求加快。旧2008/2018/2030/2040仅作为已有实现/证据参考，不再按旧工单一条条领取/等待审阅。当前轮连续做完接线、安装、双向实发和正常调度实测；只有完整结果或真正平台阻塞才结束，不要修一个局部脚本就停。
首轮以30分钟内交可用结果或明确一个实际阻塞为目标；不是到点强杀，也不生成30分钟授权到期。无需用户再批准普通改码/本机UI试验。

## 已交可运行收件/状态代码，直接用
GPT包：agents/chatgpt/reviews/LOCAL_AI_AUTODOCK_FINISH_PACKAGE_20261022_1145
- run_autodock_once.py：真实git fetch origin main→不可变远端blob元数据→原子合并seen+queue→本地adapter→记录；保留事件、同方向合并；无事件不调模型；不确定只VERIFY，不重发。
- test_runtime.py：12项隔离测试通过，含真实本地bare Git fetch（不checkout/覆盖草稿）、重启/去重/失败/过滤/显式单次测试。
- README/VALIDATION：安装步骤、adapter接口和实测局限。Windows/GUI/GitHub凭据尚需本机验证，不能把12项当部署验收。
下载到既有D:\LOCAL_AI\Watchdog\hub_two_window_notifier_1913，不另建第二套服务。保持旧日志/state备份；用新state一次baseline，不回放历史通知。既有HUB Git工作树从当前上传脚本确定，不在业务树git init，不输出remote URL/密钥。
本机先跑12项，再按README接现有GUI功能即可，不另写一套远端扫描器。若确有本机不兼容，仅修这个包，留diff/SHA，授权内继续。

## 剩下只把已有UI动作接成一个完整adapter
实现同目录ui_delivery_adapter.py的handle(event, mode)，用现有脚本、真实本地Gemma与已成功点击/键入路径，不重装模型。接口见README：
SUBMIT完整执行一次“核会话/空闲→取焦→HUB→提交→验证”；VERIFY绝不输入或Enter。
DEFERRED仅表示没有任何键入/提交；已键入/可能发送必须QUEUED或UNCERTAIN，避免再打一次。
别再停在TYPED_AWAITING_VISUAL，也不要靠独立手动Enter脚本绕过主流程；真正的视觉核验/提交分支必须在同一可执行流程里。

1. 精确目标：核本地配置中的真实GPT原会话URL/标题“接管迁移核验”，以及BLACKBOX原Agent会话。ProseMirror只是组件class，不能独自证明是正确会话；当前pane若不对，用既有已登录会话切回正确原页，不另造登录profile。
2. GPT取焦：复用昨晚已实测成功的点击辅助；前台只比真实HWND/GetAncestor，UIA runtime ID只比UIA元素。用已部署Gemma核局部真实渲染，键入仅ASCII HUB，另一框不能变化。保护用户真实草稿。
3. 提交：键入后新鲜读取实际发送按钮（空框的语音按钮会变化），优先正确按钮实际点击/调用；若走Enter须本次实际焦点确认。已有两次“Enter清空但看不到新bubble”的不确定结果，不再反复相同盲试。
4. 检查最新消息：需要把正确聊天消息区域滚到底，确认生成/忙状态以及最新用户HUB。当前仅看composer上方旧助手回复不能确认失败，先补真正滚底/最新轮次读取；不要把SCROLL动作只记进日志而不实现。不在输入框用Ctrl+End冒充聊天区域滚底。
5. 旧测试归档INCONCLUSIVE/QUEUED_CONSUMPTION_UNPROVEN，不自动重发它们，也不继续无期限追昨晚队列。当前只做一对新唯一测试事件，各HUB一次，时间/事件ID写本地日志，不拼进消息正文。发送前远端报告必须已读回。
6. Agent忙时先DEFERRED；若前端已接收排队一次，则QUEUED并只VERIFY消费，不能再键HUB。不要让当前部署Agent一直Running而要求测试“等自己空闲”。提前安排既有独立运行时的有限验证，在本轮正常结束后核同一消息；不另建永久监工。

## 直接安装并完成整轮验证
按README：
A. 初始化新runtime baseline，旧记录保留。把现有同一个计划任务Action接到run_autodock_once.py +实际--repo +--adapter +--send。保留180秒和IgnoreNew；旧queue-only/pilot不能并行发。
B. 两个新测试在本机单次命令用--test-event显式放行真实远端文件，生产Action绝不能带--test-event。同一path/blob只放行一次，避免自身报告循环。
C. 两侧实际原会话出现已提交/已消费的HUB，各有前后证据。随后至少4轮真实180秒，留远端commit、是否新事件、GUI动作/静默、无重复/回声。四轮含起点总跨度至少540秒；不拿20秒轮询冒充。
D. 两向+四轮通过交AUTODOCK_FUNCTIONAL_READY，12小时另记PENDING，不为交付空等12h。此时才请GPT技术确认；数据整理仍暂停，待下一条业务续作。

若现有界面有真实平台限制，在同一路径重复两次仍无进展就切换本任务已授权的实际点击/视觉提交办法；禁止把换模型、扩服务、更多schema/探针当修复进展。
若确实无法受控操作，明确唯一失败API/当前截图控件证据/已做的具体方法；不要再交一份“组件找到了、程序未接线”的报告。

## 最终交付（同一2008目录）
REPORT/STATUS +最终adapter/运行入口/去秘密配置/任务Action +两向证据+四轮日志。INBOX_FOR_CHATGPT指向真实最新结果。
明确当前实际PID/任务状态、最后远端收件时间、下次运行、失败是否保留队列。不得把脚本存在或模型API返回当部署通过。
本地例行由D盘进程+Ollama执行；Cursor云端Agent只负责本次施工，不用云端每3分钟值守。业务BLACKBOX/R9/规则/数据整理全部保持暂停，不删改业务。
