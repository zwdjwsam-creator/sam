# R04 evidence label correction (English; original R03 report preserved)

Scope: labels only. No historical result is rewritten, deleted or re-scored. R03 files stay byte-identical at
`agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R03/`.

## 1. Which R03 checks actually used business data

Verified by reading `tests/test_conformance_r3.py` in this cycle (fixture factory at line 191, runner at lines 475-476):

| check | data source | correct label |
|---|---|---|
| check_1_build_stamp_not_coverage | `fixture_provider()` over `FIX/TEST_REGISTRY.json` | SYNTHETIC |
| check_2_read_failure_and_budget | fixture | SYNTHETIC |
| check_3_time_filters | fixture | SYNTHETIC |
| check_4_adjustment_rejected | fixture | SYNTHETIC |
| check_5_revisions_and_shuffle | fixture | SYNTHETIC |
| check_6_routing | fixture | SYNTHETIC |
| check_7_engine_contract | fixture registry | SYNTHETIC |
| check_8_reconcile | `LocalValueProvider()` real registry | REAL DATA (read plane only) |
| check_9_real_engine_bounded | real provider through the adapter | REAL DATA (read plane only) |
| check_10_registry_scope | registry metadata | ARTIFACT, not data |

Therefore only **checks 8 and 9** are real-data observations. This matches the R03 review statement.

## 2. Misattributed R03 statement

R03 `DELTA_REPORT.md` presented the intraday example and the event example under a real-data heading.
Both came from `check_3_time_filters(fixture_provider())`: a synthetic 10-bar intraday frame and a synthetic
two-row XR-XD frame. Correct label: **FIXTURE-BASED SAFETY DEMONSTRATION**, not a production observation.

## 3. What the 21-row June result does and does not prove

It proves: for `000001.XSHE`, the CLEAN stock daily plane returns 21 rows for June 2026 when the loaded trade
calendar says 21 trade days, and R01's 10-row result was caused by family-level deduplication dropping
complementary files.

It does not prove: coverage for any other window, any other security, any other dataset, or engine admission.
It is a single-window read-plane observation.

## 4. R03 registry annotation defect (self-reported)

`ECOLOGY_REGISTRY_R3.json` writes the same two sentences into every dataset layer
(`adjustment_identity`: "RAW_NONE; factor is a separate column, never folded into close; a missing factor is not
admitted as 1.0"; `time_visibility`: "bar visible after its trade date close"). For reference datasets such as
`SECURITY_MASTER` and `INDEX_COMPONENTS` there is no bar time axis, so the sentence is not an observation.
In R04 this is recorded as conflict `R04-C13`. The R03 artifact is left untouched; the annotation is corrected
only in the R04 conflict register and in this note.

## 5. New real-data observations added in R04 (not R03 restatements)

1. `000001.XSHE` daily `2026-06-01..2026-06-03`, `fq=none`, `fill_paused=False`: real DataFrame returned,
   3 rows, status OK (native adapter evidence, `PATCH_EXECUTION.json`).
2. Coverage probe `2026-06-01..2026-12-31` against observed end `2026-09-24`: status PARTIAL, missing dates
   reported only `2026-08-31` and `2026-09-01`; the whole 2026-09-25..2026-12-31 tail was **not** counted as
   missing (conflict `R04-C11`).
3. Plane gap probe: `2026-08-31` and `2026-09-01` are calendar trade days with no row for `000001.XSHE` in
   any file whose footer statistics touch the window; the incremental files jump `20260828` -> `20260902`
   (conflict `R04-C10`).
4. Field observations on the sampled CLEAN daily file (1430 rows): `fq` NULL in every row, `factor` == 1.0 in
   every row, `pre_close` NULL in 912 of 1430 rows, `paused` in {0.0, 1.0, NULL} (conflicts `R04-C02`,
   `R04-C03`, `R04-C12`).

## 6. Standing exclusions after correction

`FOUNDATION_ACCEPTANCE=false`, `ORDER_ALLOWED=false`, `formal_backtest_active=false`. No check in R04 is a
MASTER admission decision; an OK diagnostic envelope is not admission.
