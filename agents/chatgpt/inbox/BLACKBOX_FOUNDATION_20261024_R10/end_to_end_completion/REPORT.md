# BLACKBOX FOUNDATION R10 — end-to-end completion (R13 round 2, same task)

Task: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`
Execution host: ZHANGWEI (desktop) · workspace `E:\BLACKBOX`
Verdict: **PARTIAL_EXECUTION_VERIFIED / STAGE_1_NOT_ACCEPTED**
Classification: **BLOCKED_PARTIAL_EXECUTION** (diagnostic + candidate only)
Foundation acceptance: FALSE · Formal engine admission: FALSE

Historical labels are preserved, not rewritten: `REPORT_R12_PRESERVED.md`,
`ACCEPTANCE_R12_PRESERVED.json`, `B1_B7_STATUS_R12_PRESERVED.json`,
`FINAL_REQUIREMENT_MATRIX_R12_PRESERVED.json`. The old `diag=false` / `overall=PASS` /
`COMPLETED` labels stay visible as history.

This round answers three review items and reports one defect this round found on its own.
Nothing in it asks for permission again, and no technical route was changed.

## 0. Round-2 answer in one table

| function | actual entry point executed this round | result | evidence |
|---|---|---|---|
| minute read | `candidate/local_plane/minute_bridge.py` → `脚本/blackbox_stock_minute_1m_reader_r1.py` (`STOCK_MINUTE_1M_R1`) | 10 sessions served, 6 blocked by request key with `NO_DAY_SHARDS`, no proxy | `evidence/MINUTE_PLANE.json` |
| factor lineage | `tools/trace_factor_source.py`, `classify_factor_series.py`, `find_factor_nondate_rows.py`, `profile_corrupt_factor_dates.py` over P1/P6/CACHE | two measured anomalies (integer-date files; constant-1.0 planes) wider than "12 sparse days"; **cause not established** | `evidence/FACTOR_*.json` |
| R15 ingest/clean | `formal_cleaning_r15_build_and_seal_r1.py` (`load_staging`/`ingest_item`/`seal_release`) + `r15_antileak_and_ssot_r1.py` | `R15_REPLAY_20260924_R2`, GATE PASS, production CURRENT/SSOT byte-identical. **Its output is not the compiler's input** (see §11 item 1) | `evidence/R15_CLEANING_REPLAY.json` |
| acquisition gate | original `blackbox_daily_increment_common_r1.acquisition_absence_gate` | `PROVENANCE_GATE=PASS`, `SUPPLIER_COMPLETENESS=UNKNOWN`, self-certified control BLOCKED | `CONNECTED_PIPELINE.json` |
| publish | original `blackbox_daily_increment_publish_gate_r1.publish_atomic(dry_run=False)` | published on bound candidate targets, 6 writes, 0 unbound | `evidence/PUBLISH_ATOMIC_REHEARSAL.json` |
| consolidation | `tools/consolidate_r13_round2.py` | matrix / B1–B7 / acceptance / pipeline / index / log single-sourced | `ACCEPTANCE.json#r13_round2` |
| defect found by this round | `tools/candidate_commit.py#build_identity` | `commit_id` hashed the build timestamp; fixed, pipeline 8/8 and selftest 9/9 | `evidence/COMMIT_RECOVERY.json` |

Exit codes are recorded as observed in `evidence/COMMAND_LOG.json` (including the two failed attempts:
the rehearsal's first run, exit 1, and the pre-fix pipeline, exit 5 — both kept, not overwritten).

Original code reused, with the necessary change noted:

| original path / function | reused as-is | necessary change |
|---|---|---|
| `脚本/blackbox_stock_minute_1m_reader_r1.py` | yes, imported | none in the reader; only the caller normalises a date-only lower bound |
| `任务/BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1/formal_cleaning_r15_build_and_seal_r1.py` | yes, called | task-local `ROOT`/`RELEASES`/`CURRENT`/`SSOT` injected |
| `任务/BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1/r15_antileak_and_ssot_r1.py` | yes, called | same rebinding |
| `blackbox_daily_increment_common_r1.acquisition_absence_gate` | yes, called | caller now supplies request-side evidence instead of the response's own row count |
| `任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_tip_rebase_from_current_r1.py` | yes, `--no-publish` | output/acceptance roots redirected to the candidate tree |
| `blackbox_daily_increment_publish_gate_r1.publish_atomic` | yes, `dry_run=False` | every write target rebound; no production path bound |


## 1. Minute plane: the product was always there, the wiring was not

R13 claimed "no local minute product exists". That was wrong and is withdrawn.

* product `STOCK_MINUTE_1M_R1`, source `CLEANING_CURRENT_A_SHARE_STOCK_1M`, status `READY`,
  readers under
  `数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439\standard\price\A股_stock_1m`;
* 10 day shards (2 files per session), **2026-09-11 … 2026-09-24**;
* `candidate/local_plane/minute_bridge.py` imports the original reader (not a copy), normalises a
  date-only lower bound to `00:00:00`, and forwards the query; the provider serves what comes back
  and labels it `REAL_MINUTE_PLANE`;
* inside the V4 window 10 sessions answer (30 rows per single-code probe), 6 block with
  `BLOCKED_MINUTE_PLANE_NO_COVERAGE` / reader `NO_DAY_SHARDS` (2026-09-03, 09-04, 09-07, 09-08,
  09-09, 09-10). A blocked session returns **no rows**; the daily open is never substituted.

The defect that made R13's probe return nothing was a timestamp inversion in the bridge: `"2026-09-15"`
parsed as `15:00:00`, producing a `15:00:00 → 09:35:00` range. Fixed and measured — this is why the
earlier probe reported `NO_DATA` even for covered sessions.

**What wiring the minute plane does not do:** unblock V4. The strategy file makes 6 `get_price`
calls, all `daily`, plus 9 `get_current_data` snapshot calls, and **0** minute `get_price` calls.
Minute input was never V4's blocker, so that claim is withdrawn as well. The minute path is real
for any caller that requests it.

## 2. Factor lineage: the 12 sparse days are a symptom, not the defect

Layers as measured (`FACTOR_SOURCE_TRACE.json`):

| layer | root | files | sessions | rows |
|---|---|---|---|---|
| CACHE `ADJUST_FACTOR_PIT_R1` (2026) | `数据\回测缓存\releases\..._ASOF_20260924_20260924_200439` | — | 178 | 863,710 |
| P1 `adjust_factor` | `数据\原始只读\JQData_9999_official_raw\P1_adjust_factor` | 185 batch + 37 incremental | 3,044 | 13,548,093 |
| P6 `factor_reference\adjust_factor` | same RAW tree | 38 incremental | 20 | 192,925 |

Two defects, both in the incremental supply:

1. **Date encoding.** 17 incremental files covering 2026-08-12 … 2026-09-02 (88,584 rows) carry
   `date` as `int64` positional `0..299` (300 distinct values) instead of a timestamp. No row from
   them can be joined on date, which is exactly why those sessions read as "0 dated rows" in the
   source. The row payload is otherwise intact: code sets agree 5,208/5,208 with a dense file and
   `factor` is positive and finite — so the file is recoverable, but not by us rewriting sealed RAW.
2. **Value.** Every sampled incremental file **from 2026-08-10 onward** is `factor = 1.0` for every
   row — including the files whose `date` dtype is correct (2026-08-10, 08-11, 09-03, 09-21 … 09-24,
   `factor_distinct = 1`, min = max = 1.0). A correct timestamp therefore does not make the file an
   adjustment series; it is the forbidden identity fallback, living in the supplier payload rather
   than in our code.

What that does to CACHE (`FACTOR_SERIES_NATURE.json`, `FACTOR_DENSE_VS_CORRUPT.json`):

* **12 partial sessions**, 2026-08-17 … 2026-09-01: 7, 11, 19, 29, 39, 45, 49, 64, 72, 81, 88, 89
  rows instead of ~5,200 (and 2026-08-31 is a full 5,208-row day of which 5,197 rows are 1.0);
* **17 constant sessions**, 2026-09-02 … 2026-09-24: 5,215 … 5,222 rows, `distinct = 1`, every value
  1.0. That is the **entire V4 test window**;
* per-session source comparison: 14 of the 16 checked sessions are `CACHE_EXCEEDS_SOURCE`, i.e. CACHE
  holds rows the dated source cannot account for;
* the historical batch plane is healthy by contrast: 139/139 files varied, minimum factor 0.167,
  last session per code 2026-06-12.

So the honest statement is stronger than R13's: the tested window has **no proven adjusted price on
either side of the anchor**. Earlier wording — "12 sparse sessions, everything else dense" — counted
rows and missed that the dense part is a constant placeholder.

Provider response (unchanged in spirit, now fed by this measurement): same-day join only, no
ffill/bfill, no 1.0 fallback, anchor divisor guarded, unprovable rows withheld as
`BLOCKED_UNPROVEN_ADJUSTMENT` and counted, and a **structural constant-plane detector** that refuses a
single-valued plane instead of consuming it. `evidence/PROVIDER_SEMANTIC_REPAIR.json`:
`PROVIDER_SEMANTIC_REPAIR = PASS`, 13/13 verdicts.

## 3. Real R15 cleaning on the retained batches

`candidate/run_r15_cleaning_replay.py` calls the production functions, not copies:
`formal_cleaning_r15_build_and_seal_r1.py` (`load_staging`, `ingest_item`, `seal_release`) and
`r15_antileak_and_ssot_r1.py`. Release `R15_REPLAY_20260924_R2`, as-of 2026-09-24, parent
`..._R33_FUND_NAV_ASOF_20260924_20260924_200439`.

| retained batch | rows | sha256 |
|---|---|---|
| `stock_daily__incremental_gap_20260831_20260831__full__20260831_155057.parquet` | 5,212 | `553bad19…20b063` |
| `stock_daily__incremental_gap_20260901_20260901__full__20260901_161813.parquet` | 5,214 | `25e695dd…8d4ded7` |

`GATE_RESULT = PASS`: staging loaded (2 items), `ingest_all_committed`, seal certificate written,
ledger written, anti-leak function called and passing, sealed rows equal retained rows, and the
production `CURRENT_CLEANING_RELEASE.json` and `SSOT` are **byte-identical before and after**
(`production_current_untouched = true`, `production_ssot_untouched = true`,
`switch_current_not_called = true`, `patch_hand_not_called = true`).

Not claimed: that the vendor download would have returned these rows; that production is switched;
that HAND was patched. The replay proves the functions run on the retained input, nothing more.

## 4. `response_gate`: the answer no longer certifies the question

R13 fed `acquisition_absence_gate(query_cap=resp.rows, pagination_complete="YES")` — the response
defined its own completeness. Now:

* `query_cap` and `pagination_complete` come **only** from a saved request sidecar; absent → `null` /
  `"UNKNOWN"`, never `YES` and never `rows`;
* two separate verdicts: `PROVENANCE_GATE` (bytes/sha/keys of the retained payload) and
  `SUPPLIER_COMPLETENESS` (vendor side);
* observed on the retained transport: `PROVENANCE_GATE = PASS`,
  `SUPPLIER_COMPLETENESS = UNKNOWN`, original gate
  `DATA_ABSENCE_GATE = UNKNOWN_INCOMPLETE_ACQUISITION`, `ACQUISITION_COMPLETE = NO`,
  `RESULT_LIMIT_HIT = false`, `NO_DATA_FORBIDDEN = true`;
* a negative control now feeds a self-certified completeness claim and is
  **BLOCKED_AS_EXPECTED** with `ACQUISITION_COMPLETENESS_UNPROVEN`.

`PROVENANCE_GATE=PASS` with `SUPPLIER_COMPLETENESS=UNKNOWN` is coherent: the bytes we hold are the
bytes the sidecar names, while vendor completeness was never answered and is therefore not claimed.

## 5. `publish_atomic` rehearsed non-dry-run, and one defect found on the way

Rehearsal (`evidence/PUBLISH_ATOMIC_REHEARSAL.json`), target 2026-09-24:

* `dry_run = false`, `refresh_scope_from_live` invoked once, 9 targets rebound to task-local copies
  seeded from production (`CACHE_PTR`, `CLEAN_PTR`, `FACTS`, `LEDGER`, `OPS`, `SCOPE`, `ROOT`,
  child summary, HAND-SCOPE-R2);
* `writes_observed = 6` (all `*.tmp` inside the bound root), **`unbound_writes = []`**,
  8 files changed inside the bound root, `no_write_outside_bound_root = true`;
* result `OPERATIONAL_READINESS = PASS`, `CURRENT_PUBLISH = ALLOWED`, **`published = true`**,
  `coverage_self_filled_products = []`;
* the write guard is `sys.addaudithook`; its first attempt also fired on the rehearsal's own
  evidence write (`UNBOUND_WRITE_ATTEMPT`, exit 1) — that attempt is kept in the command log, the
  guard was widened to allow exactly that one path and nothing else, then the run passed.

Honest limits (also in the file): production `CURRENT` and HAND were never written;
`published=true` means the original gate accepted the candidate pair and swapped the **bound**
pointers; the capability matrix grades by coverage dates and does not inspect factor validity, so a
placeholder factor plane can still read `AVAILABLE_FORMAL`.

**Defect found by running it twice:** `candidate_commit.build_identity` hashed `release_id` and
`release_root`, which carry the build timestamp. Two builds of the same input therefore produced
different `commit_id`s and `IDEMPOTENT_NOOP` was unreachable — the pipeline failed
`same_input_replay_noop` (kept in the command log, exit 5). Measured cause: of 766 files, **761 data
files were byte-identical** and only 5 metadata files differed (`RELEASE.json`, `SEAL.json`,
`_qa/TIP_REBASE_QA.json`, `PRODUCT_CAPABILITY_FACTS_CANDIDATE.json`, `CURRENT_POINTER_COPY.json`).
Identity is now `CC_COMMIT_IDENTITY_V2`: `asof` + `source_cleaning_release` + `parent_release_id` +
per-product `sha256/rows`. After the fix: pipeline **PASS** (8/8 verdicts) and commit recovery
**PASS** (9/9 scenarios, `same_input_replay_is_noop = true`).

## 6. Consolidated current state (this was previously self-contradictory)

`ACCEPTANCE.json` used to disagree with its own attachments: `five_requirements.R2` said
"COMPLETED … 2 executed trades" and `backtest_classification` said `COMPLETED / diag=false` with a
metrics block, while `FINAL_REQUIREMENT_MATRIX.json` and `REPORT.md` said `BLOCKED`. Both are now
derived, not retyped:

* `five_requirements` ← `FINAL_REQUIREMENT_MATRIX.json`;
* `B1_B7` ← `B1_B7_STATUS.json`;
* `backtest_classification` ← `evidence/V4_STRICT_RUN.json` (current run;
  `engine_runs/v4_r21_R13_STRICT4`): `BLOCKED_INPUT_INCOMPLETE`, blockers
  `['REQUIRED_INPUT_MISSING']`, 16/16 sessions, trades 0, orders 0, mark-starved 0,
  `diagnostic_only = true`. The 0.00% account summary of a 0-trade run is explicitly **not** a return
  claim, and the R11 recon metrics block is preserved only as a failed historical label.

Acceptance map after consolidation:

* R1 PARTIAL · **R2 BLOCKED** (blocker narrowed to the source layer) · R3 PASS · R4 BLOCKED ·
  R5 desktop BLOCKED · R5 pipeline reuse PARTIAL;
* B1 PARTIALLY_REPAIRED (lineage measured, input still defective) · B2 PARTIALLY_REPAIRED ·
  B3 OPEN · B4 OPEN · **B5 PARTIALLY_REPAIRED** (protocol now executed non-dry-run; production
  switch still unproven) · B6 PARTIALLY_REPAIRED · B7 PARTIALLY_REPAIRED.

## 7. Still unverified / blocked (not hidden)

* **Incremental adjust-factor plane 2026-08-10 … 2026-09-24**: 17 files carry a positional integer
  `date` and the planes are constant `1.0`. This is the single largest blocker, and the **cause is
  not established** — the same observations are compatible with the requested `fq` parameters and
  normalisation basis, the SDK return shape, local serialisation, or the supplier content, and this
  package does not separate them. What is established is narrower: the current adjustment input
  and its basis are **not proven to satisfy the contract**. See §11.
* **V4 window**: no proven adjusted price on either side of the anchor, so the ranking input is
  incomplete by construction. The port runs all 16 sessions and refuses to fabricate; it is not a
  strategy verdict.
* **Minute coverage**: real but only 2026-09-11 … 2026-09-24; 2026-09-03 … 09-10 is blocked.
  V4 issues **direct** minute `get_price` calls: 0. That does **not** prove V4 is independent of
  intraday data — it also makes 9 `get_current_data` snapshot calls, and the read timing of those
  snapshot fields plus the engine's mapping of them is unresolved, so no intraday semantic passes.
* **B4**: 2026-08-31 / 2026-09-01 are still not served by the mounted `CURRENT`; the candidate
  partition holds them, the switch is not authorised.
* `is_st` has no local source; as-of historical constituent membership is not bound.
* Per-date **factor lineage** is now measured evidence but still not emitted as a product sidecar.
* **B7** whole-CACHE equivalence and a publish-time regression classifier remain unimplemented.
* Production publish protocol under a real pointer swap remains unproven.

## 8. Decisions this package asks for

1. **Declare the pre-adjustment contract** (anchor basis, `fq` semantics, and whether a multi-year
   batch cross-section may be concatenated with a single-day incremental). Only after that is
   settled does "re-acquire 2026-08-10 … 2026-09-24" become a meaningful action; neither branch is
   silently chosen here, and re-download is **not** asserted as required.
2. **Minute coverage extension** to 2026-09-03 … 2026-09-10 if any caller needs it; V4 does not.
3. **Publish protocol**: authorise a production publish window so B5/B4 can be closed beyond a
   bound rehearsal.

## 9. Authority boundaries (unchanged)

`NEW_DATA_ACQUISITION_AUTHORIZED=false` · `CURRENT_SWITCH_ALLOWED=false` · `ORDER_ALLOWED=false` ·
`FOUNDATION_ACCEPTANCE=false` · `FORMAL_ENGINE_ADMISSION=false`.
No production `CURRENT` file was written; `PRODUCTION_PUBLISH_CALLED=false`;
`SEALED_DATA_MODIFIED=false`. The rehearsal's `published=true` applies to task-local bound copies
only.

## 10. Package contents

`PACKAGE_INDEX.json` lists every member with byte count and SHA256 (deliverables plus `evidence/`).
`DIFF.patch` is the unified diff against the R12 copies published on the HUB, with provenance in
`evidence/DIFF_PROVENANCE.json` (files that did not exist in R12 appear as additions, including all
code added in this round). `CHANGE_INDEX.json` names each changed file with its purpose and current
sha256. `RUN_GUIDE.md` reproduces the whole chain, candidate-only.

Reading order: `REPORT.md` → `ACCEPTANCE.json` → `FINAL_REQUIREMENT_MATRIX.json` →
`B1_B7_STATUS.json` → `evidence/PUBLISH_ATOMIC_REHEARSAL.json` →
`evidence/R15_CLEANING_REPLAY.json` → `evidence/FACTOR_SERIES_NATURE.json` →
`evidence/MINUTE_PLANE.json` → `CONNECTED_PIPELINE.json`.

## 11. Review receipt — GPT final review `REVIEWED_FINAL_PASS_BLOCKED` (consumed 2026-10-25 13:26 +08)

The reviewer appended a leading review section to
`agents/chatgpt/outbox/BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025.md`
(48,946 → 54,700 bytes). It **accepts the bounded results** listed in §0 and **rejects overall
acceptance**, and it explicitly dispatches **no new repair round** and closes the upload-wait phase.
Full transcription: `evidence/GPT_REVIEW_R13_FINAL_CONSUMED.json`.

Its five reasons, with what this package now says instead of what it said before:

1. **No single-product pass-through proof for R15 → compiler.** Correct, and now stated as such:
   the R15 output is `candidate/r15_releases/R15_REPLAY_20260924_R2`, while
   `CONNECTED_PIPELINE.json`'s compiler `argv` reads `candidate/cc/CC_REPLAY_20260924/RELEASE.json`;
   `run_connected_pipeline.py` never calls the R15 runner, and the publish rehearsal ran separately.
   The package proves that several original components **each** run, not that they run **as one chain**.
   This is an unfixed item of the original task, kept open as `R5_CHAIN_INTEGRITY`.
2. **V4 formally blocked.** Unchanged and agreed: `BLOCKED_INPUT_INCOMPLETE`, 16 sessions, 0 trades,
   0 orders, `diagnostic_only=true`; a completed 16-session loop is not a strategy verdict.
3. **The "all-1.0 → vendor fabrication → must re-download" attribution is withdrawn.** The
   integer-date files, the constant-1.0 planes and the sparse CACHE rows are **observations**; they
   cannot by themselves separate (a) the requested `fq` parameters and normalisation basis,
   (b) the SDK return shape, (c) local serialisation, (d) the supplier content. Two specific
   corrections: the source machine's `aux_billboard_adjust_index_minute_r15.py:110-115` requests a
   single day with `fields=['factor']`, `fq=None`, so a multi-year batch cross-section and a
   one-day incremental are **not proven concatenable**; and `provider._constant_plane_sessions`
   (`nunique == 1` → withhold) is **our** blocking rule, not a certificate that the vendor erred.
   `DAILY_RAW_FACTOR_COVERAGE.json` marks 2026-08-05…09-24 but its `per_session` holds only 08-05
   and 08-06 at 10 rows each, so it does not support "no usable daily source across the window".
   Refusing an unproven adjustment is kept; the asserted cause and the re-download remedy are not.
4. **"0 minute calls" is not "no intraday dependence".** Reworded in §1 and §7: direct minute
   calls are 0, `get_current_data` is called 9 times, and its snapshot fields' read timing and
   engine mapping are unresolved.
5. **Production `CURRENT` not switched is a later action, not this round's failure cause.** The
   gate's date-based `ALLOWED` does not make the factor/history coverage valid, so a candidate
   `published=true` supports no production admission.

Where this leaves the package: the bounded results in §0 stand as scoped; the overall verdict stays
`BLOCKED_PARTIAL_EXECUTION`; `R2` stays BLOCKED; `R5` stays PARTIAL with the chain-integrity gap now
named explicitly; `B5` keeps PARTIALLY_REPAIRED for the isolated rehearsal only. Nothing here is
re-run, and no acquisition, `CURRENT` switch or order is opened.
