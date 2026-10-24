# R08 required receipt correction and fixed canonical-index probe

Issued: 2026-10-24T18:55:00+08:00
Executor: ZHANGWEI
Parent: BLACKBOX_FOUNDATION_R08_OF_10_OBSERVATION_GATE_AND_EXPLICIT_BINDINGS_20261024_1812
Status: COMPLETE THE EXISTING R08 DELIVERY; NOT R09
Budget remains 8/10 delivered subject to correction, two later execution deliveries remain.
Do not count this as a new foundation round or run a fresh inventory.

## Read first

Read the complete review and binding correction:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R08_RECEIPT_AND_SCHEMA_REVIEW_20261024_1855/REVIEW_R08_RECEIPT_AND_SCHEMA.md
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R08_RECEIPT_AND_SCHEMA_REVIEW_20261024_1855/EXACT_EXISTING_SOURCE_BINDINGS.json

Use the original R08 CACHE preflight and rerun the unchanged actual Manifest preflight if required before executing these read-only controls. Verify its hashes. Do not change Manifest/HAND/production gate outcomes.

No build/rebuild, publication, CURRENT switch, supplier call, authentication, credentials read, data restoration or data cleanup is authorized. Do not rerun the R08 builder just to produce a missing first-build receipt. No production compiler import or invocation.

## 1. Stage exact audit/probe code

Use E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R08\receipt_correction\
Files are in the review folder above:
- r08_receipt_audit.py SHA256 6802053d2f87822d466556a70a24310120d99d24679f4f965fecdb108156e838
- test_r08_receipt_audit.py SHA256 883a3d8b5a20a30a8ad3f0ba49b08c91de2a71065de82326dc9de0304ddd8c6a
- canonical_index_schema_r1.py SHA256 38c0290e3c50313879924d0fd41866e62badeaa2066421647f3a9e305f6957cc
- test_canonical_index_schema_r1.py SHA256 50717907c340a5f613a9ee24d979b6ea8f040098b17ccde240e2eac8f4c3d44a
- probe_canonical_index_r1.py SHA256 b9fd6714e10db3476fe2d069c90bfa4a2ca45df395b7270c861cec3db7e868a4

Copy the unchanged reviewed r06_bundle_store.py into this folder:
SHA256 6c76c0de3aca7d96223e5883b68918c794585156e29c292962d438e6986269a2.
Use the existing reviews\R08\cache_compiler_source_R06.py, SHA256 c8ddf805a6ddc998cda507f2aa5c92f27b13a43b5445e5bfed21477c5822f336.

From the recovery root run these four commands, capturing literal stdout, stderr and exit codes separately:
    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R08\receipt_correction\test_r08_receipt_audit.py
    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R08\receipt_correction\test_canonical_index_schema_r1.py reviews\R08\cache_compiler_source_R06.py

Only after their controls PASS:
    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R08\receipt_correction\r08_receipt_audit.py
    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R08\receipt_correction\probe_canonical_index_r1.py

These controls read exact registered inputs and print evidence; only synthetic tests write temporary fixture files. They do not run build/replay, modify original data, merge index revisions or admit a backtest.
If a control fails, preserve the exact exception/input schema. Do not patch the code, expectation, metadata or source to obtain PASS. Continue independent evidence retrieval below.

The candidate manifest must already have SHA256 89d2a903fe01701c43c6cf8a90906c096aede74db082012fb6bc31d31735787f as R08 claimed. A different SHA is an evidence discrepancy to report, not permission to rewrite it.

## 2. Deliver missing original artifacts and correct statements

Upload the ORIGINAL local R08 CANDIDATE_MANIFEST.json, preserving its bytes and SHA, to this correction bundle. Do not generate one from summaries. Upload the existing raw first-build stdout/stderr/exit/time if retained. If not retained, say FIRST_BUILD_RAW_RECEIPT_NOT_RETAINED. Do not invent or rerun it.

Use the supplied independent audit to reconcile:
- pinned parent and all input/artifact hashes;
- actual full-prefix partition row counts, the R07/R08 10,426-row reporting discrepancy;
- source-2026 versus output-2026 exact price values and keys, separately from full-prefix formula context;
- actual parent/candidate Arrow schemas and the reported market-structure 8-versus-14 columns;
- exact grid-audit keys and unobserved price/factor values.

Correct the replay prose: hash replay is not rederivation. Correct the invalid full-prefix-to-one-year row-conservation comparison. Preserve all original R08 files; use append-only corrections with exact references. Do not infer data mutation or loss merely from inconsistent report totals.

## 3. Finish the original R08 implementation handoff without rescanning

Reuse the existing 950-node source-body cache and prior packages. The review has already resolved two generic writer bodies and fixed three incorrect HUB source links. Do not ask GPT to locate the same functions again.

Provide ORIGINAL_SOURCE_BODY_INDEX_CORRECTED.json:
- every reusable GitHub path must resolve, with exact blob/SHA;
- actual current source path/module name is required, not just a flat uploaded basename;
- for bodies already on HUB with matching full hash, reference them instead of re-uploading;
- for current bodies absent or different, upload the full body and its relevant local helpers now.

Specifically account for:
A. The CURRENT coverage caller bodies blackbox_data_access_resolver_r1.py and blackbox_data_coverage_control_plane_build_r1.py. Compare with existing HUB bodies first; if identical give the matching reference, otherwise upload the current versions. Include exact call signatures/expected returns for the missing common-module names and gate and self_test functions. No invocation of these possible ledger/publish writers.
B. cache_compiler_adjust_factor_pit_r1.py (reported SHA bb8a52a19e92b2003a462ce38a91c1c466831d3ee0fbcb4f22baa6c12ded99b0), its actual helper bodies and the request/sidecar/lineage record behind the ordinal-factor units. Do not manufacture a trade date from a filename. Reconcile the stated 20/37 ordinal files with the 17-file list in the bindings; enumerate already-captured file-axis evidence, no supplier call.
C. Exact source/creator references for current valuation, universe/security, tradeability, SW structure and the FUND-like view reader, using CURRENT parent/build/receipt/registry references and cached node bodies. Where still unlocated, record the exact searched provenance references and narrow unresolved dependency; do not substitute an unverified guessed callable.
D. Minute and CBOND namespaces remain separate; reuse existing binding/code bodies if already delivered. No minute-wide data scan, no equity-cache takeover of CBOND and no expansion into strategy research.
E. Actual engine package/module layout, entry and dependency/lock references from the existing R04 source index. Distinguish the real source path from a flattened uploaded name. No full-package startup, installs or MASTER outcome changes are authorized in this correction.

Repair the R09 binding document by reference: the stock RAW P2_stock_daily paths and two source hashes already exist in R05 GAP_REPAIR_INPUTS.json / R06 pins; carry those forward. Supplier credential LOCATORS and the actual download auth route already exist in R04/access_resources/SOURCE_ACCESS_REGISTER.json and ACCESS_AND_DOWNLOAD_RUNBOOK.md. Engine env-loader placeholders are not a replacement for that established download credential route. No credential values or secret-dependent hashes may be uploaded or read here.

Do not rewrite the original 154-file index MANIFEST to 732. Supply the registered expected file/hashes, observed extra-file/provenance reconciliation and original authorization references. Physical file presence alone does not close lineage/authority. Keep the source and gap-release CURRENT statuses unchanged.

The new canonical adapter fixes a reproducible schema incompatibility; it is a pure candidate transform, not an installed reader or formal data plane. Do not wire it into production or point the engine directly at RAW.

## 4. Upload/read back and finish

One append-only English bundle:
agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R08/receipt_correction_1855/

Include:
- CORRECTION_STATUS.json (same R08 slot; two future deliveries remain)
- ORIGINAL_CANDIDATE_MANIFEST.json with original SHA/byte preservation evidence
- independent audit/probe stdout, stderr, exits and exact executed code hashes
- RECONCILED_EVIDENCE.json for the listed contradictions and any failed checks
- ORIGINAL_SOURCE_BODY_INDEX_CORRECTED.json plus missing source bodies
- R09_IMPLEMENTATION_BINDINGS_CORRECTED.json (carry-forward plus exact deltas)
- raw first-build receipt or its explicit unavailable status.

Update INBOX_FOR_CHATGPT.md to this correction with the original R08/predecessor pointers preserved. Read back exact uploaded content before finishing. Do not call the correction accepted on GPT's behalf; GPT will review before releasing R09.

SOURCE_ABSENCE_CLAIMS=0
NETWORK_CALLS=0
FOUNDATION_ACCEPTANCE=false
ORDER_ALLOWED=false

After verified HUB delivery, Cursor final chat response must be exactly:
END
