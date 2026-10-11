# AUTOHUB R1 — 台式机 ZHANGWEI：双机自动领取 + ChatGPT网页/Work触发可行性实验

**执行方：台式机 Cursor Agent（ZHANGWEI）**  
**调度ID：AUTOHUB_R1_DESKTOP_20261011**  
**授权范围：仅HUB通信、无害网页实验和能力核验；不允许BLACKBOX数据复制/改动。**

## 总目标
用户要消除两次人工提醒：「告诉ChatGPT查看HUB」「告诉Cursor查看HUB」，沿用现有GitHub HUB `zwdjwsam-creator/sam`。无需Hugging Face、无需部署本地模型、暂不采购OpenAI API。先确定**真正能自动的程度**，不把能打开网页误报为能长期自动运行。

## A. 保留现有R9，先盘点现有能力
1. 只读核对现有HUB收发脚本和消息目录、Git凭证可用性（绝不记录凭证）、Cursor版本、Browser Agent及非交互CLI可用情况、Windows任务计划程序。优先复用已有脚本，不重建仓库。
2. 确认当前R9 E/D输入包、1GiB样本和原收件文件仍原样；不改动不清空。
3. 检查旧R8 ln是否已退出，如发现仍运行只报告，不在本任务中停止/重启。
4. 本轮全部脚本/日志落台式机C盘 `C:\LAN_SHARE_REPORT\AUTOHUB_R1_DESKTOP\`；HUB新建独立AUTOHUB_R1测试文件，不覆写老消息。

## B. 双机自动收发测试（可实际执行）
1. 建立/复用低频监听器（例如每60秒检查一次HUB更新，或已有更可靠的方式）。仅响应明确 `scope=COMMUNICATION_TEST` + `target=DESKTOP/NOTEBOOK` + 唯一 `task_id` + 有效内容的测试信件，保存去重状态，禁止将仓库中的普通Markdown或旧R9指令自动交给Agent执行。
2. 为笔记本SAM发布**仅含随机测试标识的PING**，目标为NOTEBOOK；确认笔记本自动ACK。若SAM端监听器尚未部署，先在报告中标记WAITING_FOR_SAM，不把人工读取冒充自动读取。
3. 再准备DESKTOP目标的PING，证明台式机能自动读取及回执。一次完整闭环后停止自动测试，不允许无限反复触发。
4. 如发现两台机器Git推送冲突，使用独立新文件名和幂等ID，不进行force-push、自动删除和全库清理。
5. 不自动执行任何BLACKBOX文件操作；正式任务自动执行待另行批准。

## C. Cursor能否直接操作网页版ChatGPT——分层验证
1. 核对实际安装版本和官方Browser工具/MCP的可用性。区分：（a）Cursor GUI Agent手动会话中的浏览器操作；（b）Cursor CLI非交互启动浏览器；（c）Windows后台无人值守控制已经登录的ChatGPT网页。
2. 通过**一次无害的浏览器只读测试**核实：能够定位已经登录的ChatGPT标签页、读取页面可见状态、找到输入框，并说明需要哪些用户确认/审批。若要实际发送测试文本，只能使用单一明确标记 `AUTOHUB_R1_BROWSER_PING`，内容不得包含业务数据、密钥或提示模型执行外部写操作；不得绕过验证码、登录、付费确认、权限审批或反自动化限制。
3. 记录发送成功与否、读取回复完成的可靠判定方式、会话中断/超时恢复、成本和登录依赖。**不允许把「Cursor能点网页」等同于「ChatGPT被GitHub通知自动唤醒」。**
4. 禁止保存浏览器Cookie、会话Token、用户密码到HUB或脚本日志；禁止请求关闭浏览器安全检查。
5. 不要进行无人值守网页机器人长时间循环，也不要操作当前用户真实BLACKBOX项目的发指令聊天，仅做单次无害PING。

## D. ChatGPT Work GitHub自动触发（只核验，不假定）
1. 查验当前用户/产品是否确实具有GitHub PR事件触发Work任务的**可用入口**及所需权限；说明支持的事件种类和创建条件。若不可从桌面环境可靠验证，明确 `WORK_PR_TRIGGER=UNVERIFIED`；不要仅凭互联网文档声称本账号可用。
2. 若功能确实具备，写出最小实验步骤/配置候选（独立测试PR、不触碰BLACKBOX业务内容）。本轮不擅自配置持续触发、工作流或GitHub Actions权限。
3. 对比「Cursor网页操作ChatGPT」和「Work GitHub PR触发」两条路线：实际可用性、需要额外人工动作、是否会触发当前同一对话、是否可无人值守、失败恢复与限制。
4. 如果两者都尚不能闭环，直说缺失哪个触发器，不凭空宣称100%自动。

## E. 安全和停止条件
- 禁止源笔记本E/D任何写入，P7继续Disabled。
- 禁止台式机E/F BLACKBOX数据复制、移动、删除、格式化及修改；旧R9数据原样保留。
- 不对真实迁移任务实施自动批准或自动执行。
- 禁止OpenAI API计费调用、本地模型部署、Hugging Face新仓库。
- GitHub仓库当前为PUBLIC，仅能提交无害测试文本和脱敏状态；绝不上传本地路径中的敏感数据、凭据、数据字典内容或真实业务数据。
- 如自动化需要管理员授权、登录新服务、付费、关闭安全限制，停止并说明。
- 实验至多一次双向PING/ACK和一次网页PING；成功即停，避免自触发循环。

## F. 交付
在C盘输出 `C:\LAN_SHARE_REPORT\AUTOHUB_R1_DESKTOP\REPORT.md`；
向HUB独立新文件回报：
`AUTOHUB_TEST_RESULT_DESKTOP.md`
必含：
- HUB_WATCHER_METHOD / NOTEBOOK_PING_ACK / DESKTOP_AUTO_RECEIVE
- CURSOR_BROWSER_GUI_SUPPORTED / CURSOR_CLI_BROWSER_SUPPORTED / CHATGPT_WEB_PING_RESULT
- WORK_PR_TRIGGER_AVAILABILITY（VERIFIED/UNVERIFIED/UNAVAILABLE）
- CHATGPT_REPLY_DETECTED / AUTO_CHATGPT_WAKE_AVAILABLE
- USER_INTERVENTIONS_REQUIRED / FAILURE_RECOVERY
- SAFE_AUTOMATION_RECOMMENDATION / R9_UNTOUCHED
- NEXT_BLOCKERS
报告后停止，不自动部署生产级无限循环。
