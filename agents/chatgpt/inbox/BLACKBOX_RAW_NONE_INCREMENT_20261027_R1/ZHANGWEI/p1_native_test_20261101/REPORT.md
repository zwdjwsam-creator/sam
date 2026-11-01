# BLACKBOX_P1_NATIVE_TEST_20261101 — one native fixture-conformance run

- task_id: `BLACKBOX_P1_NATIVE_TEST_20261101`
- execution_host: `ZHANGWEI` (Windows 11, `Windows-11-10.0.26200-SP0`)
- executed_at_utc: 2026-11-01T06:36:18.81Z → 06:36:19.14Z (outer)
- outcome: **`NATIVE_FIXTURE_CONFORMANCE_ONLY`**, outer actual OS exit **0**
- `ORDER_ALLOWED=false`, `native_price_rows_read=0`, `cleaning_run=false`,
  `backtest_admission=false`

## 1. Scope boundary, stated first

This run establishes one thing: the owner-approved stock-only P1 availability view passes
its 20 fixture tests on the native Windows runtime, and a date-only eligibility plan can be
derived from the frozen calendar. It is **not** real-data backtest admission, not native
cleaning, not a PIT establishment, and not evidence about E: price completeness. `select()`
is an availability view, not an execution or fill engine. It preserves `paused` and
zero-volume observations and certifies no tradability.

P2 (`BLACKBOX_R5_NATIVE_BINDING_P2_20261101`) is closed by GPT acceptance and was **not**
rerun here.

## 2. Policy approval, as recorded — not as inferred

| Field | Value |
|---|---|
| `policy_id` | `BLACKBOX_DAILY_AVAILABILITY_PRESUMPTION_P1` |
| `revision` | `R2_STOCK_ONLY_20261101` |
| `status` | `OWNER_APPROVED_POLICY_ONLY` |
| `policy_body_sha256` | `31dee3a67f7674db25b0ba4d56c169c941e28f857b8656454b6006401938f884` |
| `calendar_sha256` | `ab00fa8c597c9b01977cc060a202371d2de73a6a32b8a4fe6cc533a705d056d9` |
| handwritten signature | not required and not requested |
| `order_allowed` / `cleaning_allowed` / `supplier_allowed` / `current_switch_allowed` | all `false` |

`POLICY_BODY.txt` and `APPROVAL.json` hashes agree with each other and with the approval,
and with the embedded `POLICY_SHA` / `CAL_SHA` used by the tested code.

## 3. Package staging

Ten files staged unchanged from
`agents/chatgpt/reviews/BLACKBOX_P1_NATIVE_TEST_20261101/` into
`C:\LAN_SHARE_REPORT\BLACKBOX_P1_NATIVE_TEST_20261101\package`. No newline conversion,
no install, no interpreter substitution, no source patch, no skipped test.
All 9 declared payloads matched their length and SHA-256; every staged byte was re-read
against the received bytes.

`PACKAGE.json` does not hash itself; its raw SHA-256 is recorded in `ACK.json` and
`PACKAGE_VERIFY.json` instead: `568e48265add645dc2111826df6fe79b491d0957d97932845423675e17f82263`.

## 4. Duplicate and once-only guards

Pre-execution check: control root, `package/`, `result_001`, `RUN_ONCE.json` and the
return folder did not exist; no prior execution receipt for this task id; no matching
running instance. Control root confirmed ordinary/non-reparse across every path component
before any write.

The supplied runner wrote `RUN_ONCE.json` **outside** `result_001` before creating
`result_001`. Deleting the result directory cannot reopen this entry point. One run,
no retry, no cleanup, no directory substitution, no replay.

## 5. The single attached command and its actual exit

```
E:\BLACKBOX\.venv\Scripts\python.exe -B -X utf8 C:\LAN_SHARE_REPORT\BLACKBOX_P1_NATIVE_TEST_20261101\package\run_native_tests.py
```

- outer actual waited-for OS exit: **0**
- outer `OUTER.stdout.txt`: 0 bytes; `OUTER.stderr.txt`: 0 bytes (both preserved as empty)
- nested processes are separate observations from separate processes; neither exit is
  presented as the other

| Inner process | Actual exit | Window (UTC) |
|---|---:|---|
| original DATA preflight | **0** | 06:36:18.943745 → 06:36:18.996937 |
| `unittest -v test_p1` | **0** | 06:36:19.011168 → 06:36:19.083307 |

The preflight ran before the fixture tests, as specified, with `--task-class DATA` and no
`--acceptance`, `--write-manifest` or repair flag.

## 6. Test result — 20/20, no skips

`result_001/tests.stderr.txt` (1,454 B) ends `Ran 20 tests in 0.004s` / `OK`.
`result_001/tests.stdout.txt` is 0 bytes. The runner additionally asserted the literal
`Ran 20 tests` count and a trailing `OK`, so a lower count or a skip would have failed the
run rather than passed quietly.

Covered: next-session derivation, before-threshold, equal-threshold, UTC equivalence,
naive rejection, terminal unresolved, before-calendar, non-session, factor denial,
original-unchanged, paused preserved, zero-volume not filled, forbidden uses, product
scope, duplicate key, quarantine, timestamp-not-date, future-date tamper,
generation tamper, sixteen-resolved-one-unresolved.

These are fixture tests. They do not certify E: price-source completeness, native
candidate cleaning, execution constraints or the seven open RCID publication defects.

## 7. Preflight observation, preserved verbatim

`result_001/preflight.stdout.txt` (870 B) reports `MUST_READ_PRECHECK = PASS`,
`TASK_CLASS = DATA`, `KERNEL_STATUS = VERIFIED`,
`AUTHORITY_READY = YES`, `TASK_EXECUTION = ALLOWED`, with `BOOTSTRAP` and `DATA_ACCESS`
rule hashes both `VERIFIED`.

It also prints `HAND_READ = NOT_SUFFICIENT` in the same run. That is an annotation of the
authority model, not a contradictory nonzero gate result. It is recorded verbatim and it
was **not** used to override any actual exit code, in either direction.

`result_001/preflight.stderr.txt` is 0 bytes, preserved as zero bytes.

## 8. Date-only eligibility plan

`result_001/DATE_PLAN.json` covers the 17 data days in the frozen calendar after its first
day. 16 are `PRESUMED`, 1 is `UNRESOLVED`.

| Data date | Presumed available (Asia/Shanghai) |
|---|---|
| 2026-09-28 | 2026-09-29T09:00:00+08:00 |
| 2026-09-29 | 2026-09-30T09:00:00+08:00 |
| 2026-09-30 | 2026-10-08T09:00:00+08:00 |
| 2026-10-08 | 2026-10-09T09:00:00+08:00 |
| 2026-10-09 | 2026-10-12T09:00:00+08:00 |
| 2026-10-12 | 2026-10-13T09:00:00+08:00 |
| 2026-10-13 | 2026-10-14T09:00:00+08:00 |
| 2026-10-14 | 2026-10-15T09:00:00+08:00 |
| 2026-10-15 | 2026-10-16T09:00:00+08:00 |
| 2026-10-16 | 2026-10-19T09:00:00+08:00 |
| 2026-10-19 | 2026-10-20T09:00:00+08:00 |
| 2026-10-20 | 2026-10-21T09:00:00+08:00 |
| 2026-10-21 | 2026-10-22T09:00:00+08:00 |
| 2026-10-22 | 2026-10-23T09:00:00+08:00 |
| 2026-10-23 | 2026-10-26T09:00:00+08:00 |
| 2026-10-26 | 2026-10-27T09:00:00+08:00 |
| **2026-10-27** | **null — `UNRESOLVED`** |

The terminal day is unresolved because no successor session exists inside the bound frozen
calendar. No T+1 timestamp was fabricated, no holiday was interpolated, and no supplier or
calendar request was issued. I independently recomputed all 17 rows from the E: calendar
original and got an exact match, so this is a check of the artifact, not a restatement of it.

## 9. Source protection, re-read after the run

The three E: sources the runner was permitted to read were re-read on disk after
completion and all still hold their pins:

| Source | Bytes | Pin |
|---|---:|---|
| `STAGING/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/CALENDAR.json` | 914 | `ab00fa8c…d056d9` OK |
| `脚本/blackbox_must_read_preflight_r1.py` | 11,767 | `3bb85023…7fe217` OK |
| `脚本/_base.py` | 11,800 | `b8cc6074…4f2258` OK |

The runner itself also compared its in-memory originals before success and reported
`source_recheck: EXACT`. These two observations are independent of each other.

## 10. What was not read, not run, not switched

No raw price file, no Parquet, no credentials, no environment dump, no supplier module, no
paid entitlement check, no directory inventory, no CURRENT read or write, no cleaning, no
backtest admission, no orders, no scheduling, no HAND change, no release or Cache switch.
The staged `CALENDAR.json` was compared against the E: original before staging was trusted;
a metadata or calendar mismatch would have blocked rather than selecting a similar source.

## 11. Status separation

| Facet | State |
|---|---|
| Approved policy | `OWNER_APPROVED_POLICY_ONLY`, hash-bound |
| Publication to HUB | performed; see `UPLOAD_READBACK.json` |
| ACK | written and read back **before** execution |
| Attempted native execution | yes, one attached run |
| Actual exit | outer **0**; preflight **0**; tests **0** |
| Test result | 20/20, no skips |
| Unresolved dates | 1 — `2026-10-27`, terminal day |
| Real-data backtest admission | **no** |
| GPT review of this run | **pending** — nothing here claims it |
| Native cleaning / P3 | **not started** |

## 12. Receipt scope, honestly bounded

- `result_001/LOCAL_READBACK.json` covers the 8 files written before it and excludes
  itself by design; it is not a self-hashing receipt.
- `DELIVERY_MANIFEST.json` excludes itself and `UPLOAD_READBACK.json`.
  `UPLOAD_READBACK.json` excludes itself; its final observation is stated in chat.
- `FAILED.json` was not written, because the run did not fail.
- This return is not an OS-wide write or process trace and does not upgrade the P2
  evidence claim. It is the reviewed program's own behaviour plus the returned receipts.
- Fixture conformance is not a statement about any historical market value, revision
  vintage or supplier truth.
