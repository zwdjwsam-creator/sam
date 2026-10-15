# UAC_ONCE_ACK

task_id: R9_NOTEBOOK_AUTH_WINDOW_ASSIST_20261015_1005
followup_id: R9_SAM_AUTH_UAC_ONCE_20261015_1051
execution_host: SAM
observed_hostname: SAM
status: UAC_REQUESTED
ack_utc: 2026-10-15T02:56:14Z
ZHANGWEI: HOLD

script_local: C:\LAN_SHARE_REPORT\R9_SAM_AUTH_UAC_ONCE_20261015\query_auth_window_elevated.ps1
script_commit: 689ce22ae3d2b51ed265ae7449adf8f3f432c7ee
script_bytes: 3800
script_sha256: B61CD0F25DFB779CF823BD212F111C4498693EC96E4530196329CD0DD3C7C00E
launch_method: Start-Process -Verb RunAs (normal interactive UAC)
launch_planned: yes
user_clicked_yes: NOT_CLAIMED
elevated_query: PENDING_USER_UAC

COPY_AUTHORIZED=false
FULL_MIGRATION=false
PILOT_WRITE_AUTHORIZED=false
SOURCE_ACCESS_VALID=false

Hard holds observed: no password change, no credential list, no new logon, no ACL/network change, no E/D write.
ACK before/at launch. Do not interpret this as completed elevated query.