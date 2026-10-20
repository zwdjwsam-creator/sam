# ACK — CURSOR_NATIVE_BROWSER_SESSION_REPAIR_20261020_1720

host: ZHANGWEI  
windows_user: Admin  
cursor: 3.24.12 (`C:\cursor\Cursor.exe`)  
workspace: E:\BLACKBOX (project `e-BLACKBOX`)  
session_kind: GUI_Agent  
observed_at: 2026-10-20T17:59:00+0800  
status: BROWSER_MCP_NOT_ATTACHED_NEEDS_ONE_UI_ACTION

live_browser_tabs_attempt: once  
live_error: `Server not found: cursor-ide-browser (MCP provider did not re-register within 30000ms)`  
schema_discovery: GetDynamicTools sees tool schemas; live CallDynamicTool fails  
extension_log: Browser Automation activates + UI script inject OK (window6); earlier `No browser view available` then recovered  
mcp.json: not present (official ide-browser is not installed via user mcp.json — correct)  
settings.json browser/mcp keys: none  
HUB file channel (separate): already PASS in E session ACK_E_AGENT_20261020_1751  
LiteLLM dual-AI (separate): START_DOUBLE_AI_TASK.ps1 fails ThinkPad path; local litellm.exe exists — out of Browser scope
