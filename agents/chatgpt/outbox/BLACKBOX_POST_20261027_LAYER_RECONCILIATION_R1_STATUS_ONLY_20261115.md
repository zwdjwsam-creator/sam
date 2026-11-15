# Task — Resolve the Native Status of the Outstanding R1 Metadata Capture (Read-Only Status Only)

task_id: BLACKBOX_POST_20261027_LAYER_RECONCILIATION_R1_STATUS_ONLY_20261115
parent_task_id: BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1
execution_host: ZHANGWEI
workspace: E:\BLACKBOX
status: ISSUED — ACK AND NATIVE STATUS RECEIPT PENDING
ACK_REQUESTED: true
return_path: agents/chatgpt/inbox/BLACKBOX_POST_20261027_LAYER_RECONCILIATION_R1_STATUS_ONLY_20261115/ZHANGWEI/
ORDER_ALLOWED=false

## 1. Purpose

Determine the literal current local execution state of the already-issued parent task R1. The GitHub HUB has no R1 ACK, OUTER_RUN, or return directory. The R1 package pins in the reviewed GitHub bytes do not match the hashes pinned by the R1 task. The native execution state is unknown.

This task is status-only. It does not authorize, resume, replay, repair, replace, or complete R1. Do not start a new R1 process. Do not stop, signal, suspend, or otherwise control any process. If an R1 process is active, record it and stop this task without reading files that the process may be writing.

## 2. Exact read-only scope

Inspect only these exact local paths beneath the already-defined R1 output root:

`C:\LAN_SHARE_REPORT\BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1_PACKAGE\`

Exact paths to test, without wildcard or directory enumeration:

- root directory
- `package\`
- `package\capture_registered_layer_metadata_r1.py`
- `package\test_capture_registered_layer_metadata_r1.py`
- `package\PACKAGE.json`
- `RUN_ONCE.json`
- `TESTS_RUN.json`
- `TESTS.stdout.txt`
- `TESTS.stderr.txt`
- `PREFLIGHT_RUN.json`
- `PREFLIGHT.stdout.txt`
- `PREFLIGHT.stderr.txt`
- `OUTER_RUN.json`
- `CAPTURE.stdout.txt`
- `CAPTURE.stderr.txt`
- `delivery\CAPTURE_MANIFEST.json`
- `delivery\SUMMARY.json`
- `delivery\REPORT.md`
- `DELIVERY_MANIFEST.json`
- `UPLOAD_READBACK.json`

Do not inspect any other path, search another root, enumerate a directory, or follow an alias.

## 3. Process check — first operation

Run this exact PowerShell query once. It reads process metadata only and filters to Python processes whose command line names the parent task. Do not terminate or interact with any returned process.

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" |
  Where-Object {
    $_.CommandLine -and
    $_.CommandLine.Contains('BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1')
  } |
  Select-Object ProcessId, ParentProcessId, Name, CommandLine
```

If the query errors, preserve the literal error and stop; do not use another process-inspection method.

If one or more matching processes are returned:
- classify `ACTIVE_PROCESS_OBSERVED`;
- record the exact process rows;
- inspect only the root directory's existence and metadata if safe;
- do not read package, marker, log, manifest, or delivery files;
- stop and upload the status receipt.

If no matching process is returned, continue with the exact-path checks below. A process miss does not prove that R1 never ran.

## 4. Exact-path checks and package-pin measurement

For every exact path in §2, record `exists`, `length`, `LastWriteTimeUtc`, and file/directory type using literal `Test-Path -LiteralPath` and `Get-Item -LiteralPath`. Do not list directory contents.

If the three package files exist, compute their local byte counts and SHA256 using `Get-Item -LiteralPath` and `Get-FileHash -LiteralPath -Algorithm SHA256`. Compare them to the parent R1 task's expected pins:

| File | Expected bytes | Expected SHA256 |
|---|---:|---|
| capture_registered_layer_metadata_r1.py | 13128 | f40b762e97cefee39d6746fcf2c6f4d380ff537b0089a87071ba0825f8bf049c |
| test_capture_registered_layer_metadata_r1.py | 5564 | a205813cd4640dc02879eef2dffc6d65acd3d785d7ffe48bc8f8c74d2ad64cc4 |
| PACKAGE.json | 711 | 2c6fb962e3fae26bc1b44eb618b71d1c20ede4ebca8dfce258818adc5465142d |

Do not modify, replace, stage, rename, or delete any file.

If no matching process is active, read only these exact text receipts when present:
- `RUN_ONCE.json`
- `TESTS_RUN.json`
- `TESTS.stdout.txt`
- `TESTS.stderr.txt`
- `PREFLIGHT_RUN.json`
- `PREFLIGHT.stdout.txt`
- `PREFLIGHT.stderr.txt`
- `OUTER_RUN.json`
- `CAPTURE.stdout.txt`
- `CAPTURE.stderr.txt`
- `delivery\CAPTURE_MANIFEST.json`
- `delivery\SUMMARY.json`
- `delivery\REPORT.md`
- `DELIVERY_MANIFEST.json`
- `UPLOAD_READBACK.json`

Preserve the literal contents and literal exit values. Do not infer that a pin mismatch was actually encountered by the executor unless a native command receipt proves that check ran and stopped. Do not infer capture completion from file presence alone.

## 5. Required status classification

Use only the first applicable classification, and explain its evidence:

1. `ACTIVE_PROCESS_OBSERVED` — matching parent-task Python process exists. Stop without reading files.
2. `CAPTURE_ATTEMPTED_OR_COMPLETED` — an OUTER_RUN receipt proves the capture command ran; report its exact exit and manifest/readback state.
3. `NATIVE_PIN_STOP_CONFIRMED` — a native receipt proves the parent R1 pin check ran and stopped on the mismatch.
4. `PACKAGE_PIN_MISMATCH_PRESENT_EXECUTION_UNPROVEN` — local staged bytes mismatch the parent task pins, but no native receipt proves the check ran.
5. `PARTIAL_SETUP_OR_ABORTED_STATE_UNKNOWN` — some exact task-root artifacts exist, but no receipt proves the execution stage.
6. `NOT_STARTED_OBSERVED_AT_CHECK` — the exact root and all exact artifacts are absent and no matching Python process is observed. Do not claim that R1 never ran at another location or earlier time.
7. `STATUS_QUERY_FAILED` — a required read-only status query failed; preserve its literal error.

Do not create a status that implies successful R1 completion unless the exact native receipts establish it.

## 6. Forbidden actions

- Do not run the parent R1 task, its tests, preflight, or capture script.
- Do not stage or recreate the parent R1 package.
- Do not fix its package pins, add tests, patch code, or create a replacement R1 package.
- Do not read Parquet, RAW/CLEAN/CACHE data, credentials, secrets, or secret-derived hashes.
- Do not call JQData, QMT, HTTP, or any supplier/API.
- Do not perform directory scans, globbing, recursive searches, alias searches, or unrelated process inspection.
- Do not write to E:, modify the parent task root, alter RUN_ONCE, or touch any existing source, seal, pointer, CURRENT, Cleaning, cache, or history.
- Do not touch the independent R4 diagnostic.
- No Cleaning, alignment, PIT transformation, Compiler, backtest, engine start, CURRENT switch, release, publication, money movement, or order.

## 7. Return contract

Create only these two new local receipt files in a fresh task-owned temporary directory on C::

- `STATUS.json`
- `REPORT.md`

Do not create or modify any parent R1 files. The receipt must contain:
- this task ID and parent task ID;
- host, workspace, UTC start/end, cwd, exact process-query command and literal result;
- every exact path checked and its metadata;
- local package byte counts/SHA256 when available;
- exact native receipt contents and exit values read under §4;
- the classification from §5 and its evidence;
- explicit statement that no parent R1 command was run and no process was stopped.

Do not include secrets or credential contents. Do not upload parent package copies.

Upload both receipts to:
`agents/chatgpt/inbox/BLACKBOX_POST_20261027_LAYER_RECONCILIATION_R1_STATUS_ONLY_20261115/ZHANGWEI/`

Read back both uploaded files and compare exact bytes and SHA256. Upload `UPLOAD_READBACK.json` last, read it back too, and verify its own bytes/SHA256 against the local copy. If any upload or readback fails, preserve the failure and report it; do not claim completion.

Do not end the Cursor chat until all required uploads and readbacks are complete. Then end the Cursor chat with exactly:

`END`

## 8. GPT review boundary

This status receipt only resolves whether the already-issued parent task is observed running, completed, stopped, partially staged, or unobserved at the exact location. It does not authorize a new metadata capture, supplier probe, data acquisition, Cleaning, source-absence conclusion, CURRENT switch, release, engine admission, or order.

The parent R1 remains immutable. Any future replacement package, if justified after this status is known, must be separately versioned and GPT-reviewed with exact source pins, duplicate-JSON-key rejection, focused positive Windows path-reference tests, meaningful offline checks, and a new bounded read-only task.

ORDER_ALLOWED=false.
