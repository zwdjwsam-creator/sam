# BLACKBOX FOUNDATION R10 — end-to-end completion (R13, same task)

Task: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`
Execution host: ZHANGWEI (desktop) · workspace `E:\BLACKBOX`
Verdict: **PARTIAL_EXECUTION_VERIFIED / STAGE_1_NOT_ACCEPTED**
Corrected current classification: **BLOCKED_PARTIAL_EXECUTION** (diagnostic + candidate only)
Foundation acceptance: FALSE · Formal engine admission: FALSE

Historical labels are preserved, not rewritten:
`REPORT_R12_PRESERVED.md`, `ACCEPTANCE_R12_PRESERVED.json`,
`B1_B7_STATUS_R12_PRESERVED.json`, `FINAL_REQUIREMENT_MATRIX_R12_PRESERVED.json`
(the old `diag=false` / `overall=PASS` / `COMPLETED` labels stay visible as history).

## 1. What this revision changed (the three reviewed diffs)

### 1.1 Real original pipeline reuse — the substitute file is gone

The previous `tools/run_connected_pipeline.py` re-implemented the response gate, the
cleaning/anti-leak step, the cache compiler, the checkpoint and the publisher inside a
new file. That is replaced by actual calls:

| stage | real code executed | outcome |
|---|---|---|
| transport | retained RAW `P2_stock_daily` batches (no download) | 2 sessions, 10,426 rows |
| gate | `blackbox_daily_increment_common_r1.acquisition_absence_gate` + structural checks | PASS; tampered-date control BLOCKED |
| cleaning | `inherit_tree`, then `cache_compiler_daily_incremental_r1.read_price_frame` + `antileak_gate` | CC_REPLAY_20260924, 7/7 gates |
| compiler | `任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_tip_rebase_from_current_r1.py` via `--cleaning-json --parent-root --out-root --no-publish` | exit 0, `CANDIDATE_READY`, 44.5 s |
| commit | `tools/candidate_commit.py` (immutable version + one atomic COMMIT.json) | COMMITTED, verify CONSISTENT |
| publish gate | `blackbox_daily_increment_publish_gate_r1.publish_atomic(..., dry_run=True)` | evaluated only; `published=false` |

Measured facts behind the cleaning candidate (not assumed):

* production cleaning `price/stock_ohlcv_daily` = 232 parts, max date **2026-09-24**;
* it contains **0 rows** for 2026-08-31 and 2026-09-01 — the two sessions the replay supplies;
* the retained batches cover both sessions authoritatively (10,426 rows);
* no production row is replaced, and no replay row collides with a production key.

The original compiler's own gates ran on the merged plane: `stock/etf/index` anti-lookahead
`pass`, `date_max == 2026-09-24`, `SEAL.all_pass = true`, and the candidate release contains
2026-08-31 (5,212 rows) and 2026-09-01 (5,214 rows).

What is *not* claimed: the source machine's R13 cleaning stage is deliberately not used
(desktop R15 semantics are the current entry), and the original publish protocol is only
exercised in `dry_run` — see §5.

### 1.2 V4: it is a local port, and unproven data substitution was removed

The original V4 runs on JoinQuant's cloud; there is no local stock engine to "restore".
`BulletTrade + local adapter` is a **local port**, and is now described as such. Four
concrete semantic repairs, each measured (`evidence/PROVIDER_SEMANTIC_REPAIR.json`,
`PROVIDER_SEMANTIC_REPAIR=PASS`):

1. **Adjustment factor: same-day join, guarded anchor, no substitution.** The old
   `_align_factor_piecewise` (ffill + bfill + `factor=1.0` fallback) is deleted. The
   provider now joins `ADJUST_FACTOR_PIT_R1` on the exact date, divides by
   `factor(anchor)` only through a guarded divisor, and withholds any row whose same-day
   factor *or* anchor factor is absent. Withheld rows carry
   `adjust_applicability=BLOCKED_UNPROVEN_ADJUSTMENT`, are counted in
   `required_input_failures`, and a batch where nothing is provable is a hard block.
   ETF/INDEX rows are served raw and tagged `RAW_NOT_APPLICABLE_NON_STOCK`, because no
   adjustment product covers those universes.

   Measured density (`evidence/FACTOR_DENSITY.json`): 166 of
   178 2026 sessions are dense (peak
   5222 rows); **12 sessions are sparse —
   2026-08-17, 2026-08-18, 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-24, 2026-08-25, 2026-08-26, 2026-08-27, 2026-08-28, 2026-09-01, 2026-09-02** — carrying 7–89
   rows instead of ~5,200. That gap is why a pre-open read on 2026-09-03 (anchor
   2026-09-02) loses the codes with no factor that day: the withholding is the data gap
   surfacing, not a code defect.

2. **Unknown `paused` is never turned into "not suspended".** The bar-presence fill is
   deleted; the null is preserved and fails the strict request (measured on an uncovered
   window: `paused_false_rows=0`, `paused_nulls=2`, strict raises `REQUIRED_INPUT_MISSING
   paused`).
3. **Intraday requests no longer borrow the day's open.** No local minute product exists, so
   `frequency=minute` is blocked by default (empty frame + recorded failure; the strict
   raise is the total-block case). The daily-open substitution survives only behind an
   explicit `--intraday-proxy` diagnostic flag, tagged
   `INTRADAY_OPEN_PROXY_DIAGNOSTIC_ONLY`.
4. **`get_all_securities(date)` honours the date.** The master's authoritative
   `start_date`/`end_date` interval drives an as-of filter (2014-06-03 → 2,289 securities,
   2026-09-04 → 5,208). `is_st` stays unobserved and is never inferred.

Verification: `tools/verify_provider_semantics.py` — 13/13 verdicts PASS
(`PROVIDER_SEMANTIC_REPAIR=PASS`), including the
new `partial_withheld_not_aborted` case (7 served / 193 withheld in one 200-code batch,
without aborting the request).

Strict engine run (`--strict-inputs`, no proxy) over 2026-09-03..2026-09-24:
**status `BLOCKED_INPUT_INCOMPLETE`**, blockers `['REQUIRED_INPUT_MISSING']`,
trades `0`, orders `0`,
`mark_price_starved=0`, 16/16 sessions completed,
`diagnostic_only=True`.

What the removal of the substitution actually did, in order:

* the strategy's own price batches now report `获取价格数据失败` twice and its ranking step
  logs `空排名保留` in **16/16 sessions** — the 09:20 batch needs a 140-bar adjusted
  history, that history crosses the 12 sparse sessions, and the withheld rows turn the
  rolling statistics into NaN, so nothing is ever ranked;
* no fabricated fill stands in: 0 trades, 0 orders, and the benchmark series stays intact
  (4552.5784 → 4439.1443), so the engine itself ran the whole window;
* the earlier "COMPLETED with 2 fills" result depended exactly on the piecewise ffill this
  revision deleted. Removing it did not break the engine; it exposed the 12-session factor
  gap, which is the honest reason the run cannot be a strategy verdict.

All strict attempts are kept side by side in `evidence/V4_STRICT_RUNS_ALL.json` so an
earlier probe is never overwritten by a later one:
* `v4_r21_R13_STRICT` → BLOCKED_INPUT_INCOMPLETE, trades=0, blockers=['REQUIRED_INPUT_MISSING', 'MARK_PRICE_STARVED']
* `v4_r21_R13_STRICT2` → BLOCKED_INPUT_INCOMPLETE, trades=0, blockers=['MARK_PRICE_STARVED']
* `v4_r21_R13_STRICT3` → BLOCKED_INPUT_INCOMPLETE, trades=0, blockers=['REQUIRED_INPUT_MISSING', 'MARK_PRICE_STARVED']
* `v4_r21_R13_STRICT4` → BLOCKED_INPUT_INCOMPLETE, trades=0, blockers=['REQUIRED_INPUT_MISSING']

(`STRICT2` was measured before the anchor guard existed and shows 3,173 silent
`ALL_CLOSE_NAN` marks; `STRICT3` was measured while the guard aborted the whole batch;
`STRICT4` withholds per code. Only `STRICT4` describes current behaviour.)

The older `R11_TRADEABILITY_RECON` run (COMPLETED, 2 fills) remains in the package as a
**failed historical label**, not as acceptance, and it is not a return claim. No run over
this window is a strategy verdict.

### 1.3 Candidate commit: one authority, nothing rewritten in place

`run_connected_pipeline.py:382` used to write the merged frame back into `ACCUM_PART`,
then the checkpoint, then pointer and registry one by one — a crash could leave a pointer
aimed at rewritten data. Now:

* every build result is an **immutable versioned release** produced by the original compiler;
* `build_identity()` hashes what the release actually contains per product;
* `commit()` writes an immutable per-version checkpoint and then performs **one**
  `os.replace` of the single authoritative `COMMIT.json`, which carries the checkpoint digest
  — pointer and checkpoint cannot disagree;
* `verify()` re-derives the identity from disk instead of trusting the pointer.

Executed scenarios (9/9 PASS, `evidence/COMMIT_RECOVERY.json`): crash after checkpoint,
crash before the swap, real commit, same-input replay (`IDEMPOTENT_NOOP`), revised-input
failure twice with the previous commit byte-identical, crash **after** the swap (commit
already complete and consistent), revised-input commit, and both payloads still readable and
distinct. `PRODUCTION_CURRENT_WRITE=NONE` throughout.

## 2. Commands, exit codes, logs

`evidence/COMMANDS.json` holds the ledger (command, exit code, observed result). Raw logs:
`pipeline_runs/*.log`, `engine_runs/v4_r21_R13_STRICT4/backtest.log`,
`engine_runs/v4_r21_R13_STRICT4/run_result.json`. Exit codes are recorded as observed; none
is inferred from a `COMPLETED` label. The 13-check semantic verifier and the density
measurement are re-runnable (`tools/verify_provider_semantics.py`,
`tools/measure_factor_density.py`); their outputs are the two evidence files cited above.

## 3. Acceptance map status after this revision

See `FINAL_REQUIREMENT_MATRIX.json` and `B1_B7_STATUS.json` (both revised, with the R12
originals preserved). Summary: R3 PASS · R2 BLOCKED · R5 PARTIAL · R1/R4 unchanged
(PARTIAL / BLOCKED) · B1/B2/B5 PARTIALLY_REPAIRED · B3/B4/B6/B7 unchanged and open.

* **B1** is now backed by a measurement rather than a claim: dense on 166/178 2026
  sessions, sparse on 12 (2026-08-17..2026-09-02, 7–89 rows), so `fq='pre'` is
  reconstructible on most sessions and provably not on those 12.
* **R2** is BLOCKED by that gap, not by missing code: the port runs the whole window and
  refuses to fabricate the 12 sessions.

## 4. Still unverified / blocked (not hidden)

* **`ADJUST_FACTOR_PIT_R1` is sparse for 12 sessions** (2026-08-17..2026-09-02). Every
  history read that crosses them loses those rows, so the strategy's 140-bar statistics and
  its 2-bar return reads fail even on dense days. This is the single largest blocker and it
  is a **data** gap, not a code defect: densifying those 12 sessions is an acquisition the
  current credentials/authority do not cover.
* No local **minute** product, so the strategy's intraday steps cannot execute as requested.
* `is_st` has no local source; historical **as-of constituent** membership is not bound.
* Per-date **factor lineage** sidecar is still not emitted (`B1`).
* The original **publish protocol** (pointer + facts + ledger sequential writes) is only
  evaluated in `dry_run` (`B5`), and whole-CACHE equivalence (`B7`) is untouched.
* Source-machine R13 cleaning semantics are not adopted; desktop R15 is the current entry.
* The committed candidate carries the replayed sessions only; it is not a new production
  `CURRENT` and no pointer was switched.

## 5. Decisions this package asks for

1. **Factor gap**: densify `ADJUST_FACTOR_PIT_R1` for 2026-08-17..2026-09-02 (acquisition),
   or declare the anchor-based pre-adjustment contract you want. Both are recorded as
   measured options; neither is silently chosen here.
2. **Minute plane**: authorise a local minute product if the V4 intraday steps must run, or
   accept that the port only executes its daily steps.
3. **Publish protocol**: authorise a candidate-pointer exercise of the original
   `publish_atomic` so `B5` can be closed beyond `dry_run`.

## 6. Authority boundaries (unchanged)

`NEW_DATA_ACQUISITION_AUTHORIZED=false` · `CURRENT_SWITCH_ALLOWED=false` ·
`ORDER_ALLOWED=false` · `FOUNDATION_ACCEPTANCE=false` · `FORMAL_ENGINE_ADMISSION=false`.
No production `CURRENT` file was written; the publish gate's `CURRENT_PUBLISH=ALLOWED`
verdict is recorded only, and `published=False`.

## 7. Package contents

`PACKAGE_INDEX.json` lists every member with byte count and SHA256 (deliverables plus
`evidence/`), so any claim above can be traced to a file. `DIFF.patch` is the unified diff
against the R12 copies published on the HUB (provenance in
`evidence/DIFF_PROVENANCE.json` — files that did not exist in R12 appear as additions);
`RUN_GUIDE.md` reproduces the whole chain in six commands, candidate-only.
