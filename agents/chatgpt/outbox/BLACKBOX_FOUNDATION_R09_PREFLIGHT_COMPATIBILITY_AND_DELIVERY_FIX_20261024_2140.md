# Complete R09: fix the import compatibility and deliver the original operating matrix

Task ID: BLACKBOX_FOUNDATION_R09_PREFLIGHT_COMPATIBILITY_AND_DELIVERY_FIX_20261024_2140
Executor: ZHANGWEI. Existing round R09/10; this is not R10. One planned execution round remains.
Parent task: BLACKBOX_FOUNDATION_R09_CONTROL_AND_ORDERED_ENTRY_20261024_2100.

The R09 upload has been received. The original ordered entry STOP is preserved and not accepted as passed. Implement the exact GPT correction below; complete the pending original deliverables in one additive bundle. Do not repeat the inventory, global search or large SW reads.

Read in full:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R09_PREFLIGHT_FIX_20261024_2140/REVIEW_R09_CORRECTION.md

## 1. Stage the pinned fix beside the existing R09 runtime

Fetch from agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R09_PREFLIGHT_FIX_20261024_2140/:

- fix_r09_preflight_tempdir.py
- test_r09_preflight_tempdir.py
- R09_TEMP_DIR_FIX_PACKAGE.json
- R09_TEMP_DIR_FIX_TEST_RESULTS.json (GPT-host evidence only)
- REVIEW_R09_CORRECTION.md

Stage new files under the existing path recorded in your receipt:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R09\control_2100\

Check every code byte against R09_TEMP_DIR_FIX_PACKAGE.json. The existing original runtime must remain SHA256 87ff01f31d4a77736f1a2eb3eb031c81a627923eb73c61e29c0035f93e128e60. Do not edit it, `_base.py`, any guard predicate, rule/manifest, source packet or successor file. If the source is actually at a different already recorded staging path, use that exact recorded path after checking the same hash; do not search or guess a replacement.

## 2. Execute these commands, preserving literal stdout, stderr and exit codes

Working directory: E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024
Runtime: .\runtime\.venv\Scripts\python.exe
Environment: PYTHONUTF8=1; PYTHONDONTWRITEBYTECODE=1.

First, the new 10-control test:

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R09\control_2100\test_r09_preflight_tempdir.py reviews\R09\control_2100\r09_control_runtime.py reviews\R08\BODY_EXPORT_20261024_2025

Only after PASS with controls_passed=10:

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R09\control_2100\fix_r09_preflight_tempdir.py --source reviews\R09\control_2100\r09_control_runtime.py

Expected new sibling:
reviews\R09\control_2100\r09_control_runtime_preflight_fixed.py
Expected SHA256: f52236648c37eb91944fd7e03e545f18ed887dc0e2c7ec12f2dcdeb6895d9d24

The fix seeds stdlib's temporary-directory cache using the already existing successor directory, without a write probe. All write/network denials remain unchanged. It introduces zero exceptions. Repeat the fix command once for ALREADY_FIXED_VERIFIED and prove the original runner plus all four successor hashes remain unchanged.

Then run the REAL corrected entry once:

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R09\control_2100\r09_control_runtime_preflight_fixed.py --packet reviews\R08\BODY_EXPORT_20261024_2025 --successor candidate\r09\control_successor

Expected successful scope: ORDERED_CANDIDATE_CHECK_COMPLETE with genuine preflight.ok=true, required BOOTSTRAP+DATA_ACCESS, all four executed steps, 959896/959896 selected keys and zero lost close observations, the two candidate stock rows and the 5242-row diagnostic index read, one synthetic parse, real-data role and live publication denied. This remains bounded candidate verification, not CURRENT service, full MASTER admission, or latest update acceptance.

Any new failure is a STOP for that branch with original output retained. Do not replace callbacks, remove guards, authorize a temp-write exception, inject ok=True, relabel a substituted step as executed, or rerun the previous substitution harness. Finish independent documentation from existing evidence even if the entry remains blocked. Do not invent extra repairs.

## 3. Complete section C and the missing delivery evidence from the original R09 task

The six-layer summary is retained as a summary. Deliver the requested OPERATING_FLOOR_MATRIX.json covering the actual catalog/product entity set, with per-row original evidence references. Reuse the R04-R08 registries and ledgers. Account for header/blank/comment rows separately so product count equals the distinct classified product IDs; do not guess the count or re-read business data.

Keep the original required per-row fields: supplier/JQ/non-JQ; RAW/Cleaning/PIT/cache/virtual/factor/strategy role; field/dictionary and semantic binding; true producer-consumer route; must-read and applicable lesson/ordered failure action; proven read scope; real versus shadow engine route and admission; downloader/callable, checkpoint/exclusion/watermark, credential LOCATOR and login method (no values or hashes); accessible/unproven/sealed permission; measured freshness; first unresolved gate. Unknown values stay explicit with the scope searched, not inferred missing data.

Also supply the original R10_DECISIVE_BINDINGS.json, R10_EXECUTION_PREREQUISITES.md and CORRECTIONS.json. Existing FOUR_UNRESOLVED_ITEMS_NARROWED.json may be referenced as input rather than regenerated. Apply all nine qualifications in the review, especially the adjustment sidecar versus acquisition-receipt distinction, 83,503-row discrepancy, bounded SW proof, and unmeasured writer search. Narrow these using existing evidence; no new full scan, supplier call, Parquet reread or ID/seal rewrite.

For engine dependencies, cite the actual already identified packaging/import requirement records and distinguish core from optional. Do not pip install or start the engine. If a decisive requirement body or the _base import body is not on HUB, export only these already identified text files as byte-exact ASCII/base64 carriers with paths, SHA and size. No secrets and no entire engine dump.

Complete GPT_CODE_EXECUTION.json: exact commands, executed file hashes, captured exits/stdout/stderr locations for the new commands, and retained historical R09 command evidence. Historical evidence not captured is NOT_RETAINED; do not reconstruct it as a literal. Correct the manifest's remote path mapping to include exact executed_code/ and tools/ prefixes. Do not rerun old failed/bypass commands merely to fill this ledger.

## 4. Additive upload and readback

New evidence folder:
agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R09/preflight_and_delivery_fix_2140/

Include the new code, local 10-control result, exact new command captures/exits, fixed-entry hash and full original entry stdout, original runner/successor conservation, the completed matrix/prerequisites/bindings/corrections, and a precise delivery manifest. Preserve all previous R09 files unchanged. Encode BOM/UTF16 command captures as base64 original bytes if needed; a transcription is separate evidence.

Read back and verify every new file and decoded carrier. Update INBOX_FOR_CHATGPT.md to the additive status and exact paths, preserving all predecessors and stating R09/10 correction with R10 remaining. It must distinguish FULL_ORDERED_ENTRY_PASS from STOP; neither status is whole-foundation acceptance.

Only new R09 staging/evidence/sibling writes and the specified HUB writes are authorized. Production data/scripts, RAW, CURRENT, seals, engine registration, credentials and historical evidence are unchanged. No download, supplier auth/probe, formal engine startup, orders or cleanup.

FOUNDATION_ACCEPTANCE=false
ORDER_ALLOWED=false
PRODUCTION_CHANGE_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
NEW_DATA_ACQUISITION_AUTHORIZED=false

After successful upload and complete readback, Cursor chat final response exactly:
END
