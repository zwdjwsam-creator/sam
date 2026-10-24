# R10 factor-boundary execution: append-only receipt

Round: R10 continuation (not R11, not acceptance). Executor: ZHANGWEI.
Task: `BLACKBOX_FOUNDATION_R10_FACTOR_BOUNDARY_FIXED_EXECUTION_20261024`.
Reviewed: `agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R10_FACTOR_BOUNDARY_20261024/REVIEW.md` (full) and
`PACKAGE.json` before any action.

Nothing in earlier deliveries was overwritten. `FINAL_BLOCKERS.json` and both earlier reports are untouched.

## 0. Previous delivery finished first

The reviewer noted that the separate upload-readback receipt was not present in the inspected directory at review
time. That gap is now closed before this successor work: `REWORK_UPLOAD_READBACK.json`,
`INBOX_POINTER_RECEIPT.json` and `REWORK_FINISHER_READBACK.json` were uploaded into
`rework_2256/` with byte-identical readback, and the updated `REWORK_DELIVERY_MANIFEST.json` records all of them with
their own hashes while still excluding itself. No earlier file was deleted or rewritten in substance, and no rework
command was re-run.

## 1. Package identity

All five supplied files were copied byte-for-byte from the reviewed HUB package into
`reviews/R10/factor_boundary/`. The three Python digests and byte counts match `PACKAGE.json` exactly:

| file | bytes | sha256 |
|------|-------|--------|
| `r10_factor_input_contract.py` | 4046 | `e30acadd...e67c5` |
| `test_r10_factor_input_contract.py` | 4639 | `8055d618...76f8` |
| `r10_factor_desktop_check.py` | 7495 | `76693d08...3cfed0` |

No line ending was normalized, no pin regenerated, no supplied source edited. The old compiler
`cache_compiler_adjust_factor_pit_r1.py` was not hot-patched, imported, executed, or even opened for write.

## 2. The 16 supplied offline controls, on this desktop

Command: `runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\factor_boundary\test_r10_factor_input_contract.py`
Exit code 0. Literal stdout: `{"tests_run": 16, "passed": true, "scope": "PURE_OFFLINE_INPUT_BOUNDARY",
"supplier_calls": 0, "FOUNDATION_ACCEPTANCE": false}`. Stderr carries the unittest summary: 16 tests, `OK`,
0.036s. This satisfies the gate, so the dependent desktop check was allowed to run.

## 3. The fixed desktop check, exactly once

Command: `runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\factor_boundary\r10_factor_desktop_check.py --desktop-check`
Exit code 0, `status = FIXED_FACTOR_BOUNDARY_CHECK_COMPLETE`, `source_files_changed = false`,
`supplier_calls = 0`. The driver ran the genuine CACHE entry itself as a subprocess
(`describe --product ADJUST_FACTOR_PIT_R1`) and required `real_preflight.ok = true` with `MUST_READ_PRECHECK = PASS`
before installing its audit hook. It then read only the four fixed files, snapshotted their bytes, and re-verified each
hash after use.

| role | rows | date dtype | boundary |
|------|------|-----------|----------|
| RAW_0831 | 5212 | `int64` | **REJECTED — NUMERIC_DATE_AXIS_FORBIDDEN** |
| RAW_0901 | 5214 | `int64` | **REJECTED — NUMERIC_DATE_AXIS_FORBIDDEN** |
| RAW_0924 | 5222 | `datetime64[ns]` | SHAPE_VALID_ONLY_NOT_ADMITTED |
| CACHE_2026 | 863710 | `datetime64[ns]` | SHAPE_VALID_ONLY_NOT_ADMITTED |

### 3.1 The two rejected ordinal inputs

Both 2026-08-31 and 2026-09-01 RAW factor units carry integer date axes. The successor boundary rejects them rather
than letting pandas read page ordinals as nanoseconds near 1970. No date was inferred from a file name, no value was
replaced with one, and the files were not repaired. This is a successful boundary rejection, not a source-absence
conclusion (`SOURCE_ABSENCE_CLAIM_ALLOWED = false` on every path).

### 3.2 The valid-date tip and the mounted cache

RAW_0924 passes shape only: 5222 rows, single date `2026-09-24`, 5222 distinct codes, factor range exactly `1.0` to
`1.0`, `all_factor_one = true`, zero duplicate keys. That is explicitly *not* an fq, PIT or authority certificate: the
report labels provenance `NOT_PROVEN_BY_VALUES_OR_SHAPE`.

CACHE_2026 passes shape only: 863710 rows, `2026-01-05` to `2026-09-24`, 5241 distinct codes, factor range
`0.6646688228269108` to `1.0`, zero duplicate keys. Density is reported as
`OBSERVED_FACTOR_KEYS_ONLY; NOT_A_UNIVERSE_COMPLETENESS_CERTIFICATE`.

Two observations bear on B1 but close nothing:

- Session density thins sharply from `2026-08-17` (89 rows) through `2026-08-28` (19 rows), then returns to 5208 on
  `2026-08-31`, 11 on `2026-09-01` and 7 on `2026-09-02`, before resuming at 5215 on `2026-09-03`.
- The nine target observations requested by the driver are present: on 2026-08-31 the factors are
  `000001.XSHE 1.0`, `002223.XSHE 0.9846035023142652`, `301237.XSHE 0.7189900732540311`,
  `600351.XSHG 0.9719101537155483`, `600989.XSHG 0.9830099998379282`; on 2026-09-01 the four non-`000001` codes are
  each `1.0` and `000001.XSHE` has no row.

## 4. What this does and does not establish

Established, within the four fixed files: the tested successor boundary parses valid datetime axes, rejects numeric
axes, rejects duplicate keys and alias conflicts, and refuses null/nonpositive/nonfinite factors. Measured on real
desktop bytes, not only on the review host.

Not established: that the old compiler produced every malformed cache; fq provenance for any historical row; PIT
correctness; universe completeness; the 83503-row adjustment reconciliation; source-to-cache lineage; compiler
integration; any rebuild of affected history.

## 5. B1 linkage

This evidence is linked to `B1_ADJUSTMENT_RECONCILIATION` and **does not close it**. B1 remains `OPEN`. Three
questions are carried forward for the owner: `83503_ROW_RECONCILIATION`, `SOURCE_TO_CACHE_LINEAGE`,
`HISTORICAL_FQ_AND_PIT_PROVENANCE`.

The other six groups are unchanged by this round. No whole-catalog inventory was repeated and no scope was expanded.

## 6. Reporting-scope corrections requested by the review

Recorded in `REPORTING_SCOPE_CORRECTION.json`, all four as reporting fixes only:

1. Recovered candidate proof is product-specific to stock daily. ETF, index, valuation and fund candidates are not
   implied by the two stock queries, and a single `raw_present=true` must not be spread across that mixed list.
2. The canonical guide path is `E:\BLACKBOX\_OPS\CURSOR_WORKSPACE\BLACKBOX_LOCAL_OPERATIONS_R10.md`. The earlier
   string carried a stray extra `_OPS`. No reinstall was performed.
3. Template identification for the JQ daily simulation template and readme satisfies identification for those two
   artifacts only; old-strategy reconstruction is not a blocker to this data repair.
4. The verified asof-versioned exchange calendar is the session authority, not a factor-derived date union.
   Historical copied labels inside the update-plan, including a factor-derived calendar description and old gap
   wording, are neither a new missing-source verdict nor an executable permission.

## 7. Permissions unchanged

    FOUNDATION_ACCEPTANCE=false
    FORMAL_ENGINE_ADMISSION=false
    INCREMENTAL_PIPELINE_READINESS=NOT_ACCEPTED
    LATEST_FULL_UPDATE=NOT_VERIFIED
    FULL_GOAL_MET=false
    NEW_DATA_ACQUISITION_AUTHORIZED=false
    CURRENT_SWITCH_ALLOWED=false
    ORDER_ALLOWED=false

No supplier call, credential read, login, download, updater invocation, scheduler activation, package installation,
business-data write, CURRENT change, provider registration, engine construction, backtest or order occurred in this
round. The local executor's task ends after upload and full readback, pending GPT review. GPT owns the follow-on
compiler, data and contract integration.
