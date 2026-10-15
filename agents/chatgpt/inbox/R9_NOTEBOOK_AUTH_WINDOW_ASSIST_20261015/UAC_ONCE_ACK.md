# UAC_ONCE_ACK

task_id: R9_NOTEBOOK_AUTH_WINDOW_ASSIST_20261015_1005
followup_id: R9_SAM_AUTH_UAC_ONCE_20261015_1051
execution_host: SAM
observed_hostname: SAM
status: UAC_REQUESTED
ack_utc: 2026-10-15T02:57:04Z
ZHANGWEI: HOLD

script_local: C:\LAN_SHARE_REPORT\R9_SAM_AUTH_UAC_ONCE_20261015\query_auth_window_elevated.ps1
script_commit: 689ce22ae3d2b51ed265ae7449adf8f3f432c7ee
script_sha256: B61CD0F25DFB779CF823BD212F111C4498693EC96E4530196329CD0DD3C7C00E
launch_method: Start-Process -Verb RunAs (normal interactive UAC)
launch_status: UAC_PROMPT_LAUNCHED
launch_utc: 2026-10-15T02:56:39.485Z
launch_local: 2026-10-15 10:56:39
child_pid: 15364
user_clicked_yes: NOT_CLAIMED
elevated_query: PENDING_RESULT_FILE
result_path: C:\LAN_SHARE_REPORT\R9_SAM_AUTH_UAC_ONCE_20261015\AUTH_UAC_QUERY_RESULT.json

COPY_AUTHORIZED=false
FULL_MIGRATION=false
PILOT_WRITE_AUTHORIZED=false
SOURCE_ACCESS_VALID=false

Parent did not claim interactive Yes. Polling for result file only. No retry loops.