# R4 — empty-slot policy cleared; real acquisition ran and stopped on one vendor observation

task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R4_EMPTY_SLOTS
host: ZHANGWEI
order_allowed: false · current_switch_allowed: false · cleaning_allowed: false · production_raw_write_allowed: false

## Outcome

| Control | Result |
|---|---|
| Package stage, 12/12 payload length+SHA256, local readback | PASS |
| ACK_R4 + PACKAGE_VERIFY_R4 uploaded and read back before the gate | PASS |
| Native gate, 77 tests | **77/77 OK**, 0 failures / 0 errors / 0 skips, **real OS exit 0** |
| Guarded `--execute`, one attached run, real OS exit captured | **exit 2 — LIVE_BAR_NULL** |
| Reviewed empty-slot policy | **PASSED** — cleared the guard R3 failed |
| Supplier calls | 1,114 |
| Quota consumed this run | 170,538 (cumulative 175,858 of 700,000) |
| Stock sessions fully acquired | **16 / 17** |
| Stock rows downloaded | 86,948 (+80 reused read-only) |
| Raw Parquet files | 1,098 (17,085,420 bytes) |
| ETF / index | 0 / 17 and 0 / 17, never attempted |

The R3 blocker is genuinely gone. The five reviewed slots were admitted as evidence,
not as data, and the run proceeded into live acquisition — the first time this
sequence has actually downloaded anything.

## What stopped it

`acquire_daily.py:169` requires that any row the vendor marks `paused=0` carries
non-null `open/high/low/close/volume/money`. One row in one batch broke that:

| Field | Value |
|---|---|
| code | `600621.XSHG` |
| date | 2026-10-27 |
| paused | 0 |
| open / high / low | null / null / null |
| close | 14.90 |
| volume / money | 0 / 0 |

The context is clean, not a hole:

| date | paused | open | high | low | close | volume |
|---|---|---|---|---|---|---|
| 2026-10-23 | 0 | 14.09 | 15.22 | 13.79 | 14.90 | 84,069,699 |
| 2026-10-26 | **1** | 14.90 | 14.90 | 14.90 | 14.90 | 0 |
| 2026-10-27 | **0** | null | null | null | 14.90 | 0 |

The stock was suspended on 10-26 (every price pinned, zero volume), and on 10-27 the
vendor flipped `paused` back to 0 with zero volume but never populated the intraday
price set. That is a vendor-side suspended-then-reopened observation, not a coverage
gap, not a supplier outage, and not a defect in the reviewed package. The control did
exactly what it was written to do: it refused to manufacture an open price.

Consequence: 2026-10-27 stopped at batch offset 3360 after 43 of 66 batches. The
other 16 sessions are complete. ETF and index never started.

## R3 finding accepted

The reviewer was right that my `BLOCKED_DIRECTORY_EVIDENCE_R3.json` contains
`all_predate_r2_run=false` while listing 2026-10-15 timestamps. I had typed an August
epoch (1,787,846,788 = 2026-08-28) as the comparison bound instead of the R2 baseline
epoch (1,793,097,988 = 2026-10-27 18:46:28). The correct value is `true`. The five
timestamps themselves were and remain correct. The R3 file stays byte-for-byte as
published; the correction is stated here and in `ACK_R4.json`, not patched into
history. Nothing in R4 consumes that Boolean — the policy re-measures each slot live.

## Resolution options for review

- **A** Add an explicit observation state for this shape (`paused=0`, `volume=0`,
  `money=0`, close present, OHLC null), recorded as the vendor's truth, with no fill.
- **B** Isolate the single offending code per session, keep the other 79 rows, and
  record a per-code vendor gap instead of stopping the whole product.
- **C** Defer 2026-10-27 until the vendor settles and spend the time on ETF/index for
  the 16 completed sessions.
- **D** Keep the hard stop and treat any such row as a blocking vendor defect.

Recommended: **B + A**. That preserves 5,223 of 5,224 codes on the last session and
still writes the inconsistency as first-class evidence rather than discarding a whole
batch or inventing a price.

## Budget

170,538 of the 694,680 allowed was spent; 524,142 of this task's allowance remains,
and 175,858 cumulative of the 700,000 ceiling. No new login, no budget reset, no
retry, no parameter change, no environment change.

## Files

Top level: `ACK_R4.json`, `PACKAGE_VERIFY_R4.json`, `GATE_R4.json` + stdout/stderr,
`RUN_R4.json` + stdout/stderr, `COVERAGE_R4.json`, `SLOT_OBSERVATIONS_R4.json`,
`DIAGNOSIS_R4.json`, `REPORT_R4.md`, `DELIVERY_MANIFEST_R4.json`,
`UPLOAD_READBACK_R4.json`, `LOCAL_READBACK_R4.json`.

`r4_staging_output/` mirrors every newly generated R4 JSON byte-for-byte. Raw Parquet
is append-only on the host and is listed with exact path, length and SHA256 rather
than uploaded, so the retained first-80 batch is never presented as newly downloaded.
