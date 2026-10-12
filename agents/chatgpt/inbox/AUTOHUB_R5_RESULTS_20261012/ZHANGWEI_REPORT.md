# AUTOHUB R5 — ZHANGWEI Agent Autowake Preflight Report

task_id: AUTOHUB_R5_AGENT_AUTOWAKE_PREFLIGHT_20261012
host: ZHANGWEI
scope: AUTOWAKE_CAPABILITY_AND_C_ONLY_TEST
reported_utc: 20261012T011017Z
r9_migration_state: HOLD
copy_authorized: false
full_migration: false

## Core fields

| Field | Status |
|------|--------|
| CURSOR_OFFICIAL_AGENT_CLI_INSTALLED | FAIL (not found) |
| CLI_HEADLESS_TEST | BLOCKED (CLI absent; no install without extra approval) |
| AGENT_WAKE_BY_TASK_SCHEDULER | BLOCKED |
| AGENT_BROWSER_HEADLESS_AVAILABLE | UNVERIFIED / likely NO for headless CLI (GUI Browser Tab is separate) |
| MARKER_VERIFIED | PASS |
| POWERSHELL_FALLBACK_ONLY | PASS (scheduled whitelist wrote MARKER; not Agent) |
| AUTOMATIONS_AVAILABLE | UNVERIFIED (not probed in-account; cloud Agent ≠ local disk/GUI ChatGPT) |
| EXTRA_BILLING_PERMISSION_NEEDED | UNKNOWN until user approves CLI install/login or Automations |
| USER_MANUAL_STEPS | See single recommended path below |
| R9_HOLD_UNCHANGED | true |

## CLI evidence
- cursor launcher: C:\cursor\resources\app\bin\cursor.cmd version 3.24.12 — editor paths/diff/merge only
- `agent` / `cursor-agent` on PATH: no
- agent*.exe under common install roots: none found
- Did **not** run remote install script / did **not** change global Cursor permissions / did **not** incur billing calls

## PowerShell fallback (honest)
- script: C:\LAN_SHARE_REPORT\AUTOHUB_R5_AUTOWAKE\write_marker_whitelist.ps1
- scheduled_task: AUTOHUB_R5_MARKER_ONCE (ran once, then Disabled)
- last_task_result: 0
- MARKER.txt content: AUTOHUB_R5_AGENT_AUTOWAKE_PREFLIGHT_20261012
- SCRIPT_UNATTENDED_PASS: PASS
- CURSOR_AGENT_WAKE: BLOCKED
- Existing AUTOHUB_R2_COMM_TEST_RECEIVER_ZHANGWEI left intact (Ready; PING-only)

## Automations (evaluate only)
- Official docs describe GitHub/schedule cloud Automations; cloud Agent runs isolated and does **not** control ZHANGWEI local disks or the logged-in ChatGPT Browser Tab.
- Account enablement / pricing gates: not activated in this run.

## Single recommended next path (minimal extra action / cost)
Ask user for **one** approval: install + login official Cursor Agent CLI on ZHANGWEI (docs: cursor.com/docs/cli/overview), then bind a disabled-by-default scheduled task that runs only `agent -p` with a fixed C-only prompt to write `C:\LAN_SHARE_REPORT\AUTOHUB_R5_AUTOWAKE\MARKER.txt`. Do not enable Automations or cloud billing until that local CLI headless test PASSes. This is the shortest path to true `CURSOR_AGENT_AUTO_WAKE` evidence; PowerShell MARKER alone must not be called Agent wake.

## Safety
- No BLACKBOX / E/F / 1GiB sample changes
- No install, no infinite loop, one-shot tasks disabled after run
- R4 Browser/comms not re-run