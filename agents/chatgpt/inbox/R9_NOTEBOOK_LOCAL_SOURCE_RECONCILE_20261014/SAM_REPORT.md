# SAM_REPORT — BLOCKED_BASELINE_VERIFY (interim)

task_id: R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014_2312
status: BLOCKED_PENDING_BASELINE_VERIFY
host: SAM
updated_at_local: 2026-10-15 01:19:02 +08:00

## Verified OK
- SAM_ACCESS_VERIFIED=true (UNC \\192.168.100.1\R9_SOURCE_BASELINE_20261014 listable; SOURCE_BASELINE.sqlite bytes=6025072640 on share)
- Volume serials: E=2387166462 MATCH; D=3187598165 MATCH
- SOURCE_SCOPE.json SHA=e03948d4… MATCH
- SOURCE_BASELINE_CONTRACT.json SHA=46655c97… MATCH

## Baseline failure (stop per instruction)
- expect SHA256=94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba bytes=6025072640
- local after Copy-Item: f75041f199fc03fb1ea7a4366824b055afbfe38c5ae250a456ed9b404819ef09 (bytes match, SHA mismatch); Copy-Item exit unknown/failed
- after interrupted robocopy overwrite: c8056935100a1c2eb9d4e8112e17dbb260fbf433116c87e6f0b95e84890e4f9b (still mismatch)
- UNC stream hash in progress (~1.9 MiB/s over 2.5G link) to distinguish share corruption vs copy corruption
- BASELINE_VERIFIED=false → enumeration NOT_STARTED (no invented baseline)

## Auth / migration flags
COPY_AUTHORIZED=false FULL_COPY_AUTHORIZED=false FULL_MIGRATION=false
ZHANGWEI HOLD — no desktop dispatch from SAM

## Next
1) Finish UNC SHA; if UNC!=94e6 → desktop must re-publish frozen baseline on share
2) If UNC==94e6 → clean local recopy then resume no-follow reconcile