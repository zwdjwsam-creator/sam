# R04/10 execution contract: GPT safety patch and complete applicable contract handoff

HOST: ZHANGWEI
TASK_FAMILY: BLACKBOX_FOUNDATION
BUDGET_SLOT: 4/10
REMAINING_CYCLES_BEFORE_THIS_TASK: 7
REMAINING_CYCLES_AFTER_DELIVERY: 6
PREDECESSOR: BLACKBOX_FOUNDATION_20261024_R03
FOUNDATION_ACCEPTANCE: false
ORDER_ALLOWED: false
PRODUCTION_CHANGE_AUTHORIZED: false

The user has changed the operating model: GPT owns semantic decisions, integration designs and vulnerability fixes. The local AI inventories evidence, resolves exact references, and mechanically executes written task contracts. It must not invent business rules, independently rewrite the provider/updater, relax gates, choose a conflict winner, or substitute a guessed path. This instruction supersedes earlier permission to design candidate fixes autonomously.

## A. Read first; reuse completed work

Read the full GPT review and supplied scripts:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R03_REVIEW_20261024_1455/
- REVIEW_R03.md
- build_r04_patch.py
- verify_safety_patch.py
- PATCH_INPUTS.json

Read the complete R03 bundle, especially actual TEST_RESULTS and test source, rather than only DELTA_REPORT. Preserve the accepted isolated runtime and R03 files.

Reuse the R9 technical acceptance, 26-domain expected-file-list exact comparison, 950-node worklist/body cache, existing rule indexes, ecology registry, dictionary mapping and compact 66-path overview. Do not repeat a global walk, migration hash pass, 26-domain rescan, old-strategy reconstruction or another directory report.

Existing HUB evidence to consume before requesting fresh copies:
1. agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1814/ENGINE_DATA_INTERFACE_R1.json and DICTIONARY_FIELD_MAPPING_R1.json.
2. completion_1618/source_reads/FINAL_BACKTEST_ENGINE_AUTHORITATIVE_HANDOFF_R1.md and BACKTEST_ENGINE_AUTHORITATIVE_HANDOFF_R1.json under that same parent.
3. completion_1507/source_reads/BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_HANDBOOK_CURRENT.md and already-uploaded full publish/common/NAV/compiler source.
4. completion_1429/source_reads/S_FULL_DATA_UPDATE_SCOPE.json, S_PIPELINE_MATRIX.json and S_DAILY_INC_SW_CACHE.json.
5. agents/chatgpt/inbox/BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150/v2/continue_0010/correction_0650/contract_scope_1145/CONTRACT_SCOPE_1145.json, RULE_ID_INDEX_0930.json, durable/body cache and source_upload_1136.
6. Existing independent semantic review under agents/chatgpt/reviews/BLACKBOX_DATA_MANAGEMENT_INDEPENDENT_SEMANTIC_REVIEW_20261022_1519/.

These are reuse pointers, not declarations that their historical status is current.

## B. Authorized mechanical patch (no local redesign)

Fixed working root:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024

Save the exact three GPT-supplied executable/manifest files into reviews\R04_GPT_PATCH under that root. Verify HUB download bytes. Run, from the fixed working root:

```powershell
.\runtime\.venv\Scripts\python.exe reviews\R04_GPT_PATCH\build_r04_patch.py candidate\r3 candidate\r4 reviews\R04_GPT_PATCH\PATCH_INPUTS.json
.\runtime\.venv\Scripts\python.exe reviews\R04_GPT_PATCH\verify_safety_patch.py candidate\r3 candidate\r4
```

The generator checks normalized input SHA256s, refuses an existing destination, compiles generated Python and preserves R03. If a source hash, anchor, destination or test fails, report the exact mismatch; do not modify the script or source to force PASS. A pre-existing r4 may be reused only if its contents exactly match the generator outputs recorded by GPT; otherwise leave it untouched and report the conflict.

Expected scope: nine synthetic method checks. Also perform one prescribed native import/instantiation of candidate.r4.engine_adapter using the existing R3 registry and a bounded daily call for 000001.XSHE, 2026-06-01..2026-06-03, fq=none, fill_paused=False; report actual frame or exact rejection. This is diagnostic adapter evidence, not MASTER admission. Capture process exit code, interpreter, input/output hashes and stdout/stderr. Do not alter the original R03 suite to conceal the intentionally blocked index/event engine methods.

The provided patch only fixes the observed unsafe boundary and future-announcement diagnostic leak. No factory registration, full engine invocation, adjustment formula, corporate-action unit conversion, current-pointer change or real update is authorized by this task.

## C. Complete evidence handoff for GPT-authored integration

Produce a finite CONTRACT_SOURCE_MANIFEST.json before gathering copies. Start from the actual MASTER registry and existing rule/body indexes; follow all referenced normative dependencies applicable to the read plane, PRE_INGESTION gate, clock/session, adjustment/corporate events, lineage/revisions, publication and increment downloads. Include the full relevant rule families and admission matrices, not just selected successful rows. Separate historical/superseded rules, active rules, supplementary policies, experiments and strategy-only material. Use recorded supersession/authority references; never select by filename CURRENT or mtime alone.

For every item record: exact local path, role, authority identifier, parent references, current/historical/candidate status, bytes, SHA256, full-body read completion, existing HUB blob if identical, and any unresolved reference. A hash or summary is not a claim that its body was read.

Collect only missing or changed full bodies into source_contracts/ and source_engine/. Keep each text file below 400 KB; if necessary split losslessly with a manifest of ordered parts and original full-file hash. No excerpts, keyword-only dumps or paraphrases in place of a contract. Do not re-upload identical existing HUB sources; reference their exact path/blob and verify their hash against the desktop file. If an applicable item cannot be found, name the exact unresolved item and the already-searched indexed scope. Continue independent evidence collection; never guess or silently omit it.

Required source sets:

1. Engine MASTER and complete referenced admission rule families.
   Known engine root:
   E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine
   Include the actual MASTER_RULE_LIBRARY_REGISTRY_R1.json, DATA_INGESTION_GATE_RULES_R1.json, all referenced field/alias/domain/asset/frequency/PIT/adjustment/tradability/matching/factor admission matrices, current dictionary/canonical/daily-minute/matching behavior contracts and actual clock/data-visibility/session/execution-profile contracts reached by their references. Use the existing root/index to locate them; do not invent relative paths. Preserve dictionary-only factor value prohibitions.

2. Actual interface, consumers and provider semantics.
   Under the observed blackbox_jq_engine\bullet_trade tree, upload full data\providers\base.py, data\api.py, core\engine.py, package initializers and pyproject.toml. Include complete source of directly referenced helpers that govern provider injection/configuration, time context, argument forwarding, return layouts, adjustment and corporate event consumption. From the API's real imports, identify and include the reference provider implementation supplying these semantics, its directly applicable unit tests and dividend consistency test. Source inspection only: do not initialise credentials, remote SDK clients or brokers. Existing set_data_provider object injection must be examined before claiming a factory branch is necessary.

3. Data dictionary and value admission.
   For STOCK/ETF/INDEX daily and minute planes, include full applicable frozen schema, field/unit/alias/PIT/adjustment/revision/cleaning contracts referenced by existing dictionary indexes and producer manifests. Include explicit source evidence for factor and pre_close, per-ten-share dividend ratios, announcement visibility, date-only versus timestamp availability and authoritative duplicate resolution. Include contract bodies governing index snapshot historical eligibility. The older experimental schema audit is not master authority.
   Record separate diagnostic/read eligibility and engine-domain eligibility; requesting only close does not waive required factor/pre_close/matching fields.
   Do not force a factor to 1, infer unknown pause state as trading, infer fund=ETF without the asset contract, or resolve revision conflicts merely by narrower span/newer build.

4. Update and publication contracts.
   Reuse the full existing handbook and uploaded source. Add missing complete active hard-rule JSON/MDC/source references governing REQUIRED/excluded/deferred domains, per-dataset/date scopes, full product inheritance, per-domain validated cursors, corrections/dirty history refresh, failure recovery, and publication.
   Include the actual run_blackbox_research_os.py and any directly invoked updater module not already fully available in HUB, plus full current configuration/manifest bodies needed to resolve its execution path (no secrets).
   Retain the already-confirmed multi-file publication window, prior-tip-overrides-new revision issue and static-registry-overwrite risk as open defects. Do not rerun those production functions.
   Explicitly reconcile the handbook's fq_pre_post exclusion with engine fq=pre default: this is an unresolved compatibility boundary, not permission to download excluded data.
   A maximum observed date is not a verified incremental cursor and does not justify skipping earlier gaps.

5. AI entry and memory.
   Reuse the existing indexes to provide the complete active AI-entry instructions and rules that govern database access/update, plus a concise existing experience/test-memory index. Preserve the distinction between normative rules and strategy experience. Do not reconstruct old strategy code or old PnL.

## D. Current conflict register and structure clarity

Return CONTRACT_CONFLICTS.json with one row per concrete incompatibility: source A and clause, source B and clause, actual observed behavior, consequence, status and affected interface. Cite full-body file hash plus line/key. The operator records facts only; resolution_owner=GPT. Missing semantics stay UNRESOLVED, not guessed.

At minimum include:
- R03 partial admission versus MASTER reject-before-ingestion.
- Dataset factor/pre_close requirements versus source segments and reader's requested-field-only admission.
- RAW_NONE / fq_pre_post excluded versus engine fq=pre default.
- R03 bar clock assumptions versus actual clock/session/visibility rules.
- Day-over-year/build-date revision priority versus authoritative conflict handling.
- As-of/announcement and corporate-action units versus engine consumer expectations.
- Index snapshot eligibility and dated security master semantics.
- Daily/full update obligations versus existing updater/publication defects.

Correct the structure map: distinguish file existence, static call edge, runtime-observed edge, desired edge and unresolved edge. Every edge endpoint must exist as a node; local_parquet was previously an undeclared node. A registry-builder input reached indirectly through a historical R01 JSON is not a fresh CURRENT resolution. If needed, inspect only the exact named producer/input to resolve it.

Correct the R03 evidence labels: check 3 is fixture-based; only checks actually supplied the real provider count as real data. Preserve original reports; publish an English correction, not a rewritten historical result.

## E. Boundaries, language and deliverables

All writes stay in the candidate recovery tree and the specified HUB inbox/reviews. Preserve original data, engines, rules, seals, CURRENT pointers, R9 state and existing candidate evidence. No business API call, data download, broker connection, token probe or production activation this cycle. Existing isolated runtime/dependencies may be reused; do not repair global/historical environments.

All newly authored uploads, reports, status text, explanations and new comments MUST be English. Original source quotations, literal paths/identifiers and byte-preserved contract/source evidence may retain their original language; annotate them in English. Never translate or rename the actual source files to satisfy the reporting language. Never upload credentials, .env, account secrets or network tokens. If a source contains a literal secret, redact that literal, declare the redaction and report the original hash locally without revealing the secret.

One combined inbox delivery:
agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R04/
- ROUND_STATUS.json: budget_slot=4/10, remaining_after_delivery=6, actual operations and blockers.
- PATCH_EXECUTION.json and only changed candidate code/hashes.
- CONTRACT_SOURCE_MANIFEST.json + complete missing/changed source bodies.
- CONTRACT_CONFLICTS.json.
- Corrected SYSTEM_STRUCTURE and concise DELTA_REPORT in English.
- Exact next missing evidence, if any; no unsupported system-wide PASS.

Deliver available evidence even when one contract is blocked; avoid opening separate wait cycles per file. Upload, update INBOX_FOR_CHATGPT.md, read back and verify hashes. Do not output a long Cursor chat report. The final Cursor response after successful HUB delivery/readback is exactly:

END

## F. Remaining seven-cycle objective

This is the first of the seven remaining deliveries (R04). Sequence for R04..R10:
R04 exact safety patch + complete applicable contract/source handoff;
R05 GPT-authored reconciled provider/gates and actual engine API injection in isolation;
R06 GPT-authored updater/publication repairs with offline fault and replay evidence;
R07 contracted bounded real incremental update into a candidate release;
R08 finish required dataset/update chain and coverage reconciliation using existing evidence;
R09 contracted shadow engine and repeated incremental/idempotency/recovery checks;
R10 independent final acceptance, desktop launch/update runbook and explicit remaining exclusions.

This is an execution budget, not permission to declare an incomplete system accepted. Batch related work; report missing proof early. GPT will adjust the bounded sequence using the complete contracts. The final objective remains a functioning desktop data foundation and safe repeatable updates, rather than more directory summaries.
