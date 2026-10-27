# ZHANGWEI / one-shot AUTOHUB task identity read — 2026-10-27 R1

task_id: BLACKBOX_FORENSIC_READONLY_ZHANGWEI_20261027_R1
parent_dispatch_id: BLACKBOX_UPDATE_PREREQUISITES_20261027
execution_host: ZHANGWEI (exact hostname must be ZHANGWEI)
dispatch_id: BLACKBOX_FORENSIC_READONLY_20261027_R1
status: READY_ONE_SHOT_READ_ONLY_TASK_DEFINITION
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
DESKTOP_STOP_OR_DISABLE_ALLOWED=false

## Scope

Identity-check ONLY the already observed `TaskPath=\`, `TaskName=AUTOHUB_LOCAL_WATCHDOG_ZHANGWEI` scheduled task. The watchdog-control report already proved `Enabled=true; State=Running; proven_kind=null`. Do not assume it is historical catchup, do not stop it, and do not re-run watchdog_control.

After checking whether this exact follow-up was already completed/active, read the task's Windows Task Scheduler **definition** only, using native read-only methods such as `Get-ScheduledTask` and `Export-ScheduledTask` or equivalent built-in Cursor file/OS tools. Do NOT start/stop/disable/enable/delete the task. Do NOT read the executable or target script, do NOT launch Actions, and do NOT inspect unrelated tasks or live process command lines.

Record:
- Exact task path/name, enabled/state as returned and the observation time.
- Each Action's Execute, Arguments, WorkingDirectory (redact any tokens, password or sensitive literal, preserve useful non-secret paths).
- Triggers in coarse human-readable form, and definition XML hash if exported (sanitize sensitive fields before uploading; record whether redacted).
- An evidence-based identity classification: `HUB_COMMUNICATION_CONFIRMED`, `CATCHUP_CHAIN_CONFIRMED`, or `UNDETERMINED`. A friendly task name by itself is NOT evidence of identity.
- Whether any action explicitly invokes the exact SAM catchup directory or its three allowlisted watcher PS1 scripts. If missing, state only `NO_MATCH_IN_THIS_TASK_DEFINITION`, not absence of all possible tasks.

Deliver `ACK.json`, `TASK_DEFINITION_FACTS.json`, sanitized `REPORT.md`, `DELIVERY_MANIFEST.json`, `UPLOAD_READBACK.json` under:
`agents/chatgpt/inbox/BLACKBOX_UPDATE_PREREQUISITES_20261027/ZHANGWEI/task_definition_001/`
Local exclusive-create output only:
`C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027\ZHANGWEI\task_definition_001`
If task missing or access denied, report it exactly; do not ask for elevation or retry. Verify every uploaded report byte-for-byte after remote GET; no overwrite or deletion. No requirement to export full XML if it includes secrets; factual sanitized Action fields suffice.

The HUB already has `ACK_OWNER_BASELINE_20261027.json` (ack at 16:04:07 China, already complete) and two identical RCID source receipts. Do NOT rename/re-upload ACK, re-run V3, re-compare RCID, scan RAW or perform the previous 10,000-entry filename listing. No migration, acquisition, download, Research OS invocation, business script, CURRENT/SSOT/rules writes, order, process control, terminal restart, code edit or policy change. Keep the AUTOHUB task running. Finish local Cursor reply exactly END only after upload/readback.
