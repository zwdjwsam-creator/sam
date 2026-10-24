# BLACKBOX_FOUNDATION_R03_OF_10_RUNTIME_PROVIDER_CORRECTNESS_20261024_1424

TO: ZHANGWEI / Cursor E Agent
HOST: ZHANGWEI
TASK_FAMILY: BLACKBOX_FOUNDATION
STATUS: READY
BUDGET_SLOT: 3/10
REMAINING_CYCLES_BEFORE_THIS_TASK: 8
VISIBLE_PREDECESSOR: BLACKBOX_FOUNDATION_20261024_R01
R02_COMPLETION_EVIDENCE: NOT_OBSERVED_IN_HUB
FOUNDATION_ACCEPTANCE: false
ORDER_ALLOWED: false

## Mandatory communication and language
All newly uploaded reports, comments, generated explanations, status messages, and technical documentation must be in English. Preserve literal original paths, source keys, dataset identifiers, and necessary source quotations exactly, including Chinese characters; explain them in English. Do not rename source data or bulk-translate historical archives.
Upload detailed evidence to HUB only. Keep Cursor conversation output minimal. After successful artifact upload and readback, the final Cursor reply must be exactly:
END
No punctuation, links, or long report. A blocked result must also be accurately uploaded before ending; never label a failed upload as completion.

The user confirms eight remaining execution/review cycles. This task consumes the first of those eight, using budget slot R03/10. HUB currently exposes a completed R01 report but no R02 report. Preserve that distinction; do not fabricate a completed R02 or restart the budget.

## Review and scope
Reuse the R01 working tree, executable ecology registry, real-read examples, and earlier accepted evidence. Do not rescan the disk, rehash the migration, rerun the 950-document queue, reconstruct old strategies, or redownload history.
The registry and local data access are useful candidate progress, not engine integration or full coverage acceptance. A method-name count is not interface conformance.
Independent review:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R01_REVIEW_20261024_1424/REVIEW_R01.md
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R01_REVIEW_20261024_1424/reproduce_r01_edge_cases.py
The two counterexamples use exact R01 methods in a standard-library harness with source/Arrow stubs. They reproduce wrong file selection from a build timestamp and admission of an event without an announcement date. They do not execute real data, Windows, or the engine. The harness intentionally asserts old behavior; update the expected outcomes in the new regression suite.

## Deliver one working runtime/provider increment
Use the existing E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024 tree. Combine the following fixes and tests into one result, rather than opening a new reporting cycle for each issue.

### 1. Provide a working dedicated runtime
Inspect the already known interpreters and project dependency declarations. Reuse a suitable working interpreter if available; otherwise create a dedicated candidate virtual environment under the recovery tree and install only the dependencies needed for the reader and the safe DataProvider contract test, following the project's compatible constraints.
This task explicitly authorizes creating that isolated environment and installing its necessary packages from the configured trusted package source. Do not alter global Python, the broken historical .venv, production configuration, or account/environment files. Do not ask the user to install pandas or manually edit pyvenv.cfg.
Record the actual executable, versions, dependency lock and reproducible launch command. No broker or live-provider installation unless needed for the isolated approved interface.

### 2. Fix correctness before wiring the engine
- File selection: use the existing manifest/file-index coverage, frequency, security/batch and version evidence. Build timestamps are not data coverage. Do not recursively enumerate the whole dataset on every request.
- Read completeness: track selected, attempted, loaded, unreadable, and budget-skipped files separately. A read exception or file budget must not be silently dropped while returning OK. Row and file truncation must both prevent complete-success admission when requested coverage is unproven.
- Time filtering: preserve the actual request timestamp and timezone, not just its date. Enforce the applicable bar availability/announcement/PIT cutoff. A rule description string is not enforcement. Unknown knowable time must be explicitly rejected or withheld for historical/as-of use.
- Adjustment: R01 accepts fq=pre/post without applying an adjustment. Implement only an evidenced conversion, otherwise reject those modes explicitly; never relabel RAW_NONE as adjusted.
- Revisions and duplicates: use authoritative layer/revision priority and applicable time semantics. R01 keeps the last iterated row, while day files precede year files, so order can select the wrong revision. Conflicting equally authoritative values must be exposed, not silently discarded. Shuffling file enumeration must not change the result.
- Dataset routing: resolve stock/ETF/index requests through the registry and actual security classification. Do not route all securities to stock datasets. Reject unsupported or mixed requests explicitly rather than reading an unrelated root.
- Types/nulls: do not silently use unsafe casts or replace failed conversions with null while claiming complete success. Required-field nulls need field-specific admission decisions, not only the all-null check. Preserve money/amount units and original adjustment identity.
- Registry scope: replace hardcoded universal 2014 start dates/global cleaning-asof cursors with the actual per-dataset rules, observations and watermarks. Undefined ranges remain explicitly undefined; do not make the next updater redownload history from an invented start.
- Keep factor values blocked where the original policy forbids them. Factor-dictionary permission is not value-download permission. Minute joins may use existing daily/reference data only with correct code/date and knowable-time semantics; missing evidence must not become factor=1 or fabricated trading status.

Do not repeat full index-weight or finance investigations. Preserve the corrected component-code mapping and the existing historical_backtest_eligible restriction. Reopen only a specific finding needed by the implemented interface.

### 3. Add the actual engine-contract adapter
Read the real DataProvider base and relevant callers, including method signatures, expected index/column layout and exceptions. Adapt the candidate envelopes to the engine's actual successful return types; retain provenance and enforce rejected/partial results before returning a DataFrame.
get_price parameters missing from R01, including count/skip_paused/panel/fill_paused and other declared arguments, must be implemented according to the contract or explicitly rejected. Do not accept and ignore them through arbitrary kwargs.
Run real runtime conformance against the actual safe-loaded engine base in the dedicated environment. Static AST method presence alone is insufficient. If full package initialization has side effects, safely load the necessary leaf contract without executing trading/download initialization, and label the narrower test scope accurately.
Keep formal_backtest_active/engine_core_active and production factories unchanged this cycle. This is a validated candidate adapter, not permission to bypass PRE_INGESTION gates or activate live trading. Do not change the old dictionary snapshot E-drive restriction to make a value-provider test pass.

### 4. Make the structure unambiguous
Provide a compact English SYSTEM_STRUCTURE.json or equivalent, using actual inspected files and configuration:
launcher -> interpreter -> registry builder/query -> per-dataset source binding -> local reader -> contract adapter -> actual engine base/API entry;
and the separate existing download/update entry -> per-dataset cursor -> candidate output -> publication boundary.
For each relevant node/edge, give the real path, callable/config key, evidence location, current versus candidate status, read/write/network behavior, and the applicable rule. Reuse the existing 66-entry directory map; do not make another directory listing.
No guessed path, filename keyword, or historical document assertion may be presented as a confirmed active connection. If an edge is unclear, inspect the named source/configuration and resolve it, or report the exact unresolved edge and its impact. Do not claim an absent connection merely because a narrow search missed it.

## Required verification
Use small fixtures plus bounded real-data requests; do not rerun whole-source audits.
1. A file built in 2026 but covering 2014 is excluded from a 2026 coverage request.
2. A file-read failure and a file-budget overflow cannot produce a complete OK result.
3. Intraday queries exclude later bars; unknown event announcements cannot pass a supplied as-of gate.
4. Unsupported adjusted prices are rejected, or their actual adjustment is checked against the declared factor semantics.
5. Day-file/year-file overlap, null fields and conflicting revisions produce deterministic correct results or explicit rejection under shuffled file order.
6. Supported stock and ETF requests resolve to the correct dataset; an unsupported asset/source fails clearly.
7. A bounded real-data request is returned through the runtime DataProvider-compatible adapter with the expected DataFrame layout, and unsupported parameter combinations do not silently pass.
8. Reconcile R01's handwritten 22 daily rows with SMOKE_RESULTS' 10 rows. Derive the expected window from the applicable calendar/security/coverage rules, not a hardcoded count. Generate all current English summaries from one canonical test result.

Report genuine pass/fail and supported scope. Do not require all market history to prove this small runtime increment. Full engine invocation can remain a separately identified next-stage edge if this cycle verifies only the leaf contract.

## Delivery and next cycle
Upload only changed/new candidate code, an English current registry/index, dependency lock and runtime command, machine TEST_RESULTS.json, SYSTEM_STRUCTURE, and a concise English DELTA_REPORT plus ROUND_STATUS.json. Preserve old evidence by reference.
ROUND_STATUS must record budget slot 3/10, remaining-after-delivery=7, the visible predecessor, actual execution, unresolved edges, and the smallest next step toward engine integration and a real latest-data incremental update.
Provide English consolidated current artifacts rather than re-uploading translated historical logs. Read back critical artifacts before updating INBOX_FOR_CHATGPT.

Allowed writes: isolated candidate code, runtime/dependencies, fixtures, tests, reports, and HUB. Production RAW/CLEAN/CACHE/CURRENT, original engine/rules, R9 state, and account files remain unchanged. No business API calls, data downloads, publication or strategy execution this cycle. Package installation for the dedicated runtime is the explicit exception for network access.
After upload and readback, Cursor final reply: END
