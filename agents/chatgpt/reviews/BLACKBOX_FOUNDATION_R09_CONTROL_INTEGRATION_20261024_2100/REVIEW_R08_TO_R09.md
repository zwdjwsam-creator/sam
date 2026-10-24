# R08 source review and R09 implementation decision

Repository: zwdjwsam-creator/sam. Executor: ZHANGWEI. Review date: 2026-10-24.

R08's 23 original-body carriers have been fetched, decoded, and independently checked against their original SHA256 and sizes. The exact source identities are included in R09_IMPLEMENTATION_PACKAGE.json. R08 evidence work is closed for this handoff; this is execution round R09/10, with R10 remaining after its delivery. This is not foundation acceptance.

## Established facts and corrections

1. Migration fidelity was technically accepted separately. The present record does not establish migration-caused data loss. A cache miss, unreadable schema, unbound producer, or incomplete registry is not proof of source absence. The R08 stock candidate conserves its declared input keys; it does not certify every product, historical symbol universe, or latest update.
2. OEL-03's claimed transitive bypass is withdrawn. The daily orchestrator invokes the TIP compiler; TIP_COMPILER imports and calls publish_atomic. The real publisher defects are insufficient proof and sequential multi-head publication, not absence of that call. Do not add a second publisher call to the orchestrator.
3. The real shadow gate intentionally permits only SYNTHETIC_FIXTURE, SCHEMA_ONLY, METADATA_ONLY and CONTRACT_TEST_ONLY. REAL_MARKET_DATA and the other six real-data roles remain forbidden even when real_data_authorized=True. TaskEntryController belongs to this shadow architecture, not the production BulletTrade engine. Do not transplant it as a real-market admission service.
4. Fifteen canonical admission gates versus forty reason codes is not a defect by count. A semantic predicate/applicability/order mapping is needed. A rejection code need not be renamed to a gate name. Full MASTER admission remains unproven.
5. VERTICAL_RULE has fourteen phases, P0 through P13. Its CURRENT/governance seals refer to the R22 finance pair. Those receipts retain that scope; they cannot certify the current September pair or the R08 candidate by changing IDs. Current pointers identify the mounted release; historical seals prove only their recorded generation. Neither source silently overrides the other as a certificate.
6. TIP_COMPILER contains SW L2/L3 upstream release routes in inject_sw. The broad 'no L2/L3 writer' statement is withdrawn. Those exact pointer routes require generation/content qualification; a route alone does not prove current materialization. Universe/tradeability producer ownership and adjustment refresh receipt remain unresolved.
7. The acquisition architecture and PAGINATION body are not evidence that all downloaders are absent. This pagination module is an offline simulator with a blocked live path. Other located downloaders retain their own contracts. Historical live-canary flags or old quota lessons are not new download authorization.
8. The root directory map is a historical renaming record; project INIT/readme files are not the live product registry. Preserve orphan/mojibake roots as non-authoritative pending consumer evidence. No rename, delete, symlink or new directory-SSOT system is needed.
9. Ten lesson assets versus nine index rows is a metadata discrepancy, not proof that lesson 009's body is missing. Keep source evidence and repair scope separate. Six-lane rules can permit explicitly justified DEGRADED states; do not invent an all-six-PASS prerequisite.

## Source-grounded repairs supplied by GPT

build_r09_control_successor.py checks four exact original bodies and applies unique text anchors into an isolated successor tree. It does not modify their originals.

| Component | Reproduced defect | R09 successor behavior |
|---|---|---|
| Must-read preflight | Missing expected rule/kernel SHA can report VERIFIED | Missing/malformed SHA blocks; mutating CLI options are disabled in this successor |
| Request capability | Missing/string field evidence can pass; gap/alternate branches evade the field check | Explicit boolean True required for all three formal-ready branches |
| Causal capability | Missing known_at can become PASS after the clock cutoff; backtests can omit signal time | Backtest signal and explicit timezone/known_at evidence required; malformed timestamps fail closed |
| Shadow admission | An allowed result can parse another payload, replay, or survive later failed validation | Exact payload fingerprint, current result identity and single-use consumption required |
| Publisher | Pair/root identity incomplete; sequential CURRENT writes mislabeled atomic | Candidate dry-run only; root, Cleaning/Cache pair and generation checked; live call always rejected before matrix/writes |

The publisher successor deliberately does not repair production multi-head atomicity. Existing live-write code remains unreachable in it. A successful dry-run matrix is separately reported and never authorizes CURRENT. Complete date/symbol/field coverage, anti-lookahead proofs, coherent reader-generation binding and commit/rollback evidence are still required before any live publication decision.

The request-capability successor is built and tested, not installed as the production resolver. It does not transform min/max declarations into full history proof. The existing R08 exact-key/field gate remains the stronger candidate non-regression check. Do not restore the older date-only gate over it or install a compatibility shim into the two-byte production stubs.

## Actual ordered candidate entry

r09_control_runtime.py connects four executable stages:

1. Patched CACHE-class must-read preflight. It uses the established _base dependency but runs in a child with network and all file writes denied. It never uses --acceptance or --write-manifest. If imports/preflight fail under that guard, STOP; do not relax it.
2. Bind the exact R08 manifest, unchanged CURRENT pair, selected price/factor artifacts and four applicable original rule/memory bodies. No broad traversal or latest-path guess.
3. Read the two selected 2026 candidate partitions, check exact key/field non-regression, and compare the two recovered dates for 000001.XSHE. Open the already located 399303 canonical file through the pure schema adapter. This is explicitly diagnostic; RAW index adaptation does not authorize engine RAW fallback, PIT or full history admission.
4. Exercise a synthetic shadow admission once, reject the real-market role, and reject a live publisher call before its matrix can run. No formal engine startup or download is hidden in this entry.

Thirty-eight offline controls passed on the review host, including real synthetic Parquet reads through this entry, original missing-field bug reproduction, preflight preventing all downstream callbacks, changed-artifact rejection before parsing, and all seven real roles remaining closed. This is test evidence, not a claim that the desktop command has already passed. The exact result is R09_OFFLINE_TEST_RESULTS.json.

## Remaining operating-floor boundaries

The executable candidate provides reliable bounded reads and rejects unsafe transitions. It is not the entire operational database. R09 must return a compact evidence-linked matrix separating these layers: copied assets, classified assets, usable read requests, formal engine admission, incremental RAW staging, and publication/latest freshness. No layer borrows another layer's PASS.

Reuse R04-R08 inventories for all product/provenance/rule rows. Preserve the original data ecology: JQ versus non-JQ; RAW versus Cleaning/PIT/Cache; factor observations versus strategy artifacts; virtual unions versus materialized members. Do not make old strategies a prerequisite.

For update ordering, reuse the actual applicable source rules: checkpoint/backfill/exclusion before any acquisition; fixed RAW_NONE minute sequence A5m -> A1m -> A30m -> A60m -> ETF5m -> ETF1m -> ETF30m -> ETF60m; missing-only/cap pagination with exhaustion receipts; append-only RAW; Cleaning/align/PIT; cache key/field non-regression; coherent generation; formal publication; then freshness/completion accounting. The minute sequence is not a license to impose that order on unrelated interfaces. External Tushare phase namespaces and overlap watermark rules remain separate. Credentials are referenced by existing local locators only.

The four broad unresolved ownership/receipt items are not source gaps and do not authorize re-download. R09 should narrow them using existing inventories and the exact current consumers' references; do not rerun the global scan. Supply only decisive, previously undelivered bodies identified by those records, preserving byte transport when needed. R10 must use the returned evidence to decide the final supported operating scope and exact remaining blockers. Never force acceptance to satisfy the round budget.

FOUNDATION_ACCEPTANCE=false
ORDER_ALLOWED=false
PRODUCTION_CHANGE_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
