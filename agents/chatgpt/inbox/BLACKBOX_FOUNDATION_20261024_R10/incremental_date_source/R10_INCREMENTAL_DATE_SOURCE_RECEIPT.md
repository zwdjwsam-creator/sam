# R10 continuation — delivery completion, incremental RAW date axes, and the R33 adjust_factor layer

Executor: ZHANGWEI. Round: `R10_INCREMENTAL_DATE_SOURCE_AND_R33_20261025` (R10 continuation, NOT acceptance).
Outbox instruction: `BLACKBOX_FOUNDATION_R10_INCREMENTAL_DATE_SOURCE_AND_R33_20261025.md` (7,487 B).
Review note read: `reviews/BLACKBOX_FOUNDATION_R10_SOURCE_BATCH_CHAIN_20261025/DESKTOP_EVIDENCE_REVIEW_0135.md` (4,221 B).
Measurement window: 2026-10-25 01:44:08 – 01:47 +08:00.

Append-only. No earlier receipt is rewritten. Everything below was executed or read in this round.

FOUNDATION_ACCEPTANCE=false · FORMAL_ENGINE_ADMISSION=false · NEW_DATA_ACQUISITION_AUTHORIZED=false ·
CURRENT_SWITCH_ALLOWED=false · ORDER_ALLOWED=false · SOURCE_ABSENCE_CLAIM_ALLOWED=false · B1..B7 OPEN.

---

## 0. Reuse boundary

Reused, not rerun: the accepted source-batch chain controls and measurement (8 controls, 182 batches,
12,176,722 rows, source↔Cleaning identity through 2026-08-14), the 13-year Cleaning↔CACHE basis work, the
dirty-branch measurement, catalog inventory, and the original downloader lookup. The driver
`r10_factor_source_batches.py` was **not** executed in this round. No supplier call, no login, no producer
execution, no drive scan, no broad code-root scan, no credential read.

## 1. Finishing the prior delivery without a new upload cycle

The review's observation was correct and is confirmed by local bytes: the previously uploaded helper
`EXECUTED_HELPER_TOOLS/r10_sbc_manifest_upload.py` ends by writing
`r10_source_batch_chain_delivery/FINAL_BYTE_READBACK.json` locally and printing `READBACK`; it contains no
subsequent PUT of that file. The local receipt existed and was complete (21,703 B, sha256
`b116bf1df649b5752547945b837cf75fc17f60668194de68927022d65ce115c3`, 31/31 members, `readback_cn`
2026-10-25T01:30:50+08:00).

Action: uploaded **that exact pre-existing file** to
`agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/source_batch_chain/FINAL_BYTE_READBACK.json`
(commit `218250d6`). Pre-upload state was HTTP 404, matching the review. Post-upload readback: remote size
21,703 = local, remote sha256 identical, payload `readback_cn` unchanged. No time regenerated, no capture
overwritten, no member re-uploaded, no duplicate finisher. Record:
`SOURCE_BATCH_CHAIN_FINAL_RECEIPT_UPLOAD.json`.

## 2. Fixed read-only schema examination of the three located RAW files

Genuine preflight first, through the pinned operating entry, exit 0, 01:44:08.97–01:44:09.98:

    blackbox_operate_r10.py describe --product ADJUST_FACTOR_PIT_R1
    real_preflight ok=true  MUST_READ_PRECHECK=PASS  task_class=[CACHE]  problems=[]
    BOOTSTRAP   VERIFIED 704527e0…  DATA_ACCESS VERIFIED 09035518…  kernel b05a6995…

All three pin hashes were re-verified before reading and were unchanged. Nothing was imported, logged into or
fetched.

Common file facts: 4 physical columns in the order `date, code, factor, sec_type`; one row group;
`created_by = parquet-cpp-arrow version 24.0.0`; key-value metadata only `ARROW:schema` and `pandas`;
pandas `index_columns = []` (so no persisted index and no index level in the file); the in-memory frame gets a
default `RangeIndex`, name `null`, dtype `int64`; `total_null_cells = 0`.

| file | bytes | rows | `date` Arrow type | distinct dates | nulls | `factor` distinct |
| --- | --- | --- | --- | --- | --- | --- |
| `…incremental_20260831__20260831_163108.parquet` | 36,967 | 5,212 | `int64` | 300 | 0 | 1 (1.0) |
| `…incremental_20260901__20260901_171005.parquet` | 36,980 | 5,214 | `int64` | 300 | 0 | 1 (1.0) |
| `…incremental_20260924__20260925_030214.parquet` | 34,838 | 5,222 | `timestamp[ns]` | 1 | 0 | 1 (1.0) |

Observed `date` literals:

    20260831  first five [0, 1, 2, 3, 4]   last five [107, 108, 109, 110, 111]   min 0   max 299
    20260901  first five [0, 1, 2, 3, 4]   last five [109, 110, 111, 112, 113]   min 0   max 299
    20260924  first five ['2026-09-24T00:00:00' x5]  last five [same]  min=max 2026-09-24

Recorded head samples (date/code/factor, original values):

    20260831  0 "000001.XSHE" 1.0 | 1 "000002.XSHE" 1.0 | 2 "000006.XSHE" 1.0
    20260901  same pattern starting at 0 "000001.XSHE" 1.0
    20260924  "2026-09-24T00:00:00" "000001.XSHE" 1.0 | "000002.XSHE" 1.0 | "000006.XSHE" 1.0

Interpretation discipline, as instructed: the two `0..299` axes are recorded as **uninterpreted int64
ordinals**. They were not parsed as nanoseconds, not converted to calendar dates, not replaced by another time
column (none exists), and no date was inferred from either filename. This is an observation, not schema
admission.

Independent agreement: the retained R08 evidence `r08_delivery/evidence/adjust_factor_raw_date_axis.json`
records the same two files as `INT64_PAGE_ORDINAL`, distinct 300, min 0, max 299, factor 1.0, sidecar absent.
This round's separate read reproduces it exactly.

## 3. The already declared R33 adjust_factor layer

Bounded, non-recursive enumeration of exactly one product directory (limits 256 entries / 64 parquet, no
traversal through reparse targets): **18 entries, 18 parquet, 0 non-parquet, 0 reparse points**. This matches
the retained `runtime/file_index_ADJUST_FACTOR_CLEAN.json` (n_files=18, observed 2026-08-10..2026-09-24) and
the prior figure of 18; the count was recorded, not forced.

Every file: 4 columns `date, code, factor, sec_type`, one row group, `parquet-cpp-arrow 24.0.0`, pandas
`index_columns=[]`, in-memory default `RangeIndex` (`null`, `int64`), zero null cells. Schema of `date` is
`timestamp[ns]` in all 18, with exactly one distinct value each.

| R33 file | rows | date type | observed date | distinct | date > 2026-08-14 | sha256 (head) |
| --- | --- | --- | --- | --- | --- | --- |
| …_20260810__20260811_005710.parquet | 5,206 | timestamp[ns] | 2026-08-10 | 1 | no | 549d6a288f3f6fda… |
| …_20260811__20260811_233713.parquet | 5,208 | timestamp[ns] | 2026-08-11 | 1 | no | 9949bac5ded7715d… |
| …_20260903__20260904_013451.parquet | 5,215 | timestamp[ns] | 2026-09-03 | 1 | yes | 0f40821693f34623… |
| …_20260904__20260907_002941.parquet | 5,215 | timestamp[ns] | 2026-09-04 | 1 | yes | 97d437396c35f5e1… |
| …_20260907__20260908_085151.parquet | 5,216 | timestamp[ns] | 2026-09-07 | 1 | yes | b2854d54385eea8f… |
| …_20260908__20260909_161714.parquet | 5,216 | timestamp[ns] | 2026-09-08 | 1 | yes | 61c2a8fa1bff6c2b… |
| …_20260909__20260909_173601.parquet | 5,217 | timestamp[ns] | 2026-09-09 | 1 | yes | fb90758f5df7de47… |
| …_20260910__20260917_145154.parquet | 5,218 | timestamp[ns] | 2026-09-10 | 1 | yes | 25965d125759efb9… |
| …_20260911__20260918_072837.parquet | 5,219 | timestamp[ns] | 2026-09-11 | 1 | yes | e9e4145b03f47a98… |
| …_20260914__20260924_082308.parquet | 5,219 | timestamp[ns] | 2026-09-14 | 1 | yes | 2c0ad20e1ed0544a… |
| …_20260915__20260924_093041.parquet | 5,219 | timestamp[ns] | 2026-09-15 | 1 | yes | e56c1f32e5efea92… |
| …_20260916__20260924_103048.parquet | 5,220 | timestamp[ns] | 2026-09-16 | 1 | yes | 7ef2efe3ef6f1110… |
| …_20260917__20260924_114439.parquet | 5,221 | timestamp[ns] | 2026-09-17 | 1 | yes | 7fdd274c2b2a1e18… |
| …_20260918__20260924_130214.parquet | 5,221 | timestamp[ns] | 2026-09-18 | 1 | yes | ef678b17cd12cfc8… |
| …_20260921__20260924_163612.parquet | 5,221 | timestamp[ns] | 2026-09-21 | 1 | yes | 916213d04317788c… |
| …_20260922__20260924_173734.parquet | 5,222 | timestamp[ns] | 2026-09-22 | 1 | yes | e80b66f7c762d1cc… |
| …_20260923__20260924_183758.parquet | 5,222 | timestamp[ns] | 2026-09-23 | 1 | yes | 7de44a455f16a4b8… |
| …_20260924__20260925_030214.parquet | 5,222 | timestamp[ns] | 2026-09-24 | 1 | yes | 59ca656ea171c198… |

Per-file pins, byte counts, index metadata and head samples: `PER_FILE_DATE_TABLE.csv`,
`PER_FILE_DATE_TABLE.json`, `SCHEMA_EXAMINATION.json`.

Direct answers to the required questions:

* 16 of 18 files physically contain an explicit valid daily date after 2026-08-14 (all but 08-10 and 08-11).
* 2026-08-31: **not present**. 2026-09-01: **not present**. 2026-09-02: **not present**. 2026-09-24: **present**
  (one file, 5,222 rows).
* The two int64-ordinal RAW axes of 08-31 and 09-01 are **not** reproduced in this layer; R33 carries real
  timestamp axes only.
* This layer therefore spans 2026-08-10, 08-11 and 09-03..09-24, i.e. it skips 08-12..09-02 entirely.

Byte-level relation: `R33/…/adjust_factor_stock__incremental_20260924__20260925_030214.parquet` is
**byte-identical** to `P1_adjust_factor/adjust_factor_stock__incremental_20260924__20260925_030214.parquet`
(both sha256 `59ca656e…`, 34,838 B). Files were not combined, no overlap was resolved, no revision precedence
was chosen.

These are observed date/code sets in one product directory. They are not historical expected-universe
certificates, and absence here is not a supplier-absence claim.

## 4. Producer evidence, separated by kind

Only retained indexes, rule/contract references and already-uploaded or retained bodies were used. Full
detail with pins and quotes: `PRODUCER_EVIDENCE.json`.

### 4a. Governing registry row and contracts

`ECOLOGY_REGISTRY.json#ADJUST_FACTOR` declares RAW root `P1_adjust_factor` (222 parquet), CLEAN root
`…BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439/standard/reference/adjust_factor`
(18 parquet), lineage `JQ_OFFICIAL_RAW`, `engine_data_domain=adjustment_factor`,
`standard_required=["factor","fq"]`, PIT rule "factor 跳变对应 corporate action ex_date", and dictionary
contracts `domain_schema_contract.csv` (`6367c574…`), `pit_schema_contract.csv` (`1e62d187…`),
`dtype_precision_contract.csv` (`3864ff80…`).

Contract-vs-bytes difference, reported not repaired: the registry requires `factor,fq`; **none** of the 21
measured files has a physical `fq` column (they carry `date, code, factor, sec_type`). fq is therefore not
demonstrated by these bytes and was not added or inferred.

### 4b. What the retained source text says

* `jq_download_execution_r1.py` (retained, 130,769 B, `bcbfd68d…`) is the **legacy full-history** producer of
  P1 (`"T1": "P1_adjust_factor"`, line 76). Its request is
  `jqdatasdk.get_price(security=codes_batch, start_date=start_d, end_date=end_d, fields=["factor"])`
  (lines 841-848) — **no `fq` argument at all**; batches of 500 codes crossed with whole years 2014..2026
  (lines 811-818); it renames `time`→`date`, adds `sec_type` (lines 861-869), and writes
  `save_parquet(df_flat, out_path)` with `make_filename(..., date_range=f"{year}", symbol=f"batch_{idx}")`
  (lines 884-892). Its names and windows do not match the three files, and it writes no sidecar.
* `download_source_fq_pre_r1.py` (already delivered, 7,131 B, `8a496161…`) writes
  `TASK/staging/source_batches`, declares **`fq=pre`**, year-by-year, batches of 400, cutoff 2026-08-14 — not P1.
* `cache_compiler_adjust_factor_pit_r1.py` (retained, `bb8a52a1…`) **reads** P1:
  `sorted(P1.glob("adjust_factor_stock__*.parquet")) + sorted(P1.glob("adjust_factor_etf__*.parquet"))`
  (line 151) — this glob does match the `__incremental_*` files — then
  `df["date"] = pd.to_datetime(df["date"]).dt.normalize()` (line 155) and
  `df = df.loc[(df["date"] >= "2014-01-01") & (df["date"] < REFRESH_START)]` (line 156), and
  `df.loc[df["factor"] != 0]` (line 162). An int64 ordinal axis becomes 1970-01-01 at line 155 and is then
  dropped by line 156. Its own request (lines 129-135) also omits `fq`. This is observed code text plus the
  measured axis; it is a reader, not a producer identity.
* Clean-plane mechanism (retained family copies): writer `post_seal_daily_download_r8.py` declares
  `out = out.reset_index()` (line 104), `out["fq"] = None` (line 120), `df.to_parquet(str(raw_path),
  index=False)` (line 217), and a `STAGING_MANIFEST.json` PASS handoff; ingest
  `formal_cleaning_r15_build_and_seal_r1.py` keeps only `status == "PASS"` (lines 89-95), calls
  `ingest_item()` to place `stage_path` at `release_root/"standard"/clean_rel` (lines 108-135) and
  `hardlink_tree(PARENT/"standard", release_root/"standard")` (lines 337-339) with `PARENT_ID` a hardcoded
  constant (lines 23-25). That mechanism explains a byte-identical copy appearing under
  `standard/reference/adjust_factor`, but bytes alone cannot distinguish `place_file` from `hardlink`
  carry-forward, and cannot prove which run produced R33.
* Runtime rule reference (retained HAND json): the formal daily orchestrator is
  `脚本/blackbox_daily_increment_orchestrator_r1.py`, whose retained body chains INDEX_WEIGHT check →
  ETF-minute check → `cache_compiler_tip_rebase_from_current_r1.py` → scope refresh. It launches no
  adjust_factor RAW producer.

### 4c. What the receipts report

`INCREMENTAL_RECEIPT.json` (`bbbec46f…`): `update_date=2026-09-02`, `source_max_date=2026-09-02`, `fq=pre`,
`raw_fallback_used=false`, `silent_factor_one_used=false`, `backward_dirty_count=7`, action
`FULL_HISTORY_REFRESHED_DIRTY_CODES`. `SOURCE_COVERAGE.json` (`dbe8df62…`): source 2014-01-02..2026-08-14,
3068 trade days, 12,176,722 rows, 0 missing. `AUTHORITY_GATES.json` (`e820afdd…`) names only the
backward-refresh engine and the wrapper. **No receipt names a RAW producer.** Retained R09 narrowing records
that the cleaning layer's generation identity diverges by reader path (R33 pointer vs R45
parent/quarantine/ledger; `SEAL.json` 70 B carries no identity).

### 4d. What remains unresolved

The identity of the program that wrote `adjust_factor_stock__incremental_*.parquet` into `P1_adjust_factor` is
**not supplied by any retained index, rule reference or receipt**. Candidates above were checked and excluded
as writers on naming, window, request and sidecar grounds; that is a negative result inside the retained
corpus only. Per instruction the search was not expanded — status
`PRODUCER_NOT_IDENTIFIED_IN_RETAINED_INDEX`. This says nothing about whether such a producer exists, and no
supplier or market-data absence is claimed.

## 5. Identity re-verification at completion

After the comparison loop, all 21 inspected files were re-hashed: `files_checked=21`,
`all_unchanged=true` (`READ_IDENTITY_REVERIFY.json`). `source_files_changed=false`. No business-data write, no
date repair, no backfill, no refetch, no CURRENT switch, no engine construction, no order.

## 6. Ledger, manifest, readback

    COMMAND_LEDGER.json                8 recorded steps, exits, windows, capture hashes
    SOURCE_BATCH_CHAIN_FINAL_RECEIPT_UPLOAD.json  the completion action of section 1
    PREFLIGHT capture                  captures/PREFLIGHT_CACHE.stdout.bin / .stderr.bin
    R33_BOUNDED_INVENTORY.json         bounded enumeration record (limits, counts, reparse points)
    SCHEMA_EXAMINATION.json            full Arrow/pandas/index/date observations for all 21 files
    PER_FILE_DATE_TABLE.csv/.json      per-file rows, dates, pins, index metadata
    PRODUCER_EVIDENCE.json             source text vs receipt vs bytes vs unresolved, quoted
    CORRECTIONS_APPEND_ONLY.json       C1..C7
    READ_IDENTITY_REVERIFY.json        post-read re-hash of all 21 files
    EXECUTED_HELPER_TOOLS/             inspection helpers actually used
    DELIVERY_MANIFEST.json             every delivery member except itself
    FINAL_BYTE_READBACK.json           separate readback, written only after the upload completed

No parquet and no credential was uploaded. The final receipt is only claimed complete because this file and
its own readback are remotely readable under `agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/incremental_date_source/`.
