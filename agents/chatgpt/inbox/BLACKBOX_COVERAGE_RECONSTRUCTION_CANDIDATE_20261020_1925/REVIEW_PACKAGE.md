# REVIEW_PACKAGE — BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925

## Status
**CANDIDATE_READY_FOR_REVIEW**

## What changed (candidate only)
Isolated under:
`C:\LAN_SHARE_REPORT\BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925\candidate\`

| File | Role | SHA256 |
|---|---|---|
| `blackbox_data_coverage_common_r1.py` | reconstructed common | `194f012f9a145e7924116628ac85dc0710fcf7d626e1bf86b1454a92d1deeacd` |
| `blackbox_cache_coverage_non_regression_gate_r1.py` | reconstructed gate | `de9d49aaed965a5a8ad9ee054898e2abe85bd65c542301dc0ee9741388db6cc1` |
| `blackbox_data_access_resolver_r1.py` | working copy for import path proof | (copy of E resolver; unchanged logic) |
| `tests/run_candidate_tests_r1.py` | isolated risk tests | — |

Production E stubs remain 2-byte CRLF (`7eb70257…`). **Not overwritten.**

## Logic basis
Rebuilt from actual imports/calls in:
- `脚本/blackbox_data_access_resolver_r1.py` (product_date_coverage / load_trade_calendar / infer_mode)
- `脚本/blackbox_data_coverage_control_plane_build_r1.py` (full symbol set + gate/self_test expectations)
- `脚本/blackbox_data_coverage_diagnose_r1.py` (`classify_stock_daily`)
- Sealed ledger shapes in `运行/BLACKBOX_*_COVERAGE_LEDGER_CURRENT.json`
- Prior fat/thin forensic releases referenced by control_plane_build

## Candidate results (see TEST_RESULTS.json)
- Formal calendar: weekend 2026-06-07 excluded
- CURRENT STOCK_DAILY_PIT_R1: FULL_HISTORY, distinct_dates=3095, min=2014-01-02, max=2026-09-24
- Middle-gap day-set incomplete even if endpoints present
- fat(ASOF_20260810) → thin(INDEX_DAILY_732): `CACHE_RELEASE_PUBLISHABLE=false`
- fat → CURRENT restored: publishable=true
- Sample `000001.XSHE` 2026-09-01..09-10: 7 rows / 7 dates (missing calendar day 2026-09-01 on this code/window) — historical fact read only
- Modules loaded from candidate path (not E stub)

## Production untouched
- No E:\BLACKBOX\脚本 overwrite
- No Manifest / CURRENT / RAW / sealed / index publish
- No daily-increment / research / strategy start
- Original 2B files + R9 evidence preserved

## Risks
1. Not byte-identical to lost original; API inferred from callers + ledgers.
2. Full-product date extraction scans year parquet date columns — OK for STOCK_DAILY; heavy products may need future index (candidate does not invent coverage index files).
3. RAW plane year-batch scan may report gaps if partition naming/columns differ from expectation — fails closed.
4. Deploying without review could change resolver READY semantics for windows with true gaps (intended).

## Minimal deploy diff suggestion (NOT executed)
1. Human review CONTRACT_MATRIX + tests.
2. Copy only the two modules into `E:\BLACKBOX\脚本\` after backup of 2B stubs.
3. Re-run resolver smoke with `_request_start_date/_request_end_date` for STOCK_DAILY_PIT_R1.
4. Do **not** auto-publish CACHE CURRENT; do **not** regenerate control-plane ledgers unless separately authorized.
5. Keep `cache_stock_daily_pit_r1_reader_r1` unimplemented (consumers use path+parquet).
