# R10 continuation — declared local source-batch chain measured against byte-pinned R26 Cleaning

Executor: ZHANGWEI. Round: `R10_SOURCE_BATCH_CHAIN_20261025` (R10 continuation, NOT acceptance).
Package: `agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R10_SOURCE_BATCH_CHAIN_20261025/`
Date of measurement: 2026-10-25, 01:21:12–01:22:52 +08:00.

Append-only. Nothing in an earlier receipt is rewritten. This file records only what was actually
executed and observed in this round.

FOUNDATION_ACCEPTANCE=false · FORMAL_ENGINE_ADMISSION=false · NEW_DATA_ACQUISITION_AUTHORIZED=false ·
CURRENT_SWITCH_ALLOWED=false · ORDER_ALLOWED=false · B1..B7 OPEN.

---

## 1. What this round is

The previously identified gap was that the accepted factor-basis measurement compared
R26 **Cleaning -> CACHE**, while the original generator `download_source_fq_pre_r1.py` declares a
*separate* staged source at `TASK/staging/source_batches/year=YYYY/batch_NNN.parquet (+ .sidecar.json)`.
Inspecting the legacy P1 directory could not account for that declared source. This round measures the
declared staged directory itself and compares it, per year, with the already hash-pinned 13 R26
Cleaning partitions.

This is a **staged source -> Cleaning** link, a different comparison from the earlier
Cleaning -> CACHE basis work. It is not a rerun of that work.

Not done, by instruction: no rerun of dirty_branch, no old-writer run, no 13-year Cleaning-vs-CACHE
comparison, no catalog inventory, no original-source lookup, no downloader execution (any mode,
import, CLI, help, resume), no supplier/network call, no drive or all-layer enumeration, no
production patch, no business-data write, no date/factor repair, no CURRENT change, no engine
construction, no order. `supplier_calls=0`, `all_layer_search_performed=false`,
`source_files_changed=false`.

Prior dirty_branch delivery had already completed its own upload and readback
(`r10_dirty_branch_delivery/FINAL_BYTE_READBACK.json`); it was reused as instructed and **not**
re-uploaded or re-measured. No second finisher was started.

## 2. Pre-execution pin verification (before command 2)

`PACKAGE.json` was written into the stage directory **first**, so it was present before any
execution; its bytes are identical to the supplied manifest. Every declared member was then compared
by exact byte count **and** exact SHA256, with line endings preserved (no newline conversion, no
re-pinning, no substitute harness). All 8 members plus the manifest match; `all_pins_match=true`,
`stop_triggered=false`. Full record: `PRE_EXECUTION_PIN_CHECK.json`.

| member | bytes | sha256 | match |
| --- | --- | --- | --- |
| r10_factor_source_batches.py | 8,050 | adc5ab69b70495b24cb653904282f57210998fac52174ff7eeda95895d142e5e | yes |
| test_r10_factor_source_batches.py | 2,216 | 532e6c865b6d07c0d430eee97f066e34fd8e613d069e2b5afc42e272e5c557a1 | yes |
| r10_factor_input_contract.py | 4,046 | e30acaddecf03e0abd4360f60a74bae53525373e55feb51cf76d409beebe67c5 | yes |
| r10_factor_desktop_check.py | 7,495 | 76693d0834086e22b2afa62c70c4973b8271e14242ccae5c7f2a3f269d3cfed0 | yes |
| r10_factor_reconcile.py | 11,223 | 171146f589fe1dbaf6903a1a5b631718732175705cb25ccf81e08a657145ae33 | yes |
| INPUTS.json | 4,671 | fdcdbbbe6a409c7a9c5f64c3201e422268680ca5d1a4ec9e7b528020c7810d13 | yes |
| REVIEW.md | 3,877 | 3e94184b0bca629200d730da2b972d3c18066c23bb8ff7d1e0298275c0267d6d | yes |
| OFFLINE_TEST_RECEIPT.json | 209 | 7692db7f9328bdc36759eb077d09125d4126f54c3bd9dc499c3e723d981705ce | yes |
| PACKAGE.json (manifest, present pre-execution) | 1,410 | 1707c47e2183c572… (byte-identical to supplied copy) | yes |

Raw copies of all nine supplied files are in `SUPPLIED_SOURCES/` with their own byte/SHA record.

## 3. Offline controls — 8 of 8 pass

Exactly as instructed, once:

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\source_batch_chain\test_r10_factor_source_batches.py

Exit 0, window 01:21:12.750–01:21:14.767 +08:00. Literal stdout (134 B):

    {"tests_run": 8, "passed": true, "scope": "SOURCE_BATCH_BOUNDARY_OFFLINE_ONLY", "supplier_calls": 0, "FOUNDATION_ACCEPTANCE": false}

Literal stderr (111 B):

    ........
    ----------------------------------------------------------------------
    Ran 8 tests in 0.013s

    OK

Raw bytes: `captures/TEST_8_CONTROLS.stdout.bin`, `captures/TEST_8_CONTROLS.stderr.bin`.
No failure occurred, so the dependent step was permitted.

## 4. The single fixed desktop check

Executed exactly once, exit 0, window 01:21:22.357–01:22:52.047 +08:00. stdout 122,907 B,
stderr 0 B.

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\source_batch_chain\r10_factor_source_batches.py --desktop-check

Observed status field: `DECLARED_SOURCE_BATCH_CHAIN_MEASURED` (no `STOP`, no exit 3).
Exact driver output: `DRIVER_OUTPUT.json` (byte-identical to the raw capture
`captures/DESKTOP_SOURCE_BATCHES.stdout.bin`, sha256 in `COMMAND_LEDGER.json`).

Genuine preflight inside the driver, exit 0:

    argv  runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py describe --product ADJUST_FACTOR_PIT_R1
    MUST_READ_PRECHECK  PASS
    task_class          ["CACHE"]
    required            ["BOOTSTRAP", "DATA_ACCESS"]
    problems            []
    kernel sha256       b05a69958e29f7c90cf1ea794a4c437d36120bb960515ce9e26d3f4d5bdf197a (1,167 B)
    BOOTSTRAP           VERIFIED 704527e0ee7545680cbc3d23962843e4827e0bf380e18b6dd31dfc631ed5c406
    DATA_ACCESS         VERIFIED 0903551847881b0c04d9502fe49c4361e9799a69ba327cccd15b6fbacdf4f1c8

The read-only/no-network audit hook was installed after the preflight returned, before any declared
data read. Input byte identities were re-verified after the comparison loop completed.

## 5. Inputs bound

| input | identity |
| --- | --- |
| `download_source_fq_pre_r1.py` (original generator, byte-pinned) | sha256 `8a49616147748b46d168542973020aed86cb1e70d09a09a45960cb641201bcea` |
| `TASK/staging/UNIVERSE.json` | 524 B, sha256 `caf7ec1bf1921270188f329151699cda1c0cd67bc176b12932d91f41cea50411`, original bytes delivered |
| `TASK/staging/DOWNLOAD_STATE.json` | 204 B, sha256 `e6a35aca4c03f1b8a539bf96b7ad598945eb4f16199bdd89f35af4c2562aab21`, original bytes delivered |
| 13 R26 Cleaning partitions | the 13 sha256 pins carried forward from the accepted factor-basis measurement, re-verified here; per-year value in `YEAR_RESULTS.csv` |

UNIVERSE metadata observed: `n=5521`, `start=2014-01-01`, `end=2026-08-14`, `fq=pre`,
`batch=400` -> 14 declared batch indices per year. DOWNLOAD_STATE observed: `done_new=182`,
`skipped=0`, `failed=0`, `fq=pre`, `start=2014-01-01`, `end=2026-08-14`,
`finished_at_cn=2026-08-16T03:33:02+0800`, `quota_spare_end=183053183`.

The UNIVERSE `n/batch` pair is used **only** to bind the expected local file layout. It is not
treated as proof of any historical expected daily universe.

## 6. Declared staged source as measured

Only the 13 declared `year=` directories and their 14 declared `batch_NNN.parquet` +
`batch_NNN.sidecar.json` names were enumerated. No other root or task directory was scanned.

    batch parquet files measured      182   (14 x 13)
    matching sidecar json files       182
    total source rows                 12,176,722
    empty batch parquet files          15   (1,851 B each, identical bytes)
    distinct parquet sha256 values    168   (182 files; the 15 empties collapse to one)

Every batch is tagged `NEW_MEASURED_NOT_ADMITTED`. These are newly measured staged-file identities,
not supplier certificates and not source execution authority. Per-file paths, rows, bytes and both
hashes are in `BATCH_OBSERVATIONS.csv`.

The 15 empty files are `year=2014..2018` x `batch_006/012/013`. They were accepted as measurable
empties under the driver contract (sidecar agreement held); the driver would otherwise have stopped.
No cause is asserted, and an empty batch is not a completeness certificate.

## 7. Source vs Cleaning, per year

Keys are validated date/code pairs; values are factor. `src_only`/`clean_only` are non-shared keys;
`unequal` counts shared keys whose value differs.

| year | source rows | cleaning rows | src_only | clean_only | shared | unequal |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | 620,803 | 620,803 | 0 | 0 | 620,803 | 0 |
| 2015 | 665,913 | 665,913 | 0 | 0 | 665,913 | 0 |
| 2016 | 704,876 | 704,876 | 0 | 0 | 704,876 | 0 |
| 2017 | 799,798 | 799,798 | 0 | 0 | 799,798 | 0 |
| 2018 | 857,319 | 857,319 | 0 | 0 | 857,319 | 0 |
| 2019 | 890,482 | 890,482 | 0 | 0 | 890,482 | 0 |
| 2020 | 951,992 | 951,992 | 0 | 0 | 951,992 | 0 |
| 2021 | 1,062,380 | 1,062,380 | 0 | 0 | 1,062,380 | 0 |
| 2022 | 1,149,235 | 1,149,235 | 0 | 0 | 1,149,235 | 0 |
| 2023 | 1,211,865 | 1,211,865 | 0 | 0 | 1,211,865 | 0 |
| 2024 | 1,236,214 | 1,236,214 | 0 | 0 | 1,236,214 | 0 |
| 2025 | 1,251,439 | 1,251,439 | 0 | 0 | 1,251,439 | 0 |
| 2026 | 774,406 | 774,406 | 0 | 0 | 774,406 | 0 |
| **total** | **12,176,722** | **12,176,722** | **0** | **0** | **12,176,722** | **0** |

Observed: for the declared window, the staged source and the byte-pinned R26 Cleaning partitions have
identical key sets in every year and identical factor values on every shared key — zero
source-only keys, zero cleaning-only keys, zero unequal values. Nothing was repaired, filled or
reconstructed to obtain this; had any key or value differed it is printed as measured.

`MEASUREMENT_SUMMARY.json` records the same aggregates machine-readably, plus
`exact_key_and_value_identity_all_years=true`.

## 8. What this does and does not establish

Establishes, within the measured scope: a locally staged source directory, whose layout and metadata
are those the byte-pinned generator declares, reproduces the accepted R26 Cleaning adjust-factor
content exactly over 2014-01-01..2026-08-14 on shared keys.

Does **not** establish: supplier execution or provenance, the historical expected daily universe,
PIT authority, full market coverage, a closed B1..B7, or anything about records after 2026-08-14.
The generator's cutoff is 2026-08-14, so even exact identity here cannot certify the later
August/September records, the 2026-09-02 sparse partition, or the 83,503 physical-minus-declared
discrepancy. Prior single-day sparsity evidence therefore remains a separate, still-open line.

## 9. Disclosures

C1 Sequencing. Order was: pin check, one control run, one desktop run. No member was re-pinned and
the driver was executed exactly once. `PACKAGE.json` was present before execution, so this round had
no staging-incomplete stopped attempt (unlike the prior dirty_branch round).

C2 Read scope. The driver read `UNIVERSE.json` and `DOWNLOAD_STATE.json` and reported parsed
metadata only. Those two exact paths were then re-read read-only solely to deliver the original
metadata bytes requested in item 4. No directory was enumerated for that step and no other file was
opened. Delivered bytes are byte-identical (CRLF line endings intact, 28 and 9 CRLF respectively).

C3 Prior delivery. The dirty_branch upload/readback was already complete and was reused, not
repeated. No dirty_branch, old-writer, basis-comparison, catalog or source-lookup step was rerun.

C4 Sidecar agreement. The driver emits no per-batch sidecar flag; `validate_batch` raises on any
count/bound/fq/sidecar conflict and the run would have exited 3 with `STOP`. A measured result
therefore means all 182 sidecars agreed within the driver contract. This is a property of the
supplied control flow, not an extra independent assertion.

C5 Empty batches. 15 of 182 files are empty placeholders; Cleaning has no keys in those ranges
(`clean_only_keys=0` in every year). Measured as empty, not rejected. No cause asserted.

C6 Clock notation. All times here are `+08:00`.

## 10. Ledger, manifest, readback

    COMMAND_LEDGER.json       3 commands, exit codes, windows, stdout/stderr bytes + sha256
    PRE_EXECUTION_PIN_CHECK.json  per-member byte/SHA match, line endings, stage ctimes
    MEASUREMENT_SUMMARY.json  aggregates and false flags
    BATCH_OBSERVATIONS.csv    182 rows
    YEAR_RESULTS.csv          13 rows
    DRIVER_OUTPUT.json        exact driver output bytes
    METADATA_ORIGINAL/        UNIVERSE.json, DOWNLOAD_STATE.json original bytes
    SUPPLIED_SOURCES/         all 9 supplied files, exact bytes
    CORRECTIONS_APPEND_ONLY.json  C1..C6
    DELIVERY_MANIFEST.json    every delivery member except itself
    FINAL_BYTE_READBACK.json  remote blob identity vs local bytes, after upload

No parquet file was uploaded.
