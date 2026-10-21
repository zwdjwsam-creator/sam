# ZHANGWEI｜代码已审：补真实发送分支、控件绑定与远端收件
task_id: LOCAL_AI_AUTODOCK_FIX_FIRST_ZHANGWEI_20261021_2008
followup_id: LOCAL_AI_AUTODOCK_BOUND_CONTROL_FIX_20261021_2018
execution_host: ZHANGWEI
status: IMPLEMENT_CONCRETE_FIXES_CONTINUE
DATA_ORGANIZATION: PAUSED_PENDING_AUTODOCK_TECH_ACCEPTANCE
NO_BLACKBOX_BUSINESS_WRITES: true

已读20:09 REPORT/STATUS、source实码、uia_bind_targets.json。接受QUEUE_ONLY、ASCII HUB门控和实际源码上传；两边还未发送，不验收。不是模型未装好，也不需要再下载模型。
当前窗口pid43324/hwnd1247992只是快照，不可跨重启硬编码。已见Agent class=aislash-editor-input、Name为空；GPT class=ProseMirror、Name=使用ChatGPT Work；terminal=xterm-helper-textarea。

## 已定位的实际缺口
1. uia_bind_targets.ps1仅按Name匹配Agent，所以漏掉已发现的空Name ais lash输入框。local_ai_operator.agent_composer_unique把缓存+新names混合，只检查len(non_gpt)>=1，既不是唯一也没用真实class。
2. local_ai_operator.decide_and_act第231行只有CURSOR_TO_GPT执行发送。GPT_TO_CURSOR即使将来判唯一，也没有真正调用Agent发送器的分支。
3. TYPE_FIXED_NOTICE/SEND/VERIFY_DELIVERY全部进入同一发送脚本；VERIFY_DELIVERY会再次写入/Enter，不是只读验证，存在重发路径。
4. fixed消息已改HUB，但Needle仍默认报告文件名；发送HUB后搜索文件名不能证明本次消息送达。脚本又在整个Cursor窗口找Text，会把另一个聊天/草稿后代当成功。
5. uia_send_agent还保留“最后一个非GPT Edit”回退；uia_send_gpt匹配Message/prompt过宽。脚本吞掉SetFocus异常后继续全局SendWait，门控一旦打开仍可串窗。
6. 当前计划任务只运行run_queue_only.py；它只读E盘本地mirror，无远端刷新，也不调用Operator。是否有别的独立同步器尚无证据，不能说已经每3分钟读GitHub并自动通知。
7. 队列脚本先写SEEN再写QUEUE；中途异常可把未入队事件标seen。IGNORE_PARTS对两个方向一概过滤LOCAL_AI_*，还会吞掉GPT发出的合法通知器修复工单。

## 按以下顺序修，不停在“候选找到”
A. 先只读采集真实控件链：
GPT已交 agents/chatgpt/reviews/LOCAL_AI_AUTODOCK_CODE_REVIEW_20261021_2018/uia_bound_controls_probe.ps1
SHA256 be36e7ab5284d1db589dba45bd9d6c4c2420f1fecb30d5e911b17debc96ffb17。
它按class列候选、运行时ID、祖先及邻近按钮/支持pattern，不改输入/焦点/剪贴板，不点击或保存文件。仅做了静态无动作检查，Windows/PowerShell尚未运行，需本机先语法检查再运行；不把脚本存在当测试通过。
放入现有D盘工具目录运行，将JSON写到本任务evidence，再上传脱敏结果。必要时只修这个隔离探针兼容性，留新SHA。目标是定位每个composer所属会话/消息区及发送按钮；class一条命中仍只是候选。
不用让我再发一条命令才继续：结合真实结果，马上修绑定与发送器。直接复用已有UIA，不新建调度器/模型。

B. 发送与验证分开：
- 每次用新鲜UIA实例核唯一目标、所属窗口/会话，明确排除terminal与另一个聊天；不用缓存Name判唯一或任意Edit兜底。
- 先找到同会话发送按钮，若支持InvokePattern优先验证后调用。不是一律禁止键盘Enter：按钮不可用时，只有在目标输入框/前台窗口/实际FocusedElement归属都核对成功、消息及会话读回正确时，才允许单次受控键盘提交。焦点失败/歧义即阻塞，不catch后继续盲发。
- 背景调度继续QUEUE_ONLY；绑定明确后可在独立的一次性测试子进程内arm单次事件，不设全局ARM，不重复开启旧发送路径。
- 两个方向都补实际发送分支；按状态执行“候选→输入→提交一次→只读验证”。VERIFY分支绝不写输入或Enter。不确定提交结果就DELIVERY_UNCERTAIN并先查目标历史，不自动重发。
- 验证目标聊天消息区中新增的已提交用户消息HUB，关联事件ID及发送前后快照；不再用文件名Needle，也不能把窗口任意Text或旧HUB存在当成功。不覆盖用户草稿。
- 目前HUB正文无需携带测试ID；用日志/证据关联两个独立测试事件即可。Gemma只做已有本地UI识别/决策辅助，保存实际API→决策→动作链，不能让远端Cursor替它每3分钟值守。

C. 只有两向单次测试通过，才接回正常自动调度：
- 在既有任务每轮先用现有身份确认远端main的事件；如复用mirror同步，要把同步成功和新commit/SHA纳入独立调度证据，不能依靠当前Agent或17:09已到期巡视继续pull。不重置token，不读/打印凭据。
- 持久队列与已送达记录区分：先原子保存队列再保存seen，或最小地合并原子state；失败/重启不能丢事件，已送达不重发。旧状态格式/散列改变时保留历史，做一次明确baseline迁移，防老报告集体刷屏。
- 过滤按方向与事件类型：inbox的通知器自身日志/ACK/心跳不触发C2G；outbox/reviews合法修复指令不能因LOCAL_AI前缀被一概吞掉。显式排除非行动收件ACK及旧pilot，保持无回声。
- 计划任务Action接到“取远端事件→入队→按需本地Operator→验证→记录”的实际入口；保留单实例，不新增平行任务。4轮真实180秒再做一次，含无新事件静默/同事件重复/忙或GUI不可用保留队列。
- 4轮通过交功能验收；12小时保持PENDING，等实际日志，不提前宣称。

本机在这份任务授权内完成代码/小回归及单次发送验证，不需要用户再次批准。若确有不可访问控件，交实际控件/失败API及最小缺口，不用“还没写代码”当平台能力阻塞。
下一检查点先交探针JSON、修复源码diff/SHA、两侧真实测试结果或具体失败，再交独立调度证据；不要只再报候选class或计划任务Ready。
报告仍写原2008目录，更新INBOX_FOR_CHATGPT。数据整理继续暂停；禁止恢复1155、修改BLACKBOX/R9/业务规则。既有有效修复接续，不重装/扩服务。
