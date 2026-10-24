# R08 review: file meaning, rule authority, ordered transitions and incident routing

Issued: 2026-10-24T19:50:00+08:00
Host: ZHANGWEI
Slot: R08/10, continuation of the user's current R08 scope; two future execution deliveries remain.
Status: BOUNDED_RECEIPT_ACCEPTED; FOUNDATION_LOGIC_CLOSURE_NOT_YET_ACCEPTED

## Receipt disposition

GPT retrieved and independently hashed the original candidate manifest: 80,026 bytes, SHA256 89d2a903fe01701c43c6cf8a90906c096aede74db082012fb6bc31d31735787f.
GPT base64-decoded the literal UTF-16 audit/probe stdout and verified the captured byte hashes:
- audit 089c94aea9b050c8dbe361a940f930851385ad8b5dc1a484a81b48867eb06644, status RECONCILED, 21 checks, no failures;
- probe e7da723f17bf9a6c7f0310bcd139fa4ef665b7d9ef3be78e53b35f20318d6232, status SCHEMA_ADAPTER_PROBE_PASS.

The bounded current-state evidence is accepted: pinned candidate/parent integrity, exact 2026 stock price values and keys conserved, explicit unobserved grid, inherited 2026 market schema, and the fixed 399303.XSHE schema probe. The first-build raw receipt remains unavailable. Current-state audit is not a reconstruction of that execution history.

This does not close production publication, rule enforcement, engine admission, adjusted-price authority, latest data updates, or the entire BLACKBOX foundation.

## The user's clarification changes the R08 acceptance question

A directory list, a readable table and a passing schema adapter are distinct from a functioning rule-governed system. R08 must explain:
what each relevant artifact means -> which effective authority governs it -> which producer/consumer actually uses it -> which prerequisite permits the next transition -> which exact rule and implementation stop a wrong transition -> which incident/experience record prevents recurrence.

Three different kinds of connection must be recorded:
1. Filesystem paths/junctions and their actual endpoints.
2. Product/source/schema/PIT lineage and registered consumers.
3. Rule/phase/receipt dependencies and incident-trigger bindings.

An archive, strategy output, engineering lesson and production data root are not interchangeable authorities. Do not manufacture physical links to make every folder appear connected.

## Source-grounded facts GPT has read

A. HAND authority and engineering memory
R04 source_contracts/S5_AI_ENTRY_MEMORY/HAND.txt, SHA256 f709e9b5000ab2c7d499ec312fc6be4cdb2934b4ce45fc94b6b10f40020af96b:
- lines 561-571 name DATA_BASE_VERTICAL_PIPELINE_R1 and NO_PHASE_SKIP=TRUE;
- lines 573-605 subsequently name unified acquisition, governance enforcement, and a later L5 resume. These appended phase values cannot all be simultaneously current. Resolve the effective phase from the applicable authority/CURRENT and explicit supersession, not from the first or last matching word alone;
- lines 1284-1301 explicitly separate research memory from engineering memory; ENGINEERING_MEMORY_ROOTS are E:\BLACKBOX\经验卡 and E:\BLACKBOX\记忆盘;
- lines 1332-1340 pin the wrong-phase lesson:
  经验卡\JQData_download_lessons\cards\LESSON_JQDATA_010_EXTERNAL_WRONG_PHASE_FULL_TIP.md
  记忆盘\03_操作流程经验包\error_repair_lessons.json.
  The recorded external phase map is p0_financial_p1_holders_p2_fund_p3_index; tip start is not historical start.

These pointers prove that the relevant rule/lesson entries exist in HAND. Their pointed-to complete bodies, current invocation and phase guard still need closure. GPT has NOT yet read those lesson/rule bodies and will not call them understood or enforced from a title.

B. AI startup and task routing
AGENTS.md and the kernel/Manifest require HAND/task-class routing and SHA-checked MUST_READ preflight. The Manifest has a per-task budget; do not make every agent ingest the whole rule/experience library or add all files to alwaysApply.

C. Read order
BLACKBOX_DATA_ACCESS_MUST_READ_R1:
request -> Resolver(PATH) -> product/Reader -> completeness -> Capability(request window) -> result.
Path READY does not imply request readiness. Match symbol, date/window, frequency, fields and price mode, and read all registered overlapping shards.

D. Missing-source diagnosis order
BLACKBOX_DATA_COVERAGE_AND_CACHE_NON_REGRESSION_GATE_R1 and its .mdc:
RAW -> Cleaning -> Cache -> Reader -> Filter.
This is diagnosis order, not a reversal of Cache-first normal consumption.
EMPTY is not NO_DATA. All relevant registered layers/aliases/shards plus the absence gate and completeness evidence are required before absence; unknown or unavailable diagnosis stops the claim. RAW-complete data cannot be needlessly re-downloaded.

E. Update order
BLACKBOX_HAND_CACHE_FIRST_WORKFLOW_POLICY_R1:
SOURCE_DOWNLOAD -> RAW_CURRENT_UPDATE -> CLEAN -> ALIGN -> ANTI_LOOKAHEAD_PIT_GATE -> CACHE_COMPILER -> CACHE_QA_EQUIVALENCE -> ATOMIC_PUBLISH -> CACHE_CURRENT -> RESEARCH_BACKTEST.
BLACKBOX_HAND_DOWNLOAD_MUST_CLEAN_ANTILEAK_R1 gives an additional required tail including the formal/domain seal, conditional CURRENT and inventory update. The daily six-lane rule uses INGEST -> ALIGN -> CLEAN -> PIT -> ISOLATE -> CACHE -> MANIFEST -> CURRENT -> RESEARCH.
Distinguish field/time normalization from final cross-product alignment when reconciling the wording. Do not use a summary arrow to excuse a missing check or advance a live CURRENT early. No publisher changes are authorized in R08.

F. Engine admission order
DATA_INGESTION_GATE_RULES_R1 has 15 ordered PRE_INGESTION gates:
source identity -> asset code -> asset type -> frequency -> field dictionary -> field alias -> domain -> PIT -> adjustment -> tradability -> matching requirements -> factor dictionary -> factor PIT -> factor cleaning-rule dictionary -> final decision.
Every listed failure is BLOCK, warning pass is forbidden, and post-ingestion judgement/repair is forbidden. formal_backtest_active remains false. A working get_price or canonical adapter cannot replace this chain.

## Required graph: five readable stages, exact underlying steps retained

| Stage | Meaning | Required linkage to prove |
|---|---|---|
| 1 Authority and phase | select effective task rules, memory lessons and allowed phase | entry -> current authority -> complete bodies/SHA -> preflight/phase receipt |
| 2 Identity and discovery | identify original product, supplier, dictionary, scope and actual storage | registered logical product -> all relevant layers/shards -> schema/time/provenance |
| 3 Controlled transformation | normalize/clean/align/PIT without inventing data | exact writer/reader -> input/output schema -> seals -> invalidation dependencies |
| 4 Verification and release | prove full inheritance, exact coverage and coherent generation | QA/equivalence/non-regression -> paired release -> authorized publisher -> CURRENT |
| 5 Consumption and feedback | admit a request before engine ingest; retain incident/memory evidence | Resolver/Capability -> ordered MASTER gates -> consumer; failure -> rule/card/test |

These five stages are a human-readable grouping, NOT newly invented P1..P5 values, permission to skip the underlying original steps, or a replacement SSOT.

## Two additional incorrect connections to remove

1. Engine paths must come from original sources, not flat attachment names.
R04 CONTRACT_SOURCE_MANIFEST.json already records the actual E:\BLACKBOX_ENGINES tree. It places api.py at bullet_trade\data\api.py, engine.py at bullet_trade\core\engine.py, base.py at bullet_trade\data\providers\base.py, the second base at bullet_trade\data\base.py and __init____611063f6.py at bullet_trade\core\__init__.py.
The R08 reconstruction as bullet_trade/api.py, bullet_trade/engine.py or helpers is unsupported and must be withdrawn. See ENGINE_ORIGINAL_PATHS_FROM_R04.json. Check these exact physical paths on ZHANGWEI; do not declare the engine absent because the flattened delivery directory lacks a package layout.

2. The correction RC10 wrongly attributes 2026 H1 history to the August-5..11 gap release. The actual fixed probe read the full-history index_daily__399303_XSHE__to_20260804.parquet with hash 1c5b5d2b..., which contains 137 H1 sessions. The 5-session August gap cannot be the source of January-July rows. Correct the lineage narrative without editing any source release or blessing unregistered extra files.

## What is still required in R08

A compact, source-cited semantic/authority/execution map; complete bodies of the specifically missing vertical-phase/governance/engineering-lesson rules; the actual implementation and failure-trigger edges, with unimplemented/uncalled edges explicitly named. Earlier literal path/reference counts alone do not establish these links.

No claim that every contract has been read, every old strategy understood, or the system operational is authorized until the relevant chain has been reviewed and exercised at its actual entry points.

ORDER_ALLOWED=false
FOUNDATION_ACCEPTANCE=false
PRODUCTION_CHANGE_AUTHORIZED=false
NETWORK_ACQUISITION_AUTHORIZED=false
