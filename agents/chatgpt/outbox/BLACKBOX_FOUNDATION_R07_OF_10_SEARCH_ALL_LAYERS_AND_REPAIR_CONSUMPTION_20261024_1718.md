# R07/10: enforce pinned absence rules, search all relevant layers, repair local consumption

HOST: ZHANGWEI
PREDECESSOR: BLACKBOX_FOUNDATION_20261024_R06
BUDGET_SLOT: 7/10
REMAINING_CYCLES_BEFORE_TASK: 4
REMAINING_CYCLES_AFTER_DELIVERY: 3
FOUNDATION_ACCEPTANCE: false
ORDER_ALLOWED: false
PRODUCTION_CHANGE_AUTHORIZED: false
NETWORK_ACQUISITION_AUTHORIZED: false

## 1. User steering and binding terminology

The user explicitly recalls the pinned rule: complete the required cross-layer search before declaring data missing. Treat current failures primarily as import/inheritance/time-index/resolver issues to investigate. Do not assume originals are lost, and do not assume completeness without evidence.

This instruction replaces the tentative plan to run a new stock download in R07. No acquisition runner was issued or executed. No auth, quota query, supplier request, paid-module probe, replacement download or entitlement change is authorized this round. Preserve the successful R05 access evidence.

Only GPT owns semantic/code fixes. The local operator inventories, queries and executes exact supplied contracts; no arbitrary repair or rule design.

Read:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R06_REVIEW_R07_LAYER_DIAGNOSIS_20261024_1718/REVIEW_R06_AND_R07.md

Do not describe a current consumer returning zero records as 'the database is missing data'. Report the exact layer, product, request, predicate and observed result. Positive RAW/older-release evidence cannot be overridden by a shallower negative result.

## 2. Read and return the actual pinned contract chain

Already available and to be reused:
- R04 source_contracts/S5_AI_ENTRY_MEMORY/AGENTS.md.
- HAND.txt coverage section, lines 142-159 of the staged body.
- agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1429/source_reads/S_COVERAGE_NONREG_GATE.json.
- R04 source_contracts/S4_UPDATE_PUBLICATION/BLACKBOX_HAND_CACHE_FIRST_WORKFLOW_POLICY_R1.json.

HAND says:
NO_AGENT_MAY_DECLARE_DATA_MISSING_WITHOUT_COVERAGE_DIAGNOSIS
RAW_REDOWNLOAD_DEFAULT=FORBIDDEN_IF_RAW_COMPLETE
PATCH_CANNOT_SERVE_AS_FULL=true
FULL_HISTORY_NON_REGRESSION=true

Use existing rule indexes/body caches to locate and read the complete linked implementation chain, copying only missing/changed bodies to HUB:
- .cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc and the task-class mandatory-reading manifest selected by blackbox_must_read_preflight_r1.py;
- .cursor/rules/blackbox_data_missing_diagnosis_gate.mdc;
- BLACKBOX_HAND_DATA_COVERAGE_AND_CACHE_NON_REGRESSION_GATE_R1.json;
- BLACKBOX_HAND_DATA_PLANE_THREE_LAYER_STATEMENT_R1.json and applicable current ledgers;
- 脚本/blackbox_data_coverage_diagnose_r1.py;
- 脚本/blackbox_cache_coverage_non_regression_gate_r1.py;
- 脚本/blackbox_data_absence_gate_r1.py;
- their directly referenced normative/alias/time/index contracts.

Keep exact local path, authority/version, whole-file hash and read status. A staging hash is not a full-body review claim. Inspect old tools statically first: do not invoke unknown code that may rewrite ledgers, CURRENT or HAND. GPT will review the full implementations before authorizing their runtime integration. Missing references stay named and unresolved, not guessed.

Do not run the old broken E:\BLACKBOX\.venv interpreter. Use the dedicated runtime with -X utf8.

## 3. Execute GPT's offline controls and local derived rebuild

Fixed working root:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024

Stage exact scripts from the R07 review directory into reviews\R07:
r07_claim_guard.py, r07_rebuild_local.py, test_r07.py.

Also copy the unchanged GPT r06_bundle_store.py from reviews\R06 to reviews\R07, and the exact full compiler body delivered in R06 to reviews\R07\cache_compiler_source_R06.py. Expected compiler SHA256:
c8ddf805a6ddc998cda507f2aa5c92f27b13a43b5445e5bfed21477c5822f336

Verify HUB blob identity and hashes, then:

```powershell
.\runtime\.venv\Scripts\python.exe -X utf8 reviews\R07\test_r07.py reviews\R07\cache_compiler_source_R06.py
.\runtime\.venv\Scripts\python.exe -X utf8 reviews\R07\r07_rebuild_local.py --compiler-source reviews\R07\cache_compiler_source_R06.py
```

Run the real rebuild only after offline controls PASS. Expected 15 synthetic controls. The script hash-checks the compiler and extracts only its original compute_factors/market_structure functions. It NEVER executes compiler startup, write_static_registries, main, HAND writer or publisher.

The rebuild reads canonical cached price partitions through the verified R06 view, including the full stored prefix. It does not retreat to a whole RAW reload. All available prefix is used because recursive EMA state is not recreated by only 250 previous sessions. It writes only new 2026 derived candidates under:
candidate_releases\R07\R07_LOCAL_STOCK_DERIVED_RECOVERY_20261024

The stock factor product is recomputed from corrected local prices. Market core is recomputed, but five unsupported SW fields are explicitly null with PARTIAL_CORE_RECOMPUTED_SW_NOT_RECOMPUTED. This must remain partial until its own complete source/contract join is proved; no invented industry breadth.

Legacy year-reset outputs may differ because the original tip-rebase clipped to 2026 before formula execution. Record full-prefix versus year-reset semantics rather than forcing equality or silently changing formula names.

If successful, execute the same real rebuild command ONCE more to verify ALREADY_BUILT_VERIFIED and unchanged hashes. Do not delete partial outputs or edit scripts if a guard fails; preserve the exact failure and continue independent diagnosis.

No existing data, R06 candidate, seal, registry or CURRENT is changed. No real candidate commit marker is switched. No full engine or formal MASTER admission is claimed.

## 4. Complete reusable layer search for the reported problems

Produce one LAYER_SEARCH_AND_BINDING_LEDGER.json using the existing 54-dataset ecology registry, 41-product catalog, coverage ledgers, full migration mapping, file lists and completed rule indexes. Do not restart the 950-node job or enumerate millions of duplicate aliases merely to recreate a directory list.

For EACH proposed missing-data assertion, account for ALL authorized relevant source locations, not only the selected CURRENT product:
- current CACHE and historical pinned CACHE releases;
- manifest/sidecar registrations, virtual views and external product namespaces;
- current CLEAN, intermediate/sealed CLEAN releases and their parent links;
- canonical FULL_HISTORY RAW, incremental RAW and other original-data roots named by that dataset's contracts;
- dataset aliases, junction/realpaths and migrated old D-path mappings;
- staged/archived sources only when the existing index/manifest actually references them.

Search may reuse a complete index/manifest, but prove its scope/freshness and follow exact positive entries. An unreadable location, stale/partial index, unresolved alias, failed query, wrong glob or inaccessible root prevents global absence certification. It does not become NO_DATA.

Every ledger entry must identify:
dataset/product/source; asset/frequency; exact security universe and requested date/field scope; correct query time field; timezone; event/period/publication/known_at semantics; all expected roots and searched roots; actual paths/file IDs/hash references and query counts; errors/unsearched scope; earliest layer serving the request; current consumer binding; and the permitted fixed diagnosis code with evidence.

Explicitly handle:
A. The two stock dates: positive RAW and intermediate CLEAN evidence already exists. They are not SOURCE_MISSING; reuse the R06 candidate recovery and diagnose inherited consumption.
B. ETF/index/valuation/NAV date-set observations: search originals, historical and current releases before attributing a defect. An ETF-only lookup cannot establish fund-like history absence; use the real FUND/VIEW mapping.
C. NAV publication days, finance disclosure periods, weights snapshots and PIT availability are not interchangeable with daily trade-date rows. Do not call every calendar day without a row a missing datum.
D. Use the actual exchange-calendar contract/source, not ADJUST_FACTOR's dates as a calendar proxy.
E. The 18 entries without a directory under one CACHE root: classify metadata/registry, virtual view, sidecar, separate namespace, stale binding or unresolved. CACHE_MANIFEST_REGISTRY_R1 and CACHE_DEPENDENCY_REGISTRY_R1 are registry products; Tushare and minute products may live outside that root. A missing directory there does not prove missing source data.
F. pre_close/ST/paused/limits present in formal RAW but not cached: record FIELD_NOT_CACHED and the precise permitted hybrid join. Do not download them again merely because the price-cache schema drops them.
G. Time-index diagnostics: stored date/time versus row-group stats versus filename/build date; normalized code/alias; frequency; inclusive window; transaction/session cutoff; publication/known_at; partition key; selected release and consumer filter. Record a minimal actual counterexample and source line/key for any binding/index error.

Local operator may write evidence collectors for these read-only queries. It may NOT implement a new join, resolver repair, absence rule, source preference or time conversion. GPT will author those from returned exact source and contract evidence.

## 5. Enforce fail-closed claims

r07_claim_guard.py is a GPT-authored supplement, not a replacement for the original diagnoser. R07 contains no approved source-absence receipt hashes, so it authorizes ZERO new SOURCE_MISSING claims and ZERO re-downloads.

Use its classifications for already-proven scoped facts. If no closed diagnosis exists, retain UNKNOWN_STOP. Do not turn 'not found in this query' into 'original data missing'. Do not edit the guard, fabricate its inputs, or create an approval hash.

The final ledger must distinguish:
- source available, not imported/inherited;
- CLEAN available, CACHE not materialized;
- data available, reader/path/time filter fails;
- field available in another admitted layer;
- valid sparse/event/PIT non-observation;
- scope or permission limitation;
- unresolved search;
- source absence pending a fully evidenced GPT review.

Register any genuine file/content discrepancy in POTENTIAL_DATA_LOSS_REGISTER.json, but do not assume migration caused it. Compare exact R9 entity/path/hash and acceptance evidence, current aliases and provenance. If R9 previously verified that entity, current non-observation can be a later change or path problem. If originals/backups still exist, record that recovery source before considering a supplier re-download. No restoration or download is executed in R07.

## 6. One combined delivery; no extra round for this correction

Upload in English to:
agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R07/

- ROUND_STATUS.json: slot 7/10, remaining_after_delivery=3.
- GPT_CODE_EXECUTION.json and FIXTURE_TEST_RESULTS.json.
- LOCAL_DERIVED_REBUILD_RESULT.json, candidate manifest, replay evidence and artifact hashes (no large parquet upload).
- PINNED_RULE_CLOSURE.json plus complete missing/changed contract/tool bodies.
- LAYER_SEARCH_AND_BINDING_LEDGER.json.
- TIME_INDEX_AND_IMPORT_DEFECTS.json: exact observed counterexamples, consumers and source/code references.
- POTENTIAL_DATA_LOSS_REGISTER.json: can be empty; never fabricate a loss to justify download.
- DELTA_REPORT.md with precise scoped facts and next implementable fixes.

Preserve all historical evidence and add corrections explicitly. Do not repeat directory summaries or hand-copy already accepted file counts as new proof. Complete independent work even if one diagnosis is unresolved.

The final objective remains normal desktop operation, correct rule-based data consumption, engine compatibility and repeatable latest/incremental updates. This round secures the existing foundation before acquiring anything further. Remaining rounds are for integration, contracted update and acceptance, not permission to skip unresolved gates.

Update top INBOX_FOR_CHATGPT latest/bundle/checkpoint to R07, upload and read back. All new narrative, comments and status are English; original paths/quotes/source evidence retain their language. Keep secrets local. After successful upload/readback, the final Cursor response is exactly:

END
