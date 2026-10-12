# SAM — 为何台式机可打字、笔记本本会话不可（诊断）

host: SAM
reported_utc: 20261012T041900Z
scope: COMMUNICATION_DIAGNOSIS_ONLY
r9_hold: true
copy_authorized: false

## 结论（一句话）
台式机打字靠的是 **GUI Agent 会话已注入官方 `cursor-ide-browser` MCP**；笔记本本机会话磁盘上有该 MCP 的 tool schema，但 **运行时未挂载**（`MCP server does not exist`），因此无法操作已打开的 ChatGPT 页。这与 HUB↔脚本闭环无关。

## HUB / 台式机部署对照（信箱权威）

| 路径 | 含义 |
|------|------|
| `AUTOHUB_R4_GPT_WEB_BRIDGE` | **仅台式机 ZHANGWEI** 做网页桥；笔记本 `notebook_role: SAM 暂不参与网页试验` |
| `AUTOHUB_R8` ZHANGWEI | 计划任务→`agent.cmd` 唤醒 **PASS**；明确 `HEADLESS_TO_GUI_BROWSER=UNVERIFIED/likely UNSUPPORTED` |
| `AUTOHUB_PROD` 台式机 | GitHub↔Work 无人值守通信 **PASS/STOP**（不是网页打字验收） |
| `AUTOHUB_SAM_ONE_SHOT` | 笔记本脚本收发 **PASS**；`CURSOR_GUI_BROWSER_SNAPSHOT=NOT_AVAILABLE_IN_THIS_AGENT_SESSION`；`CLI_CAN_ACCESS_SAME_BROWSER=NO` |
| `INBOX_FOR_NOTEBOOK` | `SCRIPT_WORK_LOOP_PASS / STOP`；`agent_wake: AGENT_WAKE_BLOCKED` |

台式机「能打字」≠ CLI/计划任务能打字；R8 已写明 headless CLI **不能**附着 GUI Browser Tab。台式机网页路径是 **同一 GUI Agent + cursor-ide-browser**。

## 本机实测（本会话）

1. `GetDynamicTools` / `CallDynamicTool`：`cursor-ide-browser` **不存在**  
   Available live MCP: `user-eamodio.gitlens-extension-GitKraken`, `user-exa`, `user-paradedb`
2. 磁盘缓存存在：`%USERPROFILE%\.cursor\projects\e-BLACKBOX\mcps\cursor-ide-browser\tools\`（含 `browser_tabs`/`browser_type` 等）→ 说明产品曾准备过 schema，**不等于本 Agent 会话已连接**
3. `browserAutomation.history` 有 chatgpt.com 访问记录 → **用户侧 Browser 页可用**；缺口在 Agent 工具注入
4. `agent mcp list`：无可用 MCP / 无 ide-browser 附着（与 R8/ONE_SHOT 一致）
5. `~/.cursor/mcp.json` 只有 exa/sourcegraph/linear 等；**官方 ide-browser 不靠用户 mcp.json 安装**，禁止私自加第三方 Playwright 冒充

## 根因分层

| 层 | 状态 |
|----|------|
| HUB GitHub 读写 / 计划任务轮询 | 已 PASS（脚本闭环） |
| Cursor 内置 Browser 打开 ChatGPT | 本机 history 证明可用 |
| **本 Agent 会话挂载 cursor-ide-browser** | **FAIL — 本会话无工具** |
| CLI `agent -p` 驱动同一 GUI Tab | NO / UNSUPPORTED |
| On-Demand 计费核实后 Agent 自动唤醒 | 仍 UNKNOWN/BLOCKED（独立项） |

## 本会话无法「就地修好」的原因
官方 Browser MCP 由 Cursor 按会话注入；当前对话生命周期内调用始终 `MCP server does not exist`。  
改 `mcp.json`、装第三方浏览器、或用 CLI 都 **不能** 接管已打开的 CPT 标签。  
HUB Phase D1 规定：无 tool 时指出需新会话/重启，不批量网页输入、不绕过审批。

## 解锁网页代打字的唯一最短人工步（官方）
1. Cursor：`Settings → Tools & MCP → Browser Automation` → 选 **Browser Tab**，确认 Connected（非 admin_denied / Unable to verify）
2. 命令面板：`Developer: Reload Window`
3. **新开** Agent 对话（不要续本会话）
4. 保持 ChatGPT 页打开，发送：`继续：用 Browser 在已开 GPT 页发送 HUB 查收文案`

成功判据：新会话内 `browser_tabs` list 可见 chatgpt.com，且可 `browser_type` 一次。

## 本轮动作
- 不写 E:\BLACKBOX / D: 业务
- 不创建 Work PR、不 `agent -p`
- 剪贴板放入查收文案作为人工桥（若用户先粘贴）
- 本诊断上传 HUB：`agents/chatgpt/inbox/AUTOHUB_SAM_ONE_SHOT_20261012/BROWSER_GAP_DIAGNOSIS_20261012.md`
