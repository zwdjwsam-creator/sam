# R08/10 delta report — observed-segment rebuild, evidence correction, explicit R09 bindings

Round: 8 of 10. Remaining cycles after this delivery: 2.
Host: DESKTOP (E:\BLACKBOX). Predecessor: R07.
FOUNDATION_ACCEPTANCE=false, ORDER_ALLOWED=false, PRODUCTION_CHANGE_AUTHORIZED=false, CURRENT_SWITCH_ALLOWED=false.
Network calls: 0. Downloads: 0. Authentication attempts: 0. Source-absence claims: 0. Production writes: 0.

## 1. What was executed

The four supplied files were executed exactly as received, with no edits:

| file | sha256 | role |
|---|---|---|
| `r08_coverage_gate.py` | `9d90046c252b7f4c08786906cd3a95d28a5b3099493e4cb1f0ca8931fae982af` | observation/coverage gates, bounded classification, union guard |
| `r08_rebuild_local.py` | `46da05cb40ce73472ccb896916676d0f42a100d42ece4e46dcb764c64f5d8407` | observed-segment derived rebuild + grid audit |
| `test_r08.py` | `8b02040fa0f79211148292a992959469dc4c64e8401785e06a00c722c417d3d9` | 23 offline controls |
| `r07_rebuild_local.py` | `a9759390564b1ac1dc20c1098e37a52199d4bb439990522babffc90352e18a03` | unchanged R07 arithmetic, imported |

`MUST_READ_PRECHECK = PASS` for `TASK_CLASS = CACHE`, kernel `b05a6995…197a` VERIFIED, both manifest members sha-matching (`MUST_READ_PREFLIGHT.txt`).

## 2. Offline controls: 23/23 PASS

`test_r08.py` requires the hash-pinned compiler path as `argv[1]`; a directory argument is rejected by its own digest check, which is itself the intended fail-closed behaviour. With `cache_compiler_source_R06.py`
(sha256 `c8ddf805a6ddc998cda507f2aa5c92f27b13a43b5445e5bfed21477c5822f336`, identical to the R06/R07 pins):

- 23 controls passed, 0 network calls, scope `OFFLINE_SYNTHETIC_ONLY; NOT_DESKTOP_REBUILD_OR_MASTER_ADMISSION`.
- Coverage: grid/price conservation, source-byte immutability, all-null preservation without factors or zero fills, gap state reset, observed-prefix EMA arithmetic, explicit formula version, observed-only market counts, future-append stability, partial-quote / duplicate-key / ordinal-date / same-date-symbol-loss / same-key-value-loss rejections, bounded success refusing publication, RAW-presence classification, unknown-empty-source, empty-union-member rejection, real parquet build, replay, parent byte conservation, tampered-replay rejection, real two-day diagnosis, same-key close drift.

## 3. Candidate rebuild: ALREADY_BUILT_VERIFIED

`r08_rebuild_local.py --compiler-source cache_compiler_source_R06.py` → `ALREADY_BUILT_VERIFIED`.
The replay re-reads the candidate parquet, re-checks parent byte fingerprints and re-derives the audit; it does not overwrite the pinned parent, the R06 candidate or any original price value.

Observation accounting (`CANDIDATE_MANIFEST.json`):

- input rows 12,362,212 = observed 12,327,735 + unobserved 34,477; null→zero fills 0; listing/delisting inferred false.
- state policy `CONTIGUOUS_OBSERVED_SEGMENTS; NO_BRIDGING_EXPLICIT_NULL_RUNS`; formula `univ_factor_r1_v1.R08_OBSERVED_SEGMENTS`.

Candidate artifacts:

| product | rows | sha256 |
|---|---|---|
| `STOCK_FACTOR_DAILY_R1/year=2026` | 959,896 | `e70bc796a00c95448c78e802e00504d72c5907158e844f9c9c610c1d46fe7de3` |
| `MARKET_STRUCTURE_DAILY_R1/year=2026` | 178 | `0ea3bd07e5b5b4d49a132485629d7cd08f15961bc5ebf4b303b55b362b84b99c` |
| `UNOBSERVED_GRID_ROWS.parquet` | 34,477 | `1235c8e99198d0cab336aa9a98e91b8941c72dd5b07ed5c5fe67beff4d5d46b7` |

Non-regression on exact input frames: `lost_keys = 0`, `lost_field_observation_keys = 0` for both products; `PUBLISH_ALLOWED=false`, `CURRENT_SWITCH_ALLOWED=false`.

Two-day layers, published vs candidate: for both `STOCK_DAILY_PIT_R1` and `STOCK_DAILY_RAW_PIT_R1` the published view sees 0/10,426 keys in CACHE and READER (`UNRESOLVED`, `CLEANING_COMPLETE_CACHE_MISSING`) while the candidate Arrow read sees 10,426/10,426 in RAW, CLEAN, CACHE and READER with close equality to RAW on both dates. This is candidate serving evidence only; it is not engine start-up or MASTER admission.

## 4. Evidence corrections to the review's nine points

`R07_EVIDENCE_CORRECTIONS.json` carries eleven rows (C01–C11); each states the rejected R07 sentence, the measured replacement and its evidence file. Summary of the nine required items:

1. **Full index plane (C01).** `INDEX_DAILY_RAW_FULL_HISTORY_R1` was opened explicitly: CURRENT at `REL_INDEX_DAILY_FULL_HISTORY_R1_20260805_073123`, 732 per-index parquet files, 149,674,471 bytes, 2,905,568 rows, **137 valued sessions inside 2026-01-05..2026-07-29**, and `399303.XSHE` present with 5,242 rows / 3,004 valued closes 2014-03-28..2026-08-04. H1 index history therefore exists in RAW and was never minute-derived. Residual, not a loss: the release MANIFEST declares `n_files=154` against 732 on disk, and the registered scope ends 2026-08-11, so neither recovery date is inside it.
2. **RAW presence ≠ Cleaning completeness (C02).** Every classification is now layer-scoped; where the sealed Cleaning release has an earlier `cleaning_as_of`, the verdict is `REQUEST_OUTSIDE_PRODUCT_COVERAGE`, not a cleaning-presence claim. NAV batch file names are used for no completeness and no observed-value claim (C03).
3. **Universe end ≠ regression (C04).** Without a pinned earlier baseline the class is `REQUEST_OUTSIDE_PRODUCT_COVERAGE`; `CACHE_COVERAGE_REGRESSION` is not claimed.
4. **FIELD_NOT_CACHED (C05).** Four axes are kept apart: diagnostic root cause (14-value enum or null), cache-miss reason, acquisition completeness, runtime admission. A RAW-present, CACHE-absent field is a miss, never `SOURCE_LIMITATION`.
5. **Adjust factor (C06/C07).** The contract is `DAILY_DENSE` and forbids `silent_factor_eq_1`, so a change-event reading is inadmissible. 2026-09-01 holds 11 of 5,214 codes (0.21%) and only 4 of those differ from 2026-08-31 — not a corporate-action set; 12 dates in 2026 are below 5,000 rows against ~5,208 neighbours. In **20 of 37** stock incremental RAW files the `date` column is int64 `0..299` with 17–18 rows each (`300 × ~17.4 = 5,214`): a page/batch ordinal, with the trade date surviving only in the filename. In all 37 files `factor` has a single distinct value 1.0. Date coverage is not symbol-by-date coverage, and the plane is not labelled complete.
6. **FUND view (C08).** `ETF+FUND` logical union; `FUND_DAILY_PIT_R1` has zero parquet files, so the view must reject the unserved member (`CACHE_PRODUCT_UNAVAILABLE`). NAV is never converted into traded OHLCV and no fund price product is synthesised.
7. **Labels vs enum (C11).** `SOURCE_AVAILABLE_AND_AUTHORITATIVE` / `…_AND_SERVED` / `SEPARATE_NAMESPACE_OR_REGISTRY` are factual labels only; a successful diagnosis returns `root_cause=null` plus a separate status. No enum member was invented.
8. **Family-B arithmetic (C09).** Measured distribution, no invented explanation: 294 ALL-NULL codes with exactly 105 grid rows each (30,870 rows, only 2026-01-05..2026-06-12); 8 TRAILING-null codes with per-code null counts 41..90 (618 rows); 42 LEADING-null codes (2,989 rows). 30,870 + 618 + 2,989 = 34,477 and 294 + 8 + 42 = 344. "105" is a grid-row length, not a general null count; `302 × 105 = 31,710` was never a row count.
9. **Defect causality (C10).** The 2-byte `blackbox_data_coverage_common_r1.py`, the 2-byte non-regression gate and the disjoint diagnoser enum remain OBSERVED defects with located call sites; their contribution to any specific historical miss or publication is not established by static inspection and is not claimed.

## 5. Section C — explicit bindings for R09

`R09_IMPLEMENTATION_BINDINGS.json` (117,641 bytes) covers 12 domains — stock daily, ETF daily, index full-history daily, valuation, NAV, adjustment, security universe, tradeability/ST/limits, SW structure, minute namespaces, external Tushare CBOND, dictionary/factor value — with the CURRENT pair, registry revision and exact pins. **9 bindings remain unresolved** and are listed with the exact R09 action rather than guessed: ETF transform entry, `INDEX_DAILY_R1` cache writer, valuation transform entry, CURRENT adjust-factor writer, security-master/universe builder, tradeability builder, minute compiler, CBOND compiler, and the `INDEX_DAILY_RAW_FULL_HISTORY_R1` MANIFEST `n_files` (154 declared vs 732 present — a registry correction, not data loss).

`ENGINE_RUNTIME_AND_UPDATE_READINESS.json` records the runtime actually used (`Python 3.12.10`, `pip check` clean) and the declared-dependency matrix: `pandas`, `numpy`, `jqdatasdk`, `pyarrow` present; `matplotlib`, `plotly`, `pyecharts`, `python-dotenv`, `filelock`, `tabulate`, `jupyterlab`, `ipykernel` absent. `admission_gate_wiring` and `candidate_provider` are described but not enabled.

**Environment defect found while executing:** `E:\BLACKBOX\.venv\Scripts\python.exe` is unusable on this host — its `pyvenv` base points at `C:\Users\ThinkPad\...\Python312\python.exe` (`No Python at ...`, exit 103). Executions therefore used the isolated runtime at `_OPS\FOUNDATION_RECOVERY_20261024\runtime\.venv`. Logged as `BLACKBOX_ROOT_VENV_BASE_INTERPRETER_STALE`; no reinstall was attempted, since environment mutation is outside this round.

## 6. What is deliberately not claimed

Not claimed: full data foundation; engine readiness; MASTER admission; adjusted-price plane readiness; complete adjust-factor coverage; ETF/FUND price planes; index plane coverage past 2026-08-11; any source absence; any migration loss; any coverage regression; any causal history for the legacy tool defects; production publication or CURRENT switch.

## 7. Next implementable steps (GPT-owned, R09)

1. Supply the integration layer over the 9 unresolved bindings, starting with the two that block extension: `INDEX_DAILY_R1` writer and the CURRENT adjust-factor writer.
2. Correct the `INDEX_DAILY_RAW_FULL_HISTORY_R1` MANIFEST `n_files`/scope record before any index-plane extension.
3. Bind the adjust-factor RAW reader to filename-derived trade dates and fail closed on a numeric `date` axis.
4. Wire `candidate_provider` + `admission_gate_wiring` against the R08 candidate for a real engine read, without a CURRENT switch.
5. Decide the policy successor for the 34,477 unobserved grid rows (retain with status vs compact with conservation accounting) at the ingest layer, not at the guard.
