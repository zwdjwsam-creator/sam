# R05 review: accept bounded evidence; execute candidate-only gap recovery

FOUNDATION_ACCEPTANCE=false. R06 is slot 6/10: five cycles before this task, four after delivery.
No extra cycle is charged for this review.

## Evidence and decisions

R05 reports exact GPT-script execution and matching candidate hashes. The one ordinary JQ check authenticated successfully at 2026-10-24T16:00:26+08:00, returned one daily row and reported spare quota 200,000,000. This establishes that bounded request only. No repeated authentication is needed for R06.

The original engine API swallowed a marked provider rejection as an empty frame; the helper candidate propagates it. The test is an exact function-path harness with controlled startup, not an activated engine or full MASTER admission.

The two RAW units exist with pinned hashes, 5,212 and 5,214 rows, matching sidecars, no duplicate keys and zero observed numeric nulls. R05 now directly queried both cache partitions and found zero rows on the target dates. Intermediate sealed releases contain the corresponding units. The recorded parent graph supports loss of sibling increments when later releases reused an older parent. The precise historical driver body remains unavailable; the family source is not a byte-identical substitute. It is unnecessary to reconstruct that driver to recover these two hash-pinned units.

Evidence reused/read for this implementation:
- R05 GAP_REPAIR_INPUTS, delta/status/execution/access result and the existing partition-attribution body.
- Full supplied formal_cleaning_r15_build_and_seal_r1.py: parent hardlink inheritance and ingest_item path/passthrough rules.
- Existing full cache_compiler_tip_rebase_from_current_r1.py: rebuild_price_2026 and its tag_pit body.
- Existing full blackbox_daily_increment_common_r1.py: tag_raw_pit and exact RAW_PIT_FIELDS.
- Earlier update invariants: no thin-product replacement, BUILD != PUBLISH and paired generation integrity.

## Required interpretation corrections

1. The R04 actual CURRENT cleaning pointer identifies R33_FUND_NAV_ASOF_20260924 with R45 as its parent/quarantine/ledger. R05 calls R45 the active release. Do not choose by label. The supplied repair snapshots the actual CURRENT bytes, follows standard_root, verifies the cache's source_cleaning_release matches and records realpaths. If these disagree, report and stop that branch.
2. R05 calls the two other unmatched RAW files superseded because later retry files exist in CLEAN. That establishes selection history, not authoritative equivalence or revision precedence. Preserve both source versions; no automatic newest-build rule is approved.
3. The August permission receipt supports historic paid-module denial for get_money_flow, get_all_factors and a valid get_factor_values request. Several missing finance table names/invalid factor names are PROBE_FAIL, not paid entitlement denials for every grouped leaf. Separate per-interface evidence. Continue the existing skip policy without repeating probes; no entitlement change has been reported.
4. Constant factor=1 in a RAW_NONE source does not establish a usable forward/backward adjustment series. Do not infer adjusted-price support from this repair.

## GPT-authored candidate recovery

r06_gap_repair.py:
- Snapshots the actual matching CURRENT pair, never a hardcoded stale release parent.
- Reads only the bounded daily directory, exact two RAW units/sidecars, adjacent control and two cache year partitions.
- Builds a new inherited stock-daily candidate and adds exact RAW bytes at their evidenced clean_rel paths.
- Maps the two dates to the existing cache schemas using the observed compiler tags; verifies the mapping against the already-processed adjacent unit, excluding only the new lineage ID.
- Rejects unknown columns, differing adjacent mapping, changed inputs, existing target rows, duplicate keys or incomplete inheritance. No local guess fills a schema gap.
- Preserves every non-target cache row; adds exactly 10,426 rows to each affected 2026 partition if the R05 inputs remain unchanged.
- Exposes inherited unchanged products through explicit sparse references instead of copying the whole database.
- Creates a diagnostic registry binding for the candidate stock-daily root; keeps other registry entries and does not certify their inherited claims.
- Supports an output-verified idempotent replay, without creating duplicate rows.

This is an explicit candidate view, NOT a sealed formal full release. Old base references remain necessary and must not be removed. Physical product roots are inherited; registry/sidecar product reconciliation is a separate gate.

STOCK_FACTOR_DAILY_R1, MARKET_STRUCTURE_DAILY_R1 and any additional dependent products must be recomputed/revalidated before full readiness. Neither inherited status nor an unchanged maximum date is a new capability proof. No fake FULL_HISTORY, REQUIRED_FIELDS_OK or gap-free flags are generated.

## Publication design and test boundary

r06_bundle_store.py demonstrates one candidate-generation commit marker rather than separate legacy CLEAN/CACHE pointer replacements. Consumers of that candidate marker capture one manifest and resolve explicit overrides/inherited roots. This addresses the visibility boundary for those consumers only. Legacy readers of independent CURRENT files do not gain atomic consistency from it.

test_r06.py passed 11 synthetic Arrow/parquet controls: exact two-day recovery, all parent files retained, other product retained, non-target rows unchanged, candidate registry binding, idempotence, original inputs unchanged before deliberate fixture corruption, before/after-commit injected failures, stale parent rejection and corruption rejection.

Tests use isolated temporary files. They are injected failure tests, not hardware power-loss tests or a Windows kill/restart certification. A hard interruption may leave a writer lock or partial candidate; the operator must preserve/report it instead of deleting it blindly.

No production pointer replacement is authorized in R06. The generation helper is exercised in fixtures only. A real end-to-end candidate read on ZHANGWEI is still required.
