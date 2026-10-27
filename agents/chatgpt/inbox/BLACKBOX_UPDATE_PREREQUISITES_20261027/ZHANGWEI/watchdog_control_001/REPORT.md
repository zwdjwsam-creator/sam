# WATCHDOG_CONTROL_20261027 — ZHANGWEI bounded audit result

dispatch_id: BLACKBOX_UPDATE_PREREQUISITES_20261027
parent_task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
contract_id: WATCHDOG_CONTROL_20261027
host: ZHANGWEI
role: ZHANGWEI
recorded_at_cn: 2026-10-27T16:05:00+0800
status: COMPLETED_BOUNDED

FOUNDATION_ACCEPTANCE=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
SAM_EXACT_WATCHER_STOP_ALLOWED=false on this host
DESKTOP_STOP_OR_DISABLE_ALLOWED=false

## 1. Gate outcomes

Package staged byte-verbatim from the raw git blobs and verified: **4/4** payloads match
declared length and SHA256, and each file was re-read after writing with no drift.

Ten policy controls, run once with the exact prescribed command:

- actual exit code **0**
- `Ran 10 tests in 0.002s`, `OK`
- **0 failures, 0 errors, 0 skips**

Only then was `watchdog_control.py --role ZHANGWEI --out …\watchdog_control_001` executed,
once. `--allow-sam-stop` was **not** passed. The output folder was **not** pre-created.
Actual exit code **0**. Both stdout and stderr were empty; the complete script product is
`RESULT.json` (8,627 bytes, SHA256 in the manifest, byte-untouched by this report).

`host` and `role` in RESULT.json both read `ZHANGWEI`, `order_allowed=false`,
`authorized_sam_stop=false`.

## 2. What was actually stopped or disabled: nothing

`actions: []`. Zero actions. Zero `INTENT` files — the script writes an INTENT file only
when it proposes an action, so an absent `INTENT` file here means *nothing was proposed*,
not a missing export.

Desktop task identity and state, before and after, are **identical**:

| TaskPath | TaskName | Enabled | State | proven_kind |
|---|---|---|---|---|
| `\` | `AUTOHUB_LOCAL_WATCHDOG_ZHANGWEI` | true | Running | **null** |

`proven_kind = null` means the script did **not** prove this task to be the archive watcher.
It was therefore correctly left alone. This is the honest reading: the desktop *does* run a
watchdog-named task, but it was not identified as the authorized target and remains
**enabled and running**. No disable, no stop, no restart, no `Stop-ScheduledTask`.

Watcher processes: `before.processes` and `after.processes` are both **empty**. No process
matched the exact watcher identity, so there are **no watcher PIDs or creation times to
report** — an empty list is the measured outcome, not a suppressed field.

`raw_command_lines_exported=false`: the raw in-memory global process/task metadata was
never exported, consistent with the contract.

## 3. Control files on `D:`: both absent here

| Path | Status | Reason |
|---|---|---|
| `D:\CURSOR_TASK_ARCHIVE\JQ_TIP_CATCHUP_UNATTENDED_R1\TARGET_END.txt` | UNRESOLVED | FileNotFoundError |
| `D:\CURSOR_TASK_ARCHIVE\JQ_TIP_CATCHUP_UNATTENDED_R1\FINAL_STATUS.json` | UNRESOLVED | FileNotFoundError |

The `D:\CURSOR_TASK_ARCHIVE` tree is not present on ZHANGWEI, so neither control file could
be read. These are **explicit gaps**, not data absence, and no fallback scan or alternate
path was substituted. Nothing was executed.

## 4. RAW 20260924 filename listing: three directories, one capped

Only immediate, non-linked `.parquet` filenames containing `20260924` were listed, with size
and mtime. No recursion, no Parquet content read, no data hash, `contents_read=false` and
`source_absence_claim_allowed=false` on every entry.

| Directory | Matches returned | Distinct gap dates | Bytes listed | Limit |
|---|---|---|---|---|
| `P2_stock_daily` | 10 | 9 | 3,107,483 | — |
| `P3_index` | 13 | 9 | 120,574 | — |
| `P4_fund_etf_raw_none\fund_etf_price_daily` | 13 | 9 | 1,333,028 | **ENTRY_CAP** |

The nine gap dates observed in all three listings are **20260914–20260918 and
20260921–20260924**; each carries a `__full__` or plain `incremental_gap` writer stamp such
as `20260924_082242` and `20260925_030125`.

**The P4 result is partial and must not be read as complete.** That directory holds
**14,024** immediate files, so the 10,000-entry enumeration cap was hit and the script
itself marked the entry `ENTRY_CAP`. The 13 returned matches are whatever fell inside the
first 10,000 entries in enumeration order; files beyond that were never examined. Full
coverage — and therefore any absence claim — is **not established** for P4.

For all three directories: these are **filenames only**. They do not prove which
`(date, code)` rows are present or duplicated, they authorize **no deletion and no
deduplication**, and they must not replace the pinned existing inventories as context.

## 5. Errors and unknown state, stated plainly

- Two named control files unreadable (`FileNotFoundError`) — gap, not absence.
- One directory listing capped (`ENTRY_CAP`) — partial, not complete.
- One desktop task (`AUTOHUB_LOCAL_WATCHDOG_ZHANGWEI`) left **enabled and running**,
  identity unproven.
- No watcher process found at all, so nothing was verifiable as "already stopped" either.

No applied change is claimed merely because a plan was published. Nothing on this host was
stopped, disabled, restarted, deleted, downloaded, switched, published or ordered. No
supplier call, no business-module import, no credential read, no write under `E:\BLACKBOX`,
no fixture or collector rerun.

## 6. Delivered files

`ACK.json`, `PACKAGE_VERIFICATION.json`, `POLICY_TEST.json`,
`POLICY_TEST_STDOUT.txt`, `POLICY_TEST_STDERR.txt`, `COMMAND.json`,
`COMMAND_STDOUT.txt`, `COMMAND_STDERR.txt`, `RESULT.json` (script product, untouched),
`REPORT.md`, `DELIVERY_MANIFEST.json`, `UPLOAD_READBACK.json`, `LOCAL_READBACK.json`.

`POLICY_TEST_STDOUT.txt` and `COMMAND_STDOUT.txt` are legitimately 0 bytes: `unittest`
writes its verbose log to stderr, and the control script prints nothing on success.

Receipts are ordered acyclically so that no document has to embed its own or a successor's
hash; `LOCAL_READBACK.json` is last and is referenced by nothing.
