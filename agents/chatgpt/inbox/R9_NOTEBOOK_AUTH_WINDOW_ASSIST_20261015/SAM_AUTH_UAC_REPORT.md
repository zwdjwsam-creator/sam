# SAM_AUTH_UAC_REPORT

task_id: R9_NOTEBOOK_AUTH_WINDOW_ASSIST_20261015_1005
followup_id: R9_SAM_AUTH_UAC_ONCE_20261015_1051
execution_host: SAM
status: ELEVATED_QUERY_COMPLETE
reported_at: 2026-10-15T10:56:41.5718904+08:00
upload_utc: 2026-10-15T02:58:26Z
ZHANGWEI: HOLD

## Launch
launch_status: UAC_PROMPT_LAUNCHED
launch_utc: 2026-10-15T02:56:39.485Z
child_pid: 15364
script_commit: 689ce22ae3d2b51ed265ae7449adf8f3f432c7ee
script_sha256: B61CD0F25DFB779CF823BD212F111C4498693EC96E4530196329CD0DD3C7C00E
result_sha256: A48761B84C68447F8604B96F7D903034E9F500DCA0435882EFE4AF54D5FDACCF
elevated: True
identity: SAM\ThinkPad
window_half_open_utc: [2026-10-15T02:19:30Z,2026-10-15T02:19:33Z)

## Matching event counts
- Security (4625 filter): query_status=QUERY_OK matching_event_count=1
- Microsoft-Windows-SMBServer/Security: query_status=QUERY_OK matching_event_count=0
- Microsoft-Windows-SMBServer/Operational: query_status=NO_EVENTS_RETURNED_BY_QUERY matching_event_count=0

## Security event summary (non-secret)
event_id=4625 time_utc=2026-10-15T02:19:30.5609148+00:00 target=ZHANGWEI\Admin workstation=ZHANGWEI source_ip=192.168.100.1 status=0xc000006d substatus=0xc0000064 logon_type=3

## Hard holds (unchanged)
COPY_AUTHORIZED=false
SOURCE_ACCESS_VALID=false
FULL_MIGRATION=false
PILOT_WRITE_AUTHORIZED=false
no password change / credential list / new logon / ACL-network change / E-D write

Log query success does NOT restore SOURCE_ACCESS_VALID.
