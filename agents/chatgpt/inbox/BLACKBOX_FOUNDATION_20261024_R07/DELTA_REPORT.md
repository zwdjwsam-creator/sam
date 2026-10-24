# R07/10 delta report — search all layers before asserting absence, repair local consumption

Round: 7 of 10. Remaining cycles after delivery: 3.
Host: ZHANGWEI. Predecessor: R06.
FOUNDATION_ACCEPTANCE=false, ORDER_ALLOWED=false, PRODUCTION_CHANGE_AUTHORIZED=false.
Network calls: 0. Downloads: 0. Source-absence claims: 0.

## 1. User steering applied

The steering was applied as written: complete the cross-layer search before declaring data missing; treat current failures first as import/inheritance/time-index/resolver problems. The tentative R07 stock download was NOT executed and no acquisition runner was created.

## 2. Offline controls: PASS

`test_r07.py` passed 15 of 15 synthetic controls with the hash-pinned compiler body
(sha256 c8ddf805a6ddc998cda507f2aa5c92f27b13a43b5445e5bfed21477c5822f336, identical to the R06 delivery and to the task source).
Controls cover claim-guard behaviour, RAW-presence blocking, CLEAN/CACHE distinction, R9 non-attribution, r1/MA250/EMA arithmetic, causal prefix stability, post-restoration return change, duplicate rejection, candidate build, explicit SW partiality, replay and parent preservation.

## 3. Local derived rebuild: BLOCKED by a pre-existing data-shape fact

The first real invocation stopped on `ValueError: PRICE_INPUT_NULL` at `r07_rebuild_local.py:48`.
Per contract nothing was edited, deleted or re-run for idempotence.

Exact scope of the failure:

- Panel rows read: 12,351,786 (2014..2026), 13 physical partitions, year 2026 taken through the verified R06 candidate override.
- Null rows: 34,477 with open/high/low/close/volume/money null, all inside `year=2026`, dates 2026-01-05..2026-08-06, 344 codes, 143 dates.
- Every null row carries `source_version=BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260924_20260925_034534`.
- Family A: 42 codes whose first valued date equals the security master `start_date` (e.g. 603468.XSHG listed 2026-08-06). Pre-listing grid rows.
- Family B: 302 codes absent from `SECURITY_MASTER_SNAPSHOT_R1`, zero rows in 2025, exactly 105 null rows each ending 2026-06-12. Codes carried into a 2026 calendar grid without any observation.

Consequence: the guard is a full-panel predicate and the offending rows pre-date R06 and are present in the pinned parent, so no local filter or re-download can satisfy it. This is a GPT-owned ingest/densify decision (keep the rows with an explicit non-observation predicate, or compact them with row-conservation accounting).

No candidate directory was created; `candidate_releases/R07` does not exist. R06 remains intact.

## 4. Layer search: the two-date drop is consumption, not source

Positive RAW units exist for BOTH dates in every examined dataset:

| dataset | RAW 2026-08-31 | RAW 2026-09-01 |
|---|---|---|
| stock daily | 5,212 rows | 5,214 rows |
| ETF daily | 1,623 rows | 1,624 rows |
| index daily | 7 rows | 7 rows |
| valuation | 5,212 rows | 5,214 rows |
| adjust factor | 5,212 rows | 5,214 rows |
| NAV batches | 537 files | 537 files |

Cache side against the authoritative calendar (3,097 sessions, 2014-01-02..2026-09-24; both dates are sessions):

- STOCK_DAILY_PIT_R1 / STOCK_DAILY_RAW_PIT_R1 / STOCK_FACTOR_DAILY_R1 / MARKET_STRUCTURE_DAILY_R1: exactly 2 missing sessions.
- ETF_DAILY_PIT_R1 / ETF_FACTOR_DAILY_R1: products hold only 39 sessions starting 2026-07-30; both dates missing.
- INDEX_DAILY_R1 / INDEX_FACTOR_DAILY_R1: 139 missing sessions in the 2014..2026 window — 137 consecutive 2026-01-05..2026-07-29 plus the two dates.
- VALUATION_PIT_R1: 48 distinct dates against 2,003 expected sessions.
- FUND_NAV_PIT_R1: 8 missing day-keys, all eight of which have dated RAW NAV batch units.
- STOCK_TRADEABILITY_PIT_R1: 24 of 39 in-window sessions; 15 missing including both dates.
- MARKET_UNIVERSE_PIT_R1: no holes inside its window, but the window ends 2026-07-20.

Negative controls inside the same release: ADJUST_FACTOR_PIT_R1 is 3,097/3,097 complete and all three SW structure planes serve both dates with rows. That proves the two-date drop is product-specific, not a release-wide truncation.

No examined product justifies SOURCE_MISSING. The widest class is CLEANING_COMPLETE_CACHE_MISSING, then CACHE_PRODUCT_UNAVAILABLE.

## 5. Pinned contract chain

Read and hashed: kernel, the CACHE-class manifest (BOOTSTRAP + DATA_ACCESS, both sha-matching), the diagnosis-gate rule, the coverage gate rule, the three-layer statement rule, HAND lines 141-160, the three coverage ledgers, and the three tools. Bodies were staged only where not already delivered.

Three tool/contract identity defects were found:

- `blackbox_data_coverage_common_r1.py` is 2 bytes, so `--dataset STOCK_DAILY` always returns `STOCK_DAILY_CLASSIFIER_UNAVAILABLE`, `authority_ready=false`.
- `blackbox_cache_coverage_non_regression_gate_r1.py` is 2 bytes, so `FULL_HISTORY_NON_REGRESSION` and `PUBLISH_ALLOWED=false` are declared but unenforceable.
- The diagnoser's enum is disjoint from the pinned 14-member HAND enum; only `UNKNOWN_STOP` overlaps, and `SOURCE_MISSING` is not reachable.

This is the actual mechanism behind "the database is missing data": the official diagnoser cannot answer, so the observable cache hit rate is used as a substitute.

## 6. Time-index and binding defects

See `TIME_INDEX_AND_IMPORT_DEFECTS.json` (12 entries). Highest consequence after D01:

- D02 stale calendars inside the authority directory: `CALENDAR_ALL_DATES.parquet` and the bare `CALENDAR_TRADE_DAYS.parquet` both stop at 2026-08-10 and report both dates as non-sessions; path-sorted "latest" selection returns the stale file.
- D07 `FUND_LIKE_ASSET_VIEW_R1` unions ETF with an empty `FUND_DAILY_PIT_R1`, silently degrading to ETF-only.
- D12 the RAW adjust-factor unit's `date` column holds an ordinal 0..5211, so a calendar-date filter on it returns zero.

## 7. Pinned claim enforcement

`r07_claim_guard.py` authorises zero `SOURCE_MISSING` claims and zero re-downloads (approved receipt set is empty by design). Every ledger entry carries a classification from the fixed enum plus the evidence that produced it. No approval hash was created and the guard was not edited.

## 8. What is deliberately not claimed

Not claimed: MARKET_STRUCTURE_DAILY_R1 or STOCK_FACTOR_DAILY_R1 recomputed; all products ready; engine ready; adjusted-price plane ready; latest supplier coverage; R9 migration loss; any global absence; FOUNDATION_ACCEPTANCE.

## 9. Next implementable steps (GPT-owned)

1. Decide the D01 policy for non-observation grid rows and supply the corresponding guard predicate or compaction rule.
2. Restore `blackbox_data_coverage_common_r1.classify_stock_daily` and align the diagnoser enum with the 14-member HAND enum.
3. Implement `blackbox_cache_coverage_non_regression_gate_r1.py` so lost sessions block publication.
4. Bind the calendar authority explicitly and retire the stale competing files, or make selection asof-explicit.
5. Fail-closed the FUND-like view when a union member is empty; materialise `FUND_DAILY_PIT_R1` / `FUND_FACTOR_DAILY_R1` from RAW.
6. Materialise ETF full history and the index 2026 H1 plane under an explicit contract.
7. Extend the universe plane to asof, and refresh the coverage ledger windows.
