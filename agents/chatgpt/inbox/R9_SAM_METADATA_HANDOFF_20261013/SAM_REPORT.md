# SAM REPORT — R9_SAM_METADATA_HANDOFF_20261013_1524

generated_at: 2026-10-13T07:34:12.656847+00:00
hostname: SAM
HANDOFF_READY: pending_upload_confirm
COPY_AUTHORIZED: false
FULL_MIGRATION: false

## D repaired snapshot
- inner_sqlite_sha256: 4c094df43ca348acdc89498a49660ad9120d7ca3ef9bfe21f8b3c9e414257795 (48635904 bytes)
- gz_sha256: d0a17dc4dd76c9d825d01015ffd17cbd207565aceb13faa2c8ad22a72f98d3f3 (3589403 bytes)
- integrity: ok
- computed: {"file_paths": 34745, "directories": 10637, "reparse": 16, "unique_entities": 34744, "unique_content_bytes": 8163480337, "unresolved_identity_rows": 0}

## E delta canonical
- sqlite_sha256: aa58ed8bd7b22e015a041133007a9b031514eb82baf27d80ace0e48f2a48bd1c (86016 bytes)
- files=42 targets=16 errors=0 null_identity=0
- identity: Win32 dword volume serial + 64-bit file index (r9fix handle_identity)
- historical delta sha retained: 9f1a37...

## Tests
{"D_ROUNDTRIP_SHA_INTEGRITY": true, "DELTA_CANONICAL_COUNTS_AND_IDENTITY": true, "D_BASELINE_SQL_MATCH": true}

## Next
Desktop pulls HUB artifacts into new C dir; implement real D+E+delta validators. No copy/format.
