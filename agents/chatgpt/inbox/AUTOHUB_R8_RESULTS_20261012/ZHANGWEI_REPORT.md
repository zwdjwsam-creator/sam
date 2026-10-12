# AUTOHUB R8 — Scheduled one-shot Cursor Agent wake (ZHANGWEI)

task_id: AUTOHUB_R8_SCHEDULED_AGENT_WAKE_ONE_SHOT_20261012
host: ZHANGWEI
reported_utc: 20261012T015950Z
scope: AUTOWAKE_ONE_SHOT_C_ONLY

## Required fields

| Field | Value |
|------|--------|
| R7_C_INSTALL_VERIFIED | PASS |
| AGENT_CLI_VERSION | 2026.10.01-e373342 |
| R7_MARKER_ENCODING | UTF-16LE (no BOM); first bytes `41 00 55 00 ...`; NUL count 34; length 68 |
| R7_MARKER_DECODED_VALID | PASS via UTF-16LE decode → `AUTOHUB_R7_C_INSTALL_TEST_20261012` (R7 file not modified) |
| ON_DEMAND_BILLING | UNKNOWN (`agent about` shows Subscription Tier Pro+ only; billing settings not opened/changed) |
| ONE_SHOT_SCHEDULED_TASK_CREATED | PASS — `AUTOHUB_R8_AGENT_WAKE_ONCE` |
| FIRED_WITHOUT_CURSOR_CHAT_PROMPT | PASS — `Start-ScheduledTask` (not typed into Cursor Agent chat) |
| ACTUAL_AGENT_PROCESS_EVIDENCE | PASS — agent.cmd PID 8952; exit 0; 2026-10-12T01:58:15.2480086Z → 2026-10-12T01:58:56.2915979Z |
| AGENT_MODEL_CALL_COUNT | 1 (single `agent -p`; no retries) |
| HEADLESS_AGENT_WAKE | PASS |
| MARKER_VALIDATED | PASS — exact ASCII 34 bytes `AUTOHUB_R8_SCHEDULED_WAKE_20261012` (hex `41 55 54 4F ... 31 32`) |
| SCHEDULED_TASK_DISABLED_AFTER | PASS — Enabled=False; LastTaskResult=0 |
| HEADLESS_TO_GUI_BROWSER | UNVERIFIED / likely UNSUPPORTED — CLI help exposes `mcp` / login browser open, not `cursor-ide-browser` attachment to existing GUI Browser Tab |
| CHATGPT_CURRENT_PAGE_ACCESS | UNVERIFIED (not attempted; R4 GUI path not re-run) |
| EXTRA_COST_INCURRED | UNKNOWN (no explicit fee prompt; used existing Pro+ session; amount not displayed) |
| R9_HOLD_UNCHANGED | true |
| COPY_AUTHORIZED | false |

## Phase 1 notes
- Did not reinstall CLI.
- R7 marker remains UTF-16LE on disk; decoded text matches expected ID.
- No billing UI changes.

## Phase 2 evidence
- workspace: `C:\LAN_SHARE_REPORT\AUTOHUB_R8_AGENT_WAKE\workspace`
- runner: `C:\LAN_SHARE_REPORT\AUTOHUB_R8_AGENT_WAKE\run_one_shot_agent_wake.ps1`
- entry: `C:\Users\Admin\AppData\Local\cursor-agent\agent.cmd`
- flags: `-p --workspace ... --trust --output-format text` (trust limited to isolated C test folder)
- Task Scheduler LastRunTime: 10/12/2026 09:58:14
- stdout (desensitized): Created AGENT_WAKE_MARKER.txt with expected content
- Not PowerShell writing the marker; Agent process created the file

## Phase 3
- CLI≠GUI Browser bridge; remaining gap for ChatGPT web unattended send via headless CLI.
- Recommended next step: either keep using GUI Agent + cursor-ide-browser for ChatGPT web, or seek official CLI↔IDE browser bridge; do not add third-party MCP without new approval.

## REMAINING_BLOCKER
Headless scheduled Agent wake works for C-only file tasks, but does **not** prove control of the already-logged-in ChatGPT Browser Tab.

## Safety
- No BLACKBOX / E/F / R9 copy
- One-shot task disabled after run
- No infinite loops / no boot autostart of Cursor GUI