# R3 code-dtype repair and exact retained-data continuation

task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R3_CODE_DTYPE
parent_task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R1
execution_host: ZHANGWEI
SAM_role: HISTORICAL_EVIDENCE_ONLY_NO_SUPPLIER_LOGIN
status: READY_NATIVE_63_CONTROL_GATE_THEN_ONE_GUARDED_CONTINUATION
ORDER_ALLOWED=false
CURRENT_SWITCH_ALLOWED=false
PRODUCTION_RAW_WRITE_ALLOWED=false
CLEANING_ALLOWED=false

The owner explicitly authorized the supplied R3 plan and asked GPT to implement and dispatch it. This task is the exact reviewed implementation, not a request for local design. Preserve the R1/R2 packages, original26/27 failure, native39/39 success and actual R2 exit2/partial files. No local AI patches, aliases, guard changes, dependency downgrade, extra login experiment or auto retry. Do not execute the older R1/R2 commands again.

## Independent review and concrete repair

GPT directly reviewed the R2 REPORT/DIAGNOSIS/native gate/run, request/response receipts, retained Parquet/pandas metadata and all three complete registered COVERAGE bodies at source commit ed7900436e60eea4ff2f27c8792685f205e1cba3. The new code starts from the exact deployed R2 body c228138f581afccc204b7adf63b70bef0e0e3a140bcb30ce42606d79e11b633f. EVIDENCE.json and REUSE_PINS.json bind the inputs.

validate_code_column runs before storing an accepted batch. Nulls (including None/NaN/pd.NA), int/bytes/non-builtin-str values, aliases outside the reviewed six-digit .XSHG/.XSHE namespaces, unrequested codes, and unsupported code dtypes are blocked. An invalid response is preserved in the new R3 rejected directory, not admitted or coerced.

compare_code_roundtrip permits unchanged dtypes or ONLY original object -> pandas StringDtype for the code column, after exact element-type/value/order/null/index checks. It restores object on a comparison copy after proving equality and records original/stored representations; it never changes supplier identifiers or uses astype(str) on accepted data. No reverse transition, numeric dtype conversion, unrelated object-column relaxation or blanket check_dtype=False is added. The existing exact s->ms time representation rule is retained; all other fields, values, timezone/null/index constraints remain strict. The fixture and actual acquisition use the same helper.

Reviewer controls:63/63, including the original39 controls plus24 code/reuse/budget/freshness regressions. Both pandas3.0.3+pyarrow24.0.0 and the retained pandas2.2.3 environment passed; exact numpy/platform values and streams are in OFFLINE_TEST_RECEIPT.json. Linux tests are not native Windows acceptance. The actual captured80-row fixture is run through object-code write/read offline. A fake-SDK integration executes the real continuation path and proves the first80 are skipped, first-day universe/calendar are not refetched and cumulative spend includes5320. Test host/path/baseline stand-ins and fake endpoints are explicit, not production bypasses. No real supplier call was made by GPT.

## Allowed scope and exact inputs

Host: actual Windows ZHANGWEI only. Existing interpreter E:\BLACKBOX\.venv\Scripts\python.exe. Workspace E:\BLACKBOX. Do not stop the desktop AUTOHUB task, restart a terminal, kill processes, migrate data or synchronize SAM CURRENT.

Old staging is read-only:
E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R1

New exclusive output (must NOT exist before the one run):
E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R3

Only new R3 output, the C: package/receipts and test-owned OS temporary fixtures may be written. Production RAW/Clean/cache/SSOT/rules/CURRENT, preserved engines and old staging are unchanged. No copies of the retained batch/calendar/universe are made into R3; the reuse manifest records read-only path/length/SHA256 references. The reviewed package includes an immutable Base64 test fixture from the already uploaded batch for offline tests only; this is not a second acquisition or an E: data copy.

Before authentication, require:
1. Four exact desktop pointer body hashes from R2 still match. No rollback, label repair or rebind to manufacture agreement.
2. All10 REUSE_PINS inputs match byte-for-byte SHA256: BASELINE, CALENDAR, PLAN, RESULT, first request, first-day universe, three COVERAGE originals and retained raw. Any drift or missing input stops, never means source absence.
3. Retained raw15544B/SHA2561e0e6bcec4b6d0b819a97693d0aa6d348429bea9fca783ca09e1a2d6f5921631;80 rows/14 fields, exact first80 requested keys, date2026-09-28, no duplicate key. Original code dtype is evidenced by retained pandas metadata. The object-code comparison view is explicitly a metadata-based reconstruction, not a freshly captured original supplier frame.
4. The5222-code sorted first-day universe is unique and its start/end lifecycle covers09-28. The request arguments match the original reviewed fields/flags. The old result establishes actual prior3 calls and5320 consumed units.
5. Reuse the measured17-session calendar and original three-product plans through2026-10-27. No calendar or first-stock-universe supplier call is allowed. No historical backfill or overlap query. The old maximum observed September24 is this bounded continuation checkpoint, not a universal start or permanent CURRENT cap.
6. Reuse the registered RAW/Clean/cache/history/side-plane evidence and R2 time-axis results. Recheck only already recorded parent/file metadata: new Parquet/file/unknown directories, changed price file size/mtime or changed nonprice schema block before login. This is freshness validation of exact registered inputs, not a new global inventory or an absence claim. Do not bypass a new/drifting input; return the exact blocker. Existing source data may not be blindly redownloaded.

## Supplier and request contract

JQData / JQ_OFFICIAL_RAW only. R3 may call get_all_securities and get_price plus get_query_count; it must NOT call get_trade_days again. Authentication uses only the existing local noninteractive locator E:\BLACKBOX\配置\secrets\已验证\聚宽账号.txt. Never print/upload/hash credentials, tokens, cookies or secret-derived values. Do not ask the owner for credentials or change them. SAM must not authenticate concurrently. SDK source/signature/default checks precede login; timeout45 seconds/request_attempt_count1, no outer retries. No sealed paid entitlement probes.

Products: stocks, ETFs and ONLY the original seven indices:
000001.XSHG,399001.XSHE,399006.XSHE,000300.XSHG,000905.XSHG,000852.XSHG,000016.XSHG.
Stock/ETF universes: get_all_securities(types=['stock'] or ['etf'],date=d), preserving each day's exact codes/lifecycle. Stock ceiling8000/ETF4000 are task resource caps, not claims about supplier universes; unsupported namespaces or exceeded caps stop.
Price: get_price(security=list<=80,start_date=d,end_date=d,frequency='daily',fields=[open,high,low,close,volume,money,paused,high_limit,low_limit,avg,pre_close,factor],skip_paused=False,fill_paused=True,fq=None,panel=False).
Dictionary RAW_NONE_DAILY_12_R1: preserve supplier numeric values/dtypes/nulls/units, plus time/code. No local scaling, fill, adjustment or duplicate suppression. Preserve disclosed supplier paused fill. factor is retained, never used to certify adjusted-price/PIT admission. Stable key=(calendar_date(time),code). Missing/extra/duplicate keys, wrong dates, ordinal integers, missing fields, invalid pause states and live-bar nulls block. Missing keys are never silently assigned legal EMPTY. A finite single-day nonpaged request is exhausted only by exact requested/returned-key reconciliation, not by being smaller than an assumed5000 limit.

Execution order:
- Validate/reuse the first09-28 stock80-row batch, calendar and first universe offline.
- Authenticate once and measure fresh quota.
-09-28 stock: skip the exact first80; request the remaining5142 in65 batches, no new universe call.
-Other16 stock sessions: acquire each own universe, then batches<=80.
-ETF: own universe and prices for each17 sessions.
-Index: one seven-code call per17 sessions.
The dated plan remains09-28,09-29,09-30,10-08,10-09,10-12,10-13,10-14,10-15,10-16,10-19,10-20,10-21,10-22,10-23,10-26,10-27. Actual supplier availability for each day is measured by its response; partial/empty blocks. No new time lag or PIT publication timestamp is invented. Contract expires2026-10-28 23:59CN; no local extension.

## Cumulative quota and stop rules

Original total ceiling700000; already consumed5320; R3 may consume at most694680, subject to fresh actual balance. Every supplier call measures before/after and includes the inherited5320 in cumulative accounting. Do not reset the task budget at login or at the new directory. Unknown quota, increases/reset, depletion or a measured ceiling breach stops. Retain the original50000 pre-call reserve; it can stop early rather than spend to the last unit. A client cannot guarantee cancellation of an already billed server request; report any unexpected charge/overrun honestly and make no further call. Maximum2500 data calls/75 product-days, no automatic retry.

Historical16870/day x17=286790 is only an approximate planning comparison: the historical day included different calendar/metadata overhead, daily universes may change and some inputs are now reused. It is not a tariff or a guarantee the whole task will complete within the ceiling. Actual receipts govern.

Every valid response is stored in a new R3 file, read back and checked by the shared serialization helper, then audited for exact keys/null/observation states. Rejected payloads/failures remain preserved. Existing R1/R2 and R3 output are never overwritten or deleted. If any R3 output, active invocation or completed result already exists, reuse/report it rather than running twice. An existing-output guard is not permission to rename/delete and restart.

## Exact native commands and receipts

Stage all package files to:
C:\LAN_SHARE_REPORT\BLACKBOX_RAW_NONE_INCREMENT_20261027_R3_CODE_DTYPE\package
Verify every PACKAGE.json payload SHA/length, read back local bytes, and upload ACK_R3.json BEFORE the gate. Keep all older ACKs/reports intact. Check prior active/completed R3 first.

Run ONCE:
```powershell
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 -m unittest discover -s "C:\LAN_SHARE_REPORT\BLACKBOX_RAW_NONE_INCREMENT_20261027_R3_CODE_DTYPE\package" -p "test_*.py" -v
```
Require63/63,0 failures/errors/skips,literal exit0. No native dependency installation/downgrade/interpreter substitution or local code edits. Failed gate means no login/download and no automatic second attempt.

Only after that gate, ONCE:
```powershell
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 "C:\LAN_SHARE_REPORT\BLACKBOX_RAW_NONE_INCREMENT_20261027_R3_CODE_DTYPE\package\acquire_daily.py" --execute
```
Do not precreate E: output. Exit0 means STAGED_UNREVIEWED including a read-only reference to the first batch; not completed cleaning or production admission. Exit2 means blocker/partial preserved; no retry. Other nonzero exits are literal failures, not inferred PASS.

Return to the same HUB task root:
agents/chatgpt/inbox/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/ZHANGWEI/

Top-level results: ACK_R3.json,PACKAGE_VERIFY_R3.json,GATE_R3.json/GATE_R3_STDOUT.txt/GATE_R3_STDERR.txt,RUN_R3.json/RUN_R3_STDOUT.txt/RUN_R3_STDERR.txt,REPORT_R3.md,DELIVERY_MANIFEST_R3.json,UPLOAD_READBACK_R3.json,LOCAL_READBACK_R3.json. Use r3_staging_output/ for an unchanged mirror of all new script-written JSON; all R3 script output names already carry_R3 suffix. Keep new Parquet on desktop with exact identities/full key/field/quality/serialization receipts; upload exact selected bodies if requested. Original source Parquet remains its old referenced path and must not be reuploaded as a newly downloaded R3 batch. Test package filenames stay exactly as reviewed, not renamed with suffixes.

Include actual argv/cwd/interpreter/start/end/exit/streams, native package/gate evidence, read-only reused source identities, PLAN_R3/RESULT_R3 and per-product/day coverage, cumulative quota, each requested/returned key set and difference, timestamps and duration via request/response receipt times. STATE/PASS wrappers are not a replacement for receipts. A future partial result must not erase already obtained batches. Every local file must be written and read back, then every uploaded file fetched as actual bytes and compared before ending. For large files, empty Contents content is not file absence: verify exact blob bytes, size and SHA. Preserve real empty command streams and explain uncreated outputs honestly.

Use acyclic manifests/readbacks, no self-hash loops. All new HUB prose English, exact original paths/identifiers allowed. Finish Cursor chat with exactly END.

## Cleaning/publication reserved for later

R3 performs no Cleaning/align/PIT transform or release creation. receipt_at is acquisition time only, not historical supplier-publication time. Original R15 functions and candidate wrappers are already available; GPT will specify exact retained/new inputs and transformations after auditing real conservation/coverage/provenance. No V4 reconstruction or yet-unperformed update is a circular prerequisite. Relevant identity/generation/non-regression/admission defects must be resolved on the chosen publication path before a separate CURRENT contract. Do not demand a generic RCID rewrite before all raw staging; equally, do not bypass the seven reproduced defects with an ad hoc pointer switch. No trading/orders/money actions.
