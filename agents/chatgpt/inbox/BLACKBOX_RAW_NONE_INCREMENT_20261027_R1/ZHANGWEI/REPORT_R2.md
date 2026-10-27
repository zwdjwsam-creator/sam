# BLACKBOX_RAW_NONE_INCREMENT_20261027_R1_TIMESTAMP_R2 — ZHANGWEI report

repair_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R1_TIMESTAMP_R2
task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R1
parent_task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
host: ZHANGWEI
role: ZHANGWEI
recorded_at_cn: 2026-10-27T18:55:00+08:00
status: GATE_39_PASSED_ONE_GUARDED_RUN_EXIT2_BLOCKER_PRESERVED

ORDER_ALLOWED=false
CURRENT_SWITCH_ALLOWED=false
PRODUCTION_CLEANING_ALLOWED=false
PRODUCTION_RAW_WRITE_ALLOWED=false

## 1. Sequence actually executed

| step | action | result |
|---|---|---|
| 1 | stage + verify package | **6/6** payloads, byte-verbatim |
| 2 | upload `ACK_TIMESTAMP_R2.json` **before** testing | done, read back |
| 3 | native 39-control gate, **once** | **39/39 pass, exit 0** |
| 4 | `acquire_daily.py --execute`, **once** | **exit 2**, `ROUNDTRIP_NON_TIMESTAMP_DTYPE_CHANGE` |
| 5 | preserve, upload, **no retry** | this delivery |

The R2 timestamp repair itself **works**. `test_real_parquet_and_footer`, the one R1 failure,
now passes against the shared production helper, and all 12 `TimestampRepresentation`
regressions pass:
`Ran 39 tests in 1.345s / OK`, exit 0, zero skips.

The gate then correctly opened the one authorized execution. That execution **ran for real**
— it authenticated, called the supplier, and downloaded the first stock batch — and then
stopped on a **different, non-timestamp** defect.

## 2. What the run actually did

- **4 pointer bodies** re-hashed and matched their pinned values (BASELINE.json), so the
  prerequisite gate passed.
- **`get_trade_days`** returned 18 CN sessions, 2026-09-24 … 2026-10-27. 2026-09-24 was
  excluded as required; **17 completed candidates** remained.
- **`get_all_securities(types=['stock'], date=2026-09-28)`** returned **5,222** codes with
  start/end lifecycle.
- **`get_price`** was called for the first 80-code chunk of 2026-09-28 with exactly the
  prescribed arguments (`skip_paused=False, fill_paused=True, fq=None, panel=False`,
  12 fields).
- The response was written to `raw/stock/2026-09-28_00000.parquet` (**15,544 B**, 80 rows ×
  14 columns).
- The read-back dtype audit then **rejected** the frame.

**Quota consumed: 5,320 units** of the 700,000 ceiling
(`get_trade_days` 18 + `get_all_securities` 5,222 + `get_price` 80),
balance 200,000,000 → 199,994,680. Well inside bounds.

## 3. The new blocker

```
status:  BLOCKED_PRESERVE_PARTIAL
error:   ROUNDTRIP_NON_TIMESTAMP_DTYPE_CHANGE
```

Raised in `verify_parquet_roundtrip() → restore()`, whose only admitted representation change
is timestamp seconds→milliseconds. The offending column is **`code`**:

| axis | supplier dtype | stored read-back dtype |
|---|---|---|
| `code` | **`object`** | **`str`** |
| `time` | `datetime64[ns]` | `datetime64[ns]` (equal — R2 fix not involved) |
| 12 numeric fields | `float64` | `float64` (equal) |
| index | `int64` | `int64` (equal) |

Mechanism: jqdatasdk builds the response via `pd.DataFrame(OrderedDict(data))`, and `code`
stays **object** dtype. pyarrow writes it as physical **`string`**; pandas 3.0 reads physical
`string` back as the new **`str` StringDtype**, which is not equal to `object`.

Three independent corroborations:

1. the written parquet's own pandas metadata records `code` as `numpy_type='object'`,
   `pandas_type='unicode'` — i.e. object at write time;
2. physical type is **`string`** for the real file, whereas a native pandas `str` column
   writes as **`large_string`** — the two paths are distinguishable;
3. replaying the production `verify_parquet_roundtrip` against the stored frame with **only**
   `code` cast to `object` raises the **identical** `ROUNDTRIP_NON_TIMESTAMP_DTYPE_CHANGE`,
   while the unmodified frame passes.

I also ruled out the alternatives: `time` is `ns` on both sides (so not the R2 issue), the
index is `int64` on both sides, and `paused` is `float64` on both sides — an `int64` `paused`
would have been written as physical `int64`, not `double`, so that hypothesis is impossible.

**All 14 columns are present and value-equal. No price or field corruption.** This is purely
a string-representation mismatch.

## 4. Why 39 offline controls did not catch it

The controls build fixtures whose `code` column is already pandas `str` (writes as
`large_string`, reads back as `str`). The real supplier column is `object`. So the offline
suite is not a superset of the live dtype surface — the same structural gap as R1, one layer
over: the round-trip assertion is exact-dtype and sits **after** the supplier call and
**after** the raw write.

## 5. What this costs and what survives

Only **1 of 66** stock batches for the first day completed, out of an estimated 1,122 stock
batches for the 17 planned days; **ETF and index have zero data**. So this is a very small
partial, not a completed increment.

The single batch on disk is intact and would be usable if the string rule is accepted, so
the 5,320 quota units are not necessarily wasted.

## 6. Options for the reviewer

- **A** — extend the admitted representation rule from "timestamp s→ms only" to also admit
  `object ↔ str` for `code`, with exact-value and null-mask comparison before cast-back, and
  record the rule in every batch receipt. Touches production code.
- **B** — make the write representation-stable for strings too (declare/cast `code` before
  writing) so the in-memory frame and the read-back agree. Touches production code.
- **C** — add a 40th control whose fixture uses an **object-dtype** `code` column so the
  offline suite models the real supplier surface. No production-code change.

My reading: **C alone is insufficient** — it would only convert this live blocker into a
failing control. **B plus C** is the durable fix. Worth noting the contract itself demands
both "preserve original dtype metadata" and "verify dtypes on read-back"; no storage layer
can satisfy that for every pandas string dtype without an explicit declared rule, so the
rule needs widening either way.

## 7. Boundary compliance

Executed **once**, no retry. Made **3** supplier calls, all within the authorized endpoints
and argument bounds. No local patch to the package, no pandas downgrade, no interpreter
substitution, no extra login for a dtype experiment, no deletion of the R1 failure evidence
(still present). No production RAW write, no CURRENT switch, no cleaning, no order.
Credential never printed, hashed or uploaded.

`E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R1` was **not** pre-created; the
script created it itself, as required.

## 8. Delivered files

Receipts: `ACK_R2.json`, `ACK_TIMESTAMP_R2.json`, `PACKAGE_VERIFY_R2.json`, `GATE_R2.json`
(+ stdout/stderr), `RUN_R2.json` (+ stdout/stderr), `DIAGNOSIS_R2.json`, `REPORT_R2.md`,
`DELIVERY_MANIFEST_R2.json`, `UPLOAD_READBACK_R2.json`, `LOCAL_READBACK_R2.json`.

Script output: `r2_staging_output/` — all **16** files (**7,296,584 B**) copied
**byte-verbatim** from `E:`, including `RESULT.json`, `BASELINE.json`, `CALENDAR.json`,
`PLAN.json`, `SDK.json`, the three `COVERAGE_*.json`, the universe JSON, all six
`receipts/*.json`, and the raw batch parquet. Nothing reformatted, nothing edited.

Both `RUN_R2_STDOUT.txt` and `RUN_R2_STDERR.txt` are legitimately 0 bytes — the script
reports through `RESULT.json` and `receipts/`, not console output. `GATE_R2_STDOUT.txt` is
also 0 bytes because `unittest` writes its verbose log to stderr.

Receipts are acyclic; `LOCAL_READBACK_R2.json` is referenced by nothing and its own hash is
never embedded — it is verified after upload by re-fetching.
