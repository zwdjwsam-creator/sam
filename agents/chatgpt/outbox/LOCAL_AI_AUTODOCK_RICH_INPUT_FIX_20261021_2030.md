# ZHANGWEI｜继续2008：核真实草稿，改用受控真实输入事件
task_id: LOCAL_AI_AUTODOCK_FIX_FIRST_ZHANGWEI_20261021_2008
followup_id: LOCAL_AI_AUTODOCK_RICH_INPUT_FIX_20261021_2030
execution_host: ZHANGWEI
status: CONTINUE_IMPLEMENT_AND_TEST
previous_followup: LOCAL_AI_AUTODOCK_BOUND_CONTROL_FIX_20261021_2018
DATA_ORGANIZATION: PAUSED_PENDING_AUTODOCK_TECH_ACCEPTANCE
NO_BLACKBOX_BUSINESS_WRITES: true

已读20:23检查点、两向实际失败证据、uia_send_hub_once.ps1及Operator/queue更新。
接受：class候选分开、G2C实际分支已补、Verify不再调用Send、queue先原子保存再seen、outbox修复工单不再按LOCAL_AI一概丢弃。
不验收：C2G被draft_len16拦截，G2C SetValue后只读到1字符，两侧未发。后台保持QUEUE_ONLY；不恢复数据整理，不重装模型。

## 当前要解决的是富文本输入，不是再找模型
只用ValuePattern.Current.Value作为草稿/写入成功的唯一依据，尚未被本机证明可靠。
G2C的1字符可能是换行/格式字符，也可能是写入未生效；C2G的16字符可能是真草稿，也可能涉及占位文本。GPT可访问Name“使用 ChatGPT Work”本身长度15，+换行恰为16，这只是待证假设，不能据此清空用户输入。
两框均提供TextPattern，可与ValuePattern、实际渲染交叉核。

1. 先运行GPT提供的只读诊断：
agents/chatgpt/reviews/LOCAL_AI_AUTODOCK_RICH_INPUT_REVIEW_20261021_2030/uia_composer_value_probe.ps1
SHA256 cf2bb6c91dff5cea8d3279704176aebe249ef6f406de13dd3d82f0de6d9bb7ea。
输出两provider的长度、字符类别、是否仅空白/格式、是否等于可访问Name、是否确为HUB，不上传未知草稿正文。仅静态检查过，Windows需本机先parse再跑；写D盘evidence后上传。
需要时让已部署Gemma看当前composer小区域的真实截图，验证有无可见草稿；保留本地API输入摘要/输出，不上传私人聊天全文。不要继续只让模型做NOOP合成自测。

2. 根据真实结果继续输入修复，不等下一命令：
- 不覆盖未知/用户草稿；真有草稿就保留事件、标WAIT_USER_DRAFT，先继续另一个方向。用户草稿不是永久平台故障。
- 只有确认当前正确composer没有真实草稿时，先SetFocus，再核前台窗口句柄与FocusedElement属于这一个目标框（或其已核子控件），然后用实际键盘输入ASCII HUB。现有System.Windows.Forms.SendKeys可在上述实时前提下单次受控使用；也可复用已有受约束SendInput。不要使用Ctrl+A，也不要任意Edit兜底。
- 目前SetValue已实测不能可靠得到HUB，不要继续反复用同一SetValue→Current.Value循环。真实按键会走应用输入事件，必须重新读取TextPattern/渲染状态并验证具体HUB进入正确框后才提交；这不是对Windows实测结果的预先保证。
- 若读回provider始终不反映渲染，以实际控件/视觉的已验证行为建立最小适配；不把可访问Name/占位字当草稿，也不随便剔除字符后宣称已空。没有可靠证据就阻塞，具体报告两provider与截图观测差异。
- HUB输入后重新查同pane发送按钮（编辑前可能仍显示语音按钮）；支持Invoke则用。否则已核实时焦点可单次Enter，提交后只读验收，不自动再次Enter。窗口/焦点变化立即停本次动作，保留事件。

3. 同时修两处现有误验收可能：
- 当前window查找遇第一个就break，却叫NOT_UNIQUE：应收集符合进程+BLACKBOX会话的所有可见候选，恰好1个才继续；不能报了“唯一”但没检查Count。
- Count-Hub要排除整个composer子树，不是只排除Edit节点；输入框后代Text“Hub”不是历史。成功须目标会话历史新增已提交用户HUB并确认composer确实清空，不能仅pane任意同字文本数增加。保留事件baseline/runtime或局部截图关联；分不清用户消息与助手回复则DELIVERY_UNCERTAIN。
- 不用可访问Name盲清理测试残留，也不操作模型选择器/语音按钮。

## 本轮交付目标
先交上面诊断与实际输入/提交的两侧结果（成功或可核具体失败），再将修复接入已有Operator。
用两个独立事件做两向单次测试，消息正文仅HUB；事件ID在日志。背景仍QUEUE_ONLY，单次测试进程按2008既有授权arm，不需要用户新批准。
两侧通过后，继续2018尚未完成的远端收件同步/正常调度/4轮真实180秒测试。queue-only的静默不能代替完整自动发送测试。12小时仍单列，未运行不PASS。
报告仍写2008目录并更新真实指针，附新源码diff/SHA/脱敏证据；不要再以只找到class或“ValuePattern不行”结束而未尝试已授权的实际焦点键盘路径。
既有有效工作接续，不创建第二套模型或服务；原数据/R9/规则不改，数据整理继续暂停。
