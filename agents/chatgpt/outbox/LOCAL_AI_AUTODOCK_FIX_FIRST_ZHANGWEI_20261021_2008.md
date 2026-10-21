# ZHANGWEI｜当前唯一优先事项：修好本地自动对接，数据整理暂停
task_id: LOCAL_AI_AUTODOCK_FIX_FIRST_ZHANGWEI_20261021_2008
execution_host: ZHANGWEI
status: READY_IMPLEMENT_AND_VERIFY
priority: OWNER_LATEST_LOCAL_AI_FIRST_DATA_LATER
supersedes_notification_templates: LOCAL_AI_TWO_WINDOW_HUB_NOTIFIER_PILOT_20261021_1913; LOCAL_AI_GEMMA_DIRECT_OPERATOR_HANDOFF_20261021
functional_contract: agents/chatgpt/outbox/LOCAL_AI_HUB_TWO_SIGNAL_ONLY_20261021.md
DATA_ORGANIZATION: PAUSED_PENDING_AUTODOCK_TECH_ACCEPTANCE
NO_BLACKBOX_BUSINESS_WRITES: true

## 用户最新顺序
先解决本地模型部署/自动对接，完成后再做数据整理。当前不恢复1155或其它数据扫描/修表/回测/下载；保存已有结果。模型/通知器修复使用已有授权，不要再等用户逐步确认。
已核HUB：
- 18:57安装回执：Gemma4 12B vision、Qwen3 14B text、卸载显存测试通过；
- 20:02/20:03实际运行报告：Gemma API已调用，计划任务已启用，但C2G有误发到Agent及输入框残留；G2C无法唯一定位Agent；4x180秒未完成，END_TO_END_PASS=false。
因此不重新下载模型，不换模型，不新建第二套服务。修已有 D:\LOCAL_AI\Watchdog\hub_two_window_notifier_1913。

## 立即顺序执行
1. 先使现有调度器进入QUEUE_ONLY：保留HUB读取/持久化/日志，暂不对无法确认的两侧输入框执行自动输入/Enter。误发已实际发生，不能让3分钟任务继续重试旧盲发路径。保留原计划任务，单实例；只清理由本程序误填且确认未提交的自身测试草稿，不删用户草稿/历史消息。
2. 一次性工程修复：
   - 读实际local_ai_operator.py、run_pilot_1913.py及UIA发送脚本/调度配置，核计划任务Action确实进入本地Operator，而非仍调用旧pilot盲发逻辑。Cursor远端Agent只做本次工程修复，不承担每3分钟日常值守。
   - 用当前真实窗口/UIA树及已有Gemma按需截图辅助，分别绑定Cursor BLACKBOX原Agent会话和内嵌GPT《接管迁移核验》。窗口标题或“使用ChatGPT Work”标签本身不足以证明输入框归属。记录进程/窗口句柄、父子控件/会话身份与输入框，确保目标不会同时匹配两个界面。
   - 模型输出只是受限动作建议；控制器在执行前重新核目标及焦点归属，窗口/会话变化就阻塞并排队。找不到唯一Agent输入框则继续只读定位，不能在GPT框试发反向消息；禁止全局Ctrl+V/Enter盲投。
   - 正常输入严格为ASCII HUB，不发中文句子/URL/任务正文。正确会话出现新提交的用户消息HUB才记成功；输入框值、ControlType.Text回显、剪贴板及Gemma自述均不足。若结果不确定，标DELIVERY_UNCERTAIN并先查历史，不自动再次Enter。
   - GPT页面需要时滚正确聊天区域到底，等待生成/发送状态可用。用户正在写草稿或界面忙则保留队列。
   - 使用既有UIA/官方Browser及已登录会话，不另造浏览器登录态。若经实测现有界面无法受控访问，上传具体控件证据和失败点，明确BLOCKED，不以增加模型/服务/提示词掩盖。
3. 事件与上传修正：
   - 先push具体报告，远端main同路径读回及blob SHA确认后才入投递队列。此前C2G_GEMMA_2000路径多次404，现有实际文件为C2G_GEMMA_2004；修错误指针，不再通知不存在文件。
   - path+SHA+direction/task_id持久去重；忽略测试、ACK/CLAIM、心跳、通知器自身日志及收件回执，避免通知递归。测试模式只显式放行本次两个唯一测试事件，正常模式不处理旧pilot。
   - 当前通知器技术报告可按“阶段成果一次汇总”显式投递一次，不能因每轮心跳/状态更新时间重复唤醒两边。

## 实测与交付（修好一侧可测，双方通过后再恢复正常自动发送）
- 两个独立测试事件，各用HUB作为实际消息；事件ID在日志/证据中关联，不拼进发送文字。留发送前后目标身份、消息历史变化、失败/重试记录，确认无串窗。
- 验证实际本地Gemma API决策以及受限控制器动作；不是在Cursor文字里模拟Gemma。模型已安装，不重装。
- 然后开启既有独立调度，至少连续4轮真实180秒，留每轮时间、是否发现事件、是否投递/静默/阻塞、同一事件不重发。无需当前Cursor Agent持续Running；GUI窗口仍须可见可用。锁屏/休眠时保持排队，恢复后再验证投递。
- 两向真实送达+独立4轮通过可提交AUTODOCK_FUNCTIONAL_READY；12小时稳定性单列PENDING，不能提前PASS，也不用为了提交功能验收空等12小时。GPT技术复核通过后再另发数据整理续作，不凭“计划任务启用”自行恢复业务。

本轮先上传当前实际实现源码（上述.py/.ps1、去秘密配置、计划任务Action）和最小脱敏控件/发送证据到HUB附件，便于我直接审代码；继续修复，无需为上传附件停工等审。不要上传token/凭据或私人聊天全文。
报告固定目录：
agents/chatgpt/inbox/LOCAL_AI_AUTODOCK_FIX_FIRST_ZHANGWEI_20261021_2008/
REPORT.md、STATUS.json、source/、必要脱敏evidence/。
STATUS区分MODELS_READY、LOCAL_API、TARGET_BINDING_C2G/G2C、SENT_C2G/G2C、QUEUE_ONLY、SCHEDULER_ACTION、POLL_4x180S、NO_DUPLICATES/NO_ECHO、LONG_RUN_12H、DATA_ORGANIZATION_PAUSED。
更新INBOX_FOR_CHATGPT指向这次真实报告，不能还停18:57模型安装PASS。

主机仅ZHANGWEI，代码/运行文件在D:\LOCAL_AI，业务数据/R9/规则不改。此单覆盖通知器修复，不恢复已过期业务工单，不另建模型部署或多个监控器。
