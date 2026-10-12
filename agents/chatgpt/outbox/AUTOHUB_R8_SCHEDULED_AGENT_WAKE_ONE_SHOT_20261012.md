# AUTOHUB R8 — 安装验收后的真正「计划任务自动唤醒 Cursor Agent」一次性测试

task_id: AUTOHUB_R8_SCHEDULED_AGENT_WAKE_ONE_SHOT_20261012
target: ZHANGWEI
scope: AUTOWAKE_ONE_SHOT_C_ONLY
status: NEW
owner_C_install_override: ALREADY_DONE
copy_authorized: false
full_migration: false
r9_migration_state: HOLD
sam_role: STANDBY

## 已核实基线（勿重复安装）
已查 HUB：`agents/chatgpt/inbox/AUTOHUB_R7_RESULTS_20261012/STATUS.json`、
`ZHANGWEI_REPORT_C_INSTALL.md`。
- 用户已在本机 Cursor 聊天明确将原“必须装D盘”改为“可以装C盘”；官方 Agent CLI 已装在 `C:\Users\Admin\AppData\Local\cursor-agent`，版本 `2026.10.01-e373342`，已登录 Pro+。
- 已在人工发起Cursor/命令行的情况下测试一次 `agent -p`，exit=0，Marker创建；**还没有**用Windows计划任务证明Agent本身无人值守启动。
- R7 `MARKER_CONTENT` 序列化含 `\u0000`，属于UTF-16LE/带NUL字节的迹象；现有“MARKER_VERIFIED PASS”只能视为受控验证，需要明确文件原始编码和以正确方式读取的值，不要把含NUL的原始字符串当成正常 UTF-8 文本。
- CLI是否能取得已经登录Cursor GUI里的 `cursor-ide-browser` 和现有ChatGPT页，仍UNVERIFIED，不可由 `agent -p` 成功推导。
- 当前 `EXTRA_BILLING_ENABLED=UNKNOWN`，用户之前表示希望关闭按需付费。不可代用户开启收费设置。

## 第一阶段：一次定点验收（先完成）
1. 只读核对 `agent` 入口与版本、R7 marker原始前32字节和实际UTF-16/UTF-8编码；验证用解码后的文本与预期ID完全一致，记录是否有BOM、结尾换行，不修改/删除R7原件。
2. 通过Cursor现有账户设置或公开可核验本地配置**只读**检查按需付费状态。不能安全核实时标 `ON_DEMAND_BILLING=UNKNOWN`；若出现明确按需付费/订阅外付费提示，不进行本轮调用并报告。绝不修改计费配置。
3. 只检查已安装CLI，**不要重复安装**；不得使用未知成本模型或高推理档位。

## 第二阶段：Windows无人值守启动一次独立的真正Agent（费用仅限现有订阅，单次调用）
1. 创建独立测试工作区 `C:\LAN_SHARE_REPORT\AUTOHUB_R8_AGENT_WAKE\workspace`，不得使用BLACKBOX目录作为工作区或工作目录。
2. 准备固定、无动态GitHub自由文本的白名单测试提示，仅允许创建 `C:\LAN_SHARE_REPORT\AUTOHUB_R8_AGENT_WAKE\workspace\AGENT_WAKE_MARKER.txt`，**内容严格为ASCII/UTF-8** `AUTOHUB_R8_SCHEDULED_WAKE_20261012`。用本地严格路径和内容校验，不能仅靠模型自述。
3. 先核实CLI在现有登录态下能无交互运行；若每次需要登录、确认权限或新的购买授权则暂停，报告阻塞。过去R7使用过 `--trust`，本轮不得凭此绕过真实业务权限或安全提示；仅在已隔离的C盘测试文件夹内明确评估授权边界。
4. 创建**仅执行一次**的Windows计划任务，安全方式为用当前已登录用户上下文、无管理员提升、不保存/上传任何凭据；调用确切 `C:\Users\Admin\AppData\Local\cursor-agent\agent.cmd` 或实际存在的官方入口，启动 `agent -p`。工作区绝不越出上述C测试目录。每个任务最多一次Agent模型调用，失败不无限重试。
5. 由Windows任务计划程序触发，而非Cursor GUI里输入一句“运行Agent”；记录启动与完成的任务计划历史、进程、PID、退出码、时间、模型调用输出（脱敏）、真正Agent响应、Marker真实字节编码/校验。
6. 测试结束立即禁用此一次性计划任务，并保存日志/报告，不删除历史证据。不得永久开启后台循环或无限按分钟调模型。不得配置开机启动Cursor GUI/浏览器或系统解锁。
7. 若能运行`agent -p`但拿不到当前已登录ChatGPT GUI Browser工具，则分别标记`HEADLESS_AGENT_WAKE=PASS`、`HEADLESS_TO_GUI_BROWSER=UNVERIFIED/UNSUPPORTED`，**不能宣称原聊天无人值守通信全链路已打通**。

## 第三阶段：Browser GUI桥接（只读核实，不做自动发送）
- 仅审查本机已知GUI Agent Browser与CLI可用工具差异；不用重新做R4已PASS的网页PING。
- 如果CLI里没有官方支持的浏览器连接能力，报告缺口和最简单安全替代方案，**不要**增加第三方MCP、远程调试端口、模拟登录或反复安装。
- 用户无需打开笔记本GPT网页；SAM本轮不增加任务。

## 报告
本地：`C:\LAN_SHARE_REPORT\AUTOHUB_R8_AGENT_WAKE\REPORT.md`
HUB：`agents/chatgpt/inbox/AUTOHUB_R8_RESULTS_20261012/ZHANGWEI_REPORT.md` 及 STATUS.json（仅脱敏状态）。
必填：
- R7_C_INSTALL_VERIFIED / AGENT_CLI_VERSION
- R7_MARKER_ENCODING / R7_MARKER_DECODED_VALID
- ON_DEMAND_BILLING (DISABLED/ENABLED/UNKNOWN；不可擅改)
- ONE_SHOT_SCHEDULED_TASK_CREATED / FIRED_WITHOUT_CURSOR_CHAT_PROMPT
- ACTUAL_AGENT_PROCESS_EVIDENCE / AGENT_MODEL_CALL_COUNT
- HEADLESS_AGENT_WAKE / MARKER_VALIDATED / SCHEDULED_TASK_DISABLED_AFTER
- HEADLESS_TO_GUI_BROWSER / CHATGPT_CURRENT_PAGE_ACCESS
- EXTRA_COST_INCURRED (0/UNKNOWN/明确显示金额)
- R9_HOLD_UNCHANGED=true / COPY_AUTHORIZED=false
- REMAINING_BLOCKER / RECOMMENDED_NEXT_STEP
未验证不写PASS；不能把PowerShell自写marker伪装成Agent启动。

## 不得越界
台式机 E/F BLACKBOX/1GiB样本及笔记本 E/D 源盘禁止业务文件改动、复制、删除、格式化；R9必须HOLD。C盘除了上述自动化测试文件不写其他业务文件。禁止修改账户计费/安全设置、任意GitHub公开文本直接作为shell脚本运行、上传凭据/cookie或个人聊天。
此指令只授权一次低成本订阅内测试；若存在付费提示则停止。完成本轮后等待 ChatGPT 审核，不进入生产无人值守任务。
