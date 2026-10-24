# R10: activate the verified local operating entry and measure the engine boundary

Task ID: BLACKBOX_FOUNDATION_R10_OPERATING_ENTRY_AND_FINAL_SCOPE_20261024_2230
Executor: ZHANGWEI. Round: R10/10, the final planned execution delivery in this budget.
Parent: R09 correction; do not restart its inventory.

Read the entire review:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R10_OPERATING_ENTRY_20261024_2230/REVIEW_R09_AND_R10_SCOPE.md

GPT accepts the corrected R09 entry as a bounded candidate verification, and the reviewed additive Windows controls as supplemental evidence. The supplied test failure remains recorded. Future locally invented harnesses, gate substitutions and business-code repairs are not authorized. R10 must produce a usable supported entry and an accurate final scope, not a forced full-system PASS.

## 1. Stage the exact implementation and existing metadata inputs

From agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R10_OPERATING_ENTRY_20261024_2230/ stage:

- blackbox_operate_r10.py
- engine_import_probe_r10.py
- test_blackbox_operate_r10.py
- R10_INPUT_SPEC.json
- R10_IMPLEMENTATION_PACKAGE.json
- R10_OFFLINE_TEST_RESULTS.json (review-host result only)
- BLACKBOX_LOCAL_OPERATIONS_R10.md
- REVIEW_R09_AND_R10_SCOPE.md

Destination:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R10\operating_entry\

Verify code bytes/SHA against the package. Copy the four existing LOCAL metadata originals listed in R10_INPUT_SPEC.json into this same folder with the specified file names. This copies small JSON evidence only, not business data. If a local original is unavailable, fetch its exact already-uploaded HUB source path from the spec. Do not regenerate, edit or scan to replace an input. The entry checks canonical JSON SHA256 and duplicate keys; all key/value content must match the reviewed evidence. Original metadata files remain unchanged.

Use the established recovery venv with -X utf8, PYTHONDONTWRITEBYTECODE=1 and PYTHONUTF8=1. Keep the existing R09 runner, fixed sibling and four successor modules unchanged. Preserve their exact pinned hashes.

Working directory for all commands:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024

## 2. Run the supplied controls, then the supported entry

First:

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\test_blackbox_operate_r10.py

Required: PASS, controls_passed=24. Capture literal stdout, stderr and exit code. On failure, STOP the dependent execution; report the exact failure without editing tests, writing an alternate harness, relaxing assertions or changing inputs. Independent evidence-only final reporting may continue.

Only after PASS run these exact commands, retaining separate captures/exits:

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py catalog

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py describe --product INDEX_DAILY_R1

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py update-plan --product STOCK_DAILY_RAW_PIT_R1

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py query --product STOCK_DAILY_RAW_PIT_R1 --codes 000001.XSHE --start 2026-08-28 --end 2026-09-02 --fields open,high,low,close,volume,money

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py query --product STOCK_DAILY_RAW_PIT_R1 --codes 000001.XSHE --start 2025-09-22 --end 2025-09-24 --fields close

The first query exercises the explicit candidate override, the second the pinned inherited-year branch. Each must execute the REAL must-read child and produce exact session/code/field evidence. No data is filled, no source version is silently rebound, and no RAW fallback is permitted. Catalogue output should have 41 entities and 13 explicit updater joins; missing joins remain UNBOUND_IN_THIS_EVIDENCE_JOIN.

Then these two negative desktop checks; expected exit 3 is SUCCESSFUL REJECTION, not a reason to retry or repair:

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py query --product STOCK_DAILY_RAW_PIT_R1 --codes 000001.XSHE --start 2026-10-23 --end 2026-10-23 --fields close

Expected: REQUEST_OUTSIDE_PINNED_CALENDAR, SOURCE_ABSENCE_CLAIM_ALLOWED=false. The old calendar cannot silently claim a latest update.

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py query --product ETF_DAILY_PIT_R1 --codes 510300.XSHG --start 2026-08-31 --end 2026-09-01 --fields close

Expected: PRODUCT_READER_NOT_ACTIVATED; no fallback. Do not make an absence claim or widen a request to bypass this result.

## 3. Measure original engine import, once

After the controls PASS, execute once:

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\engine_import_probe_r10.py --desktop-import

The child imports the original package layout, verifies the original engine/API/provider-base hashes and loaded paths, and blocks writes, network, secrets-file access, auth/data/order calls and engine construction. No strategy, live process or account is started. Credentials/config paths are not printed and exceptions are reported by type/location, not raw messages.

A MODULES_IMPORTED_NO_ENGINE_CONSTRUCTED outcome proves import readiness only. IMPORT_NOT_READY, forbidden side effects or timeout identify a specific boundary; retain it. Do not install packages, modify imports, authorize a secret read, substitute a provider or remove a guard to manufacture success. No engine object or provider is registered by this task. A source-pin mismatch stops this branch.

## 4. Make the reviewed entry discoverable without replacing rules

Copy the supplied guide, byte-identical, to the existing workspace operations area:
E:\BLACKBOX\_OPS\CURSOR_WORKSPACE\BLACKBOX_LOCAL_OPERATIONS_R10.md

Read the existing root E:\BLACKBOX\AGENTS.md in full. Preserve a byte-exact backup in this R10 evidence scope, record its original hash/encoding, and append ONLY the following block if its marker is absent and the file is ordinary UTF-8 text. Preserve every existing line. If encoding/file identity is unsupported, leave it unchanged and report that specific block; do not invent a conversion or modify another index.

    ## R10 reviewed local operating entry
    Read `_OPS/CURSOR_WORKSPACE/BLACKBOX_LOCAL_OPERATIONS_R10.md` for the supported diagnostic entry.
    Existing mandatory contracts and task-class preflight remain applicable. This pointer grants no acquisition, publication, formal engine admission or order permission.

Verify the guide exists with the source SHA and the exact pointer is readable from the E workspace. Do not modify .cursor alwaysApply rules, production scripts, secrets, business data or the engine to install this documentation pointer. This is an additive entry link, not a new rule hierarchy.

## 5. One consolidated final delivery with honest scope

Upload English artifacts to agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/:

- Exact executed code and input-spec/package; reference prior HUB inputs rather than uploading unchanged source JSON again.
- Literal controls and every command stdout/stderr/exit, raw-byte base64 carriers where needed; no reconstructed historical captures.
- Operating catalog output and exact successful read receipts, both expected rejection receipts, engine import result, and guide/pointer readback with original AGENTS backup hash.
- FINAL_REQUIREMENT_MATRIX.json for the USER'S FIVE requirements: data ecology/dictionary/rules/lessons; engine/data contract and actual runtime; strategy artifact identification; download/incremental rules and access resources; actual desktop running/latest-update completion. For each: measured supported scope, unproven/failed predicate, exact evidence and what concrete repair is still required. Use existing records; no broad rescan.
- FINAL_BLOCKERS.json: preserve adjustment lineage/83503-row conflict, universe/tradeability owner/coverage, required empty view members, product-specific current gaps, genuine engine admission and full incremental/publication readiness if still unresolved. Do not call them missing source data without the required registered-layer search proof. Existing raw presence and no migration-loss finding remain separate.
- R10_STATUS.json separating SUPPORTED_OPERATING_ENTRY, ENGINE_IMPORT, FORMAL_ENGINE_ADMISSION, LATEST_FULL_UPDATE, and FULL_GOAL_MET. Whole-foundation acceptance cannot come from the CLI's fixed flags, a row count, an import, a synthetic fixture or one successful query. If material predicates remain unmet, state FULL_GOAL_MET=false explicitly and retain the useful supported entry. The ten-round budget is not evidence of success.

Every new file must have exact repo path, byte hash and readback proof. A manifest must not recursively include a stale hash of itself; exclude itself from its own content list and record its final hash in the separate readback receipt. Preserve earlier R09 and correction files. Update INBOX_FOR_CHATGPT.md to the actual R10 result and zero planned rounds remaining; do not start a self-created R11 or additional scanner.

No new supplier auth/download, CURRENT change, sealed-source edit, formal engine/backtest run, order, cleanup or migration is authorized. Exact new R10 staging/evidence/guide/pointer operations above are authorized. The update-plan operation is deliberately non-executing because the full acquisition-to-publication prerequisites are not yet proven.

After upload and complete readback, Cursor final chat exactly:
END
