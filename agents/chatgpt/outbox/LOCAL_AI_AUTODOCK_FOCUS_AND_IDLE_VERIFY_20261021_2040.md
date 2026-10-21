# ZHANGWEI｜继续2008：真实点击取焦，复用已排队HUB，独立验证
task_id: LOCAL_AI_AUTODOCK_FIX_FIRST_ZHANGWEI_20261021_2008
followup_id: LOCAL_AI_AUTODOCK_FOCUS_AND_IDLE_VERIFY_20261021_2040
execution_host: ZHANGWEI
previous_followup: LOCAL_AI_AUTODOCK_RICH_INPUT_FIX_20261021_2030
status: CONTINUE_IMPLEMENT_AND_TEST
DATA_ORGANIZATION: PAUSED_PENDING_AUTODOCK_TECH_ACCEPTANCE
NO_BLACKBOX_BUSINESS_WRITES: true

已读20:34 REPORT/STATUS、实际两向测试及新源码。
接受：占位/格式误判已核；Gemma在真实composer截图判断已运行；真实键盘HUB已能进入Agent。G2C目前FRONTEND_QUEUED，不是历史送达；C2G SetFocus后仍停Agent，没有键入，阻塞正确。
不重复安装、探针或已排队消息。当前剩余是实际取焦、消息提交/异步验收及后台连接。

## 1. 不再用同一SetFocus失败重复试
GPT交了一个可选的单次真实点击辅助：
agents/chatgpt/reviews/LOCAL_AI_AUTODOCK_FOCUS_CLICK_REVIEW_20261021_2040/uia_click_bound_composer.ps1
SHA256 197afbb2dab26fcaecb85f1f536a4e3afceb76cf21c39c89fb2d369fc18eeaa1
默认只检查；-FocusClick且LOCAL_AI_SEND_ARMED=1时，只对实时UIA命中、无遮挡、属于唯一正确Cursor窗口的composer点一下。没有键入、清空、Enter或提交。GPT仅静态检查，Windows/PInvoke未跑，本机先parse及检查再试，必要兼容修正留diff/SHA。
它使用当前GetClickablePoint+WindowFromPoint/GetAncestor+UIA.FromPoint校验，不用固定旧屏幕坐标，不点击模型/语音按钮。若命中无法证明，保留BLOCKED，不改为任意坐标点击。
将实际点框取焦接入现有controller；点击后重新获取控件与焦点、必要时本地Gemma检查caret/选中框，确认正确区域。SetFocus只是API请求，不是实际焦点成功的证据。

## 2. 修当前源码的两个明确逻辑问题
- uia_type_hub_once.ps1把foreground HWND与runtime ID的数字子串做相等/like比较，这是不同命名空间，必须删除。仅以真正窗口句柄（必要时GetAncestor归一）核前台；runtime ID只用于UIA元素/祖先关系。
- 已经实测Agent TextPattern对真实HUB仍返回格式空白，因此“typed后必须TextPattern精确HUB才允许提交”会永久堵住工作路径。把这次本地Gemma的实际输入截图验证接进同一个受控执行流程，不要一次先报失败，再由另一个脚本手工Enter绕过去。
同一个事件事务应为：两pane前状态→唯一正确composer真实取焦→HUB键入→实际渲染确认只在目标框出现HUB且另一框未变→提交一次→只读验收。Value/TextPattern不可靠的字段标PROVIDER_UNRELIABLE；不能又当空白自动重键HUB。
如果点击后UIA FocusedElement仍不变，先记录UIA与原生命中/真实caret矛盾。只有唯一目标原生命中、真实前台和新鲜局部视觉都一致，才可做一次单纯HUB键入验证；提交必须再核双pane结果。不因模型一句“正确”省略这些实际证据。任何串窗/歧义立即停止，不提交。
未知用户草稿仍保留。只可清理由当前事件明确新键入、尚未提交的自身HUB，不删历史。

## 3. G2C不能一直等待正在运行的自己结束
当前已经有1条排队HUB，不要再键入或Enter第二次，也不要删除它。
安排一个独立、只读、有限时的验收例程后，正常结束本轮Cursor部署Agent响应，让现有排队HUB有机会转入真实会话并被处理。例程复用本地运行时，不新增永久服务，不用反复唤醒云端模型来等它自己空闲。
跟踪同一事件：queued→进入目标会话/处理，不把排队条当已提交历史，也不为“看不到历史”重发。把实际是否消费写回证据；超时列真实状态。
正常运行可在Agent Busy时仅保留HUB事件，等空闲再投递；若已投递到前端队列，就保持QUEUED状态至消费，不重复通知。

## 4. 直接推进完整闭环
C2G修好后提交一次HUB到正确GPT原会话；G2C复用现有那一条，不再制造新测试。
两向通过后继续原2018远端main收件/持久队列/Operator实际调用/同一计划任务独立运行/4轮180秒实测。正常调度不能只有本地mirror扫描或QUEUE_ONLY。
Gemma当前已有真实视觉调用，不再重复做无关模型自测。12h仍未验证不PASS。数据整理依旧暂停，不动BLACKBOX/R9。
回报仍写2008目录，交当前实际输入/提交/排队消费状态、取焦代码与证据。不要只回一份“SetFocus还是失败”的摘要；在已有授权内完成上述已给出的实际点击与异步验证路径，无需用户另批准。
