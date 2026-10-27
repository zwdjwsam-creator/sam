# HANDOFF_NOTES — chain_source_001 (SAM)

- child_task_id: `BLACKBOX_UPDATE_PREREQUISITES_SAM_20261027`
- dispatch_id: `BLACKBOX_UPDATE_PREREQUISITES_20261027`
- generated_at_cn: 2026-10-27T14:12:58+0800
- gate: native V3 23/23 PASS (exit 0); collector attempt-3 actual exit **2** (retained partial)
- plan: `EXACT_CHAIN_SOURCE_PLAN_20261027.json`, exactly 14 named paths

## 1. Result

| seq | file | status | bytes | sha256[:16] | readback |
|---|---|---|---|---|---|
| 1 | `download_daily_r1.py` | CAPTURED | 10728 | `f6d8b81c756850c0` | True |
| 2 | `download_val_adjust_r1.py` | CAPTURED | 7232 | `2a932fbd3e6a7f30` | True |
| 3 | `download_billboard_ingest_r1.py` | CAPTURED | 5104 | `2adc8c2c34259597` | True |
| 4 | `download_xr_xd_r1.py` | CAPTURED | 5873 | `ec7bb8c9ee80c768` | True |
| 5 | `minute_download_20260924.py` | CAPTURED | 15467 | `33d8d2fa0b706464` | True |
| 6 | `ingest_minutes_r1.py` | CAPTURED | 3881 | `a7e608bd482d1551` | True |
| 7 | `ingest_minutes_flat_r1.py` | CAPTURED | 2500 | `1b6cefbbe2bcd0ca` | True |
| 8 | `sw_l123_asof_20260924.py` | CAPTURED | 13549 | `f195dd47b79193a8` | True |
| 9 | `index_minute_20260924.py` | CAPTURED | 7218 | `0809300f67fd8cd1` | True |
| 10 | `align_index_minute_20260924.py` | CAPTURED | 3976 | `33bfd6f1fd1251e0` | True |
| 11 | `patch_candidate_val_sw_republish_r1.py` | CAPTURED | 4931 | `e4f20b14bc6e87fe` | True |
| 12 | `pick_cache_candidate_r1.py` | CAPTURED | 1518 | `ce9f141239b20725` | True |
| 13 | `DOWNLOAD_ACCEPTANCE.json` | CAPTURED | 2628 | `306483d1a0bed633` | True |
| 14 | `jq_download_base.py` | REUSED_HUB_BODY | 8460 | `9c6c7a76f434fae6` | True |

Status counts: `{"CAPTURED": 13, "REUSED_HUB_BODY": 1}`.
Copied 13 bodies, 84605 bytes total,
well inside the 2 MiB/file and 16 MiB/total caps. No cap was reached.

## 2. Credential handling — and why there were two passes

Pass 1 used a keyword list that included the bare token `auth(`. That token matches ordinary code
such as `from jqdatasdk import auth` or `auth(user, pw)`, i.e. a **function call**, not an embedded
credential. It therefore blocked 8 of the 14 named sources without a literal being present.

Pass 2 re-inspected only those rows with **literal-only** patterns:

- quoted `password` / `passwd` / `pwd` / `secret` / `token` / `api_key` / `access_key` / `user_id`
  assignments (`name = "..."` with a real quoted value)
- `auth("...")` **with quoted arguments** (an actual embedded credential)
- `-----BEGIN ... PRIVATE KEY-----` blocks
- GitHub `gh[pousr]_...` and AWS `AKIA...` literal shapes

Result: 8 upgraded to CAPTURED, 0 still blocked. Pass 1 is preserved verbatim as
`SOURCE_MANIFEST_PASS1_PRESERVED.json`; nothing was discarded. At no point was any candidate literal
printed, stored, hashed or uploaded — a literal hit withholds the entire file with no hash and no
copy.

This is a **detection-quality correction of my own scanner**, not a modification of any reviewed
package file, and not a re-run of the collector.

## 3. Reuse, not duplication

`E:\BLACKBOX\脚本\jq_download_base.py` is 8,460 B / `9c6c7a76...` — byte-identical to the body
already registered in `SOURCE_INDEX.json`. Per the plan it is returned as `REUSED_HUB_BODY` with
that reference, and the redundant copy written during the export was removed locally so no duplicate
is uploaded.

## 4. GENERATOR_DIRECTORY_INDEX

`D:\CURSOR_TASK_ARCHIVE\JQ_TIP_CATCHUP_UNATTENDED_R1` — status `OK`, depth 1, **27 entries**
(limit 100), `truncated_at_limit=False`. Names and entry types only; no
body was read, no reparse point followed, no recursion.

Observed names include `run_unattended_catchup_r1.py`, `pick_cache_candidate_r1.py`,
`rm_incomplete_tip_rebase_stubs_r1.py`, `report_progress_r1.py`, the loop/watchdog scripts and their
logs and pid files, plus `__pycache__`. **No generator is asserted**: a name in this index is not
evidence that it generated any particular release, and the plan leaves generator selection to GPT.

## 5. Boundaries actually held

No download, no supplier call, no quota probe, no authentication, no credential file opened, no
retry of the collector, no production `CURRENT`/SSOT/rule write, no release publication, no V4
reconstruction, no deletion of prior evidence, no order.

A current source hash is **not** historical process attestation: these are the bytes on disk now,
not proof of which code executed on 2026-09-24. A missing path would not have been evidence of
absent business data.
