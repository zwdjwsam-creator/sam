# R10 continuation — fixed acquisition-readiness metadata capture (bytes only, no updater run)

Executor: ZHANGWEI. Round: `BLACKBOX_FOUNDATION_R10_FIXED_READINESS_METADATA_20261025` (R10 continuation).
Instruction: `outbox/BLACKBOX_FOUNDATION_R10_FIXED_READINESS_METADATA_20261025.md`.
Window: 2026-10-25 03:55:09 – 03:57 +08:00. Host ZHANGWEI, cwd `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024`,
`PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`, interpreter `runtime/.venv/Scripts/python.exe`.

Append-only. No new inventory, no repeated accepted tests, no rescan of the R04–R10 layer/dictionary/namespace/
entitlement/exclusion evidence.

FOUNDATION_ACCEPTANCE=false · FORMAL_ENGINE_ADMISSION=false · NEW_DATA_ACQUISITION_AUTHORIZED=false ·
CURRENT_SWITCH_ALLOWED=false · ORDER_ALLOWED=false · SOURCE_ABSENCE_CLAIM_ALLOWED=false · B1..B7 OPEN.

---

## 1. Reporting correction carried forward (prior receipt left untouched)

**K1.** The prior connected-candidate receipt, section 4, stated that the refresh assembly "drops non-dirty observed
rows". Its actual source **retains** them: it concatenates `observed.loc[~observed.code.isin(dirty)]` with the
revised full histories — non-dirty observations are **retained** and dirty histories are **replaced**. The earlier
receipt file is preserved as delivered; the correction is carried here only. No code or historical data was edited.

## 2. Stage and pin, before any execution

`PACKAGE.json` staged first (566 B, sha256 `e43922f5062bbab6…`), then the three pinned members. Declared and
observed bytes/sha256 all match, staged bytes are byte-identical to the supplied bytes, and the files were not
edited or re-pinned:

| member | bytes | sha256 | BOM / CRLF |
| --- | --- | --- | --- |
| `capture_readiness_metadata.py` | 3,854 | `2cff2803b589d31a…` | no / 0 |
| `test_capture_readiness_metadata.py` | 2,507 | `e03df6c6eadcc2aa…` | no / 0 |
| `OFFLINE_TEST_RECEIPT.json` | 148 | `95c6c35e7a28fe13…` | no / 0 |

Pre-conditions recorded: `r10_readiness_metadata_delivery` **did not exist**, and it was not pre-created for
staging — command captures were kept in `r10_readiness_metadata_command_captures` until the supplied script itself
created the delivery.

## 3. Genuine pinned preflight

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py describe --product ADJUST_FACTOR_PIT_R1
    exit 0   03:55:09.9102832 -> 03:55:10.9221232 +08:00   stdout 6,632 B   stderr 0 B

    real_preflight.ok = true · MUST_READ_PRECHECK = PASS · task_class = [CACHE] · problems = []
    BOOTSTRAP / DATA_ACCESS = VERIFIED (expected == actual)
    KERNEL_SHA256 = b05a69958e29f7c90cf1ea794a4c437d36120bb960515ce9e26d3f4d5bdf197a
    TASK_EXECUTION = ALLOWED

## 4. Supplied controls, then the single capture

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\fixed_readiness_metadata\test_capture_readiness_metadata.py
    exit 0   03:55:14.7924595 -> 03:55:15.8037699 +08:00   stdout 84 B   stderr 111 B

    {"tests_run": 8, "passed": true, "scope": "FIXED_METADATA_CAPTURE_TEMPFILES_ONLY"}

stderr: eight progress dots, the standard summary `Ran 8 tests in 0.032s`, `OK`. Expected 8 / passed / exit 0;
observed 8 / true / exit 0. Executed once; not rerun for capture; nothing edited.

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\fixed_readiness_metadata\capture_readiness_metadata.py
    exit 0   03:55:19.5225260 -> 03:55:20.5435199 +08:00   stdout 1,385 B   stderr 0 B

All four allowlisted records returned `ORIGINAL_METADATA_BYTES_CAPTURED`:

| record | origin | bytes | sha256 |
| --- | --- | --- | --- |
| `legacy_checkpoint` | `数据\原始只读\JQData_9999_official_raw\_checkpoint\latest_checkpoint.json` | 550 | `9b6fd7ee2bb8304e…` |
| `pipeline_matrix` | `运行\BLACKBOX_FULL_DATA_PIPELINE_MATRIX_CURRENT.json` | 9,153 | `8d8b0ced9f16c081…` |
| `increment_rule` | `运行\BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json` | 9,100 | `2084f9683f1aa838…` |
| `raw_coverage_ledger` | `运行\BLACKBOX_RAW_COVERAGE_LEDGER_CURRENT.json` | 11,392 | `f7f28c0840e50a85…` |

**Exit 0 means the four metadata copies were captured. It is not readiness, completeness, freshness or an
acquisition authorization.** No exit-3 case arose, so nothing was left incomplete. A post-run re-hash of all four
origins equals the exported copies — no drift, no input change.

## 5. What the metadata says at face value (and what was not computed)

* `legacy_checkpoint` — `task=JQ_DATA_DOWNLOAD_EXECUTION_R1`, `batch_id=20260613_005426`, `status=COMPLETED`,
  `current_T_stage=DONE`, `stop_reason=RESUME_COMPLETION`, `updated_at=2026-06-12T17:48:17.336095+00:00`. This is a
  legacy execution checkpoint of a June 2026 batch task. Its filename, COMPLETED flag and timestamp do **not**
  establish a daily cursor, no writer binding was performed, and it is **not selected as authoritative**.
* `pipeline_matrix` — `rule_id=BLACKBOX_FULL_DATA_PIPELINE_MATRIX_R1`, own `asof=2026-08-12`,
  `generated_at_cn=2026-09-25T04:04:43+0800`, `overall=PASS`, plus its release IDs, required-product presence map,
  standard pipeline and hard-rule list. Recorded as that document's own statement at its own as-of; not a fresh
  serving verdict and not used to derive an increment start.
* `increment_rule` — `rule_id=BLACKBOX_HAND_JQ_INCREMENTAL_DOWNLOAD_RULE_R1`, `status=ACTIVE`, `layer=HAND_TOP`,
  with per-dataset increment classes, PIT policies and raw/clean/cache namespaces. Recorded as rule text.
* `raw_coverage_ledger` — `schema=BLACKBOX_RAW_COVERAGE_LEDGER_R1`, `generated_at=2026-08-12T15:17:56+08:00`, a
  recorded trade-calendar authority and per-dataset windows. Not re-measured; its window is not adopted as a plan.

Not computed by this round: increment target range, expected market universe, supplier lag, missing-data verdict,
checkpoint authority, per-date lineage. `source_absence_claim_allowed=false` throughout.

## 6. Untouched and not executed

* `jq_download_execution_r1.py` — guarded; not imported, not run, not resumed, guard not removed.
* `run_blackbox_daily_incremental_data_plane_r1.py` — not invoked even in status mode, because that path writes
  current/archive state.
* No production publish gate, merge, engine construction, CURRENT switch, order, supplier call or credential read.
* Only JSON metadata was read; no parquet was opened and no path referenced inside any JSON was followed.

## 7. Delivery contents

    SUPPLIED_SOURCES/            PACKAGE.json + the three supplied members, original bytes
    captures/                    PREFLIGHT / TEST / CAPTURE stdout and stderr, literal bytes
    legacy_checkpoint.original.json, pipeline_matrix.original.json,
    increment_rule.original.json, raw_coverage_ledger.original.json   the script's own exports
    CAPTURE_RECEIPT.json         the script's own receipt, unmodified
    STAGE_AND_PIN_CHECK.json     manifest-first staging, pins, pre-conditions (destination absent)
    EXECUTION_RECORD.json        all three commands, windows, capture hashes, preflight block, verbatim streams
    BODY_PROVENANCE.json         supplied spans, exported bytes, post-run origin re-hash (no drift)
    OBSERVED_METADATA_FACE_VALUE.json  face-value fields only, with the not-computed list
    CORRECTIONS_APPEND_ONLY.json K1..K6
    B1_B7_CARRY_FORWARD.json     unchanged, no inventory rerun, no closure
    COMMAND_LEDGER.json          every step, exit and outcome
    DELIVERY_MANIFEST.json       every member except itself and the readback
    FINAL_BYTE_READBACK.json     separate readback written after the upload, then itself uploaded

No password, token, cookie or secret-derived hash is included; the supplied script refuses potential-secret inputs
before exporting any bytes or digest, and no such refusal occurred.
