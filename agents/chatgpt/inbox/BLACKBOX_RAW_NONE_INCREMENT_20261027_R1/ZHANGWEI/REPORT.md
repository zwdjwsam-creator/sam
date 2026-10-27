# BLACKBOX_RAW_NONE_INCREMENT_20261027_R1 — ZHANGWEI gate failure, execution withheld

task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R1
parent_task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
host: ZHANGWEI
role: ZHANGWEI
recorded_at_cn: 2026-10-27T18:12:00+08:00
status: GATE_FAILED_EXECUTION_WITHHELD

ORDER_ALLOWED=false
CURRENT_SWITCH_ALLOWED=false
PRODUCTION_CLEANING_ALLOWED=false
PRODUCTION_RAW_WRITE_ALLOWED=false

## 1. Headline

The package staged and verified cleanly **5/5**. The native gate then **failed: 26 passed,
1 failed, exit 1**. Because the contract makes the gates conjunctive — "Require 27/27 tests,
zero errors/failures/skips, literal exit 0" and "Only after the gate passes, run ONCE" — 
`acquire_daily.py --execute` was **NOT run**.

**No login. No supplier call. Zero quota consumed. Nothing written to `E:`.**

This is a withheld execution with preserved evidence, not a partial acquisition.

## 2. Package staging and verification

Six files were fetched as original raw git blobs, written byte-verbatim into
`C:\LAN_SHARE_REPORT\BLACKBOX_RAW_NONE_INCREMENT_20261027_R1\package\`, and re-read after
writing. All **5/5** manifest payloads match declared length and SHA256:

| file | bytes | verified |
|---|---|---|
| `acquire_daily.py` | 22,076 | ok |
| `test_acquire_daily.py` | 6,522 | ok |
| `TASK.md` | 14,045 | ok |
| `EVIDENCE.json` | 4,023 | ok |
| `OFFLINE_TEST_RECEIPT.json` | 2,986 | ok |

No line-ending conversion, no local patch, no alias, no fallback copy. `PACKAGE.json` was
also staged and re-hashed.

## 3. Gate result

Exact prescribed command, run once, exit **1**:

```
Ran 27 tests in 0.347s
FAILED (failures=1)
```

The single failure:

```
FAIL: test_real_parquet_and_footer (test_acquire_daily.Keys)
  File "...\test_acquire_daily.py", line 73, in test_real_parquet_and_footer
    pd.testing.assert_frame_equal(x,pd.read_parquet(p/'one.parquet'))
AssertionError: Attributes of DataFrame.iloc[:, 0] (column name="time") are different
Attribute "dtype" are different
[left]:  datetime64[s]
[right]: datetime64[ms]
```

All 26 other controls pass, including the substantive ones (`missing_key_blocks`,
`duplicate_blocks`, `extra_key_blocks`, `ordinal_blocks`, `live_null_blocks`,
`quota_unmeasured_blocks`, `wrong_host_before_output`, the Windows source-root boundary
tests, and `unhandled_file_not_absence`).

## 4. Root cause — a datetime unit, not corrupted data

`test_acquire_daily.py:14` builds the fixture as:

```python
x=pd.DataFrame({'time':[pd.Timestamp(D)]*2,'code':C})
```

Under **pandas 3.0.3** that yields `datetime64[s]`. Parquet has no second-resolution
timestamp, so pyarrow coerces it to `timestamp[ms]` on write (physical type confirmed from
the footer: `time: timestamp[ms]`). The re-read frame is therefore `datetime64[ms]`. Only the
**unit** differs; every value is elementwise equal.

Three controlled experiments pin this down:

| case | before | after | `check_dtype=True` | values equal |
|---|---|---|---|---|
| A — fixture as authored | `datetime64[s]` | `datetime64[ms]` | **FAIL** | yes |
| B — same data cast to `[ns]` | `datetime64[ns]` | `datetime64[ns]` | **PASS** | yes |
| C — as authored, `check_dtype=False` | `datetime64[s]` | `datetime64[ms]` | **PASS** | yes |

Case B is almost certainly why the reviewer's Linux run reported 27/27: on pandas 2.x,
`pd.Timestamp(date(...))` is `datetime64[ns]`, which does round-trip as ns. The host
environment is the difference, not the acquisition logic.

Measured environment: Python 3.12.10, **pandas 3.0.3**, numpy 2.5.4, pyarrow 24.0.0,
jqdatasdk 1.9.8, Windows 11.

## 5. The part that matters more than the test

The **same strict assertion appears in the production path**, `acquire_daily.py:337`:

```python
response.to_parquet(batch,index=True)
rawbytes=batch.read_bytes()
reread=pd.read_parquet(batch)
pd.testing.assert_frame_equal(response,reread,check_dtype=True)
```

That line sits **inside the per-batch loop, after `supplier.call('get_price', args)` has
already returned and after the batch parquet is already on disk**. So if this defect is
triggered in a real run, the sequence is: quota is spent → the raw batch file exists → the
run aborts. A naive retry would then also hit `require(not batch.exists())` and raise
`RAW_REPLAY_COLLISION` on that same batch.

Whether it actually triggers depends on whether jqdatasdk 1.9.8 under pandas 3.0.3 returns
`time` as `datetime64[ns]` or `datetime64[s]`. **That cannot be established without calling
the supplier**, which this task forbids while the gate fails. So it is reported as an
unresolved, high-impact conditional risk — not as a proven production failure.

This is exactly why the local gate exists ahead of the download, and it earned its keep.

## 6. What I deliberately did not do

- Did not patch the test or `acquire_daily.py` — the contract forbids local patches/aliases.
- Did not pin or downgrade pandas, and did not substitute another interpreter.
- Did not run `acquire_daily.py` "just to see".
- Did not retry the gate.
- Did not read the credential file; its mtime is unchanged at `2026-10-16T05:10:05`.
- Did not pre-create or create `E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R1`;
  it remains absent, and `E:\BLACKBOX\STAGING` itself does not exist.

## 7. Options for the reviewer

- **A** — pin the fixture to `datetime64[ns]` **and** make the production readback compare
  values plus a normalised unit instead of exact dtype unit. Touches production code.
- **B** — keep exact-dtype intent but make the write unit-stable (explicit
  `coerce_timestamps` or cast `time` before writing) so the round-trip cannot drift. Touches
  production code.
- **C** — declare and pin the required pandas major version and re-run the gate under it. No
  code change.

My reading: neither the fixture nor a pandas pin alone is sufficient, because the contract
simultaneously requires "preserve original dtypes" **and** "read back and verify
values/dtypes", while Parquet cannot store a seconds-resolution timestamp. **A or B is
needed regardless of environment**; C alone leaves the production line fragile.

## 8. Delivered files

`ACK.json`, `PACKAGE_VERIFY.json`, `GATE.json`, `GATE_STDOUT.txt`, `GATE_STDERR.txt`,
`EXECUTION_BLOCKED.json`, `ENV.json`, `DIAGNOSIS.json`, `REPORT.md`,
`DELIVERY_MANIFEST.json`, `UPLOAD_READBACK.json`, `LOCAL_READBACK.json`.

`GATE_STDOUT.txt` is legitimately 0 bytes — `unittest` writes its verbose log to stderr.

No `BASELINE`/`COVERAGE`/quality JSON from the script exists because the script never ran;
that absence is the direct consequence of withholding execution, not a missing export.
Receipts are ordered acyclically and `LOCAL_READBACK.json` is referenced by nothing.
