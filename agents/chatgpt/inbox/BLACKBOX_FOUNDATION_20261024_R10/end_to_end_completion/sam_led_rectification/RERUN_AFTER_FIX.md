# RERUN_AFTER_FIX — R15 cleaning replay (desktop / ZHANGWEI)

Written by SAM, 2026-10-25 (rev. R11). Supersedes every earlier version of this note.
The two code files referenced below are already in place on the desktop; this note only
explains the defect, the fixes and the exact rerun/verification procedure.

## 1. Root cause — silent long-path skip in the materialiser

The materialiser tested each source file with `Path.is_file()`. On Windows that call swallows
`OSError` (including `ERROR_PATH_NOT_FOUND` / `ERROR_FILENAME_EXCED_RANGE`) and simply returns
`False`. The staging tree contains files whose **full path length is 289 characters**, beyond the
261-character limit that the plain (non-prefixed) Win32 path accepts in this configuration.

* 12 files in `standard/price/stock_ohlcv_daily` exceeded that limit → `Path.is_file()` returned
  `False` → they were **silently skipped**, no exception, no warning.
* The 222 files that did land were all <= 261 characters.
* Consequence: the window **2026-07-03 .. 2026-07-10** collapsed to **19 codes / 31,136 rows**.
* Every trading-date key still existed, so no schema/date/coverage gate complained. The loss only
  surfaced as a shortfall in the aggregate row count of the compiled `year=2026` partitions
  (`rows_2026 = 928,760` instead of `959,896`, i.e. exactly the missing 31,136 rows).

Conclusion: this was a *path-length* defect, not a data, date-source or factor defect. Any "fix"
that edits numbers or rebuilds from a different asof would be wrong.

## 2. Fixes shipped

### 2.1 `candidate/run_r15_cleaning_replay.py` — materialisation is now fail-closed

sha256 `f2c858e4875a5a6de55f2b5cfdf46c08f83fad992c25e5897f19e6ec77804044`, 29,825 bytes.
Previous file preserved as `candidate/run_r15_cleaning_replay.py.bak_sam_led_r11`
(and the older `..._r10` backup is still there).

1. **Long-path prefix**: every materialise-side path is rewritten through a helper that prefixes
   `\\?\` (or `\\?\UNC\` for UNC paths) before any filesystem syscall, so 289-char paths are legal.
2. **Explicit `stat`**: existence is decided by `os.stat` on the prefixed path with the real
   `OSError` propagated — never by a boolean that can silently mean "I could not tell".
3. **`MATERIALIZE_INCOMPLETE` hard gate**: after materialisation the runner compares the source
   file set with the destination file set (name + size). On any difference it writes
   `MATERIALIZE_INCOMPLETE.json` into the release root and exits **3** with
   `HARD_BLOCK: MATERIALIZE_INCOMPLETE`. A partial materialisation can no longer produce a
   sealed-looking release.

### 2.2 `tools/candidate_commit.py` — rebind / repair semantics

sha256 `7cb9417cdb96be7ff4881d792db1f237f8db255f0a75eadcba90fa8c93617bf2`, 20,732 bytes.
Previous file preserved as `tools/candidate_commit.py.bak_sam_led_r11`.

The commit id is now `CC_COMMIT_IDENTITY_V2`: it hashes **data only** (`asof`,
`source_cleaning_release`, `parent_release_id`, and each product's `sha256` + `rows`). Build
metadata (release id, release path, `RELEASE.json`, `SEAL.json`, `_qa/*`) is explicitly excluded,
because every rebuild carries a new timestamp and used to make `IDEMPOTENT_NOOP` unreachable.

Resulting semantics, all recorded explicitly in `COMMIT.json`:

| situation | status | effect |
|---|---|---|
| same content, same root, same release_id | `IDEMPOTENT_NOOP` | reference untouched |
| same content, same root, stale release_id/asof label | `REPAIRED_SAME_ROOT_FIELD_DRIFT` | checkpoint + commit relabelled in place (`repaired_from_release_id`) |
| same content, different root, old root still present | `IDEMPOTENT_NOOP` | reference stays on the old root; new root recorded as `candidate_release_root` |
| same content, referenced root has moved/vanished (e.g. archived) | `REBOUND_SAME_CONTENT_NEW_ROOT` | single authoritative reference rebound to the new root (`rebound_from_release_root`) |

Rebinding is safe *precisely because* an equal commit id proves the new tree holds the same
products/rows/sha256. Nothing here writes production `CURRENT`.

## 3. Exact command to run on the desktop

One-shot (replay + original compiler, default release id `R15_REPLAY_20260924_R3`):

```bat
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\run_connected_pipeline.py --r15-rid R15_REPLAY_20260924_R3
```

Cleaning-only variant (stops after the R15 seal, no compile):

```bat
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 candidate\run_r15_cleaning_replay.py --asof 2026-09-24 --rid R15_REPLAY_20260924_R3
```

Exit code must be **0**. If the runner exits **3** with `MATERIALIZE_INCOMPLETE`, do not patch
numbers: report the `stats` block in `MATERIALIZE_INCOMPLETE.json` and stop.

## 4. Expected post-fix numbers (must match exactly, otherwise STOP)

**A. R15 standard price plane — 234 parquet files, 12 of them r2_repair**

```
candidate\r15_releases\R15_REPLAY_20260924_R3\standard\price\stock_ohlcv_daily
-> 234 parquet files, including 12 with "r2_repair" in the name
```

```bat
E:\BLACKBOX\.venv\Scripts\python.exe -c "import pathlib; p=pathlib.Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\candidate\r15_releases\R15_REPLAY_20260924_R3\standard\price\stock_ohlcv_daily'); f=list(p.glob('*.parquet')); print('files',len(f)); print('r2_repair',len([x for x in f if 'r2_repair' in x.name]))"
```

Expected: `files 234` / `r2_repair 12`. (The pre-fix run produced `files 222` / `r2_repair 0`.)

**B. Compiled `year=2026` — 959,896 rows**

In the newest release under `candidate\cc_out\releases\`, `_qa\TIP_REBASE_QA.json`:

```
price.products.STOCK_DAILY_PIT_R1.rows_2026        = 959896
price.products.STOCK_DAILY_RAW_PIT_R1.rows_2026     = 959896
price.products.STOCK_FACTOR_DAILY_R1.rows_2026      = 959896
```

Delta versus the bad run: `959,896 - 928,760 = +31,136` rows recovered.

**C. Same-input replay is idempotent and the ledger is consistent**

Re-run the *same* command on the *same* inputs a second time. Required outcome:

* `candidate_commit` returns `"status": "IDEMPOTENT_NOOP"` (a `REBOUND_SAME_CONTENT_NEW_ROOT` or
  `REPAIRED_SAME_ROOT_FIELD_DRIFT` is acceptable only if the referenced root genuinely moved or the
  label was stale — the receipt must say so). No new content commit id may appear for identical
  input.
* Then:

```bat
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\candidate_commit.py --action verify
```

must print `"status": "CONSISTENT"` (exit 0). `INCONSISTENT`, `PAYLOAD_ROOT_MISSING` or exit 4
means STOP and report the full JSON.

## 5. State of the candidate tree at hand-off

* `candidate\r15_releases\R15_REPLAY_20260924_R3` — **absent** (clean).
* `candidate\cc_out\releases\` — **0 subdirectories** (clean; directory itself kept).
* Because both were already clean, SAM archived **nothing** on this pass (`_sam_final_<ts>` was not
  created). Earlier bad outputs remain under the existing `_BAD_*_archived_*` folders — moved, never
  deleted.

## 6. Hard rules for this rerun

- Move only, never delete, on the desktop.
- No production `CURRENT` switch, no `patch_hand` — candidate outputs only.
- Do not download history; the replay uses the retained RAW batches.
- Do not hand-edit numbers in evidence files.
- Backups (`*.bak_sam_led_r11`) must stay in place; do not overwrite them.
