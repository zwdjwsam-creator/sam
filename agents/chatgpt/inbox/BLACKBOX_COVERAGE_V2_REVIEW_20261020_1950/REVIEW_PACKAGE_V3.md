# REVIEW_PACKAGE_V3 — BLACKBOX_COVERAGE_V2_REVIEW_20261020_1950

## Status
**CANDIDATE_V3_READY_FOR_REVIEW**

V1/V2 retained. Production E untouched (2B stubs).

## Exact SHA
| File | SHA256 |
|---|---|
| `code_v3/blackbox_data_coverage_common_r1.py` | `49046e63b09c0a09096a079a4b033a35ebc9e87ae981785afcb87fa3d6cce5ee` |
| `code_v3/blackbox_cache_coverage_non_regression_gate_r1.py` | `b3cb6b22ebf1b6ed0dd143ac1e487dfed35337d76b8020adf4b2d4f9af32509b` |
| `code_v3/blackbox_data_access_resolver_r1.py` | `42037d19238ff212c78e835a06476f39085f94500820f1246215e34771c82a51` |
| Rejected V2 common | `78031def8cc4b6caa3a7e824e93fad571bb8676cf6aee53398a7963b5c5963bf` |
| Rejected V2 gate | `0a5e203551ad3e9a02ee5d80ee12587de2644fce9e7b9d7458370a91672fccfc` |

## Review point 1 — resolver final license
Minimal candidate resolver diff (block §11 coverage):
- Pass `product_id` into `product_date_coverage`
- `coverage_ready` requires: supported product + extract_status==OK + empty errors + mode not in {UNKNOWN_STOP, EMPTY_OR_MISSING, INCREMENTAL_PATCH}
- Unsupported / no-window → `coverage_ready=false` (never default True)
- Window path uses day-set completeness only after license checks
- `resolved/READY` path existence unchanged; coverage license separate

Tests: UNVERIFIABLE+subset → ready false; CORP no window → ready false; never UNKNOWN+ready.

## Review point 2 — FULL_HISTORY evidence
Removed 2yr/100-day thresholds.
FULL_HISTORY only if:
1. contiguous `year=YYYY` for every year in [min,max]
2. every trade day from formal calendar in [min,max] ⊆ extracted dates
Otherwise `DAILY_HISTORY` (existing consumer enum) = history completeness unproven.
Sparse 100-date endpoints → not FULL_HISTORY.

Calendar authority: CURRENT asof match → else `BLACKBOX_RAW_COVERAGE_LEDGER_CURRENT.json` `trade_calendar_authority` → else refuse (no lexicographic latest).

## Windows
- 2026-09-01..09-10: coverage_ready=false (missing 09-01 observation)
- 2026-09-02..09-10: coverage_ready=true (candidate query chain only)

## Not claimed
PRODUCTION_READY / deploy / redownload / Manifest rewrite / causal backtest eligibility.
