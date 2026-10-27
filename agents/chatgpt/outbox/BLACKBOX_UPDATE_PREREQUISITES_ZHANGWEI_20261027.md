# ZHANGWEI: execution-bound cleaning/compiler and retained receipt handoff

task_id: BLACKBOX_UPDATE_PREREQUISITES_ZHANGWEI_20261027
parent_task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
dispatch_id: BLACKBOX_UPDATE_PREREQUISITES_20261027
execution_host: ZHANGWEI
workspace: E:\BLACKBOX
preserved_engines: E:\BLACKBOX_ENGINES
status: READY_FOR_ACK_READ_ONLY_EVIDENCE_CAPTURE
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false

## Purpose

Finish the already-outstanding execution-bound handoff, together with the evidence needed for a scoped update. This is not another v3 deployment or full-chain verification. Exact v3 source already exists in HUB; return its current identity and reuse it when matching.

## ZHANGWEI-specific collection

Run:
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 "C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027\package\collect_prerequisites.py" --role ZHANGWEI --out "C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027\ZHANGWEI\capture_001"

Logs/command ledger belong under the ZHANGWEI parent above, outside capture_001.

CAPTURE_PLAN.json names 24 exact files. Important current bodies:
- E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\tools\run_connected_pipeline.py
- The same tools\run_original_compiler_candidate.py
- The same candidate\run_r15_cleaning_replay.py
- The same candidate\run_publish_atomic_rehearsal.py
- E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\cache_compiler_daily_incremental_r1.py
- The same compiler directory's cache_compiler_tip_rebase_from_current_r1.py

The collector reads candidate\cc_commit\COMMIT.json and captures only its referenced CHECKPOINT plus RELEASE/SEAL/MANIFEST under its declared release_root, confined to the authorized recovery candidate tree. It does not select a newest directory. Escaping/missing/unreadable references remain BLOCKED/UNKNOWN. No source data is traversed and no Parquet is read by this task.

It also collects retained R15 source/manifest receipts and the existing R15_CLEANING_REPLAY.json. Reuse matching HUB bodies rather than re-uploading R15 originals. Current source hashes are not a claim about which code an earlier process executed.

## ZHANGWEI-specific return summaries

1. EXECUTION_BINDINGS.json: current runner/compiler/cleaning module identities; declared candidate root and exact referenced metadata; the already-retained command/import/exit mapping for prior successful runs if available. Missing historical invocation evidence remains UNKNOWN; no rerun.
2. CLEANING_TRANSFORM_BINDING.json: identify original load_staging, ingest_item, seal_release callsites in the current wrapper and cite retained real replay receipts. Record staging selectors, source-to-clean_rel mapping, byte placement versus actual value transforms, exclusions, align/PIT handling, and every potentially writable production/control/archive destination visible in these exact bodies. Do not import/execute original main to inspect it.
3. FACTOR_SPLICE_EVIDENCE.json: cite existing source/candidate factor-basis and date-axis results, exact related source functions and observed unresolved semantics. Do not conclude factor=1 is automatically wrong, relabel ordinal dates, fill factors, or choose an overlap request. If adjustment admission is unresolved, state which dependent products it affects, separately from RAW_NONE acquisition.
4. PREREQUISITE_DELTA.json: for each actual acquisition/cleaning predicate, give supporting receipt refs or exact remaining gaps. Do not make V4, a not-yet-authorized latest download, production CURRENT switching, or a generic v3 implementation a universal prerequisite.

Return root:
agents/chatgpt/inbox/BLACKBOX_UPDATE_PREREQUISITES_20261027/ZHANGWEI/

## Execution boundary

This is a child handoff of BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025, requested by the owner on 2026-10-27. It consolidates the existing missing-evidence handoff; it does not start a competing repair pipeline. If the same child task is already ACKed/running/completed, report its existing PID/receipt and do not launch it again. Do not stop any other running process.

Allowed: read the named local text/JSON/source files, perform the explicitly bounded SAM task lookup, parse Python as AST without importing it, and create a new evidence directory under C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027. Upload evidence to the specified HUB return folder. No writes to E:\BLACKBOX or E:\BLACKBOX_ENGINES.

Not authorized: supplier login/call/quota probe, new market-data download, production or candidate cleaning/compiler execution, commit/emit/rebind, production CURRENT or rule changes, strategy execution, global inventory, full-library hashes, deletion, rollback, formatting, trading or orders. ORDER_ALLOWED=false. Do not invoke scope_refresh, research_os status, the data-plane default/VERIFY_ONLY, original R15 main, or the attachment's unreviewed comparison script.

Existing credential locators may be checked for presence only by this collector. Never read, copy, upload or hash credential contents. Current quota and supplier availability stay NOT_MEASURED here.

## Package and commands

Reviewed package: agents/chatgpt/reviews/BLACKBOX_UPDATE_PREREQUISITES_20261027/.
Stage PACKAGE.json and its nine payloads, unchanged, under:
C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027\package\

Verify every payload byte length/SHA256 against PACKAGE.json before execution. Read relevant local instructions as text; do not run legacy status/preflight wrappers merely to obtain an unrelated green result. The collection tool imports only Python standard-library modules, never business code.

Create the host's receipt/log parent directory below; do NOT pre-create capture_001. Use the existing E:\BLACKBOX\.venv\Scripts\python.exe. If it cannot launch, retain the literal failure as NOT_RUN; do not rebuild environments or silently substitute an interpreter.

Run the supplied 17 fixture controls once on this host:
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 -m unittest discover -s "C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027\package" -p test_collect_prerequisites.py -v

Retain exact argv, cwd, executable, hostname, start/end, stdout, stderr and actual process exit code. Do not derive an exit code from a later JSON artifact. Tests use disposable fixtures, not real source data. A failed test stops collection; upload the failure without changing tests or code.

Then execute the role-specific collector command below once. Preserve its original exit:
- 0: named capture completed within declared scope; NOT foundation/acquisition acceptance.
- 2: unresolved file/read/search-boundary/drift evidence; preserve and upload partial results, do not repair or rerun.
- 3: wrong host/output boundary; do not collect; return NOT_RUN.
- Any other nonzero/launch failure: preserve stdout/stderr and already-created outputs; no automatic retry.

The tool refuses existing output directories. Never delete an old directory to make the command run.

## Evidence accounting and completion

KNOWN_HUB_BODIES.json maps pinned content hashes to existing originals, including ZIP members. A byte-identical local body is returned as REUSED_HUB_BODY with its source path/size/hash; do not upload another duplicate. A changed or new body is copied to capture_001/bodies with original bytes and a readback receipt. Missing exact paths and search limits are evidence gaps, not source-absence or data-loss conclusions. A release reference alone does not prove which process generated it.

Upload to the host-specific HUB return folder:
- ACK.json before execution, identifying child/parent task, host and whether a collector is already active.
- COMMAND_LEDGER.json plus literal test/collector stdout and stderr.
- capture_001/COLLECTION.json, DELIVERY_MANIFEST.json, LOCAL_READBACK.json and only new/changed bodies.
- The role-specific evidence summaries below. These may cite existing pinned JSON/body receipts; do not regenerate old market-data measurements.
- REPORT.md stating completed/blocked/unknown facts, actual exits, retained evidence references and remaining exact missing inputs.
- UPLOAD_READBACK.json with byte/size/SHA256 and remote git blob comparison for every uploaded payload.

Read back EVERY uploaded file, including the final manifest and readback receipt, and compare with intended bytes before ending. The readback receipt need not contain its own self-hash; verify that receipt after upload without rewriting it recursively. Local/remote verification failures remain failures. All new HUB prose must be English, with original identifiers/paths preserved. Final Cursor chat message must be exactly END.

## Following stages owned by GPT

GPT will reconcile both returns, bind candidate acquisition scopes per product, and author/test any necessary precise repair or receipt-producing acquisition code. Only then will GPT publish a separate executable Stage 2 scoped acquisition task. No universal September 25 start, September 24 re-download, supplier lag, adjusted factor, PIT timestamp or exclusion policy is delegated to local AI.

Old missing request receipts can remain UNKNOWN; new per-unit request/key/page/exhaustion receipts will prove future acquisition forward. Requested/returned counts alone are insufficient. Original R15 functions having run on two retained units is useful bounded evidence, not proof of all transformations or supplier completeness.

Factor-basis uncertainty blocks dependent adjusted-price uses; it does not automatically block an independently specified RAW_NONE scope. All 40 unbound rows need not be solved before an independent first scope is considered. V4 reconstruction, a latest download not yet performed, and production CURRENT switching are not circular prerequisites. Do not certify broken v3 booleans; a generic v3 tool is not the user's goal.

The final GPT handoff will contain per-product cursor decisions, exact acquisition contract/code/tests, and after authorized execution the raw/cleaned conservation and provenance receipts. Task publication is not an ACK or execution.

