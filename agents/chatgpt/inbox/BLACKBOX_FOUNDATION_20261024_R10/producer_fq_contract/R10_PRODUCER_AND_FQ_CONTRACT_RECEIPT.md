# R10 continuation — the incremental factor writer, and the fq/date contract question

Executor: ZHANGWEI. Round: `BLACKBOX_FOUNDATION_R10_PRODUCER_AND_FQ_CONTRACT_20261025` (R10 continuation, not acceptance).
Instruction: `outbox/BLACKBOX_FOUNDATION_R10_PRODUCER_AND_FQ_CONTRACT_20261025.md` (7,798 B, sha256 `9bd230d2…`).
Window: 2026-10-25 02:01:07 – 02:12 +08:00. Host ZHANGWEI, cwd `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024`,
`PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`, interpreter `runtime/.venv/Scripts/python.exe`.

Append-only. Reused without rerun: the accepted source-batch chain, the RAW and R33 schema measurements, the
annual reconciliation, the dirty-branch tests and the catalog inventory.

FOUNDATION_ACCEPTANCE=false · FORMAL_ENGINE_ADMISSION=false · NEW_DATA_ACQUISITION_AUTHORIZED=false ·
CURRENT_SWITCH_ALLOWED=false · ORDER_ALLOWED=false · SOURCE_ABSENCE_CLAIM_ALLOWED=false · B1..B7 OPEN.

---

## 1. The supplied locator: staged, pinned, executed once

Staged to `reviews/R10/producer_and_fq_contract/` — both members, byte-identical, line endings preserved:

    locate_incremental_factor_writer.py   7,189 B  f30e2149af5e0228472c2fe5a9806631726843a8872290ab4d7786d75b4092e1
    PACKAGE.json                            337 B  059af6d72d238629b1ad8ec86deebda1f65f141c9a161f02029745d365eb5940

Declared and observed bytes and sha256 agree for both, and the staged copies equal them. The locator's internal
`ENTRY_SHA` pin (`1b04bb3a…`) matches the actual `operating_entry/blackbox_operate_r10.py`. No re-pin, no
substitute harness.

Executed exactly once:

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\producer_and_fq_contract\locate_incremental_factor_writer.py --desktop-check
    exit 0   02:01:07.8958932 → 02:01:12.9613870 +08:00   stdout 20,290 B  stderr 0 B

    status  BOUNDED_SOURCE_CANDIDATES_MEASURED
    nested preflight exit 0, real_preflight ok=true MUST_READ_PRECHECK=PASS task_class=[CACHE]
    2,134 directories   989 .py/.ps1 files   14,141,295 source bytes   17 candidates
    35 skipped (all EXCLUDED_OR_DEPTH_BOUND)   0 errors

Captures were taken externally into `captures/LOCATOR.desktop.stdout.bin` / `.stderr.bin`; the locator writes no
output files itself. Not rerun. Skipped and error entries are retained verbatim in `LOCATOR_RESULT.json`.

## 2. Candidate review — the writer family is now identified as a candidate

Two bodies were opened as text (no import, no help, no selftest, no auth, no resume, no wrapper, no updater):

**A. `E:\BLACKBOX\任务\BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1\aux_billboard_adjust_index_minute_r15.py`**
10,815 B, sha256 `767c73c7a5c17e017d4274c57071725e0a59c1eef39194e795edff8dce57a3cc`

* root binding — `P1 = RAW / "P1_adjust_factor"` (line 20), `P6_ADJ = RAW / "P6_factor_reference" / "adjust_factor"` (line 23)
* request (lines 110-113) — `jq.get_price(chunk, start_date=day, end_date=day, frequency="daily", fields=["factor"], skip_paused=False, fq=None, panel=False)`
* response shape handling (line 115) — `parts.append(df.reset_index() if "code" not in getattr(df, "columns", []) else df)`
* date field handling (lines 122-125) — `out = pd.concat(parts, ignore_index=True)`; `if "time" in out.columns and "date" not in out.columns: out = out.rename(columns={"time": "date"})`
* column set (lines 126-128) — `out["sec_type"] = "stock"`; `keep = [c for c in ["date", "code", "factor", "sec_type"] if c in out.columns]`
* filename (line 129) — `fp = P1 / f"adjust_factor_stock__incremental_{day.replace('-','')}__{stamp}.parquet"`
* write (lines 130-133) — `out[keep].to_parquet(fp, index=False)` and the same bytes to `P6_ADJ / f"adjust_factor__incremental_{day...}__{stamp}.parquet"`
* declared clean routing (lines 136-146) — `"clean_rel": f"reference/adjust_factor/{fp.name}"`, extra `"clean_rel": f"finance/adjust_factor/{fp2.name}"`

**B. `E:\BLACKBOX\任务\BLACKBOX_FULL_DATA_UPDATE_R14_20260809_R1\full_data_update_r14_run.py`**
23,720 B, sha256 `a1ca66995ccecc15c08f982b1cc5568372d123c47a0fc16c93fdc7a653b01944`

Same request (lines 287-290), same write (lines 308-314), **plus** one extra branch the R15 body does not have:

    302-304   if "time" in out.columns and "date" not in out.columns: out = out.rename(columns={"time": "date"})
              if "date" not in out.columns and "index" in out.columns: out = out.rename(columns={"index": "date"})

That fallback can turn a bare integer index into the column literally named `date`. It is the only statement
found that is consistent with an `int64` `date` column, and it exists in R14 only.

What this establishes and what it does not:

* **Established (text):** this family produces exactly the observed name shape
  `adjust_factor_stock__incremental_<YYYYMMDD>__<YYYYMMDD_HHMMSS>`, the observed four columns in the observed
  order, the observed `clean_rel` `reference/adjust_factor/<name>` (which is the R33 product directory shape),
  requests `fields=["factor"]` with `fq=None`, `frequency="daily"`, a single-day window, and writes
  `index=False` with no sidecar.
* **Not established:** that either body, in either R14 or R15 form, actually ran for 2026-08-31, 2026-09-01 or
  2026-09-24. Their declared as-of constants are `ASOF = "2026-08-10"` (R15) and the R14 run's `asof =
  2026-08-07`. A later run of the same family would need a different as-of; no such run's receipt is referenced here.

**Corroboration that does not hold — recorded because the text predicts it:** both bodies also write a P6
counterpart. Exact-path probes show `P6_factor_reference/adjust_factor/` exists but **none** of the three names
exists there. So that predicted sibling is absent, and it is not used as evidence.

**Mtime is not the stamp:** all three P1 mtimes are `2026-10-17` (08:41:32, 09:19:10, 20:13:44), while the names
encode 20260831_163108, 20260901_171005, 20260925_030214. The stamps are produced by the writing code; the
mtimes reflect a later copy. Neither is treated as a date authority.

**Unresolved arithmetic:** the two integer-axis files have 300 distinct ordinals with 17-18 rows each. The
batch=200 request logic in these bodies would not group rows that way. The exact mechanism that produced 300
groups is left unresolved rather than inferred.

## 3. Declared historical receipts (5 exact files, no directory expansion)

`r14_full_data_update.log` is the only retained log that shows this code path completing, and it names a
same-shaped output:

    [2026-08-08T23:27:23+00:00] adjust_factor {'status': 'PASS', 'rows': 5206,
      'path': '...\\P1_adjust_factor\\adjust_factor_stock__incremental_20260807__20260809_072723.parquet',
      'path_p6': '...\\P6_factor_reference\\adjust_factor\\adjust_factor__incremental_20260807__20260809_072723.parquet'}

`R14_FULL_DATA_UPDATE_RESULT.json` repeats it under `"adjust_factor"` with the same `path` / `path_p6`, and
`R14_RESULT_SUMMARY.json` reports `cleaning_r14` domains `["billboard","adjust_factor"]` with
`release_id BLACKBOX_FORMAL_CLEANING_R14_ASOF_20260807_20260809_082152`. `aux_download.log` (R15) shows the same
function reaching `5000/5206` and completing for asof 2026-08-10, but logs no per-file record.

So there is **historical execution evidence for the family on 2026-08-07 and 2026-08-10 only** — not for the
three dates in question. A historical report is not current execution proof.

## 4. The three normative contracts

Read at the three fixed paths, each ≤2 MiB, retained prefix verified first, full sha256 measured, raw bytes
retained in `CONTRACTS/`:

| file | bytes | sha256 | rows × cols |
| --- | --- | --- | --- |
| `02_domain_schema/domain_schema_contract.csv` | 4,182 | `6367c574c27b7ddbb7a926e4899f59502f3febc76a4cf2b0092998d275458146` | 19 × 11 |
| `04_pit_schema/pit_schema_contract.csv` | 1,490 | `1e62d187b6417b875f42a9b9b45fc616b3ac1d375c88f6d77116488c783e253b` | 14 × 9 |
| `09_dtype_precision_schema/dtype_precision_contract.csv` | 1,076 | `3864ff80edeb0538881d30b70e894c4a0783eec80fb51908035ebae23e74b57f` | 13 × 7 |

Headers, verbatim:

    domain_schema:   domain | target_table_name | primary_keys | time_key | pit_visible_key | required_fields |
                     optional_fields | forbidden_fields | can_enter_clean | clean_action | expected_row_scale
    pit_schema:      domain | report_period_field | visible_date_field | trade_date_field | effective_date_field |
                     forbidden_visible_date_fields | pit_rule | lookahead_risk | notes
    dtype_precision: field_category | example_fields | storage_dtype | precision_rule | nullable_allowed |
                     forbidden_dtype | notes

Governing rows (physical line numbers are 1-based, header = line 1):

**L3 `price_fq_factor`** — `target_table_name=stock_daily`; `primary_keys=symbol+trade_date`;
`time_key=trade_date`; `pit_visible_key=` (empty); `required_fields=['symbol','trade_date','open','high','low','close','volume','money','factor','high_limit','low_limit','paused']`;
`optional_fields=[]`; `forbidden_fields=[]`; `can_enter_clean=True`; `clean_action=jqdata_native_load`;
`expected_row_scale=10K/symbol`.

**pit L2 `price_fq_factor`** — `report_period_field=none`; `visible_date_field=trade_date`;
`trade_date_field=trade_date`; `effective_date_field=` (empty); `forbidden_visible_date_fields=none`;
`pit_rule=行情日频PIT: trade_date索引`; `lookahead_risk=false`; `notes=` (empty).

**dtype L8 `date`** — `example_fields=trade_date,weight_date,pubDate,statDate,day`; `storage_dtype=date`;
`precision_rule=YYYY-MM-DD`; `nullable_allowed=N`; `forbidden_dtype=string_mixed`; `notes=` (empty).
**dtype L7 `datetime`** — `example_fields=datetime_local,datetime_utc`; `storage_dtype=datetime64[ns]`;
`precision_rule=ISO8601`; `nullable_allowed=N`; `forbidden_dtype=bare_string`.
**dtype L9 `primary_key`** — `storage_dtype=string`; `nullable_allowed=N`; `forbidden_dtype=float,date`.

Cross-reference rows that mention the same domain elsewhere: L16 `jq_factor_raw_support`
(`clean_action=factor_reference_only`, `time_key=none`), L4 `minute_price` (`time_key=datetime_local`), L19
`corporate_actions` (`time_key=announce_date`, `clean_action=jqdata_native_pit_load`).

### The four required distinctions

**(a) Required business meaning.** `factor` is a required field of `price_fq_factor`; the row must be keyed by
`symbol+trade_date`; `trade_date` is both `time_key`, `pit_visible_key`-equivalent and `visible_date_field`, and
the PIT rule states the daily market plane is indexed by `trade_date`. Date storage must be the `date` category,
`YYYY-MM-DD`, non-nullable.

**(b) Is physical column placement mandatory?** For the fields named in `required_fields` — yes, they are named
columns. **`fq` is not named in any row of any of the three CSVs**; the string `fq` appears only inside the
domain label `price_fq_factor`. Placement of an `fq` column is therefore **NOT_SPECIFIED**.

**(c) Permitted metadata / request / release binding?** None of the three CSVs describes a request-level,
sidecar, or release-level binding mechanism, nor forbids one. **NOT_SPECIFIED.** No allowance is invented, and
consequently nothing in the CSVs can be read as authorising "fq bound by request" either.

**(d) Authority precedence and enforcement hook.** `can_enter_clean=True` plus `clean_action=jqdata_native_load`
is the only admission statement; the PIT row supplies `pit_rule`/`lookahead_risk`; the dtype rows supply
`forbidden_dtype`. No CSV names an executable enforcement hook. **NOT_SPECIFIED.**

Consequence for the earlier finding: "no physical `fq` column" is **descriptive only**. It is not a contract
violation, and it is not evidence that fq was implicit. The `factor` requirement, by contrast, *is* a stated
column obligation and every one of the 21 files satisfies it. The date requirement *is* stated, and the two
int64 files do not meet its `date`-category `storage_dtype` or its `trade_date` meaning.

## 5. Decision table

Full table in `DECISION_TABLE.csv` / `DECISION_TABLE.json`. Compressed:

| row | date meaning proven | fq binding proven | producer identified | execution proven | preservation checked | failure rule that applies |
| --- | --- | --- | --- | --- | --- | --- |
| R1 RAW 20260831 | no — int64, 300 ordinals 0..299, uninterpreted | no | candidate family only | no | yes | `time_key=trade_date` unmet ⇒ not PIT-admissible; `silent_factor_eq_1` forbidden; no filename date |
| R2 RAW 20260901 | no — same | no | candidate family only | no | yes | same |
| R3 RAW 20260924 | yes within the file — `timestamp[ns]`, 2026-09-24, 0 nulls | no | candidate family only | no | yes (byte-identical to R33 copy) | fq unproven ⇒ must not be presented as `fq=pre` |
| R4 staged explicit-fq source | yes within 2014-01-02..2026-08-14 | partial — declared by the producing request, not by a field | yes | partial | yes (prior round) | scope ends 2026-08-14 |
| R5 R33 adjust_factor | yes per file (18 single-date timestamps) | no | candidate (clean_rel matches) | no | yes | copy identity ≠ completeness; absence here ≠ source absence |
| R6 candidate backward-refresh assembly | yes as previously measured | declared by receipt (`fq=pre`, no raw fallback, no `factor=1`) | yes at assembly level | partial | yes (prior rounds) | a receipt reporting `fq=pre` does not upgrade a source file whose own binding is unproven |

## 6. What changed and what did not

Changed: the producer status moved from *not identified in retained indexes* to **CANDIDATE_FAMILY_ONLY**, with
two exact bodies delivered at original bytes that reproduce the naming, columns, `clean_rel`, request and write
statements. The fq question was reclassified from a possible violation to **NOT_SPECIFIED by the normative CSVs**,
and the date question was sharpened: the CSV does state a `date`-category, `trade_date`-meaning obligation, which
the two int64 files do not meet.

Not changed: no date was repaired or inferred, no alternate date field substituted, no ordinal interpreted, no
factor filled, no `fq` column added, no product admitted, nothing installed, no updater run, no supplier call, no
download or refetch, no CURRENT change, no engine and no order.

## 7. Delivery contents

    SUPPLIED_SOURCES/            locate_incremental_factor_writer.py, PACKAGE.json (byte-identical)
    captures/                    LOCATOR.desktop.stdout.bin (20,290 B), .stderr.bin (0 B)
    LOCATOR_RESULT.json          parsed status, limits, 17 candidates, 35 skips, 0 errors, nested preflight
    CANDIDATE_BODIES/            the two writer bodies, original bytes, credential-scanned clean
    HISTORICAL_RECEIPTS/         5 exact declared log/receipt files
    CONTRACTS/                   the three CSVs, raw original bytes
    NORMATIVE_DICTIONARY_CONTRACT_READ.json   headers, every governing row with 1-based line number
    PAIR_COPY_AND_MTIME_PROBE.json            exact-path P6 probes and P1 mtimes
    BODY_PROVENANCE.json         original path, bytes, sha256, byte-identity for every delivered body
    DECISION_TABLE.csv / .json   the bounded table above
    COMMAND_LEDGER.json          every step, exit and capture hash
    CORRECTIONS_APPEND_ONLY.json C1..C7
    DELIVERY_MANIFEST.json       every member except itself and the readback
    FINAL_BYTE_READBACK.json     separate readback, written after the upload

No parquet and no credential value was uploaded. Both source bodies contain no embedded secret; they call
`jdb.auth()` which resolves credentials at runtime, and no credential file was read.
