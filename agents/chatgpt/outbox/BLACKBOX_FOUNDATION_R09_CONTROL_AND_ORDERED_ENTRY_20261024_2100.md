# R09: implement and exercise the source-pinned control entry

Task ID: BLACKBOX_FOUNDATION_R09_CONTROL_AND_ORDERED_ENTRY_20261024_2100
Executor: ZHANGWEI
Parent: R08 exact_original_bodies_2025, verified 23/23 by GPT.
Round: R09/10. One planned execution delivery remains after this round: R10.

R08 body delivery is accepted as a delivery, not as foundation acceptance. Begin this concrete implementation task; do not rebuild R08 inventories or wait for another HUB acceptance message between its independent sections.

Read the complete review first:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R09_CONTROL_INTEGRATION_20261024_2100/REVIEW_R08_TO_R09.md

## A. Stage exact GPT code and run controls

Source package:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R09_CONTROL_INTEGRATION_20261024_2100/

Stage its following files, unedited, in:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R09\control_integration\

- build_r09_control_successor.py
- r09_control_runtime.py
- test_r09_controls.py
- canonical_index_schema_r1.py
- r08_coverage_gate.py
- R09_IMPLEMENTATION_PACKAGE.json
- R09_OFFLINE_TEST_RESULTS.json (review-host evidence, do not substitute for local results)
- REVIEW_R08_TO_R09.md

Verify bytes/SHA against R09_IMPLEMENTATION_PACKAGE.json before execution. Do not change patches, pins, filenames, thresholds, assertions or input files. The reused adapter and gate are candidate helpers, not production installations.

Use the existing recovery runtime, never E:\BLACKBOX\.venv. Working directory:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024

Set PYTHONDONTWRITEBYTECODE=1 and PYTHONUTF8=1 for these commands. The existing exact source packet is:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R08\BODY_EXPORT_20261024_2025

Run once, capturing literal stdout, stderr and exit code:

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R09\control_integration\test_r09_controls.py reviews\R08\BODY_EXPORT_20261024_2025

Required local result: status=PASS, controls_passed=38. These are offline controls, including synthetic Parquet reads. They do not certify the desktop data.

Only after that PASS run:

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R09\control_integration\build_r09_control_successor.py --packet reviews\R08\BODY_EXPORT_20261024_2025

The builder creates only:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\candidate\r09\control_successor

Compare all four output hashes against expected_successor_outputs in the package. Repeat the same builder command once for ALREADY_BUILT_VERIFIED; do not modify or delete an existing partial tree. Generated successor files must never be copied over production originals.

## B. Execute the connected real-data candidate entry

Only after A passes:

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R09\control_integration\r09_control_runtime.py --packet reviews\R08\BODY_EXPORT_20261024_2025 --successor candidate\r09\control_successor

The fixed entry enforces: must-read -> source/rule/generation binding -> bounded candidate reads -> shadow/publisher block controls. Its selected data already exists in the R08 manifest; no builder, cache rewrite, re-hash of the whole migration, global traversal or supplier operation is requested.

Required evidence is the literal outcome of all four stages, not merely 'files exist' or a hand-written PASS. Expected successful scope is ORDERED_CANDIDATE_CHECK_COMPLETE, with the two recovered stock rows, preserved candidate key/close observations, the 5,242-row canonical adapter read, one synthetic parse, the real role denied and live publication denied. FOUNDATION_ACCEPTANCE and formal_backtest_active remain false.

If preflight/_base, source pins, guarded side effects, schema, identity or artifact checks fail: preserve the exact failure and STOP this dependent branch. Never remove a guard, change expectations, retry a download, edit a source, invent an admission fact or substitute a different path. Complete independent section C from existing evidence. Report the narrow failing dependency, not 'the data is absent'.

## C. Return the operating-floor matrix and final-round inputs

Reuse the existing R04-R08 ledgers, semantic map, ROOT_SEMANTIC_ROLE_MAP, exact bodies and R09 outcomes. No new broad scan or rewritten directory catalogue. Keep any referenced directory overview at depth <=4 and category level only.

Deliver OPERATING_FLOOR_MATRIX.json with one row per existing catalog product/domain. Preserve evidence references instead of re-reading every file. Each row must distinguish:

- supplier/ecology: JQ, non-JQ, derived, virtual-view or unresolved;
- physical RAW, Cleaning/PIT, cache and reader identities; field/dictionary/semantic binding; materialized versus virtual union;
- exact currently proven request scope and observation state, separately from full-history completeness;
- applicable mandatory rule/lesson IDs and the ordered producer -> consumer path, including the exact wrong-step rejection action;
- actual engine route and admission scope (diagnostic, synthetic shadow, or formally admitted); old strategy reconstruction is excluded;
- incremental downloader/callable, existing checkpoint/exclusion receipt and watermark rule, local credential locator and login method, accessible versus unproven versus sealed-permission resource;
- last measured freshness and the first unresolved gate that prevents a truthful current update/publication claim.

Use UNKNOWN/UNPROVEN with precise evidence when applicable. Do not create missing-data or migration-loss claims from a zero-row consumer. Do not collapse permission availability, successful authentication, acquisition completeness and formal usability into one boolean. Never read/upload secret values, tokens, login cookies or secret-derived hashes. Do not authenticate or probe any supplier in this task.

For the four unresolved domains in R09_IMPLEMENTATION_BINDINGS_CORRECTED.json, provide R10_DECISIVE_BINDINGS.json. Reuse the cached inventories/search ledgers first. Universe/tradeability: identify the current consumer's actual registered producer or explicitly state UNBOUND_PRODUCER with the searched records. Adjustment: locate an existing acquisition/refresh receipt or leave RECEIPT_NOT_RETAINED; never infer one from mtime or an all-ones series. SW L2/L3: start from TIP_COMPILER.inject_sw's exact current upstream pointer references rather than the withdrawn flat-string-only search. A source path and its snapshot are not interchangeable.

Only when an exact, already identified and decisive referenced body is not yet on HUB, read that specific file and upload its full original bytes as an ASCII/base64 carrier with path, SHA and size. Cap this supplement at 12 text bodies and 1 MiB total; if more is required, name the exact unfulfilled dependency rather than selecting arbitrary subsets. No entire engine dump, Parquet upload, recursive content scan or locally designed fix.

List the original engine's runtime package requirements and missing imports from the existing dependency matrix and actual pyproject/requirements record. Do not pip install, start a strategy, register a provider factory, connect an SDK fallback, or invoke an order path. An architecture fixture or leaf API harness remains separate from full engine startup.

Write R10_EXECUTION_PREREQUISITES.md: one short sequence to run the supported local read floor; the exact remaining steps needed for incremental RAW -> Cleaning -> cache -> admission/publication; which requirements already pass and which lack evidence. Retain the R22 seal's generation scope, the fixed minute sequence only where applicable, Tushare phase/namespace/watermark rules, and documented DEGRADED lane allowances. Do not invent new business policy. The actual code review and remaining fixes belong to GPT.

## Delivery and boundaries

Upload one consolidated English result bundle to:
agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R09/

Required: ROUND_STATUS.json, GPT_CODE_EXECUTION.json (file hashes, exact commands and exits), local fixture result, literal command captures, SUCCESSOR_BUILD_MANIFEST.json, ORDERED_ENTRY_RESULT.json, OPERATING_FLOOR_MATRIX.json, R10_DECISIVE_BINDINGS.json, R10_EXECUTION_PREREQUISITES.md, and an append-only CORRECTIONS.json covering the review's withdrawn inferences. A failed command must retain its failed outcome; do not replace it with a success summary. Small JSON/checkpoint evidence may be referenced from prior HUB paths rather than copied.

Read back every newly uploaded file and compare its bytes/hash. For original-body carriers verify decoded original bytes as well. Update INBOX_FOR_CHATGPT.md with exact paths, measured status, R09/10 and one remaining planned delivery, preserving predecessors. Do not create an unrelated task loop or self-imposed WAIT_HUB_ACCEPTANCE during this task.

Authorized writes: only this R09 staging/candidate/evidence scope and the specified HUB bundle/pointer. Existing production scripts, business data, RAW, CURRENT, seals, run states, credentials and historical evidence are unchanged. No supplier calls/downloads; no formal engine startup; no trading/orders; no cleanup, rename or deletion.

FOUNDATION_ACCEPTANCE=false
ORDER_ALLOWED=false
PRODUCTION_CHANGE_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
NEW_DATA_ACQUISITION_AUTHORIZED=false

After upload and complete readback, the Cursor chat final response must be exactly:
END
