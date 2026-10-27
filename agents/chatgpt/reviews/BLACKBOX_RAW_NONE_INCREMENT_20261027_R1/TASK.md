# Bounded RAW_NONE forward increment: desktop execution contract

task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R1
parent_task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
execution_host: ZHANGWEI
historical_evidence_peer: SAM
status: READY_FOR_ONE_NATIVE_GATE_AND_ONE_GUARDED_RUN
ORDER_ALLOWED=false
CURRENT_SWITCH_ALLOWED=false
PRODUCTION_CLEANING_ALLOWED=false
PRODUCTION_RAW_WRITE_ALLOWED=false
SUPPLIER_ACTION_ALLOWED=ONLY_THE_EXACT_ENDPOINTS_AND_BOUNDS_BELOW

## Owner authorization and independence

The owner explicitly requested dispatch of the revised bounded first-round plan on 2026-10-27 after GPT provided existing HUB evidence. This authorizes this concrete desktop-only task. It does not authorize stopping the desktop AUTOHUB task, blanket foundation PASS, historical chain execution, password changes, publication, or a permanent downloader. Do not ask the owner to choose a host again. SAM does not run this task and must not authenticate concurrently.

GPT independently read the captured original daily writer, registered R04 acquisition matrix (including the P8 ETF root), R07 cross-layer ledger, R10 RAW status inventory, desktop captured pointers/staging/replay sources, seven RCID counterexamples, and original supplier SDK source. Evidence identities are in EVIDENCE.json. This is acceptance of this **isolated append-only RAW_NONE acquisition path and its required prerequisites**, conditional on the native checks below. It is not acceptance of the broken commit implementation or every historical dataset. The seven RCID defects remain assigned to GPT's publication-path work; no local AI may repair or bypass them. They do not gate this isolated RAW staging operation because this operation never calls commit or publication code.

No repeated source collection: V3 fixtures, capture_003, chain_source_001, source_closure_001, watcher checks and SAM log extraction are complete in their bounded scopes. Preserve their failures, partial outcomes and receipts. Historical unproven Research OS effects and PARENT_ID bytes remain recorded unknowns; do not run them to investigate.

## Exact product and supplier contract

- Supplier/namespace: JQData / JQ_OFFICIAL_RAW. No non-JQ writes or namespace substitution.
- Products: PRICE_STOCK_DAILY, PRICE_ETF_DAILY and PRICE_INDEX_DAILY. The index universe is ONLY the original seven: 000001.XSHG,399001.XSHE,399006.XSHE,000300.XSHG,000905.XSHG,000852.XSHG,000016.XSHG. It is not all indices.
- Dependencies: get_trade_days for the actual CN session set; get_all_securities(types=['stock'] or ['etf'], date=d) for the daily universe, including start_date/end_date lifecycle receipts. These are allowed supporting metadata, not authority to update production calendars/security masters.
- Callable: jqdatasdk.get_price with security=list of at most80, start_date=d,end_date=d,frequency='daily',fields=[open,high,low,close,volume,money,paused,high_limit,low_limit,avg,pre_close,factor],fq=None,panel=False,skip_paused=False,fill_paused=True.
- RAW_NONE_DAILY_12_R1 dictionary: preserve all twelve supplier numeric fields, original dtypes and nulls; stable comparison key is (calendar_date(time),code). Price basis RAW_NONE. volume and money are the unconverted supplier units; no scaling or local adjustment. factor is retained as received and never used to adjust prices or certify factor splice/PIT. paused must be a measured supplier 0/1 observation. Local fills, dtype coercion, key aliases and duplicate suppression are forbidden.
- fill_paused=True explicitly preserves the documented existing supplier default; it is not a local forward-fill instruction. Preserve and disclose supplier-paused observations separately. Missing keys remain BLOCKED; do not invent a suspension/listing exclusion after the fact. Preserve any failed response.
- Exhaustion: the reviewed get_price endpoint has no page cursor for this finite single-day request. Every requested key must occur exactly once; returned keys outside the request, missing keys, duplicate normalized-day keys, numeric ordinal dates, missing fields, nonfinite values, unknown pause states or live-bar core nulls block the run. Small batches alone are not a completeness certificate. The old 5000 guard is not declared a universal supplier limit and is not removed from any old source.

## Forward range and pre-acquisition prerequisite gate

The maximum allowed requested date is 2026-10-27. This task expires at 2026-10-28 23:59 CN; a later continuation needs a new reviewed range, not a local edit. The observed September24 boundary is scoped to these retained inputs; it is neither a universal historical start nor a permanent CURRENT cap.

Before any login or supplier call, the supplied script:
1. Requires actual Windows host ZHANGWEI, exact E:\BLACKBOX root, and an absent exclusive output E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R1.
2. Rehashes FOUR actual desktop pointer/manifest bodies against their capture_003 or reused-original SHA256. A changed byte stops rather than rolling back/rebinding/replacing any production metadata.
3. Uses the retained layer search as context and checks only registered stock/ETF/index RAW roots (including P8_etf_fund), corresponding current CLEAN/CACHE product roots, dated releases newer than September24, and the registered strategy_data_plane_additions. This is a scoped time-axis/coverage freshness check, not a new global inventory or a request for old source bodies. It writes no original data.
4. Reads Parquet date-axis footer bounds; where absent, a single date-column read is bounded to256 MiB source bytes/2million rows. Integers are not reinterpreted as dates. Unhandled data formats, missing roots, cycles, permission/read errors, 50,000 physical Parquet files per product or depth8 are explicit blockers, never absence evidence. Non-price schemas are disclosed, not treated as price data. No file is hashed/read in full merely for an inventory.
5. Sets each product's conservative forward boundary to the greatest observed date across its registered price axes and September24. Only later supplier sessions can be selected. Existing data, even if not known complete, is not blindly redownloaded. Historical holes, an overlap day and paid-entitlement probing are out of scope. The old CURRENT date alone cannot authorize a missing-data conclusion.

After authenticated calendar retrieval, sessions on/before September24, beyond October27 or not yet finished at run time are excluded. The reviewed CN cash session boundary is15:30 CN (auction plus after-close fixed-price session); this is **not** a universal supplier publication lag. Actual supplier availability is separately measured by each exact daily response; empty/partial data stops and is not silently replaced by an older day. The session source is get_trade_days, not an unverified substitution of the exchange-link calendar. Maximum75 product-days and2,500 allowed data/metadata calls.

## Quota, authentication and resource limits

Use the existing local noninteractive credential locator only inside this specifically authorized executor: E:\BLACKBOX\配置\secrets\已验证\聚宽账号.txt. Never upload, print, hash, screenshot or include credential values in a receipt. Do not change or rotate credentials. Do not import old business download modules. The reviewed script supports the two existing label/two-line formats and suppresses supplier authentication output. No credential-derived hash is generated.

SDK signature/defaults and API source-file SHA256 are recorded before authentication. Require skip_paused=False/fill_paused=True default identities; an incompatible local API stops without a policy invention. SDK request_timeout=45 seconds, request_attempt_count=1 and enable_auth_prompt=False are set before authentication. No outer or local retries, no multi-host login or child downloader.

The owner-approved measured quota-consumption ceiling is700,000 units for this task, not a percentage of an old account balance. Record actual fresh get_query_count spare before and after every allowed call. Reserve50,000 remaining task/account units before a call; unknown counts, increases/reset, depletion or a measured overrun stops immediately. A client cannot promise a transactional server-side spend limit: the final charge of an unexpected failing call is not cancellable. No further call is authorized after the measured ceiling; report any overrun honestly. Historical16,870 units is a planning observation, not a guaranteed tariff. No probes of sealed paid products.

## Outputs, cleaning and replay rules

Only new files under E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R1 and the C: receipt/package directory may be written. Production RAW, source histories, seals, SSOT/rules, CURRENT, cache, engines and original scripts are read-only.

The script saves untouched supplier DataFrames to new Parquet with their index, reads them back and verifies values/dtypes, then validates the requested/returned keys. Failed payloads are preserved with a quality failure receipt. Every request has a prior request JSON, returned-response quota receipt and key/quality receipt. No automatic resume/replay: if any prior output exists, reuse/report its current outcome and do not launch a second run or delete it. A later GPT task will specify exact reuse of partial staging if needed.

Cleaning/align/PIT transformation in this round: **NONE**. The supplier response and (date,code) validation are preserved; no R15 ingest, align, timezone rewrite, price fill, adjustment, release construction or PIT-publication timestamp invention. receipt_at is acquisition time only. Original R15 downstream load_staging/ingest_item/seal_release and candidate wrappers are already present and will be explicitly bound to these inputs in round2 after GPT audits receipts. Do not execute their historical main functions now. A complete raw staging result is STAGED_UNREVIEWED, never FOUNDATION_PASS or CURRENT admission.

## Exact local execution

First inspect the new task return directory and fixed output for ACK, running invocation or completed results. If already active/completed, report/reuse it without stopping or duplicating it. Upload ACK.json before the native gate. The previous watcher/forensic task is not this task; do not rerun it.

Stage the entire package to:
C:\LAN_SHARE_REPORT\BLACKBOX_RAW_NONE_INCREMENT_20261027_R1\package

Fetch the reviewed files as original bytes from HUB and verify every PACKAGE.json payload length/SHA256. Do not use git line-ending conversion, local patches, aliases, policy fixes or alternate paths. Save PACKAGE_VERIFY.json.

Gate command, once, using the real existing interpreter:

```powershell
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 -m unittest discover -s "C:\LAN_SHARE_REPORT\BLACKBOX_RAW_NONE_INCREMENT_20261027_R1\package" -p "test_*.py" -v
```

Require27/27 tests, zero errors/failures/skips, literal exit0. The tests may create/remove their own OS temporary fixture directories; production E: roots remain read-only. The Parquet tests explicitly substitute the source-path policy for those temporary fixtures; the Windows string-path boundary is separately tested. This is not a new native junction proof (reuse the accepted V3 evidence). Dependencies must already be available. Do not install/upgrade packages, change policy, elevate, skip controls or replace a missing engine. Retain failure and stop if the gate fails.

Only after the gate passes, run ONCE:

```powershell
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 "C:\LAN_SHARE_REPORT\BLACKBOX_RAW_NONE_INCREMENT_20261027_R1\package\acquire_daily.py" --execute
```

Do not pre-create the E: output. Literal exit0 means scoped raw staging finished, still awaiting GPT review. Exit2 means blocker/partial retained; upload it and stop without retry. Any other nonzero exit is preserved as an actual failure, with no invented empty output or PASS. Successful unittest stdout can be empty because its report is on stderr; preserve actual streams as captured.

## Return path and completion

HUB return:
agents/chatgpt/inbox/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/ZHANGWEI/

Return ACK.json, PACKAGE_VERIFY.json, actual argv/cwd/interpreter/start/end/exit and streams for both commands, then every script-written JSON unchanged (BASELINE, COVERAGE, SDK, CALENDAR, PLAN, RESULT, universes, requests/responses, quality or failures). Preserve partial outcomes and explain genuinely uncreated products; do not fabricate empty collector/download logs. The source Parquet stays on the desktop; return its exact append-only path/bytes/SHA256 and the full stable-key/field/null/observation receipts. GPT may request exact selected payload bodies after reviewing the receipts; do not rescan or re-download them.

Also supply REPORT.md, DELIVERY_MANIFEST.json and UPLOAD_READBACK.json with acyclic identity references. Every result file must exist locally, be read back after writing, uploaded, then fetched from HUB and compared byte-for-byte before ending. Keep all pre-existing reports/failed trials untouched. Record applied actions honestly: no production actions are permitted or expected. End the Cursor chat with exactly:

END

## Round2 is reserved, not pre-executed

The owner conditionally authorized GPT to prepare a later reviewed clean/publication task after result acceptance. This contract deliberately contains no runnable CURRENT switch. GPT must audit input/output conservation, dictionaries/provenance, missing/duplicate/null observations, temporal/key coverage, exclusions/PIT, coherent generation, non-regression and applicable admission, and fix the chosen publication path without deleting safeguards. A valid independently scoped product may proceed separately only with its own coherent-generation contract; a failed product cannot be silently dropped while claiming the whole bundle is current. Do not implement the seven fixes locally or replace multi-target publication with an ad hoc atomic pointer edit.
