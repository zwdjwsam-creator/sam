# R5: isolated stock observation and exact no-refetch continuation

task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R5_ISOLATE_RESUME
execution_host: ZHANGWEI
ORDER_ALLOWED=false
CLEANING_ALLOWED=false
CURRENT_SWITCH_ALLOWED=false
AUTO_RETRY_ALLOWED=false
SAM: HOLD, historical evidence only; no login or execution.

## Scope and accepted prerequisite

R5 Stage A at snapshot a489979af7519b51996f038b9046b4631c8d1463 is accepted for exact rule/source handoff and native original preflight only. All19 delivery blobs independently match their Git identities;16 manifest contents match lengths/SHA256;6 captured bodies decode exactly. Original preflight actual OS exit0, ACQUISITION, KERNEL and three required rules VERIFIED. The collector actual exit0, no supplier call. This does not retroactively validate R4's missing preflight, accept R4 as a finished update, or approve publication.

The previously missing acquisition/HAND/current bodies are now reviewed. HAND_READ=NOT_SUFFICIENT is an unconditional informational line in the original source, not a failed reading test. Read BOOTSTRAP, DATA_ACCESS, ACQUISITION plus the pinned KERNEL, incremental HAND/CURRENT and cleaning HAND before any supplier call. RULE_PINS.json binds all10 exact rule/control/dependency inputs. Do not rewrite HAND, rules or Manifest. The20-dataset incremental CURRENT is not a price coverage certificate or a permanent09-24 cap. Use the pinned per-product/layer evidence and finite17-session plan already returned; do not rescan or invent source absence.

This task completes RAW staging only. No product is formally updated until a later reviewed Cleaning/align/PIT/cache/admission task passes. No strategy reconstruction, release publication or seven-RCID-defect bypass is authorized here.

## Preparation and duplicate protection

Read this task and current route, previous ACK/results and any active process first. If this task is already active or has an execution result, preserve it and report/reuse; do not duplicate, stop, resume automatically or run R4 again. Never use silence as evidence of a stopped process.

Stage PACKAGE.json and every file in PACKAGE.json.files unchanged in:
`C:\LAN_SHARE_REPORT\BLACKBOX_R5_ISOLATE_RESUME_20261028\package`
These are reviewed code and fixtures, not permission to execute arbitrary other files. Verify all byte lengths/SHA256 and read every staged file locally. No newline conversion, dependency installation, interpreter switch, local patch or test skip. Keep the old R1/R2/R3/R4 evidence unchanged.

The following new output MUST NOT exist or be precreated:
`E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R5`
Only acquire_r5.py creates it after the two real gates. Contract expires2026-10-29 23:59 Asia/Shanghai; target dates do not expand with the execution date.

Write `C:\LAN_SHARE_REPORT\BLACKBOX_R5_ISOLATE_RESUME_20261028\ACK_R5.json` after actually reading the bound rules. It must contain:
- task_id exactly as above; execution_host ZHANGWEI;
- package_sha256 = raw SHA256 of PACKAGE.json;
- rule_bodies_read = exact ordered list of RULE_PINS.json.files keys;
- each actual rule raw/binding hash, explicit TASK_CLASS=ACQUISITION and KERNEL_SHA;
- authorization boundaries, inherited175858/new150000/cumulative700000 quota caps;
- explicit pre-existing ACK/result/process/output check;
- upload_readback_completed=true ONLY after the ACK has been uploaded and remotely read back byte-for-byte. Set this fact in the final local ACK, upload that exact version and read it back before either command. No self-hash.

Upload ACK_R5.json and PACKAGE_VERIFY_R5.json to the return folder below BEFORE commands. No password, token, cookie, secret content or secret-derived hash in any output. Existing noninteractive credential locator may be used only by this authorized executor after both gates.

## A then B, enforced by reviewed wrapper (no SDK/auth/E output)

From the unchanged package directory, run exactly once, attached and waited for:
```
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 "C:\LAN_SHARE_REPORT\BLACKBOX_R5_ISOLATE_RESUME_20261028\package\precheck_r5.py"
```

The wrapper first binds package/rules, then runs the exact original:
```
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py --task-class ACQUISITION
```
No --acceptance/--write-manifest. The original may read only its known KERNEL/Manifest and six FILE_KEYS rule metadata inputs as in Stage A. It does not write E: on this reviewed normal path.

Only after actual preflight exit0 and literal PASS/VERIFIED output does it run the unchanged77 regression controls plus48 R5 controls (125 total), with the same interpreter:
```
-X utf8 -m unittest -v test_acquire_daily test_r3_code_and_reuse test_r4_empty_slots test_r5_resume
```
All125 must run, no failures/errors/skips, literal OK, real OS exit0. Separate raw streams, commands and actual exits are written under the C: control folder; GATE_R5.json is written only after both succeed. Capture the wrapper's own raw streams and actual OS exit externally too. If anything fails, stop, preserve/upload diagnostics; do not run the execute command. Package tests are not host preflight, and a wrapper boolean is not either gate. Do not rerun Stage A capture or change rules to make this pass.

## Exactly one continuation command, only after both gates

Upload/read back GATE_R5.json and its raw streams before execution. Then run once, attached and waited for:
```
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 "C:\LAN_SHARE_REPORT\BLACKBOX_R5_ISOLATE_RESUME_20261028\package\acquire_r5.py" --execute
```

Do NOT run acquire_daily.py --execute. That unchanged module is inherited helper/regression code only, not the R5 entry. No other business entry or historical PS1 is permitted. acquire_r5.py independently verifies bound source/rules, raw gate outputs/actual exits and package identities; gate freshness is6hours. Preserve failed output; never restart into another directory or clear a collision.

Before authentication the entry:
- Rechecks the four production pointer hashes and the original10 R1 pins, original calendar/plan and exact registered price-file metadata freshness. It reuses R04-R10 history/shard evidence; unknown directories still block. The existing exact5 empty slots are allowed only while ordinary, stable and zero-entry including hidden children. There is no invented sixth path or expanded whitelist.
- Verifies R4's3363 identified metadata files and1098 raw files against their pinned lengths/SHA256, no new inventory. Revalidates1097 previously accepted Parquets under the original strict stock guard. No broader retrospective classifier is applied to them.
- Rechecks the15489-byte failed raw SHA256 fb1a0ccb4918e6035d7e6a3695d6fbac6cbf9818c3ea2ca01bcf7928b2e8b2c7. It must yield exactly79 admitted positions and one isolated600621.XSHG/2026-10-27 position. Any other security, altered byte, additional candidate or key gap stops before login. No raw copy/rewrite/refetch.
- Uses the exact10-27 universe5224,42 accepted batches plus the one fetched failed batch3440 unique codes; difference must be1784,23 batches (22x80+24). The failed batch's80 fetched codes, including600621, are all excluded from new requests.

## Row observation and hard stops

Only a stock row that would otherwise trigger LIVE_BAR_NULL can be isolated. Exact shape: paused0, volume=money0, all open/high/low null; close/pre_close/avg/limits/factor nonnull; close=pre_close=avg exactly; Decimal ROUND_HALF_UP to0.01 matches one numerical paired limit ratio among0.05/0.10/0.20/0.30. This is a candidate signature, not an exchange/ST rule, suspension certificate, absence conclusion or PIT proof.

Label: SUPPLIER_ZERO_TRADE_PRICE_INCOMPLETE_CANDIDATE. Preserve every source value, including paused0 and all nulls. No invented open price, source flag correction, deduplication, factor adjustment or legal trading-status label. Raw file holds all80 original rows; ADMISSION_R5.json references admitted/quarantined positions, never presents a79-row rewrite as new supplier data. QUARANTINE_R5.json holds all14 original values, source identity/position and observation receipt time; no historical publication/PIT time is assigned.

At most3 isolated rows per date and10 total, including the retained600621 row; exceed either -> stop. Nonzero activity with missing required live prices, missing close, unknown paused, other null shapes, unmatched numeric pair, invalid numeric/key/dtype guards still stop. ETF wording in the owner draft is ambiguous; this narrower concrete task preserves the ETF hard stop, and index guards are unchanged. No ETF/index observation relaxation is authorized.

## Calls, fields, dates and quota

Only existing jqdatasdk1.9.8 noninteractive authentication, get_query_count for accounting, get_all_securities(types=['etf'],date=d) and get_price are allowed. No quota/SDK probe on SAM or sealed paid entitlement. Exact get_price parameters: frequency='daily', fq=None, panel=False, skip_paused=False, fill_paused=True; fields open/high/low/close/volume/money/paused/high_limit/low_limit/avg/pre_close/factor. Supplier paused-fill is preserved and recorded, never a new local fill.

Order: stock10-27 remaining1784 only; then ETF each of the17 plan dates with a fresh dated universe, stable sorted80-code batches; then the same7 index codes each date. No calendar or stock-universe replay, oldprice overlap re-download or10-28+ data.

Dates:2026-09-28,09-29,09-30,10-08,10-09,10-12,10-13,10-14,10-15,10-16,10-19,10-20,10-21,10-22,10-23,10-26,10-27.
Index codes:000001.XSHG,399001.XSHE,399006.XSHE,000300.XSHG,000905.XSHG,000852.XSHG,000016.XSHG.

Each daily universe must have unique stable code keys and valid listed lifecycle for that date; each price call must return exactly the requested finite code/date set, no duplicates/extra/missing keys. Daily unions must exhaust the universe once. Max80 is a batch bound, not a proof of supplier exhaustion or a universal5000 endpoint cap. Price responses and serialization failures are preserved; exact timestamp/code representation exceptions only, all other guards remain strict.

New consumption ceiling150000; inherited175858 is immutable; cumulative original700000 ceiling also enforced. Before each call reserve80-or-fewer units for price or4000 for ETF universe; stop before a projected overrun. Real quota delta above the projected bound, measured new/cumulative overrun, quota reset/increase or unmeasured quota stops. SDK timeout45sec, request_attempt_count=1, no automatic retry. End accounting may query get_query_count after failure; this never retries the failed data call. Success requires Q0-Q1=sum of all response deltas. A failed request may spend quota without a completed response receipt; preserve that discrepancy explicitly, never report unmeasured spend as zero.

## Results, uploads and END

Execute exit0 means RAW_STAGED_UNREVIEWED only, not formal data update or Cleaning PASS. Exit2 means partial/blocked preserved; no retry. Any other real OS exit/timeout is also preserved and reported, never converted to0. Do not delete/rewrite old data or terminate other processes. Four CURRENT identities are checked again; any drift blocks even if collection finished.

Return to:
`agents/chatgpt/inbox/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/ZHANGWEI/r5_isolate_resume/`

Return ACK/package verification, precheck wrapper and underlying native preflight/tests raw stdout/stderr/real exits, GATE_R5.json, attached execution argv/raw streams/real exit, all R5 staging JSON outputs (RESULT/BASELINE/PLAN/SDK/REUSE_MANIFEST/ADMISSION/QUARANTINE/COVERAGE/per-date coverage/universes/request-response-quality receipts). Preserve zero-byte streams as real zero-byte streams; do not copy stderr into stdout. Record explicit not-run states if a gate failed.

New Parquet files stay local; list exact path/length/SHA256, distinct from old referenced raw. Coverage cells use ACQUIRED/PARTIAL_BLOCKED/NOT_ATTEMPTED, with admitted/quarantined/unacquired sets separately. ACQUIRED means source acquisition only. Quarantined rows are neither admitted prices nor unrequested missing keys. Do not declare NO_DATA or overall update complete.

Create acyclic DELIVERY_MANIFEST_R5.json, LOCAL_READBACK_R5.json and UPLOAD_READBACK_R5.json. Read every output locally and EVERY uploaded file back byte-for-byte before ending, including all mirror JSON and manifest/companions. Git tree/blob hashes alone are not a substitute for the requested byte readback. For Contents responses encoding=none or >1MiB use git/blobs/{sha} and decode raw bytes. Preserve old failures and do not overwrite R1-R4. Only new paths inside this return folder are authorized.

Do not update mailbox routing files or delete misplaced remote artifacts; if an upload path is wrong, report exact path/error and stop that upload. No cleanup, terminal restart, watchdog/AUTOHUB/task mutation, elevation or source/rule modification. After upload/readback, end Cursor chat with exactly END. GPT will audit actual RAW-to-admission conservation and later author Cleaning separately.
