# R10 factor partition and lineage reconciliation: append-only receipt

Round: R10 continuation (not R11, not acceptance). Executor: ZHANGWEI.
Task: `BLACKBOX_FOUNDATION_R10_FACTOR_PARTITION_AND_LINEAGE_RECONCILIATION_20261024`.
Read first: `reviews/R10/factor_reconciliation/REVIEW.md` and `PACKAGE.json`, in full.

Earlier bundles — `factor_boundary/`, `rework_2256/`, the R10 delivery, `FINAL_BLOCKERS.json` and both earlier
reports — are untouched. This file adds measurement; it retracts nothing and closes nothing.

## 1. Package identity before execution

All six supplied files were copied byte-for-byte from the reviewed HUB package into
`reviews/R10/factor_reconciliation/`. Bytes and SHA256 match `PACKAGE.json` for every one, including `REVIEW.md` and
`OFFLINE_TEST_RECEIPT.json`. No newline normalization, no pin regeneration, no test replacement, no Windows harness.

| file | bytes | sha256 |
|------|-------|--------|
| `r10_factor_input_contract.py` | 4046 | `e30acadd...e67c5` |
| `r10_factor_desktop_check.py` | 7495 | `76693d08...3cfed0` |
| `r10_factor_reconcile.py` | 11223 | `171146f5...5ae33` |
| `test_r10_factor_reconcile.py` | 6386 | `60117802...4c3ca` |
| `REVIEW.md` | 5873 | `b8237218...5bfc526` |
| `OFFLINE_TEST_RECEIPT.json` | 460 | `03b28ce1...d52ab7` |

Both predecessor helpers are byte-identical to the previously executed `factor_boundary` copies. The old compiler was
not imported, executed, hot-patched or opened for write.

## 2. The 17 supplied offline controls, on this desktop

Exit code 0. Literal stdout: `{"tests_run": 17, "passed": true, "scope": "OFFLINE_PARQUET_AND_KEY_CONSERVATION",
"supplier_calls": 0, "FOUNDATION_ACCEPTANCE": false}`. Stderr: unittest ran 17 tests in 0.078s, `OK`. The gate passed,
so the dependent desktop check was allowed to run.

## 3. The fixed reconciliation check, exactly once

Exit code 0, `status = FIXED_FACTOR_RECONCILIATION_MEASURED`, `source_files_changed = false`, `supplier_calls = 0`,
`all_layer_search_performed = false`. The driver ran the genuine CACHE entry itself
(`describe --product ADJUST_FACTOR_PIT_R1`) and demanded `real_preflight.ok = true` with `MUST_READ_PRECHECK = PASS`
before installing its audit hook. It then enumerated exactly one product data directory, required the 13 expected year
partitions, and re-verified every hash after reading. No replacement root was chosen and no missing source was inferred.

### 3.1 Thirteen partitions

| year | physical rows | distinct keys | boundary | identity |
|------|--------------|---------------|----------|----------|
| 2014 | 620803 | 620803 | SHAPE_VALID_ONLY_NOT_ADMITTED | NEW_MEASURED_IDENTITY_NOT_ADMITTED |
| 2015 | 665913 | 665913 | SHAPE_VALID_ONLY_NOT_ADMITTED | NEW_MEASURED_IDENTITY_NOT_ADMITTED |
| 2016 | 704876 | 704876 | SHAPE_VALID_ONLY_NOT_ADMITTED | NEW_MEASURED_IDENTITY_NOT_ADMITTED |
| 2017 | 799798 | 799798 | SHAPE_VALID_ONLY_NOT_ADMITTED | NEW_MEASURED_IDENTITY_NOT_ADMITTED |
| 2018 | 857319 | 857319 | SHAPE_VALID_ONLY_NOT_ADMITTED | NEW_MEASURED_IDENTITY_NOT_ADMITTED |
| 2019 | 890482 | 890482 | SHAPE_VALID_ONLY_NOT_ADMITTED | NEW_MEASURED_IDENTITY_NOT_ADMITTED |
| 2020 | 951992 | 951992 | SHAPE_VALID_ONLY_NOT_ADMITTED | NEW_MEASURED_IDENTITY_NOT_ADMITTED |
| 2021 | 1062380 | 1062380 | SHAPE_VALID_ONLY_NOT_ADMITTED | NEW_MEASURED_IDENTITY_NOT_ADMITTED |
| 2022 | 1149235 | 1149235 | SHAPE_VALID_ONLY_NOT_ADMITTED | NEW_MEASURED_IDENTITY_NOT_ADMITTED |
| 2023 | 1211865 | 1211865 | SHAPE_VALID_ONLY_NOT_ADMITTED | NEW_MEASURED_IDENTITY_NOT_ADMITTED |
| 2024 | 1236214 | 1236214 | SHAPE_VALID_ONLY_NOT_ADMITTED | NEW_MEASURED_IDENTITY_NOT_ADMITTED |
| 2025 | 1251439 | 1251439 | SHAPE_VALID_ONLY_NOT_ADMITTED | NEW_MEASURED_IDENTITY_NOT_ADMITTED |
| 2026 | 863710 | 863710 | SHAPE_VALID_ONLY_NOT_ADMITTED | PRIOR_PIN_MATCH |

Every partition passed input shape, so the distinct keys sum globally: 12,266,026 unique date/code keys, proven
unique within disjoint verified calendar years. Original physical row counts are recorded as-is; nothing was
deduplicated, no date was reconstructed, no factor was filled and no revision precedence was chosen. The twelve
2014-2025 hashes are measured identities of the bytes inspected, not publication or supplier authority.

### 3.2 Count reconciliation, returned as observed

- Physical rows across the 13 partitions: **12,266,026**. Distinct keys: 12,266,026.
- Sidecar declared: **12,182,523**. Physical minus declared: **83,503**, which reproduces the prior delta.
- Measured 2026: **863,710**. Declared `n_rows_year_2026`: **863,710**. These are equal.
- Therefore the whole 83,503 shortfall sits in 2014-2025: measured **11,402,316** against an implied
  **11,318,813**, a difference of exactly 83,503.
- Per-year sidecar baselines: `NOT_AVAILABLE_IN_THIS_SIDECAR`. Count mismatch cause: `NOT_ESTABLISHED_BY_ARITHMETIC`.
  No source-absence claim, and `B1_CLOSED = false`.

The sidecar carries no per-year baseline, so the aggregate cannot name a faulty year and does not justify rewriting
one. Reproduction of the delta establishes arithmetic only.

### 3.3 Cleaning 2026 versus CACHE 2026, a different comparison

Cleaning `BLACKBOX_FORMAL_CLEANING_R26_ADJFACTOR_PIT_ASOF_20260814_20260816_044000` 2026 partition: 774,406 rows,
774,406 distinct keys, `2026-01-05` .. `2026-08-14`, 5227 codes, sha256 `e20315ba...44a4`.
CACHE 2026: 863,710 rows, sha256 `3f44139e...6a46d`.

| measure | value |
|---------|-------|
| clean_only keys | 0 |
| cache_only keys | 89,304 |
| shared keys | 774,406 |
| unequal factors on shared keys | 13,199 |
| row delta cache minus clean | 89,304 |

By date, the shared range carries 88 or 89 unequal factors every session from `2026-01-05` through `2026-08-14`;
from `2026-08-17` onward every key is `cache_only` because the Cleaning product ends at `2026-08-14`. The
`cache_only` counts across `2026-08-17..2026-08-28` run 89, 88, 81, 72, 64, 49, 45, 39, 29, 19, then 5208 on
`2026-08-31`, 11 on `2026-09-01`, 7 on `2026-09-02`, before resuming at 5215 from `2026-09-03`. Those values repeat
the earlier R08 observation. A smaller record count is a product-content observation, not source absence, an
expected universe or migration loss.

Sample unequal pairs are of the form `clean = 1.0`, `cache ≈ 0.9958` for the same code and date (e.g. `000009.XSHE`
on `2026-01-05`: clean `1.0`, cache `0.995850647180803`). `precedence_decided = false`, `source_lineage_proven =
false`; the driver's own warning applies: a tuple match is not supplier/PIT provenance and unequal factors may have
different anchors. This comparison never extends the R26 as-of certificate into September.

The 89,304-row Cleaning-vs-CACHE difference is **not** the 83,503 product-sidecar difference. Neither explains the
other without per-partition/key evidence.

## 4. The two literal searches, in retained resources only

Searched `317` retained files across the R04-R10 source-body and index trees plus the reviewed operating entries, by
literal byte substring, read-only. No drive or catalog scan was launched.

- `BACKWARD_DIRTY_FULL_HISTORY_REPLACE`: 5 hits.
- `n_rows_year_2026`: 4 hits.
- Original source-body hits for either literal: **0**.

Hits, all product metadata or round artifacts quoting it:

| path | sha256 | lines |
|------|--------|-------|
| `r09_correction/ADJUST_FACTOR_SIDECAR_RECONCILIATION.json` | `e81e4d18...70b5fcd` | 15, 18, 58 |
| `r09_delivery/EVIDENCE_INPUTS_R09.json` | `6b9fcd6c...251f4ccc9` | 1418, 1421 |
| `r09_delivery/FOUR_UNRESOLVED_ITEMS_NARROWED.json` | `c1dafe65...4c9102b` | 127, 130 |
| `r09_delivery/R09_DELTA_REPORT.md` | `d12f5d6d...7cb597c6` | 110, 113 |

The registered product sidecar itself —
`...\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439\ADJUST_FACTOR_PIT_R1\COVERAGE.json`,
462 bytes, sha256 `b613442e42abfb34e46ce391e533f806653439ed92855cca54a347c9fcca7b46` — is where both literals actually
live. It declares `product_id ADJUST_FACTOR_PIT_R1`, `date_min 2014-01-02`, `date_max 2026-09-24`, `n_codes 5465`,
`n_rows 12182523`, `fq pre`, `reason BACKWARD_DIRTY_FULL_HISTORY_REPLACE`,
`tip_extended_at 2026-09-24T19:56:50+00:00`, `tip_source` the RAW `adjust_factor_stock__incremental_20260924`
unit, and `n_rows_year_2026 863710`. That is publication metadata, not an acquisition or transform receipt, and it
names no executable writer.

Existing HUB references, no re-upload needed:
`agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R09_CORRECTION/ADJUST_FACTOR_SIDECAR_RECONCILIATION.json` and
`agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R08/receipt_correction_1855/source_bodies/cache_compiler_adjust_factor_pit_r1.py`.

**Lineage status: `UNRESOLVED`.** The only declared binding is a metadata-level claim that the 2026 tip extension came
from one named RAW unit, and it says nothing about 2014-2025. No retained transform or run receipt cites
`BACKWARD_DIRTY_FULL_HISTORY_REPLACE`, and no supplied original body contains either literal, so
`transform_or_run_receipt_binding_2014_2025 = NOT_RETAINED_IN_THE_REVIEWED_CORPUS`. This is a precise unresolved
dependency, not a declaration that the writer is nonexistent, that the RAW source is absent, or that the sidecar is
wrong.

## 5. B1 linkage, stated exactly

This evidence is linked to `B1_ADJUSTMENT_RECONCILIATION` and **does not close it**. B1 remains `OPEN`. Carried
forward for the owner: exact writer and transform receipts for 2014-2025, historical fq and PIT provenance, and
all-layer factor source resolution. A row-count reproduction, a shape PASS or a 17-test suite PASS cannot close B1.

## 6. Other groups and permissions unchanged

The other six integration groups are unchanged; no whole-catalog inventory was repeated. No supplier call,
credential read, login, download, updater invocation, scheduler activation, package installation, business-data
write, CURRENT change, provider registration, engine construction, backtest or order occurred in this round.

    FULL_GOAL_MET=false
    FOUNDATION_ACCEPTANCE=false
    FORMAL_ENGINE_ADMISSION=false
    INCREMENTAL_PIPELINE_READINESS=NOT_ACCEPTED
    LATEST_FULL_UPDATE=NOT_VERIFIED
    NEW_DATA_ACQUISITION_AUTHORIZED=false
    CURRENT_SWITCH_ALLOWED=false
    ORDER_ALLOWED=false

The local executor's task ends after upload and full byte readback, pending GPT review. GPT owns the next compiler,
data and contract decisions.
