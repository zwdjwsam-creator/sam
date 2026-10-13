# ZHANGWEI REPORT — AUTOHUB_CONSOLE_POPUP_FIX_ZHANGWEI_20261013

host: ZHANGWEI
task_id: AUTOHUB_CONSOLE_POPUP_FIX_ZHANGWEI_20261013
reported_utc: 2026-10-13T01:58:39.0062767Z
claim_note: Desktop inbox pointer was stale (still MWB); executed from published outbox after owner notice that inbox update failed.

## POPUP_SOURCE / CONFIDENCE
- POPUP_SOURCE: Scheduled Task workers launching visible `powershell.exe` without `-WindowStyle Hidden`
  1) `AUTOHUB_PROD_INBOX_POLL_ZHANGWEI` → `prod_inbox_poll.ps1` (every ~5 min)
  2) `AUTOHUB_R2_COMM_TEST_RECEIVER_ZHANGWEI` → `autohub_r2_comm_receiver.ps1` (~1 min)
- CONFIDENCE: HIGH (task actions matched LAN_SHARE_REPORT AUTOHUB scripts; LastRun correlated with console cadence)
- NOT modified: AsusDriverHub, SpaceAgentTask, Cursor IDE / PSES terminals, PowerToys/MWB GUI, Disabled one-shot AUTOHUB_R4B/R5/R8

## RELATED_SCHEDULED_TASK_AND_ORIGIN
| Task | Origin script | Before action | After action |
|---|---|---|---|
| AUTOHUB_PROD_INBOX_POLL_ZHANGWEI | C:\LAN_SHARE_REPORT\AUTOHUB_PROD\scripts\prod_inbox_poll.ps1 | powershell.exe -NoProfile -ExecutionPolicy Bypass -File ... | wscript.exe //nologo run_hidden.vbs + same script |
| AUTOHUB_R2_COMM_TEST_RECEIVER_ZHANGWEI | C:\LAN_SHARE_REPORT\AUTOHUB_R2_DESKTOP\autohub_r2_comm_receiver.ps1 | powershell.exe -NoProfile -ExecutionPolicy Bypass -File ... | wscript.exe //nologo run_hidden.vbs + same script |

Hidden launcher: `C:\LAN_SHARE_REPORT\AUTOHUB_POPUP_FIX_ZHANGWEI_20261013\scripts\run_hidden.vbs`
(uses `WScript.Shell.Run ..., 0` + `powershell -WindowStyle Hidden -NonInteractive`)

## BACKUP_LOCATION / ROLLBACK_READY
- BACKUP_LOCATION: `C:\LAN_SHARE_REPORT\AUTOHUB_POPUP_FIX_ZHANGWEI_20261013\backup\`
  - AUTOHUB_PROD_INBOX_POLL_ZHANGWEI.xml
  - AUTOHUB_R2_COMM_TEST_RECEIVER_ZHANGWEI.xml
- ROLLBACK_READY: true (`Register-ScheduledTask -Xml (Get-Content backup\*.xml -Raw)`)

## RUNS_OBSERVED / WINDOW_VISIBLE_AFTER_FIX / HUB_POLL_STILL_WORKING
- RUNS_OBSERVED: 2 forced cycles (+ R2 natural mid-cycle LastResult=0)
  - run1: R2/PROD LastTaskResult=0 at ~09:56:40; poll log `poll_20261013T015641Z.json`
  - run2: R2 LastTaskResult=0 ~09:58:03; PROD 0 ~09:58:00; poll logs `poll_20261013T015757Z.json` / `poll_20261013T015801Z.json`
- WINDOW_VISIBLE_AFTER_FIX: false for AUTOHUB workers (no lingering worker powershell; during_run2 briefly saw hidden powershell count=1 then 0; VBS window style 0)
- HUB_POLL_STILL_WORKING: true (PROD poll JSON continuing to write; tasks remain Enabled/Ready; not disabled)
- Current actions:
  - PROD: wscript.exe //nologo "C:\LAN_SHARE_REPORT\AUTOHUB_POPUP_FIX_ZHANGWEI_20261013\scripts\run_hidden.vbs" "C:\LAN_SHARE_REPORT\AUTOHUB_PROD\scripts\prod_inbox_poll.ps1"
  - R2: wscript.exe //nologo "C:\LAN_SHARE_REPORT\AUTOHUB_POPUP_FIX_ZHANGWEI_20261013\scripts\run_hidden.vbs" "C:\LAN_SHARE_REPORT\AUTOHUB_R2_DESKTOP\autohub_r2_comm_receiver.ps1"
- Latest task info: PROD last=0 @10/13/2026 09:58:00; R2 last=0 @10/13/2026 09:58:03

## Safety
- UNKNOWN_TASKS_UNTOUCHED: true
- AUTOHUB not disabled: true
- No reboot
- BLACKBOX untouched
- UGREEN/2.5G untouched
- MWB: enabled=true process=True (not reconfigured)
- R9_HOLD_UNCHANGED: true
- COPY_AUTHORIZED: false
- SAC VerifiedAndReputablePolicyState: 0 (unchanged by this task)

## NEXT_ACTION_IF_BLOCKED
If a console still flashes: capture Task Scheduler 200/201 around the flash; only remediate if action still points to known AUTOHUB script under C:\LAN_SHARE_REPORT. Do not hide unknown publishers.