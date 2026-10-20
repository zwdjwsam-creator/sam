# CONTRACT_MATRIX_V2 — 1940 review fixes

parent: BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925  
review_id: BLACKBOX_COVERAGE_CANDIDATE_REVIEW_20261020_1940  
status: CANDIDATE_V2 (not production)

## SHA

| Module | SHA256 |
|---|---|
| `code_v2/blackbox_data_coverage_common_r1.py` | `78031def8cc4b6caa3a7e824e93fad571bb8676cf6aee53398a7963b5c5963bf` |
| `code_v2/blackbox_cache_coverage_non_regression_gate_r1.py` | `0a5e203551ad3e9a02ee5d80ee12587de2644fce9e7b9d7458370a91672fccfc` |
| Rejected V1 common | `194f012f9a145e7924116628ac85dc0710fcf7d626e1bf86b1454a92d1deeacd` |
| Rejected V1 gate | `de9d49aaed965a5a8ad9ee054898e2abe85bd65c542301dc0ee9741388db6cc1` |

## Gate contract

- Empty `products` → `CACHE_RELEASE_PUBLISHABLE=false` / `REJECT_EMPTY_PRODUCTS`
- Parent missing / unverifiable / child unverifiable → reject (not PASS)
- Retention: `child_dates ⊇ parent_dates` for each product; **new dates allowed, lost parent dates forbidden**
- No count/min/max/percentage substitutes for set equality
- Unsupported product id → reject

## Extract contract

- Allowlisted products only: STOCK_DAILY_PIT_R1, STOCK_DAILY_RAW_PIT_R1, INDEX_DAILY_R1, STOCK_FACTOR_DAILY_R1
- Date columns allowlist per product (STOCK/INDEX: `date` only)
- Any partition error → `coverage_extract_status=UNVERIFIABLE` (never OK with errors)
- No pandas full-table schema fallback

## Mode contract

- FULL_HISTORY only if year_span≥2, distinct≥100, multi year_slices, extract OK
- Two dates → `DAILY_HISTORY_PARTIAL` (not FULL_HISTORY)
- Unsupported / unverifiable → `UNKNOWN_STOP`

## Classify / consumer

- Nested `cache.coverage.{min_date,max_date,distinct_dates,row_count}` + top-level `coverage_mode` for `control_plane_build.write_reports`
- No `TRUE_MISS_AFTER_ALL_PLANES` / `download_required=true` without verified scans; gaps → `CANDIDATE_OBSERVATION_UNVERIFIED_GAP` or `ENVELOPE_REVIEW`

## Calendar

- Authority: `P0_meta/calendar_cn_exchange/calendar_cn_exchange_v2_asof_*/CALENDAR_TRADE_DAYS.parquet`
- Formal columns: `trade_date` | `calendar_date` only
- Pure non-trade window inside coverage → `[]` OK
- Outside calendar coverage → raise UNKNOWN_STOP

## Adapter diff (candidate only)

- `code_v2/blackbox_data_access_resolver_r1.py`: `ROOT = Path(r"E:\\BLACKBOX")` pin so candidate path does not break pointers; coverage imports resolve from `code_v2/`
- Tests write fixtures under tempfile only; no E production writes
