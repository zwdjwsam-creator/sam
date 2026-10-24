# BLACKBOX local operating entry

Execution host: ZHANGWEI. Workspace: E:\BLACKBOX. The preserved engine source is in E:\BLACKBOX_ENGINES.

Read the existing BLACKBOX kernel and the task-class must-read manifest before operating. This guide is an entry pointer, not a replacement rule, seal, data dictionary or permission grant. Mandatory original contracts and applicable lesson cards remain authoritative within their recorded scope.

## Supported entry

Runtime:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\runtime\.venv\Scripts\python.exe

CLI:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R10\operating_entry\blackbox_operate_r10.py

Use `-X utf8` and `PYTHONDONTWRITEBYTECODE=1`. Do not use the old E:\BLACKBOX\.venv, which references the notebook base installation.

Operations:

- `catalog`: joins the 41 existing catalog entities to recorded physical schemas, dependency/field ownership, source-domain records and explicit update bindings. The four evidence inputs and their semantic hashes are fixed in R10_INPUT_SPEC.json. This does not scan the business tree or open its Parquet data.
- `describe --product PRODUCT_ID`: returns the actual recorded schema, provenance/physical binding and update route for that product. Unknown links stay unknown. JQ-compatible Tushare products are not JQ-native. A cache fact, factor, virtual union and vendor RAW file retain different roles.
- `query --product STOCK_DAILY_RAW_PIT_R1 --codes 000001.XSHE --start 2026-08-28 --end 2026-09-02 --fields close`: reads actual R08 candidate RAW_NONE observations. Supports at most five explicit canonical codes and a 31-calendar-day window, with the six recorded OHLCV/money fields. It checks the real must-read preflight, exact source/current/calendar hashes, every requested session/code key, field observations and post-read identity. It does not infer a universe, listing date, adjustment factor, tradeability or PIT eligibility.
- `update-plan --product PRODUCT_ID`: shows the recorded downloader/callable, credential locator if documented, checkpoints/watermarks and required processing order. It performs no login, request, download, write or publication. A historical download-gap label is a record to reconcile with later evidence, not authorization to re-download.

Every operation runs the genuine CACHE-class must-read preflight. A STOP is retained as a STOP. No callback substitution or local policy repair is allowed. A zero-row reader is never source absence; inspect the existing registered layer/search evidence before any missing-data statement.

## Scope and version identities

This entry selects the pinned R08 candidate manifest and its explicit overrides, preserving the mounted CURRENT pair as its parent. It does not switch CURRENT. Ordinary reads after the pinned calendar's last session (2026-09-24) reject until a new reviewed calendar/generation is bound. That rejection does not prove source absence.

Historical CURRENT/RELEASE/MANIFEST/SEAL records have distinct identities and incomplete bindings. Retain them. Do not edit old IDs/seals to make metadata agree. A supplied parent or source hash change stops the entry rather than silently rebinding to a different release.

The catalog is evidence navigation. A date range or date union is not every-symbol/field coverage. Metadata reporting CURRENT_SERVES_MEASURED_WINDOW is a historical statement, not a fresh serving verdict. In particular:

- INDEX canonical full history was already found and read in R08. Do not replace it by minute reconstruction or a blind download because an old cache reader skipped its canonical_code field.
- The universe's historical measured window is not a current trade filter.
- Adjustment COVERAGE.json is not an acquisition receipt; 83,503-row reconciliation and per-date lineage remain open.
- FUND_LIKE is a virtual union; an empty required member must not be silently treated as an ETF-only result.

## Engine and updates

engine_import_probe_r10.py `--desktop-import` performs one guarded import of the actual engine modules. It forbids file writes, network, secret-file reads, auth/data/order calls and engine construction. An import success is not a backtest, provider admission or profitable strategy. A blocked import reports its exact dependency/event; do not remove guards or install packages as a guessed fix.

Full formal engine admission remains separate: field/time semantics, universe, tradeability/limits, adjustment, known-at/PIT, session/matching contracts and generation bindings must satisfy their actual contracts. Synthetic shadow architecture remains synthetic only.

Incremental operation order is the applicable original contract: must-read -> checkpoint/backfill/exclusion -> registered layer search -> bounded stable request/pagination -> append-only RAW receipts -> Cleaning/align/PIT -> exact key/field cache non-regression -> generation-bound admission -> coherent publication -> per-domain freshness/completion. Preserve the fixed minute sequence only on its specified RAW_NONE minute lanes; keep Tushare namespaces and permitted DEGRADED lanes separate.

This entry authorizes no acquisition, CURRENT publication, formal engine run or orders. Never expose credentials or secret-dependent hashes. Old strategy reconstruction is not a prerequisite for diagnosing the data foundation.

## Candidate factor diagnostic (R10, recovery workspace only)

Exact 11-check command (read-only, synthetic, in-memory):

    E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\runtime\.venv\Scripts\python.exe -X utf8 ^
      reviews\R10\connected_factor_candidate\test_r10_factor_candidate_pipeline.py

Expected: `tests_run=11`, `passed=true`, exit 0, scope `CONNECTED_CANDIDATE_GATES_SYNTHETIC_ONLY`.

Actual function chain, all modules under `reviews/R10/connected_factor_candidate/`:

    r10_factor_response_gate.assemble_responses
      -> r10_factor_refresh_assembly.assemble_candidate
        -> r10_factor_candidate_merge.candidate_merge

`candidate_pipeline` returns these five stage names, in this fixed order:

    REQUEST_RESPONSES_VALIDATED
    OVERLAP_BOUNDARY_VALIDATED
    DIRTY_DAY_BOUNDARY_VALIDATED
    HISTORY_PRESERVING_MERGE_PASSED
    PUBLICATION_NOT_AUTHORIZED

The last stage is an intentional no-publication boundary. There is no publisher API in this chain, so it does not
execute or certify the production publish gate.

Synthetic diagnostic only; no real-data authority, publication or formal engine admission.

The unchanged global acquisition prohibition applies: this diagnostic performs no supplier call, download,
refetch, business-data write, CURRENT switch, production patch, engine construction or order, and it establishes
nothing about historical input authority or the expected market universe.
