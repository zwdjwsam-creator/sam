# FOUNDATION EXECUTION GUIDE (R08/10, tip 1950)

Scope: what each foundation artifact means, which authority governs it, who produces and consumes it,
which predecessor permits the next step, and which rule stops a wrong step.
This is a reading guide, not a new policy. FOUNDATION_ACCEPTANCE=false. ORDER_ALLOWED=false.

## 0. How to read the bundle

| file | use |
|---|---|
| SOURCE_AND_RULE_BODY_INDEX.json | every body cited here, with live SHA256, effective status and whether it is enforced |
| ROOT_SEMANTIC_ROLE_MAP.json | 23 role rows covering the 41 observed root directories |
| ORDERED_EXECUTION_AND_FAILURE_MAP.json | 4 workflows, per-transition contracts and evidence strength |
| WRONG_STEP_TRIGGER_MATRIX.json | 14 concrete wrong steps with the rule, the code and the card |
| ENGINE_ORIGIN_PATH_RECHECK.json | the 21 recorded engine paths, hashed in place |
| PROVENANCE_CORRECTIONS.json | the two withdrawn claims |
| OPEN_EXECUTION_LINKS_FOR_GPT.json | 15 real gaps |

Evidence strength scale: TEXT_REFERENCE_ONLY < CALLSITE_PROVEN < ISOLATED_TESTED < ACTUAL_ENTRY_EXERCISED.
Nothing in this round reaches ACTUAL_ENTRY_EXERCISED for the engine admission chain.

## 1. Authority and phase (group 1)

Order: conversation -> injected kernel rule -> AGENTS.md -> TASK_CLASS -> MUST_READ manifest -> preflight -> PASS.

- HAND.txt is stable: SHA256 `f709e9b5000ab2c7d499ec312fc6be4cdb2934b4ce45fc94b6b10f40020af96b`, identical to the SHA GPT pinned, 107154 bytes. No delta.
- HAND appends assign DATA_BASE_ACTIVE_PHASE three different values (P1 at line 566, P2 at 578, P12_L5 at 598).
  They are chronological snapshots. The effective value is the CURRENT file plus the latest applicable append:
  `active_phase = L5_RESEARCH`, L1-L4 SEALED, P12 PASS, P13 CONDITIONAL (PHASE2B HELD).
- Vertical rule `BLACKBOX_HAND_DATA_BASE_VERTICAL_PIPELINE_R1` keeps NO_PHASE_SKIP=TRUE and 13 phases P0..P13.
  No runtime guard implements it (OEL-01). Do not claim it is enforced.
- The phase CURRENTS embed R22 cleaning/cache ids from 2026-08-14. The live pointers are
  cleaning R33 / cache FUND_NAV asof 2026-09-24. Pointer wins; embedded ids are historical (OEL-11).

## 2. Identity and discovery (group 2)

`request -> resolver -> product/reader -> coverage -> capability -> result` (BLACKBOX_DATA_ACCESS_MUST_READ).

- Path READY is not request readiness. The resolver resolves a path and a reader; the capability resolver decides
  whether this specific window/grain/field set can be served (`REQUEST_READINESS=AVAILABLE_FORMAL`, `TASK_DATA_GATE=PASS`).
- Finance statements are ambiguous by construction: `AMBIGUOUS_DATASETS` requires `--scope` (CONSOLIDATED vs PARENT).
- Aliases are an explicit table; there is no fuzzy match.
- The resolver registry snapshot `BLACKBOX_DATA_ACCESS_INDEX_CURRENT.json` has 37 products but was generated against the
  2026-08-17 cache release, 38 days behind the live CURRENT. Quote the pointer, not the snapshot.

## 3. Controlled transformation (group 3)

Declared order (cache-first rule + anti-leak tail + six lanes):

SOURCE_DOWNLOAD -> RAW_CURRENT_UPDATE -> CLEAN -> ALIGN -> ANTI_LOOKAHEAD_PIT_GATE -> CACHE_COMPILER ->
CACHE_QA_EQUIVALENCE -> ATOMIC_PUBLISH -> CACHE_CURRENT -> RESEARCH_BACKTEST

- Field/time normalization (CLEAN) is distinct from cross-product alignment (ALIGN). Do not collapse them.
- Acquisition is paginated by contract: PAGINATION_COMPLETE, ORDER_DETERMINISTIC, DUPLICATE_LOSS=0, SILENT_TRUNCATION=0.
  A 5000-row page is not completeness. The acquisition engine's live path is deliberately a stub.
- Cache build inherits the parent release; any dependent product must be recomputed or exactly inherited (OEL-02 blocks proof).
- External evidence is an isolated plane: tushare_p0 for financials, p1 holders, p2 fund, p3 index;
  tip_start = max(data_max-3d, hist_end+1d), never HIST_START outside a first build.

## 4. Verification and release (group 4)

BUILD != PUBLISH. The only atomic publisher found is `publish_atomic()`:
generation must equal `cache_release_id`, every production product must be AVAILABLE_FORMAL, then a backup and a pointer write.

Two problems, both real:
1. The non-regression gate that must refuse a release with lost dates is a 2-byte stub (OEL-02).
2. The daily orchestrator never calls the publisher; it runs the TIP rebase compiler and then refreshes scope (OEL-03).

Therefore: no CURRENT switch is justified by this bundle, and no release may be called verified on the strength of
the publish gate alone.

## 5. Consumption and feedback (group 5)

Absence: RAW -> Cleaning -> Cache -> Reader -> Filter, then the closed verdict enum from the absence gate.
`CONFIRMED_ABSENT` requires rows==0 AND pagination complete AND completeness COMPLETE. Everything else is UNKNOWN_*.
This is a diagnosis order, not a reversal of cache-first consumption. Empty is not NO_DATA.

Engine admission: 15 ordered PRE_INGESTION gates (source identity -> ... -> final decision), each BLOCK with
`BLOCK_*_GATE`, warning pass forbidden, post-ingestion repair forbidden, formal_backtest_active=false.
The live implementation `PreIngestionGate` uses a different 40-code vocabulary and runs inside
`TaskEntryController` (MASTER -> PRE_INGESTION -> parse). `bullet_trade/core/engine.py` does not import it.
Treat the 15-gate text as authoritative in intent and unenforced in code (OEL-07, OEL-08).

## 6. Memory roles (do not merge)

| root | role | enforcement |
|---|---|---|
| 经验卡 | 10 incident cards + index + manifest (download, quota, PIT, 5000 cap, wrong phase) | no loader; agents select by trigger |
| 记忆盘 | 17 machine lessons + approval ledger + archives | no runtime reader; expected_block_mode is declarative |
| 研究记忆 / DAILY_RESEARCH | research continuity (brief, trace, calls) | separate role; must not be promoted to a rule |
| HAND lines 1284-1301 | the separation itself | effective |

A lesson that HAND explicitly mandates keeps that mandated role (LESSON_JQDATA_010 / EXTERNAL_EVIDENCE_WRONG_PHASE_FULL_TIP_GUARD_R1).
Everything else stays a lesson, not a rule.

## 7. The two corrected statements

1. The engine is at its original package layout, all 21 recorded paths present with matching SHA256.
   Flat delivery names are copies, not layout. See ENGINE_ORIGIN_PATH_RECHECK.json.
2. H1 2026 index rows come from the full-history release ending 2026-08-04
   (`index_daily__399303_XSHE__to_20260804.parquet`, sha256 1c5b5d2b...), not from the five-session August gap release.
   Both releases keep their own role. Nothing was edited to make this true.
