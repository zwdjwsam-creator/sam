# R10 review: partial diagnostic delivery; full foundation NOT ACCEPTED

Executor for rework: ZHANGWEI. Parent task: BLACKBOX_FOUNDATION_R10_OPERATING_ENTRY_AND_FINAL_SCOPE_20261024_2230.
This is R10 remediation, not a completed foundation or a new self-designed R11.

## User instruction and acceptance decision

The user expressly requires all foundation and incremental-operation prerequisites to pass before new incremental acquisition starts. The user also authorized continuation when acceptance fails. Exhausting ten planned slots does not end authorized remediation and does not permit a false PASS.

FOUNDATION_ACCEPTANCE=false
FORMAL_ENGINE_ADMISSION=false
INCREMENTAL_PIPELINE_READINESS=NOT_ACCEPTED
LATEST_FULL_UPDATE=NOT_VERIFIED
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false

Do not start downloads, supplier authentication/probes, auto-updaters, schedules or a night-mode orchestrator. The previous one-row JQ access test is scoped historical evidence, not current blanket access. No account, subscription, source or restricted-domain expansion is authorized.

Distinguish:
1. Prerequisite readiness: executable download/clean/cache/publication contracts, resource boundaries, failure/restart behavior and original-rule gates verified before acquisition.
2. Latest update completion: measured per-domain result after a separately issued acquisition task.
No circular claim that a future download has already completed is required or permitted. Both remain unaccepted now. This distinction grants no acquisition permission.

## Evidence actually reviewed

Source bundle: agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/

Reviewed R10_REPORT.md, R10_ROUND_STATUS.json, R10_FULL_GOAL_ASSESSMENT.json, R10_COMMAND_AND_EXIT_LEDGER.json, R10_PACKAGE_INTAKE.json, R10_REAL_BOUNDED_QUERY.json, R10_REAL_NEGATIVE_CONTROLS.json, R10_REAL_UPDATE_PLANS.json, R10_DESKTOP_ENGINE_IMPORT_OUTCOME.json and delivery/readback manifests; inspected executed entry and import-probe sources.

Independently recomputed UTF-8 byte lengths and SHA256 against the manifest for:
- captures/DESKTOP_OFFLINE_CONTROLS.txt: 1235 bytes, match.
- captures/DESKTOP_QUERY_STOCK_RAW.txt: 3562 bytes, match.
- captures/DESKTOP_ENGINE_IMPORT_PROBE.txt: 816 bytes, match.
- executed_code/blackbox_operate_r10.py: 11988 bytes, match.
- executed_code/engine_import_probe_r10.py: 5902 bytes, match.
This is not an independent hash verification of every file in the bundle. The local upload readback is retained as reported evidence for other files.

Accepted only within measured scope:
- 24 offline synthetic controls passed on the desktop.
- catalog/describe/update-plan diagnostics ran; 41 entities, 13 explicit updater joins.
- One candidate query returned 4/4 requested stock/date keys with finite close observations.
- Six negative requests were rejected.
- Original engine modules imported structurally in a guarded child. An import-time os.mkdir was attempted and denied.

The engine's module-level Logger initialization attempts os.makedirs("./logs"), then swallows the exception. This explains the probe verdict. It is NOT evidence of a missing dependency or an established engine startup failure. Do not install packages, remove guards or patch only a logger to assert full engine readiness. An unguarded import was not tested. Formal provider admission, engine construction and runtime remain unproved.

## Concrete R10 delivery omissions

The original task required:
- 2026-08-28..2026-09-02 query with open,high,low,close,volume,money. Delivered query used only close.
- 2025-09-22..2025-09-24 inherited-year query. No corresponding capture or ledger entry was delivered.
- update-plan for STOCK_DAILY_RAW_PIT_R1. Six other plans were delivered instead; the exact stock plan is not in the capture list.
- Byte-identical operations guide installed in _OPS/CURSOR_WORKSPACE plus preservation and append-only linking of root AGENTS.md. No installation, original backup or pointer readback evidence was delivered.
- FINAL_REQUIREMENT_MATRIX.json, FINAL_BLOCKERS.json and R10_STATUS.json. Assessment/round reports contain useful partial facts but do not fully replace the five-requirement matrix, including strategy artifact identification and documented access boundaries.
- Exact implementation-package delivery/reference. R10_IMPLEMENTATION_PACKAGE.json is not in the inbox tree.

No failure is inferred from a missing capture. Classify these as NOT_EXECUTED_OR_NOT_DELIVERED until literal evidence exists. Do not reconstruct stdout from a report, narrow fields or select an easier history window.

## Material integration blockers retained, with correct scope

1. Adjustment: recorded COVERAGE count 12182523 vs R07 physical count 12266026 (83503 difference); 2026-09-01 measured at 11 rows. Requires same-scope partition/key/field and source-transform reconciliation. Neither count wins by declaration. Sidecar is not a supplier receipt.
2. Universe/tradeability: current producer and request coverage are unproved in the reviewed join. R10 navigation has an explicit tradeability updater declaration. "Producer unbound in evidence" does not mean no producer exists locally. Reconcile source identity, actual callable and measured scope before implementation.
3. Required view members: reported empty FUND members are observations at specified cache roots. Complete registered-layer search remains necessary before any original-source absence statement. No silent ETF-only union is accepted.
4. Current versus candidate: R10 stock candidate query serves the recovered dates while the old mounted release may not. Keep candidate, CURRENT and raw presence separate; do not re-open an already-closed candidate defect as if no recovery occurred. The "11 products" observation is a historical measured scope, not an all-layer absence verdict.
5. Formal engine: diagnostic module import is insufficient. Exact provider/field/time/PIT/universe/status/matching and generation contracts must be wired and tested.
6. Update/publication: update-plan prints navigation; it proves no writer, checkpoints, resume, non-regression, coherent release or freshness. Preserve applicable distinct stock/factor/minute/finance/external lanes and paid-source exclusions.
7. Generation: selection pointers, release provenance, product-addition manifest and seal have different roles. Historical identities remain unchanged; a fresh serving/admission envelope must bind actual sources. Relabelling old metadata is not a repair.

The five end requirements remain the user's original goal. Diagnostics are useful infrastructure, not completion.

## Source reuse for GPT-owned follow-on implementation

Do not ask for or re-export bodies already present merely because a later summary omitted them:
- R04/source_engine/S3_ENGINE_SOURCE/globals.py already supplies the full logger module.
- R04/source_engine and source_contracts contain original engine/provider/API and rule-library bodies.
- R06/source_bodies/cache_compiler_daily_incremental_r1.py and R04/access_resources/source_bodies/S4_UPDATE_PUBLICATION__run_blackbox_daily_incremental_data_plane_r1.py are available.
- R08/exact_original_bodies_2025 contains 23 original-byte carriers, including must-read, ingestion, pagination, compiler/publication, rules and lesson bodies.
- R09_CORRECTION/ADJUST_FACTOR_SIDECAR_RECONCILIATION.json and GENERATION_IDENTITY_ROLES.json retain the precise source/identity evidence.

Local AI may inventory, read, copy exact supplied files, run exact commands and report facts. It must not invent a new harness, data policy, producer, business-code patch or admission rule. GPT owns substantive repair code and rule integration after original bodies and applicable contracts are reviewed. A missing body should be requested by exact original path only after confirming it is absent from existing HUB resources.

Complete the bounded R10 rework in the companion outbox instruction. Do not claim the seven material predicates are closed merely because delivery omissions are corrected.
