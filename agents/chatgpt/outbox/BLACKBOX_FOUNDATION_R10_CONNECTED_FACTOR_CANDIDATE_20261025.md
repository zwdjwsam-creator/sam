# R10 continuation: connect the validated response gate to history-preserving candidate assembly
Executor: ZHANGWEI only. Continue R10; no acquisition, production switch or foundation acceptance.
Package: agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R10_CONNECTED_FACTOR_CANDIDATE_20261025/

## Prior delivery accepted within its actual scope
GPT independently verified all 18 factor_response_gate delivery members plus the original-byte manifest against its remotely readable FINAL_BYTE_READBACK.json: 19/19 agree. Raw stdout reports tests_run=20, passed=true, exit 0; genuine CACHE preflight passed. Supplied source and fixture identities agree. The test-only DeprecationWarning is retained; no rerun or test edit is required for it.
Do not rerun those 20 controls, earlier AST tests, source searches, parquet/schema checks, annual comparisons, catalog inventory or upload cycles.

## What is newly connected
r10_factor_candidate_pipeline.py actually calls:
1. assemble_responses from the accepted response gate;
2. validate prior-overlap/date boundaries;
3. validate dirty-code refresh keys and values on the requested day;
4. assemble_candidate from the existing refresh assembly, which calls candidate_merge;
5. return the candidate with publication/engine/acquisition/CURRENT/order authority false.

There is no publisher API in this component. The last stage is an intentional no-publication boundary, not execution or certification of the production publish gate.
The new dirty-day consistency check rejects a full-refresh tip that disagrees with the validated day's reply before it can replace that reply.
Prior overlap must strictly precede the requested day; duplicate-day precedence is not guessed.
Historical source authority, actual expected market universe and cross-source factor-basis authority remain external prerequisites, not proved by this chain.

GPT's 11 new integration controls passed. Successful tests call the actual staged candidate modules, including the real candidate_merge. Failure-order controls check that bad dates, missing securities or fq mismatch prevent downstream merge invocation. Dirty-history regression and missing expected keys are rejected by the existing merge. No legacy updater, actual data, SDK or publisher is run.
Do not describe a synthetic success as a repaired real-data source or a formally admitted engine.

## 1. Stage the exact package
Destination:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R10\connected_factor_candidate\
Stage all eight files, including PIPELINE_PACKAGE.json first:
r10_factor_candidate_pipeline.py
test_r10_factor_candidate_pipeline.py
r10_factor_response_gate.py
r10_factor_input_contract.py
r10_factor_refresh_assembly.py
r10_factor_candidate_merge.py
PIPELINE_OFFLINE_RECEIPT.json
PIPELINE_PACKAGE.json

Verify every declared byte count and SHA256 before execution. Existing pure response/input/refresh/merge modules are reused byte-identically, not rewritten local substitutes. Preserve BOM/line endings exactly. No re-pinning, test editing, alternate harness or production installation.

Read current AGENTS and applicable must-read contracts. Use the existing recovery venv,
cwd E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024,
PYTHONUTF8=1, PYTHONDONTWRITEBYTECODE=1.
First run the existing genuine pinned operating-entry CACHE preflight (describe --product ADJUST_FACTOR_PIT_R1), with literal stdout/stderr/exit capture; failure stops dependent work.

## 2. Execute one connected candidate check
After successful preflight, run exactly once with external captures from the start:
.\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\connected_factor_candidate\test_r10_factor_candidate_pipeline.py
Expected tests_run=11, passed=true, exit 0.
These are new connected-flow checks; do not re-execute the previous standalone 20-test suite.
On failure, retain the actual output and stop dependent work without changing tests/source or retrying solely for capture.

The execution scope is entirely synthetic/in-memory. Do not supply the malformed RAW files, manufacture request bindings for them, derive dates from filenames, assert fq=pre for a None request, fill factors or run a real-data merge.

## 3. Make the candidate diagnostic discoverable, within recovery only
Only after the 11 checks pass, append a short diagnostic-only section to the existing recovery guide:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R10\operating_entry\BLACKBOX_LOCAL_OPERATIONS_R10.md

Keep its existing content intact and save the prior bytes in the new delivery. The section must include:
- the exact 11-check command above;
- the actual function chain response_gate -> refresh_assembly -> candidate_merge;
- the five stage names returned by candidate_pipeline;
- "Synthetic diagnostic only; no real-data authority, publication or formal engine admission";
- the unchanged global acquisition prohibition.
This only documents an installed candidate diagnostic in the recovery workspace. Do not patch the pinned blackbox_operate_r10.py, normative contracts, root must-read files, live updater or historical originals. If the exact existing guide is unavailable, report that separately without searching for a replacement or inventing an install success.
Return before/after bytes/hashes and append-only diff as installation evidence. No new inventory or repeated checks.

## Delivery
English append-only receipt, all supplied files, pre-execution package verification, raw genuine preflight and 11-check captures, actual commands/exits, guide before/after/diff and measured scope.
State separately:
- standalone source response gate: prior 20-control result reused;
- connected response/refresh/merge candidate: actual new 11-control result;
- production writer, real-data source authority, actual publish gate and formal engine: not exercised or admitted.
Carry forward B1..B7's existing unresolved status without rerunning their inventories. Do not declare wholesale closure.

Local:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\r10_connected_factor_candidate_delivery\
HUB:
agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/connected_factor_candidate/
One self-excluded manifest, separate final byte readback, and upload/readback of the final receipt itself. Update agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md preserving prior content.
No business-data write, historical source repair, supplier call, new download, refetch, production patch, CURRENT change, engine construction or order.
FOUNDATION_ACCEPTANCE=false
FORMAL_ENGINE_ADMISSION=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
SOURCE_ABSENCE_CLAIM_ALLOWED=false
After full upload/readback, Cursor final response exactly END.
