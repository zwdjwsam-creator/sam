# REVIEW_PACKAGE_V2 — BLACKBOX_COVERAGE_CANDIDATE_REVIEW_20261020_1940

## Status
**CANDIDATE_V2_READY_FOR_REVIEW**

Production E stubs still 2B; V1 candidate retained; no deploy.

## Review points (1940) → V2 result

| # | Blocking issue | V2 result |
|---|---|---|
| 1 | Gate % threshold / count-only; swap dates; missing baseline PASS | Set retention; lost_40/swap1/parent_missing/both_missing/empty_products all reject; no-loss+new dates allow. Real fat→thin lost_count=3064 reject |
| 2 | Partial extract OK | Bad parquet sibling → UNVERIFIABLE + UNKNOWN_STOP; gate rejects unverifiable child |
| 3 | 2 dates = FULL_HISTORY; arbitrary PIT date col | 2 dates → DAILY_HISTORY_PARTIAL; unsupported CORP → UNKNOWN_STOP / UNSUPPORTED_PRODUCT |
| 4 | classify missing cache nest; TRUE_MISS download | Nested cache.coverage present; download_required=false; root_cause ENVELOPE_REVIEW for 9/1 window observation |
| 5 | Fake-green tests | resolver.resolve_product actually called; coverage_ready=false for missing 2026-09-01; strict unsupported asserts |
| 6 | Calendar first-col / weekend | trade_date\|calendar_date allowlist; weekend empty OK; outside coverage refuse |

## Exact SHA
- common V2: `78031def8cc4b6caa3a7e824e93fad571bb8676cf6aee53398a7963b5c5963bf`
- gate V2: `0a5e203551ad3e9a02ee5d80ee12587de2644fce9e7b9d7458370a91672fccfc`

## Paths
Local: `C:\LAN_SHARE_REPORT\BLACKBOX_COVERAGE_CANDIDATE_REVIEW_20261020_1940\`  
HUB: under parent 1925 inbox `code_v2/` `tests_v2/` + this review folder.

## Not claimed
PRODUCTION_READY / original restore / redownload authorization / E deploy.
