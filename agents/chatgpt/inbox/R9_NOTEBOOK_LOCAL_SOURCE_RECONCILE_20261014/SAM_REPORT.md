# SAM_REPORT — R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014_2312

## Status
- **status**: COMPLETE
- **host**: sam
- **updated_at**: 2026-10-15T06:34:16+0800
- **followup**: R9_NOTEBOOK_SOURCE_RECONCILE_PROGRESS_AND_FINISH_20261015_0628
- **ZHANGWEI**: HOLD
- **COPY_AUTHORIZED**: false

## Access / Baseline
- **SAM_ACCESS_VERIFIED**: true (live E/D enumeration finished; UNC baseline 94e6… verified earlier)
- **BASELINE_VERIFIED**: true
- **baseline_sha256**: 94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba
- **baseline_bytes**: 6025072640
- **baseline_quick_check**: ok

## Enumeration (no rescan; delivery from finished run)
- **SOURCE_ENUMERATION_COMPLETE**: true
- **paths_enumerated**: 8953561
- **dirs_done**: 233665
- **queue_pending**: 0
- **dirs_error**: 0
- **SOURCE_METADATA_MATCH**: false
- **SOURCE_CURRENT_MATCH**: false
- **HISTORICAL_CONTENT_MATCH**: UNPROVEN
- **SOURCE_SCAN_STABILITY**: UNPROVEN
- **USN**: null — journal not used; stability therefore UNPROVEN

## Delta totals
| kind | count |
|------|------:|
| ADDED | 51 |
| MISSING | 42 |
| SIZE_MISMATCH | 141 |
| **total** | **234** |

### Per-root delta
| root_id | ADDED | MISSING | SIZE_MISMATCH | current_nodes | dirs_enumerated |
|---------|------:|--------:|--------------:|--------------:|----------------:|
| D_BLACKBOX_DESKTOP_INIT_R1 | 0 | 0 | 0 | 17 | 3 |
| D_BLACKBOX_REMOTE_LINK_R1 | 0 | 0 | 0 | 17 | 2 |
| D_JQ | 0 | 0 | 0 | 126 | 8 |
| D_PIT_PRODUCTS | 1 | 0 | 0 | 47 | 13 |
| D_backtest_lab | 0 | 0 | 15 | 24524 | 4861 |
| D_backtest_lab_backups | 0 | 0 | 0 | 10775 | 3055 |
| D_backtest_lab_candidate_releases | 0 | 0 | 0 | 31 | 9 |
| D_backtest_lab_shadow_experiments | 0 | 0 | 0 | 8722 | 2680 |
| D_blackbox_data | 0 | 0 | 0 | 1140 | 7 |
| E_BLACKBOX | 50 | 42 | 126 | 8908162 | 223027 |

## PID lineage
- venv/parent **20796** → worker **source_reconcile_r1.py** **22336**
- worker START 2026-10-15T02:14:46+0800 → DONE 2026-10-15T03:58:26+0800
- ACK pid historical: 34236
- active source_reconcile at delivery: **false** (no second run started)

## DB on C only (not uploaded)
| db | bytes | sha256 | quick_check |
|----|------:|--------|-------------|
| CURRENT_ENUM.sqlite | 9812078592 | ffb4caa64c4b95e3fe60a5d071799530e8c32b4a4f80692d79aa976e967a01b6 | ok |
| DELTA.sqlite | 147456 | 6f68cdb84eee5a70dd67b6fbf008bde79a2a8ea8325b050f8f9b8071a4f0e5d4 | ok |

Paths:
- `C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014\db\CURRENT_ENUM.sqlite`
- `C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014\db\DELTA.sqlite`

## Scripts (local src)
- `C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014\src\source_reconcile_r1.py`
- `C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014\src\reparse_nofollow_r1.py`
- see SCRIPT_REFS.json for sha/bytes

## Artifacts in this delivery
- SAM_REPORT.md
- SOURCE_RECONCILE_SUMMARY.json
- FILE_SHA256.json (uploaded bytes only)
- SCRIPT_REFS.json
- DB_FACTS_ON_C.json
- DELTA_SAMPLES.json
- DELTA_SHARD_ALL_234.csv
- GATE_OUTBOX.json

## Notes
- Queue empty + roots done → COMPLETE; delivery refresh only, **no rescan**.
- Metadata/current mismatch is real (234 deltas), not an incomplete scan.
- HISTORICAL_CONTENT_MATCH remains UNPROVEN (baseline lacks content-hash plane).
- Do not treat this COMPLETE as migration authorization.
