# SAM AUTH FINAL READONLY REPORT — FOLLOWUP 1040

followup_id: R9_SAM_AUTH_FINAL_READONLY_CHECK_20261015_1040
parent: R9_NOTEBOOK_AUTH_WINDOW_ASSIST_20261015_1005
execution_host: SAM
reported_at_local: 2026-10-15T10:46:12+08:00
ZHANGWEI: HOLD
COPY_AUTHORIZED: false
SOURCE_ACCESS_VALID: false

## Verdict
- events_readable: **false**
- uac_required: **yes** (LOCAL_UAC_CONFIRMATION_REQUIRED)
- elevated_query_executed: **false** (NOT_RUN)
- matching_event_count: **null** (cannot assert 0)
- ThinkPad local account facts: collected (non-secret)

## 1) Admin channel / elevation
- SAM\ThinkPad is in local Administrators (with SAM\Administrator).
- Current agent session integrity: Medium Mandatory Level; IsInRole(Administrator)=false.
- SeSecurityPrivilege not held in current token.
- No already-authorized High-IL admin execution channel reusable by this agent.
- Per instruction: interactive UAC would be required; STOPPED without bypass, without installing services/tasks, without wait/loop, without multi-prompt.

## 2) Auth window elevated readonly query
- Target window: 2026-10-15 10:19:30—10:19:32 +08:00 = [02:19:30Z, 02:19:33Z)
- Non-elevated reconfirm: Security / Microsoft-Windows-SMBServer/Security / Operational → **AccessDenied** (Get-WinEvent + wevtutil).
- Elevated query status: **NOT_RUN** / reason **LOCAL_UAC_CONFIRMATION_REQUIRED**
- Artifact: AUTH_WINDOW_ELEVATED_RESULT.json (= AUTH_WINDOW_EVENTS_ELEVATED.json)

## 3) ThinkPad source account (non-secret)
- exists=true, enabled=true, principal_source=Local
- PasswordRequired=false (does NOT prove blank password)
- PasswordLastSet=2026-10-14T10:28:49+08:00
- PasswordExpires=null / no expiry observed
- member_of_administrators=true
- LimitBlankPasswordUse (HKLM Lsa)=1 (blank-password network logon restricted by policy)
- No passwords/hashes/SIDs/creds read; no empty-password attempt; no .1/admin against .2

## 4) Boundaries held
- No saved-cred rescan for 192.168.100.2
- No window expand / no manufactured logons
- No password/ACL/network/share changes
- No E/D writes; no candidate/code changes
- Desktop ZHANGWEI remains HOLD; COPY not authorized

## Minimal missing step
User (or operator) confirms one interactive UAC elevation on SAM for a single readonly Security/SMBServer query of the same 2s window — then re-run elevated query only. Do not reset account/password outside explicit authorization.

## Artifacts
- FOLLOWUP_ACK.md / SAM_ACK_FOLLOWUP_1040.md
- AUTH_WINDOW_ELEVATED_RESULT.json / AUTH_WINDOW_EVENTS_ELEVATED.json
- SOURCE_ACCOUNT_STATE.json / SOURCE_ACCOUNT_FACTS.json
- SAM_AUTH_FINAL_READONLY_REPORT.md / SAM_REPORT_FOLLOWUP_1040.md
- FILE_SHA256.json