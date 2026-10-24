# BLACKBOX FOUNDATION R08/10 — repair observed-price consumption and close explicit bindings

Issued: 2026-10-24T18:12:00+08:00
Recipient: ZHANGWEI / local Cursor AI
Predecessor: BLACKBOX_FOUNDATION_20261024_R07
Budget: slot 8/10; 3 remaining before this task; 2 remaining after delivery.
Do not create extra rounds or restart a general inventory.

## Objective and authority

Use the existing migration/inventory/contracts to repair the measured consumption defects. A failed/current reader is not a source-loss verdict. GPT owns all semantic/code changes; execute supplied code unedited and perform read-only inventories. Never improvise repairs.

Read the companion review completely:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R07_REVIEW_R08_CONSUMPTION_20261024_1812/REVIEW_R07_AND_R08.md

First run the actual Manifest preflight for CACHE and save its exact stdout/exit and Manifest/body hashes. Use the CACHE-class BOOTSTRAP/DATA_ACCESS files already delivered in R07. Read applicable HAND, three-layer, coverage, immutability and source-specific contracts. A preflight/hash failure blocks execution, not the remaining read-only handoff. Do not replace hard gates with a HAND_READ statement.

NETWORK_ACQUISITION_AUTHORIZED=false
AUTHENTICATION_ATTEMPTS_AUTHORIZED=0
NEW_DOWNLOADS_AUTHORIZED=0
SOURCE_ABSENCE_CLAIMS_AUTHORIZED=0
PRODUCTION_CHANGE_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
FOUNDATION_ACCEPTANCE=false

No production script replacement, legacy tool invocation with unknown writes, source cleanup, secret reads, or supplier calls are authorized here.

## A. Stage and execute exact GPT code

Recovery root: E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024
New scripts: reviews\R08\
GitHub source folder:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R07_REVIEW_R08_CONSUMPTION_20261024_1812/

Stage and verify byte-for-byte:
- r08_coverage_gate.py SHA256 9d90046c252b7f4c08786906cd3a95d28a5b3099493e4cb1f0ca8931fae982af
- r08_rebuild_local.py SHA256 46da05cb40ce73472ccb896916676d0f42a100d42ece4e46dcb764c64f5d8407
- test_r08.py SHA256 8b02040fa0f79211148292a992959469dc4c64e8401785e06a00c722c417d3d9

Copy unchanged dependencies into the same reviews\R08 folder:
- r06_bundle_store.py from the reviewed R06 package, SHA256 6c76c0de3aca7d96223e5883b68918c794585156e29c292962d438e6986269a2
- r07_rebuild_local.py from the reviewed R07 package, SHA256 a9759390564b1ac1dc20c1098e37a52199d4bb439990522babffc90352e18a03
- cache_compiler_source_R06.py from the R06 source delivery, SHA256 c8ddf805a6ddc998cda507f2aa5c92f27b13a43b5445e5bfed21477c5822f336

The R07 module is imported only for its checked pure-function extraction and physical parquet reader. Do not run the R07 CLI or the production compiler. Do not edit globals, source, tests, schemas, expected counts, approved receipts or hashes to force success.

From the recovery root execute:
    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R08\test_r08.py reviews\R08\cache_compiler_source_R06.py

Only if all 23 controls PASS execute once:
    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R08\r08_rebuild_local.py --compiler-source reviews\R08\cache_compiler_source_R06.py

Expected fresh output:
candidate_releases\R08\R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024\CANDIDATE_MANIFEST.json

If successful replay exactly once and require ALREADY_BUILT_VERIFIED with all source/output hashes unchanged. Read back both physical product partitions, the audit and manifest. Expected live null-state totals are 34,477 rows / 344 codes / 143 dates; the code independently measures them. R06 and all price inputs must remain unchanged.

No partial directory may be deleted or reused after a guard/build failure. Preserve traceback and exact input schema/counterexample, then continue independent read-only sections B/C. A guard failure does not authorize a local filter, repair, retry with modified code or download.

Do not infer UNKNOWN_SECURITY, pre-listing or delisting merely because a code is absent from today's security snapshot. The supplied policy preserves rows and only records observation state.

The code generates fresh candidate coverage gates and bounded RAW/CLEAN/CACHE/Arrow-reader diagnoses for the two days. These are not the installed legacy gate, universal search closure, MASTER admission or production readiness. No tool name/path may imply otherwise.

## B. Correct and finish the specific R07 evidence

Use the existing 54-dataset registry, 41-product catalog, R06 dependency plan, all recorded domain file lists and the 950-node body cache. No root-wide filesystem crawl or repeated minute data scan.

1. FULL index-daily plane first:
   E:\BLACKBOX\数据\原始只读\strategy_data_plane_additions\INDEX_DAILY_RAW_FULL_HISTORY_R1
   Use its registered file lists/manifests and all overlapping shards, not P3 seven-code patches. Read actual rows for 2026-01-05..2026-07-29, 2026-08-31 and 2026-09-01, including 399303.XSHE if present under the actual scope. Report frequency/fq, schemas, time/key/value semantics, observed code/date counts and source metadata. Record file/query errors as unknown. A missing dated filename is not a negative query.
   Do NOT derive daily bars from minute bars, infer seven indices represent 732, or download anything.

2. Correct the Family-B row-count claim using observed per-code null/valued counts. 302*105=31,710, whereas reported null rows were 31,488. Record the actual distribution and whether 105 refers to grid rows or null rows. Do not invent the explanation.

3. Correct root-cause/field-miss/completeness/admission axes as required by the review:
   - RAW files present != Cleaning complete.
   - Sparse NAV/publication records != absent daily market bars.
   - FIELD_NOT_CACHED != source missing or an unavailable vendor field.
   - Stale universe window != a proved regression without a baseline.
   - Date-set coverage != symbol/date/field completeness.
   - Successful observations have separate factual statuses; don't add to the fixed root-cause enum.

4. For ADJUST_FACTOR specifically, query the exact requested symbol/date keys and factors on both recovery dates in CACHE, registered current/intermediate Cleaning, and registered RAW. Trace the ordinal RAW date to sidecar/request/transform evidence. Do not reinterpret an ordinal as time or use a filename alone to certify a date. Distinguish point snapshots/change-event semantics from daily dense factors using the actual product contract. Report the 11-row September-1 fact without calling it full coverage.

5. FUND-like view: inspect the actual invoking reader and required union semantics. No automatic ETF-only success if a required member is unserved. Do not turn NAV into traded OHLCV, manufacture fund-price products, or treat the empty directory as lost original data.

6. Any genuinely unreadable/missing exact registered file goes into POTENTIAL_DATA_LOSS_REGISTER with exact path/entity/expected SHA and the indexed R9/local history already available. Search registered aliases/history/recovery sources. No broad rehash of R9, no migration-loss attribution from one path failure, no restore/download this round.

## C. Deliver implementation-ready bindings for the remaining two rounds

This is a targeted handoff from existing evidence, not another inventory project.

Create R09_IMPLEMENTATION_BINDINGS.json. Cover stock daily, ETF daily, index full-history daily, valuation, NAV, adjustment, security/universe, tradeability/ST/limits, SW structure, minute namespaces, external Tushare CBOND namespaces, and dictionary/factor-value distinctions. For each, carry existing proof forward by exact HUB path/blob/hash and supply only the missing implementation facts:

- exact authoritative logical product, supplier/provenance and RAW/CLEAN/CACHE/sidecar/view roots;
- registered file-list/manifest locator with full SHA; every overlapping shard relevant to the requested scope, including annual and increment files;
- each selected physical source's path, full SHA, row count, schema, time field/encoding, key/frequency/fq, actual scope, valued-observation counts, completeness/pagination evidence or explicit unknown;
- exact source/clean/cache revision precedence with original contract reference; conflicting overlapping values and unknown identity must remain blocked, never newest-filename wins;
- the actual complete transform/reader entry and its transitive local helpers, original schemas and PIT/known_at rules; no invented callables or imports;
- selected parent CURRENT pair and registry/catalog revision, candidate overrides and invalidated dependent products;
- exact reusable source bodies already on HUB by reference, upload only newly required missing bodies; actual creation/refresh code for current calendar, universe, tradeability, adjustment, valuation and FUND-like view reader if absent from prior handoffs;
- module dependencies and script call sites for legacy coverage-common/diagnoser/non-regression gate. The successor functions delivered here remain isolated until GPT supplies a tested compatible integration.

For source file lists, prefer existing canonical lists over enumerating directories. If a registered root/reference cannot be resolved, name that exact unresolved binding; do not guess or silently skip it.

Engine/runtime preparation: reuse the full R04 engine sources/contracts and R05 boundary patch, not re-upload them. Read the actual pyproject and lock/config references; list installed versus missing dependencies in the dedicated recovery runtime using metadata and pip check only. Capture exact current package entry, provider creation/injection, admission-gate wiring and all required 5 provider methods by source reference. Do not import a startup path that may auth/download, start a formal backtest, change MASTER outcomes, or claim a selected-function harness equals full-package startup. Any missing callable/helper body needed for R09 must be uploaded now, with full SHA.

Increment preparation: bind the existing daily scope/rules, no-retry/paid exclusion state, actual credential LOCATORS only, local coverage watermark per domain, target-calendar source, downloader request signature, safe output/receipt path, source-to-Clean-to-Cache successor flow and all publication gates. Never upload secret bytes/headers/cookies/.env or secret-dependent hashes. Do not repeat a paid permission probe. A previously validated one-stock query does not certify all interfaces.

## D. Delivery and communication

Publish one English-language bundle:
agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R08/

Required:
- DELTA_REPORT.md and ROUND_STATUS.json (slot 8/10, remaining 2)
- MUST_READ_PREFLIGHT.txt + hashes, GPT_CODE_EXECUTION.json, FIXTURE_TEST_RESULTS.json
- LOCAL_REPAIR_RESULT.json, actual candidate manifest or exact guard failure
- OBSERVATION_AND_NON_REGRESSION_EVIDENCE.json, TWO_DAY_LAYER_DIAGNOSES.json, replay/readback evidence if build succeeded
- R07_EVIDENCE_CORRECTIONS.json and INDEX_FULL_PLANE_PROBE.json
- R09_IMPLEMENTATION_BINDINGS.json plus only missing source bodies
- ENGINE_RUNTIME_AND_UPDATE_READINESS.json
- POTENTIAL_DATA_LOSS_REGISTER.json (may be empty)
- source/body index with full SHA and HUB references

Do not upload parquet, 8GB state/plan, a giant directory tree or duplicate prior source packages. Keep code/field/path identifiers exact even if Chinese; newly authored prose must be English.

Before close, upload the bundle, verify exact remote readback, update INBOX_FOR_CHATGPT.md to this R08 result and preserve predecessor pointers. Report literal outcomes; no forced PASS, source-absence claim, download request or extra round. No self-created WAIT_HUB_ACCEPTANCE mid-task.

After successful HUB readback, Cursor chat final response must be exactly:
END
