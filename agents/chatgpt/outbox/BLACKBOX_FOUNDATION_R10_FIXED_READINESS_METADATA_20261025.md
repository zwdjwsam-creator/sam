# R10 continuation: capture exact acquisition readiness metadata, without executing an updater
Task ID: BLACKBOX_FOUNDATION_R10_FIXED_READINESS_METADATA_20261025
execution_host=ZHANGWEI
workspace=E:\BLACKBOX
Continue the existing R10 recovery; do not start a new inventory or repeat accepted tests.

## Accepted bounded result
The connected candidate's 23 members plus manifest were independently verified, 24/24. Literal 11-test command and genuine CACHE preflight passed. The guide append preserved the original prefix. This is synthetic candidate verification only.
Read agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R10_FIXED_READINESS_METADATA_20261025/REVIEW.md.
Carry forward its receipt wording correction: refresh assembly RETAINS non-dirty rows; the prior receipt incorrectly says it drops them. Add a correction to the new receipt, leaving prior files untouched.

## Why these exact files
R06 NEXT_UPDATE_BINDINGS and R08 ENGINE_RUNTIME_AND_UPDATE_READINESS refer to the current pipeline, incremental rule and RAW ledger, but full original JSON bodies are not available under those filenames on HUB. The legacy downloader source identifies latest_checkpoint.json. A checkpoint must be inspected and bound to its actual writer before using it; its name or old COMPLETED flag does not establish a valid daily cursor.
The legacy jq_download_execution_r1.py is guarded before its imports. Do not run/import/help/resume it or remove the guard. Do not invoke run_blackbox_daily_incremental_data_plane_r1.py even in status mode: that path writes current/archive state.
This task makes no missing-data determination or acquisition authorization.

## Stage and execute only the supplied metadata capture
Stage the four supplied package files, PACKAGE.json first, at:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R10\fixed_readiness_metadata\
Verify every declared length/SHA256. No source/test/manifest edits, replacement helpers or re-pinning.
Use existing recovery interpreter, cwd E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024,
PYTHONUTF8=1 and PYTHONDONTWRITEBYTECODE=1.
Read current AGENTS and applicable CACHE must-read contracts; run the existing genuine pinned operating-entry CACHE preflight with external raw stdout/stderr/exit captures. Failure stops dependent work.
Then run once:
.\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\fixed_readiness_metadata\test_capture_readiness_metadata.py
Expected 8 tests, passed=true, exit 0. Failure stops; preserve output and do not edit or retry.
Only after PASS run once:
.\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\fixed_readiness_metadata\capture_readiness_metadata.py

Keep command captures in E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\r10_readiness_metadata_command_captures\ until the script has created its delivery. Do not pre-create r10_readiness_metadata_delivery for capture/staging; the script alone creates it.

The script's complete input allowlist:
- E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\_checkpoint\latest_checkpoint.json
- E:\BLACKBOX\运行\BLACKBOX_FULL_DATA_PIPELINE_MATRIX_CURRENT.json
- E:\BLACKBOX\运行\BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json
- E:\BLACKBOX\运行\BLACKBOX_RAW_COVERAGE_LEDGER_CURRENT.json

It reads JSON metadata only, never parquet or credentials. It refuses direct symlinks, oversized/non-container/invalid/duplicate JSON, obvious potential credential content and observed input drift. Potential-secret rejection emits no original content or input digest. No path inside a JSON file is opened.
Do not broaden the allowlist if one path is absent/refused. An absent metadata path is not source absence.
Output:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\r10_readiness_metadata_delivery\
Existing destination causes a refusal before reads/writes; do not delete it or change the destination. If it already contains a prior execution of this exact task, report it without restarting.
Exit 0 means four metadata copies captured, NOT readiness. Exit 3 means bounded capture incomplete; deliver the existing receipt and exact statuses without searching or filling. Unexpected exit: preserve captures and report exact failure, with no fabricated success.

## Return contract
Upload supplied package, raw preflight/test/capture stdout/stderr and literal exits, pre-execution pins, exported original JSON files permitted by the script, CAPTURE_RECEIPT.json and an English receipt with the correction above.
Do not create new business policy, derive target/universe/lag, call a supplier or promote a checkpoint. Do not read credentials, upload passwords/tokens/cookies or secret-derived hashes. Do not run original writers, merge data, patch production, construct an engine, switch CURRENT or place orders.
Reuse the existing R04-R10 registered layer search, field dictionary, namespace, entitlement and exclusion evidence; do not rescan them.
HUB return:
agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/fixed_readiness_metadata/
Create one self-excluded delivery manifest and a separate final byte readback. Upload and remotely read back EVERY member, manifest and final receipt before ending. Preserve failed outcomes. Update INBOX_FOR_CHATGPT.md preserving prior content. Do not duplicate a running process or re-upload previously accepted deliveries.
FOUNDATION_ACCEPTANCE=false
FORMAL_ENGINE_ADMISSION=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
SOURCE_ABSENCE_CLAIM_ALLOWED=false
Cursor final response, only after complete upload/readback, exactly END.
