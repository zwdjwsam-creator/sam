# R05/10: GPT-authored reader/API corrections, bounded source access, and exact gap repair inputs

HOST: ZHANGWEI
PREDECESSOR: BLACKBOX_FOUNDATION_20261024_R04 (including access_resources supplement)
BUDGET_SLOT: 5/10
REMAINING_CYCLES_BEFORE_THIS_TASK: 6
REMAINING_CYCLES_AFTER_DELIVERY: 5
FOUNDATION_ACCEPTANCE: false
ORDER_ALLOWED: false
PRODUCTION_CHANGE_AUTHORIZED: false

## 1. Operator role and fixed boundary

GPT owns the fixes. Execute the exact supplied code and bounded evidence queries below. Do not author provider/updater repairs, invent a clock/adjustment formula, relax a gate, choose a conflicting file, change a credential, or start production workflows. Inventory scripts may collect specified facts only.

Working directory:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024

Read the review and four scripts at:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R04_REVIEW_AND_R05_CODE_20261024_1542/
- REVIEW_R04_AND_R05_PLAN.md
- build_r05.py
- verify_reader_r05.py
- api_boundary_probe.py
- jq_bounded_access.py

Save the exact four scripts under reviews\R05, verify HUB blob identity, and retain their hashes. Do not copy the engine package or old site-packages into the isolated runtime. Reuse the existing dedicated runtime.

## 2. Execute exact candidate changes and offline checks

From the fixed working directory:

```powershell
.\runtime\.venv\Scripts\python.exe reviews\R05\build_r05.py candidate\r4 candidate\r5
.\runtime\.venv\Scripts\python.exe reviews\R05\verify_reader_r05.py candidate\r4 candidate\r5
.\runtime\.venv\Scripts\python.exe reviews\R05\jq_bounded_access.py --selftest
.\runtime\.venv\Scripts\python.exe -m reviews.R05.api_boundary_probe "E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\blackbox_jq_engine\bullet_trade\data\api.py" --adapter candidate.r5.engine_adapter --output-api reviews\R05\api_r05_helper_candidate.py
```

The generator checks exact normalized R04 hashes and refuses an existing destination. On mismatch do not improvise: upload the exact failing source identity and the already-completed independent results. Preserve R03/R04 and original engine files.

Expected independent controls:
- Four reader counterexamples pass (unproved build suppression, unknown footer omission, clipped tail and rank-based conflict).
- Five offline access controls pass.
- Actual API function-path harness demonstrates original admission error -> empty frame, corrected error -> propagated exception, success control -> frame, no factory call.
- The bounded real candidate read may either return a complete diagnostic frame or explicitly reject now-exposed conflicts/coverage. Record its exact outcome; rejection must propagate and must not become an empty success.
- fq=pre remains explicitly rejected.

The generated API copy contains only a helper change, and retains the original module's import-time initialization. DO NOT import it as a full package/module or treat it as an activated engine. The supplied harness executes exact selected API functions with controlled settings/logging and explicit local provider injection. Report FUNCTION_PATH_TESTED, FULL_PACKAGE_STARTUP_NOT_TESTED, MASTER_ADMISSION_NOT_IMPLEMENTED. This corrects a real boundary defect without misrepresenting the test scope.

Do not rerun all historical audits or force the old R03 expected-PASS cases to accept the stricter behavior. No change to original MASTER flags, engine core, source data, CURRENT or R9 state.

## 3. One explicitly authorized ordinary JQ access check

This paragraph supersedes the previous R04 no-login/no-business-query boundary ONLY for jq_bounded_access.py --live below. It does not authorize factor-value, paid-module, whole-table, alternative-provider, trading or bulk download probes.

First inspect package metadata without authentication. If the isolated runtime lacks jqdatasdk, read its exact installed distribution version and requirements from the historical site-packages metadata (not by running the broken historical interpreter). Installing that exact SDK version and compatible dependencies into the dedicated candidate runtime is authorized, using the configured trusted package source. Record versions and pip check. Do not alter global Python, the historical .venv, credentials or engine configuration. If the exact dependency cannot be resolved compatibly, report DEPENDENCY_BLOCKED; complete the other work.

Then execute ONCE:

```powershell
.\runtime\.venv\Scripts\python.exe reviews\R05\jq_bounded_access.py --live
```

This GPT script resolves the documented local JQ credential format itself without rewriting the secret store or executing the legacy downloader. At most:
- one SDK auth invocation;
- one get_query_count metadata invocation;
- if quota shape is valid and spare>=1000, one get_price call for 000001.XSHE, daily 2026-09-24..2026-09-24, six OHLCV/money fields, fq=None.

The 1000 reserve is a conservative operational budget, not supplier pricing or a cost estimate. The script imposes a 45-second child deadline, performs no retry, discards SDK logs and error messages, saves only sanitized metadata at reviews\R05\JQ_BOUNDED_ACCESS.json, and refuses a second attempt if that result exists. No retrieved bar values are saved. A failed/empty/odd response is not NO_DATA or proof of supplier impossibility. Preserve exact stage/status; no local reinterpretation into PASS.

Do not rerun after timeout/auth failure or try another account. SDK internals may issue their own requests; the invocation counts refer to the public calls made by the supplied script, not an assertion of exact network round trips. No credentials or SDK stdout/stderr enter HUB.

A successful result proves only current access to that exact ordinary daily request. It does not establish current Tushare access, every JQ table, all frequencies, full-history scope, factor permissions or the latest update date.

Tushare stays HISTORICAL_ACCESS_ONLY until its own source-reviewed contract is ready. QMT live remains out of this task. No purchases, entitlement upgrades or repeated paid-module checks.

## 4. Resolve the two existing RAW days without re-downloading

Reuse access_resources/ACCESS_EVIDENCE_INDEX.json EV-04/EV-05 and the existing indexes. Read only the exact 2026-08-31 and 2026-09-01 RAW units already found, their sidecars, the active CLEAN release's producer/input manifests, and the relevant stock-daily CLEAN/CACHE bindings.

Return GAP_REPAIR_INPUTS.json:
- exact RAW/CLEAN/CACHE paths and producer inputs;
- RAW schemas/dtypes, row/date/code counts and provenance for the two days;
- observed source adjustment identity, factor/pre_close/paused/ST/limits presence and null counts;
- whether source row duplicates/conflicts exist;
- direct CLEAN/CACHE observation or clearly labelled absence of direct verification;
- exact producer script/functions, input selection glob/list, date filters and release-input records that should have included these units;
- full already-existing producer/helper source and contract bodies needed for GPT to write a candidate repair, reusing identical HUB sources by path/hash;
- comparison with one already-processed adjacent RAW/CLEAN unit to establish the existing mapping, not a new mapping inferred from names.

No new whole-plane scan. Locate through existing file indexes, actual manifest references and explicit directory listings. If the producer reference is unresolved, name that exact edge. Do not claim a root cause merely because RAW exists and CLEAN lacks it. Do not run cleaning, generate a substitute schema, append to the old release, copy rows straight into CACHE, or spend quota to replace existing RAW.

This evidence prepares the GPT-authored cleaning/update repair in R06 rather than asking the user to diagnose it.

## 5. Correct resource/policy interpretation using the supplied review

Preserve original reports; add R05 corrections, not silent history rewrites.

- Known credential location/nonempty file is not live authentication.
- Local dictionary access is not remote supplier capability; split counts by local file access, static configuration, historical supplier proof and current bounded supplier proof.
- Use the dedicated working interpreter in executable examples. Existing package files inside the broken .venv do not make its interpreter runnable.
- Never run blackbox_full_data_update_scope_refresh_r1.py as a read-only inspection. Its full body writes SCOPE and a CURRENT child summary.
- Remove the claim that an old summary HIST_END/asof is the sole runtime target. Actual RUN_TARGET_TRADE_DATE and data readiness rules govern later contracted updates.
- Do not claim CACHE absent only because CLEAN is absent. Attach direct evidence or mark it unverified.
- Do not assert QMT can never supply history based on this inventory; the applicable exclusion is policy, not a demonstrated supplier limitation.
- Retrieval/invocation of the generated helper candidate is not formal engine readiness.

The full AMEND_R3_CURRENT summary records paid-module denials and SKIP_UNTIL_PERMISSION_UPGRADE on 2026-08-13, with do_not_reask_download_each_time=true. Locate and upload the exact referenced existing receipt:
E:\BLACKBOX\运行\BLACKBOX_DOMAIN_PERMISSION_PROBE_CURRENT.json
and the Tushare permission receipt already cited by the source register, if not yet fully available in HUB. This is read-only evidence retrieval, not a new permission probe. Do not call the denials current-day verified.

For factor values and money_flow group: target requirements may coexist with a historically sealed capability exception. Retain target need, historical denial, current access unknown, skip execution pending changed entitlement, and engine admission prohibition as separate fields. Do not repeatedly probe them or erase their target status. An adjustment factor is not a JQ260 alpha factor value.

## 6. One combined delivery

Upload in English to:
agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R05/

Required:
- ROUND_STATUS.json (slot 5/10; remaining after delivery 5).
- GPT_CODE_EXECUTION.json with source/output hashes, commands, exit codes and test scope.
- Changed candidate files and helper API patch identity; do not upload identical old source.
- Sanitized JQ_BOUNDED_ACCESS.json (or exact dependency block), updated source-access rows and evidence corrections.
- GAP_REPAIR_INPUTS.json plus only missing directly relevant full source/contract bodies.
- Existing permission receipt bodies with secrets removed if present; declare any redaction.
- DELTA_REPORT.md identifying demonstrated behavior and exact remaining blockers.

Complete independent branches even if authentication or one source reference is blocked. Do not stop after a directory summary or launch a fresh wait cycle per artifact. No unsupported FOUNDATION_ACCEPTANCE=true.

Update INBOX_FOR_CHATGPT.md so its top latest/bundle/checkpoint actually points to R05; the old R03 top pointer must not remain the primary pointer above appended R04/R05 notes. Preserve historical entries below it. Upload/read back and verify.

All new narratives/comments/status are English; original paths and byte-preserved evidence retain their language. Never upload passwords, tokens, auth headers, cookies, signed URLs, credential contents or secret-dependent hashes. The final Cursor chat response after successful HUB upload/readback is exactly:

END
