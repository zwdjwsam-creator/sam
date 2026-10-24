# Restart readiness retrospective — V4 backtest and daily incremental update

Task: `BLACKBOX_RESTART_READINESS_REVIEW_20261025` (owner-initiated, read-only)
At: 2026-10-25T07:22:44+08:00 (UTC+8) · Host: ZHANGWEI · Workspace: E:\BLACKBOX

`FOUNDATION_ACCEPTANCE=false` · `FORMAL_ENGINE_ADMISSION=false` · `NEW_DATA_ACQUISITION_AUTHORIZED=false`
`CURRENT_SWITCH_ALLOWED=false` · `ORDER_ALLOWED=false` · `SOURCE_ABSENCE_CLAIM_ALLOWED=false` · B1..B7 OPEN

## 0. Method and its limits

Only already-measured artifacts and the local contracts were reused; no payload was re-measured.
Any statement of the form "not present" was made only after a complete name enumeration whose exclusions
are recorded in `FULL_SCAN_LOG.json` (S1..S6). Two probe misses turned out to be wrong paths (C2, C3),
and one apparent unbound edge turned out to be bound at import level (C1). Neither became a defect claim.

Nothing here authorises a download, a cleaning run, a CURRENT switch, an engine construction or an order.

## 1. Answer — V4 backtest

**Formal standard: NO. Diagnostic-only: YES, with a declared scope.**

What is already true:

* MUST_READ preflight for `BACKTEST` returns `MUST_READ_PRECHECK = PASS`, `AUTHORITY_READY = YES`,
  `TASK_EXECUTION = ALLOWED`, with BOOTSTRAP / DATA_ACCESS / BACKTEST rule hashes VERIFIED.
* The three gate scripts exist: causal-information gate, backtest preflight, price-plane gate
  (plus the unified minute-plane preflight).
* The daily plane exists with year partitions 2014..2026 for `STOCK_DAILY_PIT_R1`,
  `STOCK_FACTOR_DAILY_R1` and `ADJUST_FACTOR_PIT_R1`; the mounted CACHE release carries
  51 product directories and the CLEAN release carries
  158,826 parquet files.

What blocks a *certified* backtest:

| id | blocker | measured basis |
|---|---|---|
| ENV-1 | documented interpreter cannot start | `E:\BLACKBOX\.venv\Scripts\python.exe` exits 103: `No Python at C:\Users\ThinkPad\...`; `pyvenv.cfg home` points to a profile that does not exist. System Python 3.12.10 has pyarrow/numpy/requests but no pandas and no jqdatasdk |
| BT-4 (B1) | PRE-adjustment chain not certifiable | `ADJUST_FACTOR_PIT_R1` sidecar declares 12,182,523 rows, physical count is 12,266,026 (+83,503), no per-date lineage; pre/post unimplemented and `factor=null` in batch segments |
| BT-5 (B2) | universe / tradeability coverage | universe measured window ends 2026-07-20; tradeability spans 2026-07-13..2026-09-03 with 15 missing sessions |
| BT-6 (B4) | two sessions inside the mounted CURRENT | 2026-08-31 and 2026-09-01 are not served for 11 products including `STOCK_DAILY_PIT_R1`; the candidate release serves them but is unpromoted |
| BT-7 (B5) | formal engine | import attempts `os.mkdir` (`bullet_trade/core/globals.py:156` from `:421`) and swallows it; engine never constructed; no local value provider branch; `adapter_function` null |
| BT-8 | strategy body | only the JoinQuant paste template `V4_R21` (SOURCE_SHA `c0ac8b48…`, 2179 lines); no local port, no local runner |
| BT-9 | recency | CACHE/CLEAN as-of 2026-09-24, today 2026-10-25 → 31 days; the V4 EOD gate would classify any recent signal day as `DATA_GAP` by its own rule |

Additionally, the V4 EOD production candidate the gate hardcodes
(`D:\CURSOR_TASK_ARCHIVE\CROSS_PRODUCTION_CANDIDATE_R1`) is absent, and no
`run_v4_three_eod_*.py` or `V4_THREE_EOD_AFTER_CLOSE_*` output exists on C:, D:, E: or F:
(S2 complete name enumeration). `D:\CURSOR_TASK_ARCHIVE` exists and is empty.

The honest output is a bounded diagnostic backtest over 2014-01-02..2026-09-24, with 2026-08-31 and
2026-09-01 declared as gaps, prices on a declared basis, all three gate receipts attached, labelled
`DIAGNOSTIC_ONLY`, and no formal return claim.

## 2. Answer — daily incremental update

**One trading day: YES, with three preconditions. The 31-day backlog: NO, not certifiable.**

What is already true:

* Preflight for `ACQUISITION` is PASS with `AUTHORITY_READY = YES`.
* Six-lane manifest `DAILY_DATA_MANIFEST_20260924`: A_JQ, B_T_EXTERNAL, C_GLOBAL_SELLSIDE,
  D_DOMESTIC_RESEARCH, E_US_NEWS, F_US_MARKET all `STATUS=PASS`, `DEGRADED_LANES=[]`,
  `ALL_LANES_READY=YES`, built 2026-09-25T04:08:21+0800 for `CN_RESEARCH_DATE=2026-09-24`.
* Every body in the chain has a live copy on disk: `post_seal_daily_download_r8.py`,
  `formal_cleaning_r15_build_and_seal_r1.py`, `r15_antileak_and_ssot_r1.py`,
  `cache_compiler_tip_rebase_from_current_r1.py`, `blackbox_daily_increment_publish_gate_r1.py`,
  the orchestrator, the data-plane runner and the sellside runner.
* Publish is bound: the TIP compiler does `from blackbox_daily_increment_publish_gate_r1 import publish_atomic`
  (line 36). The orchestrator's unused `GATE` constant is not an unbound edge (C1).
* The supplier credential file that `jq_download_base.py:19` reads exists (presence only, content not read).

What blocks a certified run:

| id | blocker | measured basis |
|---|---|---|
| ENV-1 | interpreter | as above; the writer needs pandas and jqdatasdk |
| DI-7 | no increment cursor | `scope.increment_cursor` is null for every dataset in R3; the RAW coverage ledger stops at 2026-08-12; the legacy `JQ_DATA_DOWNLOAD_EXECUTION_R1` COMPLETED checkpoint is explicitly not a valid cursor |
| DI-8 (B6) | writer / checkpoint / resume / non-regression | update-plan output proves navigation only; 13 products bound, 28 unbound |
| DI-9 | supplier pagination | the R10 pagination repair is accepted as `OFFLINE_LIST_MODEL_ONLY`; two agreeing synthetic lists are not a live supplier order proof |
| DI-10 | Lane B | `EXTERNAL_EVIDENCE_MATERIALIZATION_PARTIAL`: 10 READY / 12 PARTIAL / 1 NO_PERMISSION; `fund_nav`, `fund_share`, `fund_portfolio` are `NO_RECORD_CONFIRMED` with 0 rows |
| DI-11 | backlog | the chain is single `--run-target-date`, candidate then publish; a 31-day catch-up means repeated bounded appends plus B6 resume evidence plus the whole-table factor revision that B1 still blocks |

B3 is consistent with DI-10: `FUND_DAILY_PIT_R1`, `FUND_FACTOR_DAILY_R1` and `FUND_LIKE_ASSET_VIEW_R1`
hold 0 parquet in the mounted release while the upstream fund APIs returned no records. That is a
documented source result, not a local deletion, and it still needs either materialisation or an exact
contract permitting exclusion.

Preconditions, in order:

1. restore an import-capable interpreter (recreate `.venv`, or repoint `pyvenv.cfg home`);
2. derive one per-dataset cursor from the CURRENT watermark 2026-09-24 and the exchange calendar,
   instead of the invalid legacy checkpoint;
3. declare B1/B2/B6 open in the run record and publish only through the import-bound `publish_atomic`;
   `CURRENT_SWITCH_ALLOWED` stays false in this review session.

## 3. Staleness

`CURRENT_CACHE_RELEASE` as-of **2026-09-24**; `DAILY_DATA_MANIFEST_20260924`; today **2026-10-25**.
The readiness statements in those files are true *at their own as-of*, not now.
`DAILY_INCREMENTAL_READY=YES` must not be quoted as a present-tense fact.

## 4. Corrections carried append-only

C1 publish binding (see above) · C2 `/CURRENT/` path guess · C3 sellside task path · C4 the scan was
extended to all four drives before concluding · C5 the credential file is one level deeper than the
first listing suggested. Details in `CORRECTIONS_APPEND_ONLY.json`.

## 5. Not claimed

Missing files are not claimed. Truncation-free download, field/unit/PIT correctness, complete external
coverage, coverage of the 42 non-observed R3 datasets, and any strategy result are not claimed.
The V4 strategy could still be rebuilt and run on JoinQuant; this review only speaks about the local plane.

## 6. Pending tip, disclosed

`agents/chatgpt/outbox/BLACKBOX_FOUNDATION_R10_EXACT_RUNTIME_SOURCE_HANDOFF_20261025.md`
(created 2026-10-25T06:14:50+08:00) asks for five inert source exports plus `EXACT_RUNTIME_EDGES.json`.
The owner issued this retrospective directly, so that tip is **not executed and not claimed** here.

## 7. Files

`RESTART_READINESS_VERDICT.json` · `CONTRACT_MATRIX.json` · `ENVIRONMENT_PROBE.json` ·
`GATE_PROBE.json` · `FULL_SCAN_LOG.json` · `EVIDENCE_INDEX.json` ·
`CORRECTIONS_APPEND_ONLY.json` · `PACKAGE.json` · `DELIVERY_MANIFEST.json`
