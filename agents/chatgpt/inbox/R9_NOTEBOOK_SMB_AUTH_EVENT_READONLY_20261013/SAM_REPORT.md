# SAM readonly SMB auth diagnostic — R9_NOTEBOOK_SMB_AUTH_EVENT_READONLY_20261013

**task_id:** R9_NOTEBOOK_SMB_AUTH_EVENT_READONLY_20261013_2101  
**executed_on:** SAM (Windows identity `SAM\ThinkPad`)  
**gate:** ALLOWED_PENDING_HUMAN — no hard_block_hits  
**constraints:** READONLY; COPY_AUTHORIZED=false; FORMAT_DONE=false; FULL_MIGRATION=false  

## Time window (local +08:00)

2026-10-13 20:10:00 — 20:40:00

## Security Event ID 4625

| Item | Value |
|------|--------|
| Query API | Get-WinEvent -FilterHashtable (Security, Id=4625, Start/End) |
| Raw 4625 in window | 0 (channel returned no records for window) |
| After filter (LogonType=3, Workstation=ZHANGWEI or Ip 192.168.100.*) | **0** |
| AccessDenied on Security | **No** |
| Notes | Empty result surfaced as “no matching events” exception; treated as zero events, not permission failure. |

## SMBServer / related logs (existence + enabled only; not modified)

| Channel | Readable | Notes |
|---------|----------|--------|
| Microsoft-Windows-SMBServer/Operational | No | Unauthorized operation reading log metadata |
| Microsoft-Windows-SMBServer/Security | No | Same |
| Microsoft-Windows-SMBServer/Audit | No | Same |

Shares visible (name/path only): `E_DRIVE`→`E:\`, `D_DRIVE`→`D:\`, plus admin/default shares and BLACKBOX-related shares (see JSON).

## Account facts (readonly)

- **Current session:** `SAM\ThinkPad` (NTLM, authenticated)
- **Local user ThinkPad:** exists, Enabled=true, PrincipalSource=Local, PasswordRequired=**false** (does not prove empty password)
- **Event TargetUserName(s):** none in window — no candidate from 4625

## Share ACL summary (candidate-filtered + Everyone)

| Share | Path | Relevant entries |
|-------|------|------------------|
| E_DRIVE | E:\ | Everyone — Allow — Full |
| D_DRIVE | D:\ | Everyone — Allow — Full |

No per-user ACE matched event accounts (no events). Everyone Full indicates share-level ACL is not the primary 1326 gate for anonymous/guest denial scenarios; auth still required at session layer.

## AUTH conclusion (evidence-bound)

See `AUTH_NEXT_ACTION.json`:

- **AUTH_FAILURE_CAUSE:** `NO_MATCHING_EVENT`
- **SOURCE_ACCOUNT_CANDIDATE:** null
- **USER_LOCAL_SECRET_ENTRY_NEEDED:** UNKNOWN

## Artifacts

- `src/query_smb_auth_events_readonly.ps1`
- `reports/SMB_SERVER_AUTH_EVENTS.json`
- `reports/SOURCE_ACCOUNT_AUTH_INFO.json`
- `reports/AUTH_NEXT_ACTION.json`
- `reports/FILE_SHA256.json`

## AccessDenied summary

- Security 4625 read: **not denied**
- SMBServer log channel metadata: **denied / unauthorized** (three channels)
