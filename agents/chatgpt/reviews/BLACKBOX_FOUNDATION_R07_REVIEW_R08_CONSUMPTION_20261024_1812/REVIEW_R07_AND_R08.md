# GPT review of R07 and R08 corrective contract

Reviewed at: 2026-10-24T18:12:00+08:00
Repository: zwdjwsam-creator/sam, main
Predecessor inbox: agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R07/
Disposition: BOUNDED_EVIDENCE_ACCEPTED; GLOBAL_SEARCH_CLOSURE_AND_FOUNDATION_ACCEPTANCE_NOT_ACCEPTED
Budget: R07 consumed slot 7/10. R08 is slot 8/10; two deliveries remain after R08.

## Accepted evidence

The exact R07 supplied files were executed without edits; the 15 offline controls passed. The real build correctly stopped before candidate creation on PRICE_INPUT_NULL. R06 and original data were preserved. The observed inherited all-null price rows, the explicit calendar version, and the three historical tool defects are useful measured evidence. No download, source-absence claim, migration-loss attribution, or production publication is accepted or requested.

The original RAW units for the two stock dates are present, and R06 already rebuilt their candidate consumption path. The same two dates have positive RAW evidence in ETF/index daily and valuation. These facts reject a source-loss explanation for those exact units; they do not certify every field, symbol, period, or downstream product.

## Corrections required before any global claim

1. L04 did not list/open the full index-daily plane explicitly mandated by the contract:
   E:\\BLACKBOX\\数据\\原始只读\\strategy_data_plane_additions\\INDEX_DAILY_RAW_FULL_HISTORY_R1
   The mandatory rule names this 732-index plane and includes 399303.XSHE. P3 seven-index daily patches and the minute plane cannot stand in for it. Do NOT aggregate minute bars or acquire index daily data before resolving this plane and its registered overlaps.
2. Positive RAW existence does not establish Cleaning completeness. L03/L04/L06/L09 classifications must be justified by actual corresponding Cleaning observations; otherwise retain layer-scoped facts and UNKNOWN_STOP. NAV batch filenames are not pagination-exhaustion or observed NAV-value proof.
3. L08's stale universe end alone is not proof of coverage regression. Regression needs a pinned earlier/baseline scope that was lost. Distinguish REQUEST_OUTSIDE_PRODUCT_COVERAGE from established loss.
4. L10 FIELD_NOT_CACHED is a cache-miss reason, not a source limitation when the RAW fields are present. Keep diagnostic root-cause, cache-miss reason, acquisition completeness, and runtime admission separate.
5. ADJUST_FACTOR has 3,097 dates but only 11 rows on 2026-09-01 in the report. Date coverage is not symbol-by-date coverage or valid adjustment authority. An ordinal RAW date axis is not a timestamp. Do not label the whole plane complete or use factor=1 as an adjustment series.
6. FUND NAV is not interchangeable with exchange-traded fund OHLCV. Never synthesize FUND_DAILY bars/factors from NAV to make a union nonempty. The view must reject an unserved member unless the exact product contract explicitly permits a qualified partial result.
7. SOURCE_AVAILABLE_AND_AUTHORITATIVE, SOURCE_AVAILABLE_AND_SERVED, and SEPARATE_NAMESPACE_OR_REGISTRY may be factual labels, not members of the pinned 14-value root-cause enum. Successful diagnosis may have root_cause=null and a separate success status; do not invent a new root cause.
8. Family-B arithmetic needs a correction: 302 * 105 = 31,710, not 31,488 null rows. Total A+B matches 34,477, but the statement “exactly 105 null rows each” is inconsistent. Produce the observed per-code distribution and correct the statement; do not invent an explanation.
9. Empty gate/common modules and enum incompatibility are observed defects. Their causal contribution to every historical miss or prior publication is not established by static inspection alone. Do not promote a mechanism hypothesis into a proven incident history.

## GPT-owned R08 price-observation policy

Do not modify/drop/fill original price data or R06 prices. A row with all six open/high/low/close/volume/money null is an UNOBSERVED_GRID_ROW, not a zero quote, a listing/delisting assertion, or a source-absence fact.

The candidate factor grid preserves every date/code and every source price value. Its derived columns are null on unobserved rows with an explicit status. A row with only some price fields null, an invalid key/date, nonfinite observed input, or invalid close/volume/money stops the build.

The hash-pinned original formulas run on contiguous observed segments. Explicit internal null runs reset rolling/recursive state; no forward/backward fill, zero return, or EMA bridge is invented. Leading placeholders do not become history. Formula version changes to univ_factor_r1_v1.R08_OBSERVED_SEGMENTS; outputs remain candidates, not silently compatible formal factors. Omitted dates not represented by rows are NOT thereby proved complete.

Market core counts observed quotes, not the authorized PIT investable universe. SW fields stay null with a partial status. No entire-market or engine admission follows.

## Supplied code and exact checks

- r08_rebuild_local.py builds a fresh R08 candidate from the pinned R06 view, preserving original data. It binds the explicit versioned calendar, records its full SHA, and checks its R07 prefix and exact scope. It never selects a calendar by glob.
- r08_coverage_gate.py tests exact keys and field observations. Losing a symbol on an otherwise retained date fails. It also provides bounded positive-evidence classification and an empty-member union guard.
- These are successor candidate controls, NOT an installed repair of the legacy HAND-path scripts and NOT a universal absence authority. SOURCE_MISSING and re-download remain unapproved.
- The live two-day check reads the hash-pinned RAW, byte-identical candidate Cleaning and candidate price partitions, proves date/code/close equality, and distinguishes published cache miss from candidate serving. This Arrow reader check is not engine startup or MASTER admission.
- test_r08.py: 23 offline behavioral controls PASS, including actual synthetic parquet builds/replay, tamper rejection, same-key value drift, observation state, causal-prefix stability and source-byte preservation.
- No desktop execution, network request, production switch, complete data foundation, or full-engine run was performed by GPT.

## Remaining critical path

R08: execute exact candidate repair and gates; correct the above evidence; deliver complete explicit source/reader/update bindings for R09 without another broad scan.
R09: GPT-owned integration and contract-driven update implementation, based on actual R08 evidence.
R10: end-to-end acceptance and any precisely authorized final update. The round limit never authorizes fabricated PASS or skipping a hard gate.

FOUNDATION_ACCEPTANCE=false
ORDER_ALLOWED=false
NETWORK_ACQUISITION_AUTHORIZED=false
PRODUCTION_CHANGE_AUTHORIZED=false
