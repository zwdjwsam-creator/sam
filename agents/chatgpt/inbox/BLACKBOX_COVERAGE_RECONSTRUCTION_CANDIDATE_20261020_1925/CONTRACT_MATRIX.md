# CONTRACT_MATRIX — BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925

status: CANDIDATE_RECONSTRUCTION (not original restore)  
host: ZHANGWEI  
COPY_AUTHORIZED=false  

## API surface (candidate)

| API | Source callers | Semantics / evidence | This round support | Refuse when unknown |
|---|---|---|---|---|
| `product_date_coverage(path)` | resolver; control_plane_build | Returns exists/min/max/distinct/dates/year_slices/row_count; date-column projection only | Hive `year=*/part_*.parquet` with discoverable date col (`date`/`trade_date`/…) | No date col → `coverage_extract_status=DATE_COLUMN_UNKNOWN`, empty dates (not fake READY) |
| `infer_mode_for_product(id, cov)` | resolver; control_plane_build | FULL_HISTORY / DAILY_HISTORY / INCREMENTAL_PATCH / UNKNOWN_STOP / EMPTY_OR_MISSING | STOCK_DAILY* + INDEX_DAILY historical set; generic DAILY heuristics | extract unknown/empty → `UNKNOWN_STOP` |
| `load_trade_calendar(start,end)` | resolver; control_plane_build | Formal CN exchange trade days from P0 parquet | `calendar_cn_exchange_v2_asof_*` preferred | 0 days in window → raise (no Mon–Fri fake) |
| `find_calendar_trade_days()` | control_plane_build | Authority calendar path | same | missing file → FileNotFoundError |
| `cache_current()` / `cleaning_current()` | control_plane_build | CURRENT JSON → release_id + standard_root | `数据/回测缓存/CURRENT_CACHE_RELEASE.json`, `数据/清洗成品/CURRENT_CLEANING_RELEASE.json` | missing JSON → exception |
| `raw_stock_daily_dates` / `cleaning_stock_daily_dates` / `cache_stock_daily_dates` | control_plane_build | Window vs calendar day-set; gap counts | STOCK_DAILY plane only | other datasets → not implemented here |
| `classify_stock_daily(start,end)` | diagnose; control_plane_build | Multi-plane root_cause; `raw_status` COMPLETE/INCOMPLETE | STOCK_DAILY | calendar fail → UNKNOWN_STOP |
| `compare_coverage(expected, available)` | imported by control_plane | missing list; complete flag | generic day-set | n/a |
| `HISTORICAL_REQUIRED` / `CRITICAL_BACKTEST_PRODUCTS` | control_plane_build | prior ledger shape | STOCK_DAILY_PIT_R1, INDEX_DAILY_R1 critical | others optional |
| `now_cn` / `wjson` | control_plane_build | helpers | yes | n/a |
| `gate(parent, child, products)` | control_plane_build.run_qa | fat→thin reject; `CACHE_RELEASE_PUBLISHABLE` | STOCK_DAILY_PIT_R1 proven on sealed fat/thin | unknown extract on required fat parent → regression |
| `self_test()` | control_plane_build.run_qa | `PATCH_FULL_HISTORY_GATE_TEST.PASS` | synthetic mode check | n/a |

## Explicit non-goals / refuse

- Do **not** invent `cache_stock_daily_pit_r1_reader_r1` (resolver name is convention only).
- Do **not** treat min/max envelope as middle completeness.
- Do **not** write E:\BLACKBOX\脚本, Manifest, CURRENT, RAW, sealed.
- Do **not** claim PRODUCTION_READY / full BLACKBOX recovery.
- Security listing/suspend completeness: **not** in this candidate (refuse / out of scope).
- Control-plane ledger rebuild / publish: **not** run.

## Contradiction notes

1. Old cache ledger (2026-08-12) showed CORP products as UNKNOWN_STOP with 0 dates; current CURRENT release CORP may expose a date column → mode may be DAILY_HISTORY. Candidate follows live extract, not frozen ledger.
2. Window 2026-09-01..09-10: calendar expects 2026-09-01; CURRENT STOCK_DAILY sample for 000001 starts 2026-09-02 → `coverage_ready=false` / gap=1. Candidate **blocks** rather than READY-washing.
