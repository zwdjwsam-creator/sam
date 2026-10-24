# R06 review and R07 correction: diagnose layers before asserting source absence

User steering received during preparation: all required data layers must be searched before a missing-data conclusion; prioritise import order, time indices and binding defects. The source data must not be re-downloaded merely because one consumer does not serve it.

The drafted acquisition runner was not uploaded, authorized or executed. R07 performs NO new network/data acquisition. This correction is part of R07, not an extra budget cycle.

## Actual top-level authority located and read

Existing HUB sources:
- agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R04/source_contracts/S5_AI_ENTRY_MEMORY/AGENTS.md (entry, absence gate, HAND-first and time rules).
- HAND.txt at that same source set, coverage-control section (lines 142-159 in the staged body).
- agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1429/source_reads/S_COVERAGE_NONREG_GATE.json (complete normative body).
- R04 source_contracts/S4_UPDATE_PUBLICATION/BLACKBOX_HAND_CACHE_FIRST_WORKFLOW_POLICY_R1.json (complete).

The relevant HAND clauses are:
NO_AGENT_MAY_DECLARE_DATA_MISSING_WITHOUT_COVERAGE_DIAGNOSIS
RAW_REDOWNLOAD_DEFAULT=FORBIDDEN_IF_RAW_COMPLETE
PATCH_CANNOT_SERVE_AS_FULL=true
FULL_HISTORY_NON_REGRESSION=true

The fixed existing diagnosis vocabulary distinguishes SOURCE_MISSING, RAW_COMPLETE_CLEANING_MISSING, CLEANING_COMPLETE_CACHE_MISSING, CACHE_COVERAGE_REGRESSION, CACHE_PRODUCT_UNAVAILABLE, READER_LOAD_MISSING, READER_DATE_SLICE_MISSING, FILTER_EMPTY, UNIVERSE_EMPTY, PIT_ASOF_EMPTY, SOURCE_LIMITATION, REQUEST_OUTSIDE_PRODUCT_COVERAGE, AMBIGUOUS_DATASET and UNKNOWN_STOP.

The exact referred .mdc, coverage diagnoser, absence gate and ledger bodies are not all available in the inspected HUB tree. Retrieve their full bodies through the existing index in R07, rather than pretending the summary is the complete implementation.

## R06 evidence accepted within scope

Both candidate price partitions contain 959896 rows, each adding 5212+5214 to the observed parent 949470. Non-target rows were preserved; the stock daily view contains all 232 inherited files plus two added units. Replay and the four-date candidate read succeeded. Legacy CURRENT and original data were unchanged.

UTF-8 interpreter mode resolved the supplied fixture's locale-dependent read. It did not require a business-data repair. All following commands explicitly use -X utf8.

These observations prove the bounded candidate repair. They do not prove system-wide source absence, full engine readiness or a completed latest-data update.

## Correct prior overstatements

- Current CACHE having no record at a date is a consumer/layer fact. My earlier shorthand 'data gap' was imprecise and must not be promoted to missing original data.
- The two stock dates already have positive RAW and intermediate CLEAN evidence. They are an import/inheritance/serving issue; source absence and re-download are forbidden for that scope.
- R06 date-set comparisons for other products are observations, not established source holes. Re-evaluate against the actual calendar, security universe, periodicity, NAV publication and PIT/known_at semantics. ADJUST_FACTOR's dates are not an authoritative exchange-calendar substitute.
- Eighteen catalog entries lacking a directory under one cache release do not establish eighteen missing datasets. CACHE_MANIFEST_REGISTRY_R1 and CACHE_DEPENDENCY_REGISTRY_R1 are registry products; Tushare products may bind through their own namespace/sidecar roots; minute planes have separate unified/clean roots.
- R9 accepted file/content fidelity is strong migration evidence, not a reason to assume every original business scope was complete. Conversely, a failing current query is not migration-loss evidence. Trace expected entity/path/hash and acceptance history before attributing a loss to transfer.

The user's view that originals remain complete is the investigation starting point, not a substitute for evidence. Positive source findings are retained and cannot be contradicted by a shallower negative lookup.

## GPT-authored enforcement and local recompute

r07_claim_guard.py prevents a cache-only miss from becoming a source-absence or re-download decision. The R07 approved source-absence receipt set is intentionally empty: no new global absence claim or download is authorized. This supplements, rather than replaces, the existing diagnoser. Future GPT instructions may pin an actually reviewed receipt; the local operator may not edit that decision.

r07_rebuild_local.py hash-checks the complete supplied compiler and extracts only compute_factors and market_structure, without running module startup, write_static_registries or main. It reads the full stored price prefix through the R06 candidate and recomputes stock-derived candidates.

EMA12/26 are recursive: a 250-session-only reload cannot reproduce the full stored-prefix state. The source's tip-rebase code clips to 2026 before computing, while full-history formulas imply a continuous prefix. R07 explicitly uses the full stored prefix. This can differ from legacy year-reset outputs; record that distinction rather than forcing equality against a reset cache.

Market core metrics can be recomputed. The five SW fields are not produced by that pure function and remain null with an explicit PARTIAL status. No stale industry breadth or all-product READY is invented. No engine, adjusted-price or production publication readiness is implied.

## Independent tests performed

test_r07.py passed 15 synthetic controls: layer classification, positive RAW evidence blocks download, R9 attribution constraint, unreviewed absence receipt blocked, r1 arithmetic, rolling-250 arithmetic, full-prefix EMA, causal prefix stability, post-restoration returns change, duplicate-key rejection, candidate file build, explicit SW unknowns, replay and parent preservation.

The test scope is synthetic Arrow/parquet plus exact original formula functions. No desktop business rebuild, global absence search, supplier call or production update was performed by GPT here.

R07 scope: finish current local consumer-chain recovery and a reusable complete layer-diagnosis ledger; source retrieval/update can resume only through a later explicit contract based on that diagnosis. Final goal remains functioning desktop data access, engine compatibility and repeatable updates.
