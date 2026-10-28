# R5 ISOLATE_RESUME — corrected fixture R2 executed: RAW staged, unreviewed

task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R5_ISOLATE_RESUME
dispatch_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R5_FIXTURE_R2
execution_host: ZHANGWEI
outcome: RAW_STAGED_UNREVIEWED (execute actual OS exit 0)
language: English (as required)

## Bottom line

Both real gates passed natively, the single authorised continuation command then ran once and returned actual OS exit 0. RAW staging for the finite 17-session plan plus the remaining 1784 stock codes is complete and **unreviewed**. This is not a formal data update, not a Cleaning pass, not PIT admission, not publication and not a CURRENT switch.

## Gate A — original host preflight

Command run once by the reviewed wrapper, exact original path:

```
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py --task-class ACQUISITION
```

Actual OS exit 0. Literal output: `MUST_READ_PRECHECK = PASS`, `TASK_CLASS = ACQUISITION`, `KERNEL_STATUS = VERIFIED`, `AUTHORITY_READY = YES`, `TASK_EXECUTION = ALLOWED`, `TASK_EXECUTION_FORBIDDEN = FALSE`. KERNEL `b05a69958e29f7c90cf1ea794a4c437d36120bb960515ce9e26d3f4d5bdf197a` (1167 bytes); BOOTSTRAP, DATA_ACCESS and ACQUISITION all VERIFIED with expected equal to actual. stdout 1157 bytes, stderr a true zero-byte stream.

`HAND_READ = NOT_SUFFICIENT` appears as the known unconditional informational line and is not a failure.

## Gate B — all 128 native controls

Same interpreter, `-X utf8 -m unittest -v test_acquire_daily test_r3_code_and_reuse test_r4_empty_slots test_r5_resume`.

Actual OS exit 0. `Ran 128 tests in 3.678s`, literal result line `OK`, zero failures, zero errors, zero skips. 77 unchanged regression controls plus 51 R5 controls, including the three new `WindowsReadPolicy` controls that execute the ORIGINAL guard function code under an OS-name proxy and confirm fixed allowed roots, sibling/external rejection and path rejection ahead of hash checks.

`GATE_R5.json` was then written with package SHA256 `183d7658…0b20`, ACK SHA256 `0d2fc8c2…de48`, `expected_tests: 128`, both phase exits 0, and the 10 rule bindings. It was uploaded and read back (gate age at execution start: 21 s, well inside the 6 h freshness bound).

The previous 125-test failure and its folder are preserved untouched; the old package was not rerun and nothing was deleted.

## Correction scope actually verified before running

| file | change |
|---|---|
| `acquire_r5.py` | `CONTROL` directory constant only |
| `precheck_r5.py` | `CONTROL` directory constant only |
| `test_r5_resume.py` | two byte-identity fixtures wrapped in a documented `unittest` permission seam plus 3 new Windows-guard controls |
| `acquire_daily.py` | byte-identical to the previous package |
| all business, price, admission, path and quota logic | unchanged |

`allowed_windows_path` still allows exactly `e:\blackbox\` and `e:\blackbox_engines\`. `acquire_r5.py` contains no patch or mock code and still calls `a.require_allowed_read(path.resolve(strict=True))` unchanged, so the production guard is intact and the seam exists only inside test contexts. No test skipped, no E: fixture directory created, no newline conversion, no dependency installed, no interpreter switch.

Package: 23 payloads all match byte length and SHA256, `PACKAGE.json` raw SHA256 equals the dispatch binding `183d765869f407a9be557c2b48429ebb9acb7ced047af23893d1fd3284820b20`, 24 files staged, zero CRLF conversions.

## Execution — exactly one command

```
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 "C:\LAN_SHARE_REPORT\BLACKBOX_R5_ISOLATE_RESUME_FIXTURE_R2_20261028\package\acquire_r5.py" --execute
```

Run once, attached and waited, actual OS exit 0, elapsed 150 308 ms, both streams true zero-byte files, `retry: false`. `acquire_daily.py --execute` was not run.

`RESULT_R5.json`: `status RAW_STAGED_UNREVIEWED`, `baseline_after UNCHANGED`, `order_allowed false`, `current_switch_allowed false`, `cleaning_allowed false`.

## Calls, receipts and quota

| item | value |
|---|---|
| supplier calls | 422 (`get_price` 405, `get_all_securities` 17) |
| request receipts | 422, response receipts 422, failure receipts 0 |
| call numbering | continuous 1..422, every `retry` false |
| Q0 / Q1 | 200000000 / 199941037 |
| Q0 − Q1 | 58963 |
| sum of response deltas | 58963 |
| new spend vs 150000 cap | 58963 ≤ 150000 |
| cumulative vs 700000 cap | 234821 ≤ 700000 (= 175858 inherited + 58963) |
| per-call delta above its reserve | none |
| quota-chain break | none |

Price calls were 405 batches of at most 80 codes (min 2, max 80); ETF universe calls reserved 4000 each. Parameters on every price call: `frequency='daily'`, `fq=None`, `panel=False`, `skip_paused=False`, `fill_paused=True`, `start_date == end_date`, with the 12 required fields. Dates used are exactly the 17 plan dates, maximum `2026-10-27`; no 10-28+ data and no calendar, stock-universe or old-price replay was requested. SDK 1.9.8, `request_attempt_count=1`, timeout 45 s.

## Coverage and conservation

All 51 product/date cells are `ACQUIRED` (17 stock, 17 ETF, 17 index). Every cell has `PAGINATION_COMPLETE=YES`, `ORDER_DETERMINISTIC=YES`, `PAGE_BOUNDARY_STABLE=YES`, `DUPLICATE_LOSS=0`, `SILENT_TRUNCATION=0` and an empty `unacquired_codes` set. `COVERAGE_R5.json` carries `source_absence_claim false` and `staging_only true`.

| component | admitted | quarantined |
|---|---|---|
| reused R4 evidence (1099 entries) | 87027 | 1 |
| newly acquired (405 entries) | 30433 | 0 |
| total | 117460 | 1 |

`ADMISSION_R5.json` has 1504 entries whose admitted positions sum to 117460 and whose quarantined positions sum to 1; both totals equal the `COVERAGE_R5.json` sums exactly, so no row is double-counted and no row is lost. New Parquet holds 30433 rows across 405 files, equal to the new admitted count.

Stock 2026-10-27 closes exactly: 3439 reused admitted + 1784 newly admitted = 5223 admitted, plus 1 quarantined = 5224 expected. `600621.XSHG` was never re-requested — it sits in the excluded failed-batch 80 — so it is neither a newly admitted price nor an unrequested missing key.

## The single quarantine row

`600621.XSHG`, `2026-10-27`, zero-based position 7, sourced from the preserved R4 failed body (`15489` bytes, `fb1a0ccb…b2c7`), revalidated by hash before use and not copied, rewritten or refetched.

Preserved source values, all 14 of them and unchanged: `paused 0.0`, `volume 0.0`, `money 0.0`, `open/high/low null`, `close 14.9`, `avg 14.9`, `pre_close 14.9`, `high_limit 16.39`, `low_limit 13.41`, `factor 1.0`.

Label `SUPPLIER_ZERO_TRADE_PRICE_INCOMPLETE_CANDIDATE`, `legal_suspension_status NOT_INFERRED`, `historical_pit_timestamp NOT_ASSIGNED`, `source_values_changed false`. This is a candidate numeric signature only — not an exchange rule, not an ST determination, not a suspension certificate, not a PIT proof and not an absence conclusion. Quarantine caps: 1 row on the date (cap 3) and 1 total (cap 10).

## State left behind

`E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R5` was created by `acquire_r5.py` alone, after both gates, as designed. `BASELINE_R5.json` records the pre-run pointer hashes and the gate receipt, and the run ends with `baseline_after UNCHANGED`, so no production pointer moved. No R1–R4 evidence was deleted or rewritten. No order, no CURRENT switch, no cleaning, no publication, no rule edit, no watchdog or terminal action, no mailbox routing change.

## Delivery

`staging_output/` mirrors all 1309 R5 staging JSON files (8 root receipts, 35 per-date coverage, 405 quality receipts, 844 request/response receipts, 17 ETF universes) in 9 commits. Every one was fetched back from `git/blobs` and compared byte-for-byte to the local file: **1309/1309 equal, 0 mismatched, 22 867 699 bytes remote**. Git hashes were not used as a substitute for that byte readback.

The 405 new Parquet files stay local per contract; `PARQUET_MANIFEST_R5.json` lists each one with exact path, length, SHA256 and git blob SHA1.

Also delivered: ACK, package verification, wrapper and inner preflight/tests raw streams with real exits, `GATE_R5.json`, execution argv and raw streams with the real exit, this report, and the acyclic manifest with local and upload readbacks.

## Limits of this delivery

RAW staged and unreviewed only. GPT still owes actual RAW-to-admission conservation audit, dictionary, provenance, temporal and PIT review, and a separately authored Cleaning task. The seven RCID publication defects remain open. Nothing here authorises a release, a CURRENT switch or an order.
