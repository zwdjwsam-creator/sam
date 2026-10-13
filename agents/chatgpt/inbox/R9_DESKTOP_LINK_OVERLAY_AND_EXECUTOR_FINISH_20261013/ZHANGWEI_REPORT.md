# ZHANGWEI_REPORT — R9_DESKTOP_LINK_OVERLAY_AND_EXECUTOR_FINISH_20261013_1709

host: ZHANGWEI
SAM: HOLD

INPUT_BINDINGS_VALID=true
LINK_MAPPING_COMPLETE=true
PLAN_COMPLETE=true
PLAN_SCOPE=offline bound snapshot only, not a live source-tree freeze
COPY_IMPLEMENTATION_READY=true
ACCEPTANCE_IMPLEMENTATION_READY=true
SOURCE_LIVE_PREFLIGHT_PENDING=true
WRITE_TESTS_NOT_RUN=true
E_DISK_WRITE_TESTS=NOT_RUN
FORMAT_DONE=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false

R3 map file SHA256 1c00ece5db519bf39de33473b5cbb81728cbdd65d8d38d6e00532f4a136084fe. The internal digest 2fa725f6… was not used as the file hash. Historical closure and serial 806508DF were not reused as authorization.

The existing plan was backed up, then updated in place. Ordinary counts stayed at file_paths 8715067, entities 1223721, unique_content_bytes 365007198749, logical_path_bytes 5085136765894, dirs 233660, links 4825.

Ids 25–40 matched the 16 D reparse rows. Each target is under E:\BLACKBOX and has delta file evidence: 14, 1, 14, and twelve 1s, totaling the 42 delta files. No link cycle in 4841 walked edges. Migrated link paths are under E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE\…; targets stay under E:\BLACKBOX\….

write_entity_bytes, create_local_hardlink, rebuild_reparse, and accept_on_disk are implemented in r9_copy_body.py and covered by fake-IO tests. The copy CLI still returns 3 before any write, including when both flags are passed. No E: write, no format, no real hardlink or junction test.

Source UNC \\192.168.100.2\E_DRIVE\BLACKBOX remains WinError 1326. Credentials and network were not changed.
