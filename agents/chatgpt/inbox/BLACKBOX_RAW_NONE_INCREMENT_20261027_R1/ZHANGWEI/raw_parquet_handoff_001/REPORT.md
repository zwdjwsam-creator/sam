# R5 raw-Parquet body handoff — REPORT

task_id: `BLACKBOX_R5_PARQUET_BODY_HANDOFF_20261028`  
parent_task_id: `BLACKBOX_RAW_NONE_INCREMENT_20261027_R5_ISOLATE_RESUME`  
execution_host: `ZHANGWEI`  
return_path: `agents/chatgpt/inbox/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/ZHANGWEI/raw_parquet_handoff_001/`

Owner authorized transferring these exact raw-Parquet bytes for independent GPT
decoding, amending the earlier local-only restriction **for these bytes only**.

## Outcome

| step | command | actual OS exit | stdout | stderr |
|---|---|---|---|---|
| data preflight | `blackbox_must_read_preflight_r1.py --task-class DATA` | **0** | 870 B | 0 B |
| byte-transfer controls | `-m unittest -v test_capture_raw` | **0** | 0 B | 1164 B |
| capture helper | `capture_raw.py` | **0** | 0 B | 0 B |

Each ran exactly once, attached and waited, with its own raw stream handles and its
own real OS exit. Nothing was retried, merged, reordered or converted to 0.
`CAPTURE_STDOUT.txt` and `CAPTURE_STDERR.txt` are genuinely zero bytes, not a stderr
copy in place of an empty stdout.

Final status string from the helper: `EXACT_RAW_BODY_HANDOFF_ONLY`.

## Gate 1 — DATA preflight

```
MUST_READ_PRECHECK = PASS
TASK_CLASS = DATA
KERNEL_SHA256 = b05a69958e29f7c90cf1ea794a4c437d36120bb960515ce9e26d3f4d5bdf197a
KERNEL_STATUS = VERIFIED
KERNEL_BYTES = 1167
HAND_READ = NOT_SUFFICIENT
AUTHORITY_READY = YES
TASK_EXECUTION = ALLOWED
TASK_EXECUTION_FORBIDDEN = FALSE
rules_loaded:
  - BOOTSTRAP
    expected_sha256 = 704527e0ee7545680cbc3d23962843e4827e0bf380e18b6dd31dfc631ed5c406
    actual_sha256   = 704527e0ee7545680cbc3d23962843e4827e0bf380e18b6dd31dfc631ed5c406
    status = VERIFIED
  - DATA_ACCESS
    expected_sha256 = 0903551847881b0c04d9502fe49c4361e9799a69ba327cccd15b6fbacdf4f1c8
    actual_sha256   = 0903551847881b0c04d9502fe49c4361e9799a69ba327cccd15b6fbacdf4f1c8
    status = VERIFIED
READ_THESE:
 - E:\BLACKBOX\契约\必读\BLACKBOX_BOOTSTRAP_MUST_READ.md
 - E:\BLACKBOX\契约\必读\BLACKBOX_DATA_ACCESS_MUST_READ.md
```

`MUST_READ_PRECHECK = PASS`, `KERNEL_STATUS = VERIFIED`, `BOOTSTRAP` and
`DATA_ACCESS` both `VERIFIED` against the Manifest pins, `AUTHORITY_READY = YES`.
`HAND_READ = NOT_SUFFICIENT` is the fixed informational line the task exempts from
gate status; it was not treated as a failure and not edited.

## Gate 2 — byte-transfer controls

```
test_duplicate_plan_rejected (test_capture_raw.RawHandoff.test_duplicate_plan_rejected) ... ok
test_exact_bytes_zip_and_source_unchanged (test_capture_raw.RawHandoff.test_exact_bytes_zip_and_source_unchanged) ... ok
test_existing_hub_body_reference_not_zipped (test_capture_raw.RawHandoff.test_existing_hub_body_reference_not_zipped) ... ok
test_existing_output_not_overwritten (test_capture_raw.RawHandoff.test_existing_output_not_overwritten) ... ok
test_hash_drift_failure_kept (test_capture_raw.RawHandoff.test_hash_drift_failure_kept) ... ok
test_part_boundary_and_crc (test_capture_raw.RawHandoff.test_part_boundary_and_crc) ... ok
test_path_traversal_rejected (test_capture_raw.RawHandoff.test_path_traversal_rejected) ... ok
test_payload_plan_identity (test_capture_raw.RawHandoff.test_payload_plan_identity) ... ok
test_real_retained_parquet_bytes_not_reencoded (test_capture_raw.RawHandoff.test_real_retained_parquet_bytes_not_reencoded) ... ok
test_unknown_file_never_read (test_capture_raw.RawHandoff.test_unknown_file_never_read) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.077s

OK
```

`Ran 10`, literal `OK`, 0 failures, 0 errors, 0 skips, actual exit 0. These are
byte-transfer / ZIP / plan-identity controls. They are **not** price-value or
original-engine Cleaning acceptance, and are not presented as such.

## Gate 3 — what was captured

- New bodies captured: **1502** files, 23,448,612 source bytes.
- Reused HUB bodies (reference only, deliberately not re-zipped): **2**.
- Plan rows total: **1504** — 1502 capture + 2 reference.

| archive | bytes | members | SHA256 | CRC |
|---|---|---|---|---|
| `raw_part_001.zip` | 7,404,549 | 471 | `73c546944f6156dd6542952791219467b0199836c4d867b263df37fdb604b8ba` | OK |
| `raw_part_002.zip` | 7,399,408 | 471 | `1ed7442221f6f4b614f885ccb29b558c6e1ace0978643c7b9fcd01596946fde5` | OK |
| `raw_part_003.zip` | 7,400,494 | 461 | `374caadfb59b0738c3b8e5b9f77b0273af408fa7a056205541c95847acd1a548` | OK |
| `raw_part_004.zip` | 1,477,101 | 99 | `77fca9522bb363d9da8bd0db2ff2fa9703bdfdd941f4f60ecb6e5cd0dcb8fdcc` | OK |
| **total** | **23,681,552** | **1502** | | |

All four archives are at or below the 8 MiB cap; no part exceeded the 7 MiB source
budget. Every archive passed CRC readback and every member was re-read and hashed
against its plan row.

The two reference rows, recorded in the plan as already present on HUB:

- `R1/raw/stock/2026-09-28_00000.parquet` — 15,544 B, `1e0e6bcec4b6d0b8…` → `agents/chatgpt/inbox/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/ZHANGWEI/r2_staging_output/raw/stock/2026-09-28_00000.parquet`
- `R4/raw/stock/2026-10-27_03360_R4.parquet` — 15,489 B, `fb1a0ccb4918e603…` → `agents/chatgpt/inbox/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/ZHANGWEI/failed_batch_600621_R4/raw/stock/2026-10-27_03360_R4.parquet`

The isolated `600621.XSHG` position inside the R4 failed-batch original stays where
it is: that 80-row batch is referenced whole, not stripped, and no new raw batch was
manufactured to replace 79 admitted positions.

## Independent verification (not the helper self-report)

- All **1502** planned capture members present in ZIPs: yes; unplanned members: 0.
- Members whose bytes+length+SHA256 match the plan row: **1502/1502**.
- REUSE rows wrongly zipped: **0**.
- All **1504** planned sources re-read after the run: **0** drifted. Source bytes are unchanged.
- No extracted copies uploaded beside the archives: none.

## Boundaries held

| boundary | value |
|---|---|
| supplier calls | 0 — no login, no quota movement, no query |
| Cleaning | not run |
| CURRENT switch | none |
| orders | none |
| writes on `E:` | none; all output on `C:` |
| source mutation | none; 1504 sources re-read identical |
| SDK / business imports | none |
| local code patch / rule / HAND edit | none |
| cleanup, process, watchdog, task action | none |
| glob / walk / search / sixth slot | none; only planned paths read |
| secrets | none requested, none uploaded, none hashed from |

## What exit 0 does and does not mean

Exit 0 means **exact raw-body handoff only**: the planned bytes were copied
unmodified into CRC-verified archives. It is not decoded values, not field/dtype/
null acceptance, not supplier ground truth, not Cleaning, not PIT admission, not
publication, and not a CURRENT switch. GPT owns the decode and the later Cleaning
contract.

## Reading order for the audit

1. `ACK_RAW_BODY.json` — task/package/plan identity, boundaries, duplicate check.
2. `PACKAGE_VERIFY.json` — 7/7 payload pins verified, package `PACKAGE.json` SHA256.
3. `PREFLIGHT_*`, `TESTS_*`, `CAPTURE_*` — raw streams and real exits.
4. `capture_001/raw_part_001..004.zip` — the bodies, `ZIP_STORED`, unmodified.
5. `capture_001/RAW_BODY_MANIFEST.json` — helper manifest, 1504 source records.
6. `INDEPENDENT_VERIFY.json` — my own re-read of members and sources.
7. `DELIVERY_MANIFEST.json`, `LOCAL_READBACK.json`, `UPLOAD_READBACK.json`.

