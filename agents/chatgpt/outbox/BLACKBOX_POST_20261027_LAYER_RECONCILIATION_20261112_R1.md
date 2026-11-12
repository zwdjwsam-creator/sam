# Task — Post-2026-10-27 Registered Layer Metadata Capture R1

task_id: BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1  
execution_host: ZHANGWEI  
workspace: E:\BLACKBOX  
status: ISSUED — ACK AND NATIVE EXECUTION PENDING  
ACK_REQUESTED: true  
return_path: agents/chatgpt/inbox/BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1/ZHANGWEI/

## 1. Purpose and boundary

This is a read-only metadata capture prerequisite. It is not R6 acquisition, a supplier-availability probe, a Cleaning run, or a source-absence determination.

Capture only the exact 11 registered metadata/dictionary files pinned in the reviewed script. Use the existing R07/R10 registry and layer-search evidence; do not scan directories or search for aliases. The script records literal date references for the 11 candidate exchange sessions below. A missing literal reference is not evidence that source data is absent.

Candidate sessions for metadata lookup only:
2026-10-28, 2026-10-29, 2026-10-30, 2026-11-02, 2026-11-03, 2026-11-04, 2026-11-05, 2026-11-06, 2026-11-09, 2026-11-10, 2026-11-11.

The R5 review cites the official SSE/SZSE 2026 holiday schedules. The SSE notice was fetched successfully in the GPT review; the direct SZSE fetch timed out in that review. These dates remain candidate lookup dates only. P1 remains frozen through 2026-10-27 and must not be extended or activated by this task.

## 2. Reviewed package pins

Stage these exact files from the reviewed folder into:
C:\LAN_SHARE_REPORT\BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1_PACKAGE\package\

- capture_registered_layer_metadata_r1.py — 13,128 bytes; SHA256 f40b762e97cefee39d6746fcf2c6f4d380ff537b0089a87071ba0825f8bf049c
- test_capture_registered_layer_metadata_r1.py — 5,564 bytes; SHA256 a205813cd4640dc02879eef2dffc6d65acd3d785d7ffe48bc8f8c74d2ad64cc4
- PACKAGE.json — 711 bytes; SHA256 2c6fb962e3fae26bc1b44eb618b71d1c20ede4ebca8dfce258818adc5465142d

Do not edit, patch, reformat or regenerate these files. Verify byte counts and SHA256 before execution. If any package pin differs, stop and return the mismatch.

The fixed output root is:
C:\LAN_SHARE_REPORT\BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1_PACKAGE\

If that root, its delivery subdirectory, or RUN_ONCE.json already exists before staging, stop. Do not delete, rename, reuse or overwrite it.

## 3. Required pre-execution checks

The measured ZHANGWEI interpreter is:
E:\BLACKBOX\.venv\Scripts\python.exe
Python 3.12.10, Windows x64.

Before running the preflight, verify these exact local source pins:
- E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py — 11,767 bytes; SHA256 3bb85023387ce976aaf03694073936b0da5b5ef710f80f6284e8347f067fe217
- E:\BLACKBOX\脚本\_base.py — 11,800 bytes; SHA256 b8cc60746f92dc63049e8e6b6b6f39c6553dd98b69374b9f797d49b2654f2258

If either pin differs or either file is absent, stop. Do not repair or replace the preflight.

Run the package's 12 offline tests first, from the package directory. Capture stdout, stderr and the literal OS exit. Required command:

    & 'E:\BLACKBOX\.venv\Scripts\python.exe' -B -X utf8 -m unittest -v test_capture_registered_layer_metadata_r1

If the actual exit is nonzero or the suite does not report 12 tests passed, stop before the metadata capture.

Then run the pinned read-only must-read preflight once. Capture stdout, stderr, JSON and literal OS exit. Required command:

    & 'E:\BLACKBOX\.venv\Scripts\python.exe' -B -X utf8 'E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py' --task-class DATA --json

Proceed only if the actual exit is 0 and the JSON reports:
- MUST_READ_PRECHECK = PASS
- AUTHORITY_READY = YES
- TASK_EXECUTION = ALLOWED
- TASK_EXECUTION_FORBIDDEN = FALSE

Otherwise stop and return the exact failure. Do not bypass, edit rules, or retry.

## 4. Exact capture command

After ACK, package-pin verification, tests and preflight all pass, run the capture exactly once, from the package directory:

    & 'E:\BLACKBOX\.venv\Scripts\python.exe' -B -X utf8 'C:\LAN_SHARE_REPORT\BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1_PACKAGE\package\capture_registered_layer_metadata_r1.py'

Capture stdout, stderr, start/end UTC, cwd, exact argv and literal OS exit in OUTER_RUN.json. Do not retry under any circumstances. The script itself creates RUN_ONCE.json and the delivery folder, reads only its fixed allowlist, and writes only beneath the C: output root.

Expected exits:
- 0: all 11 exact files captured and parsed, with no immutable dictionary pin mismatch.
- 2: partial evidence (exact path missing, parse error, size cap, unstable read, or immutable pin mismatch). Preserve and upload the partial result; do not retry.
- 4: existing RUN_ONCE/delivery root; preserve the collision and stop.
- Any other exit: preserve literal output and stop.

A changed CURRENT pointer hash is not itself failure: the script records CHANGED_SINCE_HISTORICAL_BASELINE and captures the current bytes. The two normative CSVs are immutable pins; a mismatch is blocking but the actual bytes are still preserved in the partial delivery.

## 5. Exact read scope

The script reads only these exact paths:
- E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\ECOLOGY_REGISTRY_R3.json
- E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\r10_writer_cursor_bindings_delivery\ACQUISITION_WRITER_CURSOR_BINDINGS.json
- E:\BLACKBOX\运行\BLACKBOX_RAW_COVERAGE_LEDGER_CURRENT.json
- E:\BLACKBOX\运行\BLACKBOX_CLEANING_COVERAGE_LEDGER_CURRENT.json
- E:\BLACKBOX\运行\BLACKBOX_CACHE_COVERAGE_LEDGER_CURRENT.json
- E:\BLACKBOX\研究系统\数据平面\CURRENT\DAILY_DATA_MANIFEST_CURRENT.json
- E:\BLACKBOX\研究系统\数据平面\CURRENT\DAILY_DATA_PLANE_CURRENT.json
- E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json
- E:\BLACKBOX\数据\回测缓存\CURRENT_CACHE_RELEASE.json
- E:\BLACKBOX\数据\原始只读\JQData_reference_dictionary\20_unified_data_schema_contract_freeze_full_R1\02_domain_schema\domain_schema_contract.csv
- E:\BLACKBOX\数据\原始只读\JQData_reference_dictionary\20_unified_data_schema_contract_freeze_full_R1\04_pit_schema\pit_schema_contract.csv

No other source paths are authorized. No directory enumeration, glob, recursive scan, cache reader query, Parquet read, supplier call, network call or credential read is authorized.

## 6. Forbidden actions

- No JQData, QMT, HTTP or other supplier/API call.
- No credential, password, token, cookie or secret-derived hash read/upload.
- No RAW, Parquet, Cleaning output or cache data-file read.
- No write, rename, delete, overwrite, migration or format operation on E:.
- No modification of the registry, coverage ledgers, dictionaries, current pointers, historical seals or source evidence.
- No Cleaning, alignment, PIT transformation, Compiler run, backtest or engine start.
- No CURRENT switch, release, publication or order.
- Do not execute, stop, duplicate or modify the outstanding R4 diagnostic.
- Do not infer source absence from a missing metadata reference, cache miss, stale index, empty virtual member or schema mismatch.

ORDER_ALLOWED=false.

## 7. Return and readback contract

Return every output under:
agents/chatgpt/inbox/BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1/ZHANGWEI/

Include:
- ACK.json
- package pin verification receipt
- TESTS_RUN.json, TESTS.stdout.txt, TESTS.stderr.txt
- PREFLIGHT_RUN.json, PREFLIGHT.stdout.txt, PREFLIGHT.stderr.txt
- RUN_ONCE.json
- delivery/CAPTURE_MANIFEST.json
- delivery/SUMMARY.json
- delivery/REPORT.md
- every file under delivery/capture_001/
- OUTER_RUN.json, CAPTURE.stdout.txt, CAPTURE.stderr.txt
- DELIVERY_MANIFEST.json
- UPLOAD_READBACK.json

Upload ACK before executing. Upload all result files, then read back every uploaded file and compare exact byte count and SHA256. Upload UPLOAD_READBACK.json last, read it back too, and verify its own bytes/SHA256 against the local copy. Do not end the Cursor chat until every file is uploaded and read back. Then end the Cursor chat with exactly:

END

If any upload or readback fails, preserve the failure and do not claim completion.

## 8. GPT review boundary

This task only provides current registered metadata and dictionary evidence. It does not prove row-level coverage, source availability, source absence, data completeness, Cleaning correctness, PIT admission or R10 full-foundation acceptance.

GPT will independently review the returned bytes, generation identities, date references, dictionary rows and layer references before deciding whether a separate exact row-level inspection or acquisition contract is justified. No R6 supplier task is authorized by this metadata capture.
