## 当前待办：SAM完整交接 + ZHANGWEI R13 合并审核（同一任务，2026-10-25）

双方本轮反馈已到。SAM 的源码交接、FOUNDATION_RUNTIME_MAP.md 及24件必要源码/配置补充已经交付；源机本项交接收口，不再要求重建未保留的09-24控制台历史。ZHANGWEI 持续执行原任务，保留环境、原编译器候选运行、未知值不再补造、单COMMIT候选恢复的已有成果，不重做迁移/盘点/旧测试。

GPT读取了R13重点源码与实际回传，确认原tip compiler被真实调用；单COMMIT恢复证据、严格V4阻断结果是进展。整体仍未验收，R13声称“三个差异全部关闭”范围过强。当前只收口以下三项，不向owner再提技术路线或重复授权选择：

### 1. 接回已存在的分钟输入，定位复权缺口到实际来源层

R13的“无本地分钟产品/须授权新建或下载”与其DATASET_STATE冲突：
PRICE_STOCK_1M.CLEAN = 40个文件、24,998,880行，外边界2026-09-11..09-24，根为现行standard/price/A股_stock_1m；
RAW的P7_stock_raw_none_replacement_1m = 11,790文件，已有抽样记录；
SAM原件脚本/blackbox_stock_minute_1m_reader_r1.py（PRODUCT_ID=STOCK_MINUTE_1M_R1，fetch_stock_minute_1m）及runtime map E17已给出实际入口。
这证明存在来源，不证明原请求全窗口/全代码完整。请将原reader接入本地provider，按策略实际请求时间/代码核对现有范围，沿reader已实现且契约允许的来源顺序查已登记根。只补查原请求尚未回答的分区；不全盘扫描，不把09-11之前的缺口外推成整个分钟面不存在。确实不支持的请求显式BLOCKED；RAW_NONE与复权要求不能混同，禁止开盘价代理或伪造分钟线。保留原V4请求窗口，短窗仅可标诊断。

12个复权稀疏日已在CACHE测到，但“因此必须采集/需要换复权契约”尚无跨层依据。
仅对FACTOR_DENSITY列出的12日及实际缺失(date,code)检查已定位P1_adjust_factor、R15 staging/retained batches、reference/adjust_factor和此前已核实候选/源批次；优先复用既有R04–R10证据。读取必要列，核日期、fq/基准/锚点及来源身份后才允许派生候选。不要把整数序号当日期，不用常数1、ffill/bfill或未知状态替代。日线RAW中的factor列也须按真实请求语义验证，不能看见列名就认为等价。
能在本地有效恢复的直接修复；确实无权威输入则列出精确键/字段/日期及检查过的既定来源，作为待我审核的采集缺项。CACHE稀疏只证明消费层缺值；峰值90%“dense”阈值也不是历史完整性证书。
证券主表按上市区间过滤已有改善，但单快照不证明包含历史退市证券或历史指数成分；is_st未知仍是实际依赖。不得以过滤后剩余证券构造正式策略结论，缺输入的排名/绩效仍不准入。

### 2. 用现有R15完成真实入库/清洗调用，并让覆盖门读取真实证据

R13的build_candidate_cleaning_from_retained.py实际做的是inherit_tree + 自写replay parquet + 原compiler reader/antileak。
这是有效候选构建，但没有调用R15的load_staging/ingest_item/封版与r15_antileak_and_ssot完整流程，不能声称整个原下载后清洗已接通。现有SAM补包已经给出R15真实源码，保留台式机版本，使用当前实际R15函数，最小化注入候选STAGING_MANIFEST、输出、ledger/quarantine/seal路径；禁用或重定向main中的生产指针/规则改写。保留原真实检查，不以新的同名实现替代。直接重放已有08-31/09-01两批，保留原字段/sidecar与来源，不再索要源码。

run_connected_pipeline.response_gate目前调用：
acquisition_absence_gate(n_rows=resp.rows, query_cap=resp.rows, pagination_complete="YES")。
返回行数自充query_cap、代码自填分页YES，不构成完整性证明；4000..7000行带也不是供应商请求规模。让实际适用writer/分页/断点控制接收保存的原请求与返回证据，区分“保留批次字节与键一致”与“原供应商结果完整”。缺少原请求清单/终止页/重放证据的断言保留UNKNOWN，不能制造YES放行采集。
本地transport可替换网络，真实writer/transform和错误传播须实际调用；仅代码存在或absence gate返回PASS不足以准入。复用已通过局部控制，只跑此次连接受影响的检查。

### 3. 完成已授权的候选发布演练并交回统一现态

R13报告请求“再授权候选publish_atomic演练”无需转交owner：原任务已授权隔离候选指针发布，生产CURRENT仍禁止。
调用原publish_atomic的非dry-run路径前，将它及其传递调用的CLEAN_PTR/CACHE_PTR/FACTS/LEDGER、backup、scope/child摘要等所有写入目标显式绑定任务目录；特别是refresh_scope_from_live仍会写scope，不能只重定向两个指针。保留真实gate，不把它替换成总返回PASS。可写目标不能完全隔离时停止此调用并给出具体路径阻断，不能冒险运行。
基于已完成的不可变候选/单COMMIT机制验证实际成功/中途失败/恢复；不重复9项未受影响的旧检查，不把旧多文件顺序替换标为事务。生产读者尚未使用新COMMIT时如实说明，候选机制不能冒充生产原子性。

集中更新同一包的REPORT/ACCEPTANCE和原有B1–B7状态，以及CONNECTED_PIPELINE、COMMAND_LOG/RUN_RESULT的当前索引：它们现在仍指向R12内容，R13实际结果在evidence里。保留旧件并指向当前实际运行，不重跑只是为改标签。
命令需是实际可运行的完整参数；日志/真实退出码直接引用已保留原件，“python -c 'count ...'”、省略号及<sealed>不能当精确执行记录。已未保留的如实注明，无需倒造。

### 本次固定收尾

仅完成上述三项在本地可修部分，仍缺权威输入的分支精确BLOCKED，并继续其他独立分支；不反复执行同一个失败，不增加第四项调查。一次集中回传：原链条哪些确已执行、查询/分钟请求哪些可用、V4原请求具体卡在哪些输入、断点/候选提交是否一致、真正仍需外部获取的最小缺项。不得以新建一批报告代替运行，不再让owner选择技术步骤。

尚未执行的最新采集和生产CURRENT切换分别记“授权阶段未开启”，不能循环拿它们当必须先执行的前置修复。实际数据/分页/清洗前置缺口仍必须如实通过或阻断。NEW_DATA_ACQUISITION_AUTHORIZED=false；CURRENT_SWITCH_ALLOWED=false；ORDER_ALLOWED=false；FOUNDATION_ACCEPTANCE=false；FORMAL_ENGINE_ADMISSION=false。原任务ID不变，无新轮次。
源机当前无需追加任务；台式机本地连续修复，完成后供GPT集中审核。

---

# R10 — complete the local system with existing data, then submit one acceptance package

task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
target: ZHANGWEI
execution_host: ZHANGWEI
workspace: E:\BLACKBOX
status: READY
priority: OWNER_OUTCOME_DIRECTED_CONTINUATION
supersedes_pending_task: BLACKBOX_FOUNDATION_R10_EXACT_RUNTIME_SOURCE_HANDOFF_20261025
phase: EXISTING_DATA_INTEGRATION_AND_ACCEPTANCE
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false

## Owner correction — recover and reuse the laptop workflow first (2026-10-25)

The owner asks why SAM laptop AG has not provided its original tasks, runtime and download logic as one complete handoff for ZHANGWEI to reuse. That source-workflow handoff was not explicitly required in the previous instruction. Correct this omission within THIS task; do not create another sequential source-review round or discard completed desktop work.

Execution hosts: SAM supplies the existing source workflow; ZHANGWEI performs destination adaptation and validation. Use the established inter-machine share / AG coordination channel where available; do not ask the owner to relay individual files or commands. This HUB amendment is not evidence that SAM has received or completed the request. Record actual delivery/receipt. If the laptop or its AG is unreachable, report that exact access blocker without guessing its state and continue independent authorized desktop work.

Obtain the laptop's original retained task definitions and actually used entry scripts, the transitive project modules/configuration needed by those entries, dependency specifications, and the existing command/run records identifying the last demonstrated working version. Include the actual download request semantics (dates, fields, adjustment/PIT), pagination, checkpoint/resume and revision behavior, then cleaning, validation, compilation/publication order and local query/backtest bindings to the extent they really existed. Reuse existing manifests and logs; identify absent or unproven capabilities honestly. Do not demand new broad inventory or a narrative reconstruction in place of executable source. Do not export credential contents; preserve bindings to local credential locations.

Make these files directly available to the desktop through the existing share or a compact source/config handoff. Reference them in the SAME consolidated package already requested; do not wait for GPT to approve every source file. Prefer reuse of the original implementation and established semantics over reimplementation. Compare the desktop differences that matter: drive/path mappings, Windows user/runtime, compatible dependencies, source/release locations and invocation configuration. Preserve valid current desktop fixes and unrelated work; no blind overwrite or migration restart.

Validate the adapted original workflow on retained real data in the already authorized isolated candidate context. Existing successful laptop run records establish only their recorded scope; file presence or a last-asof label is not proof that every old capability worked. If backtesting existed only on JoinQuant and no local provider existed, say so and complete only the necessary desktop adaptation rather than inventing a historical local implementation. Keep unresolved original defects visible; copying the source does not certify its completeness.

Do not interrupt an active safe run or restart uploads to perform this correction. Use the source workflow for remaining work as available. The completion deliverables and stopping conditions do not expand. New supplier acquisition, production CURRENT switching and orders remain unauthorized.

## Outcome and authority

The owner rejected the repeated source-export / component-review loop and requested a concrete completion solution, then sent HUB to proceed. This is the consolidated execution instruction for the existing R10 work, not another inventory round.

Build and actually run the local system using existing data. Work continuously through local inspection, implementation, meaningful tests, diagnosis and repair. Submit a consolidated real execution result for independent GPT review. Do not ask the owner to select among coverage measurement, reconciliation and cursor binding, transfer source text, run commands, or manage individual steps.

This instruction supersedes earlier GPT task-specific restrictions that limited R10 to inert source export, prohibited local business-code repair, or prohibited offline engine construction/backtest and existing-data transformation. Those operations are now authorized within the isolated scope below. Applicable substantive data contracts, required task preflight, source preservation, PIT requirements, claim guards and publication/acquisition restrictions remain in force. Do not weaken assertions or fabricate a certificate to obtain PASS.

If the five-source handoff is unfinished, use those files directly during integration; do not finish a source-export-only detour first. Reuse any work already produced. Do not run duplicate workers against the same candidate or relaunch accepted old suites merely to create a new receipt.

## Fixed scope and preservation

1. Dataset scope is the 54 entries of the existing ECOLOGY_REGISTRY_R3.json at E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\, enriched with later accepted R04–R10 evidence. Keep the 41 operating-catalog products and old 75-item inventory as separate denominators; map existing identities explicitly rather than equating their counts.
2. Old SYSTEM_INVENTORY completion_1814 is closed. Reuse its 26-domain path checks, 1803 comparisons and D1–D5 dispositions. Do not redo migration, global filesystem inventory, old full-year factor comparisons or already accepted source-batch equality.
3. Original RAW, sealed CLEAN/CACHE releases, published ledgers and CURRENT pointers remain unchanged. Work under E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\ with versioned candidate data and code. Never edit a hard-linked source inode through a candidate path: copy changed files to independent files first.
4. Inspect actual local dependency bodies as needed for the three deliverables; per-file GPT permission and source handoff are not required. Record relevant code identities and diffs. Read local AGENTS/must-read contracts and execute the genuine applicable preflight. Do not bypass a substantive data constraint.
5. Repair candidate code and the supported offline operating path, provider integration, runtime/logging paths and transformation orchestration as needed. Back up changed ordinary workspace code, preserve unrelated work, and record exact changes. Prefer explicit candidate/runtime binding over changing shared production defaults.
6. Use the existing recovery runtime, fixing only dependencies needed for this task. No model installation, new vendor selection, account/auth change, credential export, paid-source request or supplier quota use. Existing local configuration may be bound without exposing secrets; prevent imports or default constructors from making external data or order calls.
7. No new supplier data acquisition, live provider calls, real account connection, historical deletion/overwrite, CURRENT change or production release. Legacy P7 acquisition guard remains in force. Offline candidate publication tests may write only candidate pointers inside this task directory.

## Deliverable 1 — current data state and defensible update basis

Create one current dataset matrix from R3 plus subsequent accepted evidence. The R3 snapshot is not the final state: later source/CLEAN comparisons, restored candidate dates and factor-basis results must be incorporated with their exact scope.

For all 54 entries record identity, layer/path/version, temporal or non-temporal role, observed range, relevant known gaps/conflicts, accepted evidence references, actual consuming/updating entry and current readiness. For absent evidence use explicit UNKNOWN/BLOCKED, not an invented range or a missing-source claim.

Only measure the remaining unanswered scope. Reuse valid observations where file identities still match. Read footer statistics first for range questions; where statistics are insufficient or key-level reconciliation requires values, read only the relevant columns/partitions. Min/max is an outer bound, not a completeness certificate. Keep daily, minute, snapshot, event and non-temporal semantics distinct.

Reconcile RAW -> CLEAN -> CACHE for the unresolved intervals/products that affect this delivery, especially the recorded August/September gaps. Distinguish upstream valid observations, transformation omission, source rows with unusable dates, revisions and unresolved expected coverage. Repair consumption/derived candidate defects using existing authoritative input where possible. Do not infer dates from names, fill unknown prices/status/factors, extrapolate historical constituents, relabel total-return/pre/raw bases or convert UNKNOWN into zero.

Bind each applicable dataset's incremental plan to its actual writer, validated local state and update semantics. Record separate observed maximum, last demonstrated complete unit and downstream processed boundary. An unknown historical expected universe cannot be supplied by a current code list. June COMPLETED, a stale raw_coverage_ledger, file names, asof labels and a null registry field are not authoritative cursors. Where no safe start/revision overlap can be established without external evidence, record the specific blocked predicate and required input; do not guess or reset a checkpoint.

No all-dataset common start of 2026-09-24 is permitted. Non-incremental/non-temporal entries may be explicitly NOT_APPLICABLE with their existing contract cited. A proposed acquisition plan is not executed acquisition and is not authorization.

## Deliverable 2 — real local queries and the original engine

Connect the existing local data provider to the original engine and supported query entry in an explicitly bound offline candidate context. Fix actual code/runtime defects; an import-only probe or synthetic replacement engine does not meet this deliverable.

Run real queries across the registered data families supported by the existing contracts, including required multi-field and historical reads. Report every family/product as exercised, blocked, or contractually inapplicable; do not generalize one stock read to the whole system. Required empty virtual-view members must remain explicit blockers rather than returning only a populated member.

Use an existing documented strategy artifact and its existing configuration, recording its identity. Run the ORIGINAL engine through an actual completed offline backtest on existing real data within demonstrated support. Do not silently narrow its securities/date range, change strategy rules, replace required fields, or use a simplified demonstration engine to manufacture success. If its documented request exceeds supported inputs, retain that failed request and exact reason; an explicitly labeled diagnostic run may help repair but does not replace the requested run.

Bind calendar, adjustment convention/anchor, tradeability, historical universe, PIT/availability time, units, matching assumptions and source generation wherever the existing engine/strategy requires them. Preserve existing rules for unknown or unavailable observations. Separate actual engine execution from GPT formal admission: a successful candidate backtest may be submitted for admission; the local AI cannot self-certify whole-foundation acceptance or trading permission.

Write all engine logs/results under this task scope. No brokerage/live order adapter may be activated.

## Deliverable 3 — connected update/cleaning candidate using retained real batches

Integrate the accepted date/index response gate, coverage/error propagation, factor refresh assembly and pagination controls into the ACTUAL applicable writer/transform path, not only standalone helpers. Implement proper failure propagation through cleaning, anti-leak validation, cache compilation and candidate publication.

Read the real finance adapter, publish gate, index-minute align/anti-leak, R15 cleaning/anti-leak and compiler code locally as needed. The abandoned five-source handoff is supporting material, not a prerequisite export round.

Replay retained genuine local response/source batches through the connected path, substituting only the external transport with a clearly identified local replay reader. Preserve response date/index semantics and real batch provenance. Synthetic negative controls may supplement this replay; they cannot replace it or establish upstream completeness.

Demonstrate:
- malformed dates, failed/short batches and unproven coverage stop before merge/publication;
- valid index dates survive serialization, and an existing partial day is not silently skipped;
- dirty-history replacement retains other securities' new-day records and does not truncate valid historical keys;
- factor-basis checks follow the actual contract and do not treat physical fq-column absence as a violation where the contract does not require that column;
- relevant replay/checkpoint consistency and idempotence: rerun on the same retained inputs creates no duplicate keys, lost accepted observations or drift;
- failed execution leaves the last valid candidate readable. Test the actual candidate commit protocol, including paired-registry consistency where applicable; do not claim multiple atomic replacements constitute a transaction.

Do not advance any production acquisition cursor or publish CURRENT. Record retained-batch limitations explicitly. If a required real batch/input is not available locally, name it precisely and keep the dependent assertion BLOCKED.

## Acceptance and stopping conditions

Acceptance scope is fixed to the three deliverables above and the existing user's five requirements / B1–B7 obligations; do not add unrelated optimization, redesign, new data families or historical forensic investigations.

Update B1–B7 individually from their existing definitions and later evidence. For each open item identify the concrete failed predicate, affected deliverable, actual repair attempted and remaining input. Previously resolved evidence questions remain resolved within their measured scope; no arbitrary new PASS certificate is required.

Continue independently through repairable local code/runtime issues and rerun only affected meaningful checks. Do not stop at a source-export report, a plan, an import probe or another isolated test suite. Do not change tests to mirror faulty implementation.

Stop the relevant dependent branch if it requires unauthorized external acquisition, a substantive business-rule decision, destructive source change, unavailable authoritative input or user-only credentials. Continue independent authorized branches. For a repeated unchanged failure after an attempted fix, provide a specific new diagnosis before further retries; do not rerun the same command indefinitely. A genuine blocked result is acceptable reporting, but it is not project completion and does not authorize downloads.

Stage 1 is submitted as READY_FOR_GPT_REVIEW only when its applicable predicates pass; otherwise submit BLOCKED with exact actionable failures and completed work preserved. FOUNDATIONAL_ACCEPTANCE and FORMAL_ENGINE_ADMISSION remain false pending independent review, regardless of local test counts.

Stage 2 is a subsequent GPT-issued scoped acquisition task AFTER GPT accepts all prerequisite foundation/acquisition/cleaning checks. The owner has conditionally authorized missing incremental download and cleaning, but this task does NOT activate that authorization. Do not download automatically after local PASS. Final project completion additionally requires the authorized acquisition/cleaning results and real query/backtest regression to pass review.

## One consolidated handoff

Deliver to:
local: E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\
HUB: agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/

Keep the handoff practical:
- REPORT.md: what now runs, exact supported scope, failures and stage-1 verdict;
- DATASET_STATE.json: all 54 entries, coverage/reconciliation/update basis and reused evidence;
- ACCEPTANCE.json: the three deliverables, existing five requirements and B1–B7, evidence per predicate, independent-review flags;
- actual changed ordinary code/diff and a code/artifact identity index; reuse unchanged HUB sources by reference;
- exact commands, timestamps, exit codes and raw stdout/stderr for meaningful integration/query/backtest/replay executions, including failed attempts and relevant regression outcomes;
- operational guide with the actual runnable commands, candidate paths and rollback/restore instructions.

Do not upload market parquet or credentials. Use one payload manifest excluding itself and one final remote readback; avoid recursive self-hashes, repeated upload cycles and per-source handoff packages. Do not duplicate already accepted payloads. Update the established INBOX_FOR_CHATGPT.md with this task ID and actual result. If long-running, append a concise real progress checkpoint in this same directory stating completed/active/blocked work; a progress checkpoint is not an acceptance result and is not a request for another microtask.

No A/B/C technical-choice prompt to the owner. After completed handoff/readback, Cursor chat final response exactly END.


## Execution clarification after restart_readiness_review — same task, no new round

The 2026-10-25 07:22:44 desktop retrospective was received. GPT read ENVIRONMENT_PROBE.json, GATE_PROBE.json, RESTART_READINESS_VERDICT.json and CORRECTIONS_APPEND_ONLY.json directly from HUB. This is a targeted review of those records, not independent certification of every scan or the complete payload.

The retrospective is not execution of this completion task. Its pending-tip statement is stale: the exact-runtime five-source handoff has been superseded. Fetch this entire current canonical task before continuing. Do not ask the owner to choose environment repair versus five-source export.

Execution order:
1. Establish a working local runtime first. ENVIRONMENT_PROBE itself reports the existing recovery runtime at _OPS\FOUNDATION_RECOVERY_20261024\runtime\.venv\Scripts\python.exe, with pandas/pyarrow/numpy. Validate actual imports and entry execution there and continue the integrated work immediately where it works. The broken root .venv is not evidence that no usable runtime exists. Record any additional actual dependency failure. For standard root command restoration, rebuild the venv against the installed Admin interpreter with the project's compatible dependency specifications, preserving the old environment and unrelated work; do not rely on changing pyvenv.cfg home alone as a complete portability fix. Required ordinary runtime dependency installation is permitted; supplier auth/data calls remain prohibited.
2. Continue the three existing deliverables locally: current dataset state/update basis, actual queries/original offline engine, retained-batch transformation and candidate-publication replay. Do not stop after interpreter repair or another readiness retrospective. If V4 requires a local port, use its exact retained source/config and preserve algorithm semantics; identify unresolved API/PIT dependencies rather than replacing the strategy with a demonstration.
3. Submit real execution progress and the consolidated final package under end_to_end_completion. If the V4 formal request is blocked, preserve its actual failed predicate and continue independent authorized dataset/replay work. A diagnostic run remains diagnostic.

Interpretation corrections to carry in that same consolidated result:
- Preflight ALLOWED proves the preflight check passed, not supplier/download authorization. "Single day can run" is unproven until the integrated candidate path is actually exercised; the three proposed fixes are not a proof of full readiness.
- Do not derive every dataset's cursor from CURRENT 2026-09-24 plus a calendar. Use the per-dataset valid/completeness/revision evidence required above. The 31-day difference is calendar age, not 31 missing trading sessions or a proven missing range.
- With CURRENT_SWITCH_ALLOWED=false, publish_atomic may only be exercised against isolated candidate pointers. Calling the production publish function against real CURRENT is prohibited.
- Import-level binding establishes a source dependency, not successful invocation, failure propagation or transactional publication. Prove the relevant actual candidate behavior with retained batches.
- Lane NO_RECORD_CONFIRMED/0 rows is not by itself proof that the supplier had no relevant records or the sole explanation for empty required views. Record the measured request/result scope; no new supplier-absence certificate is implied.
- Reuse later accepted R10 evidence when reconciling B1/B4 and other blockers. The 83,503 count difference alone is not data loss, and factor raw-value differences alone are not adjusted-price differences. Keep content equality, factor-ratio equivalence, lineage and expected coverage as separate predicates. Keep existing candidate-restored dates separate from mounted CURRENT gaps.

No additional full-disk search or repeated five-source export is required by this clarification. No new acquisition, production publication or trading authority is granted. The sole active task remains BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025.


## GPT interim review of the 08:46 delivery — continue this SAME completion task

Reviewed directly on HUB: REPORT.md, ACCEPTANCE.json, PACKAGE_INDEX.json, DATASET_STATE.json and CANDIDATE_REPLAY.json. The payload is still arriving; this is an interim content review, not a full byte/readback or runtime certification. Finish the current single upload; do not restart it or duplicate unchanged outputs.

The reported overall PASS is not accepted for stage 1. Preserve completed work and classify the current result as BLOCKED / partial execution, with the 16-session run DIAGNOSTIC_ONLY. This does not reopen the completed inventory or require another source-only handoff. Continue the same three deliverables below within their existing authority.

1. Real engine/queries: the reported 14 ambiguous-NA errors and two missing-limit warnings mean required V4 steps did not execute normally. Engine COMPLETED and zero future-data interceptions cannot certify strategy/PIT correctness. Keep these failures visible and make missing required input fail the requested run rather than silently skip strategy logic. Use existing authoritative local RAW/CLEAN/candidate inputs to restore tradeability/status where supported; the retained replay batches themselves include paused/high_limit/low_limit. Check the relevant already located inputs, without a new all-disk scan. Do not infer ST or historical universe, fill unknown values, or assert supplier download is necessary solely from the CACHE maximum. If the required authoritative local inputs truly cannot satisfy the request, mark that branch BLOCKED with the exact missing product/field/interval and continue independent work. Preserve the original strategy source/config, map any port/wrapper identity, and document whether actual fill timing/prices follow the retained engine/strategy contract. A 16-session diagnostic is not a substitute for the documented requested backtest scope.

2. Dataset/update basis: the current matrix reports 37 readable-but-cursor-blocked datasets, three blocked datasets, and 40 NOT_BOUND cursors. This remains deliverable-1 work, not a passing update plan. Implement/validate local candidate checkpoint and resume bindings where the retained writer/batch evidence supports them; keep unsupported starts explicitly blocked rather than ask the owner to invent dates. Repair specific matrix classification errors using the measured schemas, without rerunning the full inventory: CALENDAR_CN_EXCHANGE contains calendar_date yet was labelled NO_TIME_AXIS; ROOT_ABSENT / no admitted FACTOR_VALUE product does not by itself establish contractual NOT_APPLICABLE; UNDETERMINED_SCOPE remains unresolved unless its exclusion has an actual controlling definition. Reuse valid existing measurements and accepted R04–R10 evidence; distinguish product-specific bounds from shared-root samples and restore index date semantics where applicable. Do not generate a new completeness claim from footer extrema.

3. Connected retained-batch pipeline: CANDIDATE_REPLAY.json demonstrates reconstruction/comparison of 10,426 rows for two dates. It does not yet demonstrate the full previously requested actual writer-response gate -> cleaning/anti-leak -> compiler -> isolated publication/resume path, nor its failure propagation/idempotence. Continue that existing integration using the actual applicable code and a local transport replay. Reuse the accepted component controls and the successful two-day reconstruction. Add only the affected meaningful integrated checks already required by this task; no repeat of all old suites or source-export detour. If the necessary retained response/provenance does not exist locally, state the exact dependent assertion as BLOCKED; do not replace it with synthetic success.

Consolidate the results into the SAME package and existing B1–B7/five-requirement acceptance map. Supply the already requested changed provider/wrapper/replay code or diff, runnable guide, exact commands/exit codes/raw logs and genuine engine artifacts as part of this package, without uploading market data or credentials. The current PACKAGE_INDEX names 11 members; upload in progress is not a missing-file verdict. Do not claim the complete package has been independently verified until its members and final readback are present.

Stopping rule unchanged: finish repairable local integration and submit one honest completed-or-blocked result. Runtime repair and actual execution are progress worth preserving. Do not stop merely because the diagnostic engine returns exit 0, and do not expand into unrelated investigations. No new acquisition, CURRENT switch, production publication, live account or order authority is granted. The owner is not being asked for a technical-step choice.


## Artifact review after the remaining indexed logs arrived — same task

Read agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R10_END_TO_END_20261025/ARTIFACT_REVIEW_1006.md with this task. All eleven indexed payloads now match their byte counts and SHA256; this does not constitute final handoff or stage-1 acceptance. RUN_RESULT records positive paused_rows_inferred_from_bar_presence in 75/80 observations and five minute requests using INTRADAY_OPEN_PROXY. Apply the existing no-invented-status/original-execution-contract requirements to those exact observations. Preserve the original diag=false/PASS outputs as failed historical labels and return corrected current classification with the already-requested provider/wrapper code and actual outcomes. This review issues no new executable command, test rerun, source-only task or supplier permission. Do not interrupt an active process or restart the upload. Continue the same completion task and finish one consolidated handoff; Cursor final remains exactly END.


## 双机合并审阅 — SAM 原件已到，继续同一任务（2026-10-25）

本段是同一完成任务的最新纠正，优先于此前“恢复原本地股票引擎”等不符合源机事实的描述。两边材料已经到齐，不再等待源机、不新增盘点/源码导出轮、不重跑已通过且未受改动影响的检查。

### 已核实并保留的成果

GPT 已读取 SAM 的交接说明、适配说明、运行记录和 SOURCE_INDEX；从 HUB 获取 ZIP，实测 567589 bytes，SHA256 bdfafc3122266eff9005215949401d685739a29503c5807f6c0477d41b41d89d。解包后逐项核对 90 个代码文件及 28 个配置文件，118/118 长度与 SHA256 一致。原 V4 策略 SHA256 为 8d9334dd6ed2053b6cb297ea5780408c106c9cf2e0b7138629685e4f589d992e，与台式机 RUN_RESULT 一致。这里只认证原件身份，不认证源机报告中的每项运行能力。

交接位置：
- HUB: agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/source_workflow_sam/
- SAM 已提供共享目录（按 DELIVERY_NOTE 的实际 UNC 读取）；若不可达，直接使用 HUB ZIP。
ZHANGWEI 记录实际接收和使用的原件。保留已恢复的可用环境、provider 修复、真实批次与已通过结果；不重建整个环境，不盲目覆盖原件，尤其不能以源机 2B 空壳覆盖已有实现。

GPT 同时读取了台式机 R12 报告、验收矩阵、RUN_RESULT、CONNECTED_PIPELINE 以及 provider、engine wrapper、replay script 的完整源码。此次未宣称整个台式机 34 成员包均已完成独立字节核验，亦未准入其收益。

### 合并判断与本次仅需处理的三个差异

1. **源机流程复用：完成实际调用链，停止用替代脚本证明原流程接通。**

源机源码确认 Lane A 的 blackbox_full_data_update_scope_refresh_r1.py 从 CLEAN/CACHE CURRENT 派生摘要并写 scope，它不下载。“SOURCE_ASOF 等于 CLEAN_ASOF 等于 CACHE_ASOF”不能独立证明下载完成。该程序也不是纯只读，不能照交接说明直接在生产区试跑；六 Lane 的其他分支会采集，禁止为了验证 A 启动全部 INGEST。

台式机 tools/run_connected_pipeline.py 没有导入/调用原 writer、R13/R15 cleaning、原 cache compiler 或 publish gate：response_gate、clean_and_antileak、merge/compiler、checkpoint、publisher 均在新文件自行实现。它使用真 RAW 的结果值得保留，但不能标成“只替换了外部 transport 的原链路 PASS”。其中 factor_refresh 仅检查 code/factor 列存在，未证明原复权刷新或真实分页接入。

现在使用已到的 SAM 原件和台式机现有生产源码，按实际当前入口选择原 writer/cleaner/compiler（源机 R13 不应机械覆盖台式机 R15）。只对本次调用需要的环境和路径作候选适配，保留真实函数体，接入本地 retained transport；API 网络、生产默认输出及 CURRENT 写入必须隔离。原 tip compiler 已提供 --cleaning-json / --parent-root / --out-root / --no-publish，优先使用其原有候选入口；检查并重定向其日志等其他写路径，不能只看 --no-publish 就认定无副作用。对没有候选参数的原件作最小路径/依赖注入，不复制业务算法再以同名阶段冒充。

复用已有 08-31/09-01 两批及原有负向控制，完成原函数实际执行、失败传播及重复运行。若 retained 输入无法覆盖某个原函数，精确标 BLOCKED，不重开全库调查。可复用已经验证的输入，不再要求 owner 传源码。

2. **V4：认清本地移植，去掉未经支持的数据替代。**

SAM 的原 V4 在聚宽云端，没有可直接复制的本地股票引擎。现有 BulletTrade + adapter 是本地移植候选，应保留；纠正“原聚宽引擎恢复/跑通”的表述。不得拿可转债引擎替代 V4 来交付，也不要求 owner 因此重新选择技术路线。

R12 的 input_blockers=[] / diagnostic_only=false 不能作为语义通过：
- provider.py:518–571 把 ADJUST_FACTOR_PIT_R1 解释成 event-ish，使用 ffill/bfill 并对无因子的代码回退 1.0；与已核实的 DAILY_DENSE 契约不符。此前稀疏物化不能自动变成事件序列。必须使用已有权威同日因子或已证明有效的修订/基准关系；缺证时明确阻断相关复权请求，不能 bfill 未来值或将未知回退为 1。
- provider.py:680–694 仍将未知 paused 填 False；RUN_RESULT 的 80 条观测中仍有 4 条正的 paused_rows_inferred_from_bar_presence。严格模式不得在空值检查前先填成非停牌。
- provider.py:698–726 对盘中请求以当日 open 替换 high/low/close，并以前一日 volume/money 替换当日值；RUN_RESULT 有 11 条 INTRADAY_OPEN_PROXY 观测。没有未来数据并不等于保留原策略的盘中价量和成交语义。需要分钟输入的请求使用已有真实分钟源；没有相应输入则该请求明确 BLOCKED，代理模式只能显式诊断。
- get_all_securities(date) 实际返回 08-12 单一 snapshot 且未按请求日期过滤；is_st 仍未知。只对策略真实需要的历史股票池和 ST 过滤建立权威绑定，不能忽略参数或豁免字段来获得正式通过。已知不足保留为具体数据依赖。

修复后由实际输入、API/调度/撮合语义决定分类，不能由 --diag=false 决定能否准入。真实引擎已执行16日是成果；2笔成交和零空值告警不能证明策略等价。无需为改变标签重跑长回测；仅在实际逻辑修复且必需输入满足后重跑受影响窗口。缺权威输入则提交确切产品/字段/日期及已查来源，不无限重试，不宣称正式收益。

3. **候选提交：保证失败后上一次结果仍可读。**

run_connected_pipeline.py:382 将新分区直接写回 ACCUM_PART，随后先写 checkpoint，再顺序替换 pointer/registry。异常发生在分区覆盖、checkpoint 或第二个指针替换期间时，旧指针可能已指向被改写数据或与断点不一致。现有“提交前拒绝坏批次”检查并未验证这个失败点，不能证明整个提交过程安全。

在上项原调用链的同一候选适配中修复，不另造发布系统：将每次结果写为独立候选版本，完整验证后由单一权威提交引用或可恢复的原协议切换；checkpoint 与所提交的数据身份一致。只验证这条实际候选提交的中途失败/恢复，以及同输入重放和有修订输入续跑的行为。不要触碰生产 CURRENT；不要宣称两个 os.replace 是跨文件事务。

### 收敛与停止

以上均为原任务已有“原流程复用、禁止未知补值、真实链路、失败不损坏上次候选”的具体失败，不增加第四项交付或新数据域。技术步骤由本地连续执行，不再向 owner 发 A/B/C 选择，不再提交仅源码或准备度报告。

结束时沿用同一 package，给出：实际复用的原函数/路径及必要改动；原流程候选运行的真实命令/日志和进程退出码（不要由 COMPLETED 反推退出码）；V4 本地移植的实际支持范围/未满足输入；各原有阻断的具体状态。保留失败证据和原 R12 标签，不覆盖历史事实。不能修的分支精确停止，独立可修分支继续，完成一次集中回传。

“未做最新下载”和“生产 CURRENT 未切换”是本阶段授权边界，本身不能循环当作本阶段必须先执行的修复。分别列清候选能力是否验证、数据/语义是否满足、后续生产动作是否尚未授权。不能通过这一区分抹去真正的数据或采集前置缺口，也不能自启第二阶段。禁止为了等全库更新而重做迁移或扩展调查。

NEW_DATA_ACQUISITION_AUTHORIZED=false；CURRENT_SWITCH_ALLOWED=false；ORDER_ALLOWED=false。
FOUNDATION_ACCEPTANCE=false；FORMAL_ENGINE_ADMISSION=false，等待独立审核。沿用现有任务 ID；无新轮次。


## Owner clarification — 整个底座运行链路交接，非仅9月24日更新（同一任务）

执行分工：SAM 补齐源机实际运行关系；ZHANGWEI 继续现有修复并直接复用。owner 指出需要整个底座的运行链路；GPT 上次只列最近一次更新记录，表述过窄。9月24日只是端到端证据样本，不代替全底座的入口/调用/消费关系。本段补齐原任务已有整体流程交接，不增加新数据域、全库盘点或新轮次。

SAM 在已有 source_workflow_sam 交接包补一份 FOUNDATION_RUNTIME_MAP.md，直接引用已交118件和现有 meta/PIPELINE_STRUCTURE.json、CODE_SEMANTICS.json，不重新打包已有源码。按真实入口列分支，覆盖既有范围：
- 启动入口、工作目录、运行时、规则/字典/权限预检及配置加载；
- 原始采集/下载、分批分页/断点、清洗/校验/封版、缓存编译与发布；
- 数据解析/查询如何实际读值，研究/选股/策略/回测分别怎样调用数据和字典；
- 研究结果/名单/报告的输出位置与下游使用者，日增触发、失败停止、续跑与恢复。
实际并行或独立的分支分别说明，不强行画成单条自动流水线。聚宽云端、本地、人工/AG串联、未实现部分明确区分；不要用“原来可用”代替证据。迁移/MWB/模型安装等无关工作不在本次交接范围。

每个入口/调用边只需写清：
实际文件与函数或命令 → 参数/配置 → 输入数据/版本指针及路径 → 输出 → 谁消费 → 调用是代码自动完成还是人工/AG触发 → 最近已有运行证据或未验证状态。
对规则/字典说明实际读取点和约束；文件存在但无人读取须如实标注。源码引用现有索引身份，不制造一批重复哈希回执。

附最近一次已有成功或部分成功运行的原命令、必要临时脚本和原始日志，重点定位生成现行 R45/R33 及 tip cache 的实际调用。只有摘要的写“仅状态摘要”；未保留命令/日志的写“未保留”，不得据此推断没有发生，也不能重跑来伪造历史证据。只补实际被调用而当前包确实未含的源码及必要配置；凭据内容不导出。

这是静态/既有记录交接：使用已知源码、配置、任务及日志目录，不进行全盘扫描，不调用任何可能采集或改写生产摘要的 status/daily_incremental 命令，不下载、不清洗、不切 CURRENT、不下单。不要求重建不存在的本地V4引擎。

收尾标准固定：已有实际入口与它们的调用/数据消费/输出关系均有落点或明确的断边/未保留说明；交付一份可供台式机照着运行和排错的现状图表，不是设计未来系统。到此结束源机本项交接；不因历史记录未保留继续取证循环。直接放同一共享/HUB目录并在原笔记本回执标明新文件。台式机无需停下来等待，原已授权的候选修复继续。所有下载、CURRENT与交易限制不变。
