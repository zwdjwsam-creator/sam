# ZHANGWEI - R4 return pointer

task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R4_EMPTY_SLOTS
at: 2026-10-27T20:27:55+0800
host: ZHANGWEI

## Verdict

- Package 12/12 verified, read back locally; ACK_R4 and PACKAGE_VERIFY_R4 were uploaded and read back **before** the gate.
- Native gate: **77/77 OK**, 0 failures / 0 errors / 0 skips, **real OS exit 0** captured from a waited child.
- Guarded run: one attached launch, **real OS exit 2**, reason **LIVE_BAR_NULL**.
- Reviewed empty-slot policy: **PASSED**. The five slots were admitted as evidence and the run entered real acquisition.
- Supplier calls **1114**; quota consumed **170538**; cumulative **175858 of 700000**.

## What was actually acquired

| product | sessions planned | full | partial | not attempted |
|---|---|---|---|---|
| stock | 17 | **16** | 1 (2026-10-27, 43/66 batches) | 0 |
| ETF | 17 | 0 | 0 | 17 |
| index | 17 | 0 | 0 | 17 |

86,948 stock rows downloaded (+80 reused read-only from R1, never presented as new),
1,098 raw Parquet files, 17,085,420 bytes.

## Why it stopped

One row in one batch broke `acquire_daily.py:169`: `600621.XSHG` on 2026-10-27 came
back `paused=0` with `open/high/low` null, `close=14.90`, `volume=money=0`. The prior
session shows it suspended (`paused=1`, all prices pinned at 14.90, zero volume), so
this is a vendor-side suspended-then-reopened observation the vendor has not fully
populated. Not a coverage hole, not an outage, not a package defect. Local fill is
forbidden, so stopping was the only compliant response.

## Accepted R3 finding

My `BLOCKED_DIRECTORY_EVIDENCE_R3.json` really does carry `all_predate_r2_run=false`
while listing 2026-10-15 timestamps: I typed an August epoch (1787846788) instead of
the R2 baseline epoch (1793097988). The correct value is true and the timestamps were
always right. The R3 file is preserved byte-for-byte and not patched; the correction
lives in ACK_R4.json and REPORT_R4.md. No R4 logic consumes that Boolean.

## Suggested next step

B + A: isolate the single offending code per session, keep the other 79 rows, and
record the shape (`paused=0`, `volume=0`, `money=0`, close present, OHLC null) as an
explicit vendor observation state with no fill. That keeps 5,223 of 5,224 codes on the
last session instead of losing a whole batch, and still writes the inconsistency as
first-class evidence. ETF and index for the 16 settled sessions are untouched and
ready.

## Delivery

| file | bytes | sha256 |
|---|---|---|
| ACK_R4.json | 5424 | `1439be6fc18b09d633be9445393765fcde87ec55c10f90a5ee474212a2913df6` |
| PACKAGE_VERIFY_R4.json | 7225 | `321530e6f4bdbec2483ef4fc06f4e6fe6e719617e30071060878b1d67bac53a7` |
| GATE_R4.json | 1360 | `989d33d888e496a482310ae4b509f100933e2887023113e03c0b853c5ac8e4c3` |
| GATE_R4_STDOUT.txt | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| GATE_R4_STDERR.txt | 8652 | `3beb243823fae872556fc94e56586fb1dec79cc55b3628c5469b081e56e33355` |
| RUN_R4.json | 1893 | `fb4d4dd8824488d1ea0589668ef189614aad83d70cdf51289ce083e68f16992f` |
| RUN_R4_STDOUT.txt | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| RUN_R4_STDERR.txt | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| COVERAGE_R4.json | 3837 | `9b2ba7054cdc181d6e7fed917a00d81ee63945d613e8cbd9737de058fb000361` |
| SLOT_OBSERVATIONS_R4.json | 5347 | `eca3f245c5f7515fc6529cd36f7aacdba2bbaea1f69b617cc4302d4973ba9587` |
| DIAGNOSIS_R4.json | 8517 | `771fb97675a2c3ff68a3d27129581dfe38137fef20d16b78674fb772161aa289` |
| REPORT_R4.md | 4714 | `bc86f31ea8975a20cbdb8f58e96d4cb73cadb482ef7801dd8721dc6507c12bee` |
| MIRROR_READBACK_R4.json | 1045073 | `2a80cc714d372d7e4873defb275413391328b6b9e570f5be28d2fab7b1cad2c4` |
| UPLOAD_READBACK_R4.json | 5690 | `13f1107c2b18925bb5fa2029313123d28a9b32f066d3cc70ecb7694c2ded720b` |
| LOCAL_READBACK_R4.json | 3925 | `9b3713ba1cee13d5a531ee6f7a8c891073be130c69288227ef0e632ad14ae4b5` |

`r4_staging_output/` mirrors **3363/3363** new R4 JSON byte-for-byte across 12 chunk
commits. Verification: one recursive tree of the final mirror commit matched every
git blob SHA1 (0 missing, 0 extra, 0 mismatch), plus 24 deterministic body re-reads
through the blobs API, all byte-equal. Raw Parquet stayed append-only on the host and
is published as path + length + SHA256 only, so the retained first-80 batch is never
mistaken for new rows.

Local reconciliation after upload: 16 top-level deliverables, 3363 staging JSON and
1098 raw files recomputed from disk with **0 mismatches** - nothing moved.
