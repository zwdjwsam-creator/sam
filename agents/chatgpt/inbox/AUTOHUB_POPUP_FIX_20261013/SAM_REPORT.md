# AUTOHUB_POPUP_FIX_SAM_20261013 — SAM REPORT

task_id: AUTOHUB_CONSOLE_POPUP_FIX_SAM_20261013
host: sam
reported_at: 2026-10-13T10:05:00+08:00
scope: SAFE_WINDOWS_CONSOLE_WINDOW_REMEDIATION_ONLY
r9_hold: true
copy_authorized: false
source_e_d_untouched: true

## POPUP_SOURCE
A_CONFIRMED_AUTOHUB (confidence: HIGH)

## SOURCE_EVIDENCE
Two Windows Scheduled Tasks under `\` fire every PT1M with visible `powershell.exe` (no `-WindowStyle Hidden`):

1. `AUTOHUB_SAM_NOTEBOOK_POLLER`
   - Before: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\LAN_SHARE_REPORT\AUTOHUB_SAM_ONE_SHOT\scripts\sam_notebook_poller.ps1`
   - Principal: ThinkPad / Interactive
   - Observed LastRun ~every minute; LastTaskResult previously 0
2. `AUTOHUB_R2_COMM_TEST_RECEIVER_SAM`
   - Before: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\LAN_SHARE_REPORT\AUTOHUB_R2_NOTEBOOK\scripts\autohub_r2_comm_test_receiver.ps1`
   - Principal: ThinkPad / Interactive
   - Same 1-minute cadence

Classification: A_CONFIRMED_AUTOHUB only. Untouched: PowerToys/MWB UI, Cursor terminals, WPS/AMD/other tasks, unidentified processes.

## CONFIRMED_AUTOHUB_TASKS
- AUTOHUB_SAM_NOTEBOOK_POLLER
- AUTOHUB_R2_COMM_TEST_RECEIVER_SAM

## OTHER_TASKS_UNTOUCHED
true (no non-AUTOHUB / unknown tasks modified)

## TASKS_MODIFIED
Both confirmed tasks above.

## BEFORE_AFTER_COMMAND
- BEFORE (both): `-NoProfile -ExecutionPolicy Bypass -File <C-script>`
- AFTER (both): `-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File <same C-script>`
- Scripts, triggers (PT1M), principal/logon type, and working logic unchanged.

## BACKUP_XML_LOCATION
`C:\LAN_SHARE_REPORT\AUTOHUB_POPUP_FIX_SAM_20261013\backup\`
- `AUTOHUB_SAM_NOTEBOOK_POLLER.xml` (+ `.before.txt` / `.after.txt` / `.patched.xml`)
- `AUTOHUB_R2_COMM_TEST_RECEIVER_SAM.xml` (+ same sidecar files)

## ROLLBACK_PROVEN
Rollback method ready: `Unregister-ScheduledTask` + `Register-ScheduledTask -Xml` from the original `.xml` backups. Not executed (receiver still running; manual `-WindowStyle Hidden` script launches returned EXIT=0).

## HIDDEN_EXECUTION_VERIFIED
PARTIAL→YES for window visibility:
- During observation windows, `VISIBLE_COUNT=0` (no powershell/pwsh MainWindowTitle).
- Mid-run LastTaskResult `267009` (`0x41301` SCHED_S_TASK_RUNNING) seen while tasks still executing — expected, not treated as failure.
- Manual hidden launches of both scripts: EXIT=0.
- Transient `0x800710E0` once after first `Set-ScheduledTask` action-only edit; mitigated by re-registering from patched full XML preserving original settings.

## HUB_RECEIVER_STILL_WORKS
YES (pollers still scheduled Ready/Running on 1-minute cadence after fix; script files unchanged; no READY-triggered model/PR forced this run).

## TWO_CYCLES_OBSERVED
YES (≥2 LastRunTime advances observed post-change; no user-visible console tied to those runs).

## USER_VISIBLE_WINDOWS
NONE observed for the two AUTOHUB tasks after Hidden args applied.

## KNOWN_LIMITATIONS
- `-WindowStyle Hidden` may not hide every console creation path; if popups return, next step is audited C-disk VBS wrapper (not applied this round).
- Did not attribute screenshot-only evidence; used scheduled-task metadata + process window handles.
- UGREEN / MWB tasks unchanged (UGREEN already DRIVER_PASS+LINK_2P5G; MWB still WAITING_FOR_DESKTOP).
- Did not run old `外部大脑信箱_fetch_outbox.py`; qmt HARD_BLOCK left intact.

## Fields
SOURCE_E_D_UNTOUCHED=true
R9_HOLD=true
COPY_AUTHORIZED=false
POPUP_SOURCE=A_CONFIRMED_AUTOHUB
STATUS=FIXED_HIDDEN_AUTOHUB_POLLERS
