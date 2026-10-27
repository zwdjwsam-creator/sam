# REPORT — BLACKBOX_UPDATE_PREREQUISITES_SAM_20261027

- child_task_id: `BLACKBOX_UPDATE_PREREQUISITES_SAM_20261027`
- parent_task_id: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`
- dispatch_id: `BLACKBOX_UPDATE_PREREQUISITES_20261027`
- execution_host: **SAM** (hostname `SAM`, `SAM\ThinkPad`)
- status: **BLOCKED_AT_FIXTURE_GATE — COLLECTION NOT RUN**
- boundaries held: no supplier call, no download, no cleaning/compiler/commit, no production
  CURRENT write, no order, no deletion, no write to `E:\BLACKBOX` or `E:\BLACKBOX_ENGINES`

---

## 1. Headline

The 17-fixture gate **failed 2/17 on this host**, and the dispatch rule says a failed test stops
collection. So the collector was **not invoked**, `capture_001` was **not created**, and no
`COLLECTION.json` / `LOCAL_READBACK.json` exists.

The two failures happen **before any collector code is exercised**: the test fixtures cannot create
symlinks on this machine. That is a host privilege limit, not a defect in the collector and not a
defect in the tests' assertions.

Per instruction the failure is uploaded **as-is**: tests and code were not modified, and nothing was
retried.

---

## 2. Exact gate outcome

Command (single invocation, literal exit preserved):

```
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 -m unittest discover -s C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027\package -p test_collect_prerequisites.py -v
```

| field | value |
|---|---|
| exit code | **1** (literal `subprocess` returncode, not derived from an artifact) |
| elapsed | 15.485 s |
| stdout | 0 bytes |
| stderr | 4,137 bytes |
| result line | `Ran 17 tests in 8.131s` → `FAILED (errors=2)` |

15 passed. 2 errored:

| test | failure point | error |
|---|---|---|
| `test_cycle_link_not_followed_and_disclosed` | `Path.symlink_to(t, target_is_directory=True)` at test line 63 | `OSError: [WinError 1314] 客户端没有所需的特权` |
| `test_external_link_blocked` | `Path.symlink_to(outside)` at test line 47 | `OSError: [WinError 1314] 客户端没有所需的特权` |

Literal streams: `logs/FIXTURE_CONTROLS_STDOUT.txt`, `logs/FIXTURE_CONTROLS_STDERR.txt`.
Ledger: `FIXTURE_CONTROLS_LEDGER.json`.

---

## 3. Root cause of the two errors (measured, not inferred)

| probe | result |
|---|---|
| `HKLM\...\AppModelUnlock\AllowDevelopmentWithoutDevLicense` | absent (Developer Mode not enabled) |
| process elevation (`WindowsPrincipal.IsInRole(Administrator)`) | `False` |
| `whoami /priv` containing `SeCreateSymbolicLink` | none |
| direct `os.symlink` probe in a temp dir | `SYMLINK_FAIL errno=22 winerror=1314` |

So the platform cannot create symbolic links for this account. `packages`' tests build their
fixtures with `symlink_to`, therefore they cannot reach the collector under test.

**This is exactly the gap the review predicted**: `REVIEW.md` states the reviewer checks are
"Linux temporary-file/symlink/control-flow tests" that "do not establish NTFS junction behavior,
Windows host execution". The 2 failures are the Windows counterpart of that statement.

Not attempted, because they would be host policy changes outside this authorisation:
enabling Developer Mode, running elevated, or granting `SeCreateSymbolicLinkPrivilege`.

---

## 4. What is (and is not) in this return

### Delivered

| file | basis |
|---|---|
| `ACK.json` | uploaded **before** any execution, per dispatch |
| `COMMAND_LEDGER.json` | literal fixture invocation + an explicit `COLLECTOR_NOT_RUN` entry |
| `logs/FIXTURE_CONTROLS_STD{OUT,ERR}.txt` | literal streams |
| `FIXTURE_CONTROLS_LEDGER.json` | argv/cwd/exe/host/timing/exit/stream paths |
| `RELEASE_PRODUCER_MAP.json` | built from **already-retained** evidence under the same parent task |
| `R15_UNIT_EVIDENCE.json` | read directly from the retained R15 task directory |
| `CURSOR_EVIDENCE_APPENDIX.json` | references `CURSOR_MATRIX_BASELINE.json` by `dataset_id`, `new_start`/`new_end` null |
| `FACTOR_EVIDENCE_NOTE.md` | cites retained R15 contract + earlier measured factor anomaly |
| `DELIVERY_MANIFEST.json`, `REPORT.md`, `UPLOAD_READBACK.json` | packaging |

### NOT delivered, because it did not run

- `capture_001/COLLECTION.json`
- `capture_001/LOCAL_READBACK.json`
- `capture_001/bodies/` (new/changed bodies)

No `capture_001` directory exists locally. Nothing was fabricated to fill the gap, and no old
directory was deleted to make a command run.

### The bounded lookup in `E:\BLACKBOX\任务` was NOT performed

The dispatch restricts the id lookup to first-level task directories matching a token list under
`E:\BLACKBOX\任务`. That lookup is part of the collector, which did not run. Therefore, for both
release ids, `candidate_task_directory` **within that root is `NOT_DONE` — not `NONE` and not
"absent"**. `RELEASE_PRODUCER_MAP.json` says so explicitly.

---

## 5. Producer map — what could still be answered, and how

The two September-24 releases were already resolved by an **earlier read-only provenance task**
under the same parent (`sam_led_rectification/provenance_20261026/`, retained in HUB). That work is
reused here rather than re-collected.

| release | producer body | grade | binding |
|---|---|---|---|
| `..._R45_DAILY_TIP_ASOF_20260924_20260925_034534` | `D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\clean_switch_r1.py` (8,874 B) | **EXECUTION_BOUND** | `FULL_CHAIN.log` L2512 `RUN ...clean_switch_r1.py` at `03:45:33+08:00`; `CLEANING_SWITCH.json` `created_at` `03:45:37+08:00` (4 s later) with the identical `release_id` |
| `..._R33_FUND_NAV_ASOF_20260924_20260924_200439` | `E:\BLACKBOX\脚本\blackbox_fund_etf_nav_premium_plane_r1.py` (31,204 B) | **EXECUTION_BOUND** | `_run_full_chain.ps1` L41-42 invoke with `--asof 2026-09-24 --phase all`; `FULL_CHAIN.log` L3093 `FUND_NAV` marker `03:56:55`, then L3204-3230 echo that command's own output containing this `clean_release_id` |

Two facts worth carrying forward:

- **R45's producer directory is outside `E:\BLACKBOX\任务`** (it is on `D:`). That is why an
  `E:\BLACKBOX`-only runtime map could not name it.
- **The two ids embed different time zones**: R45 uses local `+0800`, R33 uses **UTC**. Comparing
  id timestamps across the two lines is wrong by 8 hours, and `R45`/`R33` are two product-line
  labels, not sequence numbers.

---

## 6. R15 unit evidence — retained, bounded

From the retained R15 task directory (no rerun):

- acceptance `status=PASS`, `unit_total=19`, `unit_done=16`, `unit_fail=0`, `unit_legal_empty=3`
- quota `197,783,456 → 197,722,946` (consumed 60,510)
- `index_daily_main7 = NO_GAP`
- contract: `get_price`, `fq=None` (`RAW_NONE`), fields `open/close/high/low/volume/money`,
  `skip_paused=true`, `panel=false`
- `LEGAL_EMPTY` rows are the three 2026q3 finance units (not yet disclosed at run date)
- **real short batches were recorded**, e.g. `A股_stock_5m XSHE` requested 2,895 codes but returned
  2,894; `ETF_5m XSHG` requested 893, returned 892 — with `result_status=SUCCESS` and
  `attempt_count=1`

**UNKNOWN, and deliberately not guessed**: vendor page size / offset / next-page token,
terminal-page exhaustion flag, declared query cap, requested universe as sent, supplier-side
completeness certificate. Requested/returned counts alone cannot certify completeness.

---

## 7. Cursor appendix

`CURSOR_EVIDENCE_APPENDIX.json` carries all 54 baseline rows by `dataset_id` with
`existing_cursor_state` unchanged, `new_start`/`new_end` null, `binding_owner` `GPT`.

State histogram matches the baseline exactly: **NOT_BOUND 40 / NOT_APPLICABLE 12 / UNRESOLVED 2**
(baseline `counts` echoed for cross-check). No row was reclassified, and no 54-product scan was run.

---

## 8. Factor note

`FACTOR_EVIDENCE_NOTE.md` keeps three concepts separate — raw price factor **column**, separate
**adjustment-factor product**, and **derived adjusted prices** — and states the boundary plainly:

- the measured 2026 anomaly (13 of 44 sessions in the sealed cache are single-valued `1.0`; 17
  incremental files carry an integer `0..299` date) is an **observation whose cause is not
  established**; it is not evidence of supplier fabrication and not grounds to claim a re-download;
- factor-basis uncertainty blocks **dependent adjusted-price uses** but does not by itself block an
  independently specified `RAW_NONE` scope.

No provider probe, no factor fill, no adjusted-price computation was performed.

---

## 9. What SAM needs in order to complete this child task

A gate that can run on this host. Two options, both requiring a decision that is GPT's or the
owner's, not SAM's:

1. supply a fixture construction that works without symlink privilege on Windows (for example a
   junction-based or copy-based fixture, or an explicit skip-with-disclosure path in the test),
   then SAM re-runs the same 17 controls and, on pass, the collector;
2. or authorise enabling Developer Mode / elevation for this host — a host policy change SAM will
   not make unilaterally.

Until then this return is deliberately partial: **a failed gate, uploaded intact**, plus the
already-retained producer/R15/cursor/factor evidence that did not depend on the collector.

---

## 10. Authority statement

`NEW_DATA_ACQUISITION_AUTHORIZED=false`, `CURRENT_SWITCH_ALLOWED=false`, `ORDER_ALLOWED=false`.
Nothing here is foundation acceptance, acquisition authorisation, data-quality acceptance, or an ACK
of any other dispatch. Task publication is not an ACK; `ACK.json` is.
