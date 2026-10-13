# SAM 笔记本 — MWB 回归修复（最新唯一优先指令，2026-10-13）

task_id: `MWB_SAM_REGRESSION_RECOVERY_20261013`
target: SAM / 笔记本 Cursor
status: READY
instruction: `agents/chatgpt/outbox/MWB_SAM_REGRESSION_RECOVERY_20261013.md`

用户证据覆盖旧结论：任务执行中 SAM物理鼠标已能在两机屏幕来回穿梭；ZHANGWEI物理鼠标能跨入SAM但无法返回；**SAM端口修复任务结束后，原能用的跨屏功能反而失效**。当前优先对照SAM最近变动（尤其ValidateRemoteMachineIP true→false和入站规则）做非敏感差异审计和最小可逆恢复。禁止盲目重装/重置密钥/修改网卡SMB。台式机当前复测任务暂缓。R9 HOLD，COPY_AUTHORIZED=false。

报告：`agents/chatgpt/inbox/MWB_SAM_REGRESSION_RECOVERY_20261013/SAM_REPORT.md`

---

# SAM 笔记本 — 当前唯一任务指针

task_id: `MWB_SAM_INBOUND_15100_FIX_20261013`
status: WAITING_DESKTOP_RETEST
target: SAM / 笔记本 Cursor
report: `agents/chatgpt/inbox/MWB_SAM_INBOUND_15100_FIX_20261013/SAM_REPORT.md`
peer_next: ZHANGWEI 复测 `Test-NetConnection 192.168.100.2 -Port 15100/15101`

摘要：本机 IPv4 监听与自测 PASS；修复前无 MWB 入站规则且有线口 Public；已建最窄 Allow 规则（.2←.1 仅 15100/15101）。反向 TCP 须台式机确认。APP_ROUTE_PENDING（仍见 WLAN 旁路会话）。R9 HOLD；SECRET_EXPOSED=false；NETWORK_UNCHANGED=true。

历史任务指针保留在下方（非当前权威）。

---

# ARCHIVE_HEAD

旧指针见 git history；当前权威为上方 WAITING_DESKTOP_RETEST。
