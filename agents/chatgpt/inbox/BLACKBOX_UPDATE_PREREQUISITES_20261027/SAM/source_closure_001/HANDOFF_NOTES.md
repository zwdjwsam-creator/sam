# HANDOFF_NOTES — source_closure_001 (SAM)

- child_task_id: `BLACKBOX_UPDATE_PREREQUISITES_SAM_20261027`
- parent_task_id: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`
- dispatch_id: `BLACKBOX_UPDATE_PREREQUISITES_20261027`
- execution_host: SAM (historical-source / evidence peer only)
- task: `EXACT_SOURCE_CLOSURE_TASK_20261027_1501.md`
- plan: `EXACT_SOURCE_CLOSURE_20261027_1501.json` (`EXACT_ORIGINAL_GENERATOR_AND_RCID_CLOSURE_R1`)

---

## 1. Result

Exactly **one** named source was read, per the SAM role in the plan:

| seq | source | status | bytes | sha256 | readback |
|---|---|---|---|---|---|
| 1 | `D:\CURSOR_TASK_ARCHIVE\JQ_TIP_CATCHUP_UNATTENDED_R1\run_unattended_catchup_r1.py` | **CAPTURED** | 29,975 | `9416691f21c2a7c7…` (full value in the manifest) | `true` |

- Line endings preserved raw: **698 CRLF, 0 lone LF** (pure CRLF file). Bytes stored exactly as
  read; no newline normalisation.
- Size and mtime were re-stat'ed after the read and were unchanged (no `SOURCE_CHANGED_DURING_READ`).
- Caps were not approached: 29,975 B against a 2 MiB/file and 8 MiB/total limit.
- No recursion, no wildcard, no fallback root, no directory search, no import, no execution.

`LOCAL_READBACK.json` records the byte-identical local re-read of the captured copy.

## 2. Its actual role — reported plainly, not invented

The task said to return the source even if it is **not** a generator, and to state its actual role.
It is **not a market-data generator**. Measured from the body:

- It is a **task-package templater plus unattended driver** for the daily TIP catch-up.
  `COPY_GLOBS` names 14 template scripts copied from `JQ_DAILY_TIP_20260909`; the copy step rewrites
  dated tokens (`2026-09-09` → asof, `20260909` → compact) and rewrites `PARENT_ID` inside the
  copied `clean_switch_r1.py`.
- It **regenerates `_run_full_chain.ps1`** as a literal string (an f-string in this file), whose
  ordered `RunPy` steps are: `download_daily_r1.py`, `download_val_adjust_r1.py`,
  `download_billboard_ingest_r1.py`, `download_xr_xd_r1.py`, `code/minute_download_<compact>.py`,
  `ingest_minutes_r1.py`, `ingest_minutes_flat_r1.py`, `sw_l123_asof_<compact>.py`,
  `code/index_minute_<compact>.py`, `code/align_index_minute_<compact>.py`, `clean_switch_r1.py`.
  This is the **origin of the `RUN ...` markers** seen in `FULL_CHAIN.log`.
- It then invokes the chain with
  `subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-File", script])`
  and advances day by day in a loop, gated on a `15:05` Asia/Shanghai cutoff for sealing today's
  tip, with `PROGRESS.json`, `UNATTENDED.log`, `unattended.lock`, `TARGET_END.txt` and `FATAL.json`
  as its own state files.

So: it is the **generator of the per-day task package and of the full-chain PS1**, and the driver
that runs them. Market-data acquisition itself lives in the copied `download_*` bodies, not here.

## 3. Two concrete closures this body provides

**(a) It names the writer of the September-24 completion record.** `write_completion()` calls
`wjson(ROOT / "运行" / f"BLACKBOX_JQ_{mmdd}_TIP_INCREMENT_COMPLETION_CURRENT.json", body)`, so for
asof 2026-09-24 the producer of `运行\BLACKBOX_JQ_0924_TIP_INCREMENT_COMPLETION_CURRENT.json` is
this file's `write_completion`. That record appeared in an earlier capture plan without a producer
and is now bound to an exact source body. It also writes the sibling
`JQ_DAILY_TIP_<compact>\COMPLETION_STATUS.json`.

**(b) It shows what that record can and cannot certify.** In that body, `FINAL_STATUS` and
`JQ_MAINCHAIN.STATUS` are computed **only** by comparing date strings:
`"PASS" if source == asof == clean == cache else "PARTIAL"`. There is no row count, key set, hash,
page or exhaustion check in that computation. A `PASS` there therefore means *the three CURRENT
date strings agree*, not that the underlying data is complete. This is consistent with the review's
statement that neither a historical PASS nor a nonempty batch proves acquisition prerequisites.

## 4. Corroboration of the "runtime rewrite" concern

The generated PS1 contains, for the candidate patch step:

```powershell
$txt  = [System.IO.File]::ReadAllText($patch)
$txt2 = [regex]::Replace($txt, "BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_{compact}_[A-Z0-9_]+", $candName)
[System.IO.File]::WriteAllText($patch, $txt2)
RunPy $patch
```

i.e. a candidate script **is rewritten on disk, then executed**, inside the same generated chain.
That is direct source evidence supporting the owner summary's point that a historical shell could
rewrite a body before running it, and that today's bytes are not automatically the historical
executed bytes. SAM asserts nothing beyond that.

## 5. Boundaries held

- No import or execution of this body or any historical chain; no `download_*`, watchdog, cleanup or
  loop script was read or run.
- No additional directory search, no factor-file scan, no SDK probe, no download.
- No credential file access, no authentication, no quota/supplier request. Literal-only inspection
  found **no embedded credential literal** — the file contains **zero** auth constructs
  (`auth_ordinary = 0`), so nothing was withheld on that ground.
- No `CURRENT`/SSOT/rule write, no release, no V4, no deletion, no terminal restart or process kill.
- Prior SAM evidence preserved: collector attempt-3 **exit 2** retained partial (not rerun), the
  14-source handoff (13 captured + `jq_download_base.py` reference), V1/V2 failures, the scanner
  first-pass false positives, and the disclosed late-ACK / separate-session provenance.
- SAM's data plane stays **historical evidence only**; nothing was promoted, published or
  synchronised towards the desktop baseline.

A source body is **not** historical execution proof. A missing exact path would be a gap, not
absence of business data.
