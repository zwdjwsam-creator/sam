# SAM_REPORT — R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014_2312

- status: RUNNING
- phase: baseline_exclusive_recopy
- host: SAM
- exclusive_recopy_pid: 29780
- BASELINE_VERIFIED: false
- root_cause: Concurrent parent robocopy (PID 6864, started 00:27:14) overlapped a completed stream-copy that had already matched SHA 94e6; local file mutated to SHA c8056935... and sqlite quick_check failed.
- action: exclusive recopy to SOURCE_BASELINE.sqlite.partial then atomic replace after SHA verify; lockfile state\BASELINE_COPY.lock
- SOURCE_ENUMERATION_COMPLETE: false
- SOURCE_METADATA_MATCH: false
- SOURCE_CURRENT_MATCH: false
- HISTORICAL_CONTENT_MATCH: UNPROVEN
- SOURCE_SCAN_STABILITY: UNPROVEN
- COPY_AUTHORIZED: false
- ZHANGWEI: HOLD
- scripts: src/recopy_exclusive_r1.py, src/source_reconcile_r1.py, src/reparse_nofollow_r1.py, src/hub_upload_running_r1.py
- resume after BASELINE_VERIFIED: `E:\BLACKBOX\.venv\Scripts\python.exe -u C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014\src\source_reconcile_r1.py --mode run`
- work_dir: C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014
