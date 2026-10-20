# REPORT — 官方 Browser 未挂到本 E Agent（网页 GPT 代操作阻塞）

observed_at: 2026-10-20T17:59:00+0800  
host: ZHANGWEI / Admin / Cursor 3.24.12  
workspace: E:\BLACKBOX

## 三条对接通道（分开验收）

| 通道 | 含义 | 本机状态 |
|---|---|---|
| HUB 文件信箱 | GitHub outbox/inbox ↔ ChatGPT | **可用**（本 E 会话已拉任务并回传） |
| 官方 Browser → chatgpt.com | Agent 代操作 GPT 网页 | **阻塞**（本会话 MCP 未附着） |
| 双挂 LiteLLM API | 模型路由，不是 ChatGPT 网页 | **脚本坏**（硬编码 ThinkPad `litellm.exe`）；本机已有 litellm，另案修 |

用户要的「和 GPT 自动对接」若指 **ChatGPT 网页代打字**：卡在第 2 条。  
若指 **信箱自动收发**：第 1 条已通——对话框发 `HUB` 即可。

## 诊断证据

1. 一次 live `browser_tabs list` → Server not found / MCP re-register timeout（不循环重试）。  
2. 扩展日志（脱敏）：`Cursor Browser Automation extension activated` + `Browser UI script injected successfully`；说明窗口侧扩展在跑，**不等于本 Agent 工具已注入**。  
3. 与 10/12 SAM 诊断同类：schema/磁盘可见 ≠ 会话挂载；禁止往 `mcp.json` 塞第三方 Playwright 冒充。  
4. 旧 D 会话 Browser PASS **不计入** 本 E 会话。

## 根因分层（有证据）

| 层 | 判定 |
|---|---|
| 扩展未安装 | 否（日志激活） |
| Browser 视图偶发缺失 | 曾有 `No browser view available`，后恢复 inject |
| **本 Agent 会话未附着 cursor-ide-browser** | **是（live 调用失败）** |
| CLI/headless 代替 GUI | 不支持（历史 R8） |

## 变更

无配置改写；未 Reload；未清 cookie；未启 LiteLLM。

## 最短一次 UI（Agent 无法代点设置）

1. `Cursor Settings` → `Tools & MCP` → `Browser Automation` → 选 **Browser Tab**，确认 Connected  
2. 命令面板：`Developer: Reload Window`  
3. **新开** Agent 对话（勿续本会话）  
4. 保持 ChatGPT 页打开，发送：`HUB`（剪贴板已写入 `HUB`）

成功判据：新会话 `browser_tabs` 能列出 chatgpt.com；HUB 文件通道可继续使用无需等 Browser。
