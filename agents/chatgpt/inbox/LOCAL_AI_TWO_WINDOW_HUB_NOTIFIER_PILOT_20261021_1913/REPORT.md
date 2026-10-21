# LOCAL_AI_TWO_WINDOW_HUB_NOTIFIER_PILOT_20261021_1913 REPORT

at: 2026-10-21T19:31:41+08:00
host: ZHANGWEI
workspace: E:\BLACKBOX (HUB mailbox only)
runtime: D:\LOCAL_AI\Watchdog\hub_two_window_notifier_1913
models: NOT reinstalled (Ollama/Models/Watchdog remain under D:\LOCAL_AI)
NO_BLACKBOX_BUSINESS_WRITES: true

## Deployed
- config + seen store + delivery log + mutex under D:\LOCAL_AI\Watchdog\hub_two_window_notifier_1913
- preload_seen marked 453 existing mailbox objects (first poll silent after preload)
- UIA scripts for Cursor IDE window (rejects external Chrome titled with Cursor)
- scheduler loop script: run_scheduler_loop.ps1 (180s) — ready, not forced as permanent forever service in this pilot

## Window / controls
- Cursor IDE window found: `HUB integration with GPT - BLACKBOX (工作区) - Cursor`
- Embedded ChatGPT composer UIA name: `使用 ChatGPT Work` → GPT_CHAT_IDENTIFIED=true
- Agent composer: NOT unique (edits visible: terminal stale banner + ChatGPT Work only) → CURSOR_AGENT_IDENTIFIED=PARTIAL
- Official Browser MCP: Server not found (re-register timeout) during send attempts
- Gemma4 vision: not called

## Cursor → GPT (test_id C2G_1913_1925)
1. Wrote pilot inbox trigger and pushed to HUB
2. Browser MCP blocked → UIA ValuePattern/clipboard into `使用 ChatGPT Work`
3. UIA tree echo found for `PILOT_C2G_TRIGGER_C2G_1913_1925` → **CURSOR_TO_GPT_DELIVERED=true**
4. Evidence: evidence/c2g_verify.json
5. Trigger URL: https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/LOCAL_AI_TWO_WINDOW_HUB_NOTIFIER_PILOT_20261021_1913/PILOT_C2G_TRIGGER_C2G_1913_1925.md

## GPT/HUB → Cursor Agent (test_id G2C_1913_1928)
1. Wrote/pushed pilot outbox tip PILOT_G2C_TRIGGER_G2C_1913_1928.md
2. Attempted UIA notify to Agent session
3. Agent edit not uniquely addressable; text echo appeared in UI tree but likely ChatGPT surface
4. **GPT_TO_CURSOR_DELIVERED=false** (honest; not claimed PASS)
5. Outbox URL: https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/outbox/PILOT_G2C_TRIGGER_G2C_1913_1928.md

## Poll 4 cycles
- After preload: cycle1 saw the pilot deltas; cycles 2–4 silent
- Interval used this session: 20s (short proof). Tip nominal 180s covered by run_scheduler_loop.ps1
- NO_DUPLICATES / NO_ECHO_LOOP: true for recorded C2G event_id
- LONG_RUN_12H: NOT_YET

## Fixed notification templates (as required)
1. Cursor→GPT: 「Cursor 有新结果已上传 HUB，请查收 inbox。结果：<url>。请审阅并将后续任务发布至 outbox/reviews。」
2. GPT→Cursor: 「GPT 已在 HUB 发布新的任务或复核，请查收 outbox/reviews，按既有授权范围处理。任务：<id+url>。」

## Blockers
- cursor-ide-browser MCP re-register timeout
- Cursor Agent composer not exposed distinctly in UIA
- 12h long-run not yet evidenced

## STATUS.json fields
See companion STATUS.json in this folder.