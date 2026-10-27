# R3 code-dtype repair — gate PASS, guarded run BLOCKED before authentication

task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R3_CODE_DTYPE
host: ZHANGWEI
order_allowed: false · current_switch_allowed: false · production_raw_write_allowed: false · cleaning_allowed: false

## Outcome

| Control | Result |
|---|---|
| Package stage + 8/8 payload SHA/length + local readback | PASS |
| ACK_R3 uploaded before the gate | PASS |
| 10/10 REUSE_PINS byte-for-byte against the retained R2 staging | PASS |
| Four desktop pointer body hashes vs the R2 baseline | 4/4 PASS, no drift |
| Native gate, 63 tests | 63/63 OK, 0 failures / 0 errors / 0 skips, literal exit 0 |
| Guarded `--execute`, one run | **exit 2 — REGISTERED_DIRECTORY_SET_UNPROVEN** |
| Supplier calls | **0** |
| Quota consumed | **0** (still 5,320 cumulative inherited) |

The code-dtype repair this task was built for is verified. The run did not reach it:
it stopped one control earlier, at the new registered-freshness check, before
authentication. Nothing was requested from the supplier, so nothing can be
reported as missing or empty.

## Why it stopped

R3 introduced `check_registered_freshness`. Line 412:

```python
require(not any(c.is_dir() and c not in ancestors for c in children),'REGISTERED_DIRECTORY_SET_UNPROVEN')
```

Every subdirectory under a parent of a registered Parquet file must itself be an
ancestor of a registered Parquet file. Five directories violate it:

| Directory | Entries (incl. hidden) | Files inside | Created |
|---|---|---|---|
| `P2_stock_daily\none_adj` | 0 | 0 | 2026-10-15 14:17:25 |
| `P8_etf_fund\fund_dividend` | 0 | 0 | 2026-10-15 14:17:25 |
| `P8_etf_fund\fund_nav` | 0 | 0 | 2026-10-15 14:17:25 |
| `P8_etf_fund\fund_profit` | 0 | 0 | 2026-10-15 14:17:25 |
| `P8_etf_fund\fund_share` | 0 | 0 | 2026-10-15 14:17:25 |

All five were created together twelve days ago by the layout writer in
`任务\BLACKBOX_ALL_DOWNLOADED_DATA_FQ_FULL_AUDIT_AND_DELETE_WRONG_R1`, and
`fund_share` / `fund_profit` / `fund_dividend` are declared product slots in
`脚本\jq_download_execution_r1.py` lines 2823–2825. They are declared-but-never-populated
slots, not new arrivals and not absence evidence.

This is not a regression from R2. R2 never ran this control, which is why R2 got
as far as the roundtrip check while R3 stops sooner. The package, the environment
and the data are unchanged.

## What this host deliberately did not do

- Did not delete, move or populate the five slots. Mutating production RAW is
  outside this task's write scope.
- Did not edit the package to allowlist them. Local code edits are forbidden.
- Did not call zero entries "no data". `EMPTY_SLOT != NO_DATA`.
- Did not retry, change a parameter or change the environment. Exit 2 means stop
  and preserve.

## Resolution options for review

- **A** Governed empty-slot allowlist driven by an on-disk product registry: pass
  when the slot is declared and still zero-entry.
- **B** Split the control into `DECLARED_EMPTY_SLOT` (recorded, non-blocking) and
  `UNKNOWN_DIRECTORY` (blocking).
- **C** Relocate declared-but-unpopulated slots outside the registered price
  parents, under explicit write authorization.

Recommended: **B**, sourcing the declared-slot list from the existing product
registry in `jq_download_execution_r1.py`. A alone will not catch genuine empty-dir
drift; C moves the data but leaves the control ambiguous.

## Files in this directory

`ACK_R3.json`, `PACKAGE_VERIFY_R3.json`, `GATE_R3.json` + stdout/stderr,
`RUN_R3.json` + stdout/stderr, `REUSE_VERIFY_R3.json`,
`BLOCKED_DIRECTORY_EVIDENCE_R3.json`, `PLAN_R3.json`, `RESULT_R3.json` (byte-identical
read-only reference to the file R3 wrote under `E:\BLACKBOX\STAGING\...R3`),
`COVERAGE_R3.json`, `DIAGNOSIS_R3.json`, `MANIFEST_R3.json`, `REPORT_R3.md`.

`RUN_R3.json` records that the OS exit code was derived structurally rather than
captured, because the launch was detached; the single run was never repeated.
