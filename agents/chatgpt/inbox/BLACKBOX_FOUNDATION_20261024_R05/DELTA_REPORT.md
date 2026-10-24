# R05/10 DELTA REPORT — reader/API corrections, one bounded JQ access check, gap repair inputs

HOST: ZHANGWEI
ROUND: BLACKBOX_FOUNDATION_20261024_R05 (budget slot 5/10)
PREDECESSOR: BLACKBOX_FOUNDATION_20261024_R04 + access_resources supplement
FOUNDATION_ACCEPTANCE: false
ORDER_ALLOWED: false
PRODUCTION_CHANGE_AUTHORIZED: false

## 1. What was executed, exactly as supplied

| # | Command (working directory `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024`) | Exit | Result |
|---|---|---|---|
| 1 | blob check of the 5 supplied files | 0 | 5/5 git blob sha1 match the HUB blobs |
| 2 | `runtime\.venv\Scripts\python.exe reviews\R05\build_r05.py candidate\r4 candidate\r5` | 0 | candidate created; R04 untouched |
| 3 | `... reviews\R05\verify_reader_r05.py candidate\r4 candidate\r5` | 0 | PASS, 4 counterexamples |
| 4 | `... reviews\R05\jq_bounded_access.py --selftest` | 0 | PASS, 5 offline controls |
| 5 | `... -m reviews.R05.api_boundary_probe <api.py> --adapter candidate.r5.engine_adapter --output-api reviews\R05\api_r05_helper_candidate.py` | 0 | PASS |
| 6 | `... -m pip install --no-input "jqdatasdk==1.9.8"` | 0 | exact historical version installed into the dedicated candidate runtime |
| 7 | `... -m pip check` | 0 | No broken requirements found. |
| 8 | `... reviews\R05\jq_bounded_access.py --live` | 0 | BOUNDED_ACCESS_VERIFIED |

No command was retried. No credential was read into any artifact. No engine, CURRENT or R9 file was modified.

## 2. Demonstrated behaviour

Four independent reader counterexamples pass. Each one is a real behavioural difference between the R04 reader and the R05 candidate, not a renamed control:

1. two overlapping builds of the same family — R04 selected 1, R05 selects 2 (version suppression removed);
2. an unreadable file with an unknown footer — R04 selected 0 and dropped it silently, R05 selects 1 and surfaces `UNKNOWN_REQUIRES_REVIEW`;
3. a tail that no file serves — R04 reported no missing dates, R05 reports `2026-06-03` as unserved;
4. two revisions at different ranks with different values — R04 reported no conflict, R05 reports the conflict.

The consequence is stated honestly in the supplied review: the R05 reader will reveal *more* rejections than R04. That is evidence to trace, not a licence to pick the convenient file. The old R03 expected-PASS cases were deliberately not re-asserted against the stricter behaviour.

The API boundary defect is real and reproduced on the actual engine source (`api.py`, sha256 `49c496…3dee`):
`get_price` catches generic exceptions and `_raise_if_not_implemented` only re-raised `NotImplementedError`, so a provider's fail-closed rejection became an **empty DataFrame** — indistinguishable from "no data". With the helper candidate, the same rejection **propagates**.

The generated helper is a **function-path harness only**:

- FUNCTION_PATH_TESTED = true (exact `set_data_provider`, `get_price`, `_call_provider_get_price*`, `_raise_if_not_implemented`, `_build_empty_price_frame`, `_ensure_auth`, settings/logging paths, with the remote factory replaced by an assertion that must never fire — `factory_calls = 0`);
- FULL_PACKAGE_STARTUP_NOT_TESTED = true;
- MASTER_ADMISSION_NOT_IMPLEMENTED = true.

Against the R05 candidate adapter the harness returned a real diagnostic frame (3 rows, `bb_status=OK`) and rejected `fq='pre'` with `ADJUST_MODE_UNEVIDENCED`. Neither outcome is a MASTER admission or an engine-ready statement.

## 3. The one authorized ordinary JQ access check

- SDK: `jqdatasdk==1.9.8`, distribution version read from `E:\BLACKBOX\.venv\Lib\site-packages\jqdatasdk-1.9.8.dist-info\METADATA` as a **file**; the broken historical interpreter was never executed.
- Installed only into `runtime\.venv` (Python 3.12.10). Dependencies resolved: SQLAlchemy 2.1.6, thriftpy2 0.4.20, PyMySQL 1.2.3, msgpack 1.2.3, ply 3.11, requests 2.34.2, urllib3 2.8.0, certifi 2026.10.23, charset_normalizer 3.5.2, idna 3.20, typing_extensions 4.16.0. `pip check` clean.
- Public calls made by the supplied script: **1** auth, **1** `get_query_count`, **1** `get_price`. No retry, no second account, no factor-value call, no broad table query.
- Result: `BOUNDED_ACCESS_VERIFIED`, quota `total=200000000 / spare=200000000`, one row, all six required fields non-null, request `000001.XSHE / 2026-09-24 / daily / fq=None`.
- Scope limit: this proves **current access to that one ordinary daily request**. It does not prove current Tushare access, every JQ table, all frequencies, full-history scope, factor permissions or the latest update date. `full_dataset_access_proven=false` is recorded in the result itself.
- The 1000-query reserve was an operational budget, not supplier pricing; spare was far above it.

## 4. The two RAW days — resolved without re-downloading

The R04 phrasing "CLEAN, and therefore CACHE" is withdrawn and replaced with a direct observation.

Layers, all verified this round:

- **L3 vendor RAW — AVAILABLE.** 2026-08-31: 5,212 rows / 5,212 codes; 2026-09-01: 5,214 rows / 5,214 codes. Both sidecars hash-match their bytes. Schema is the 15-column RAW_NONE plane, `fq` typed null, `factor` uniformly 1.0, zero nulls in all twelve numeric fields, `paused ∈ {0,1}`, limits and `pre_close` present, zero duplicate `(time, code)` rows.
- **L2 active CLEAN — units ABSENT,** observed by directory listing of the active release (232 parquet files, neither target present).
- **L1 CACHE — units ABSENT, directly observed:** the `year=2026` partition of both `STOCK_DAILY_RAW_PIT_R1` and `STOCK_DAILY_PIT_R1` returns exactly 0 rows on 2026-08-31 and 2026-09-01, against 5,212 rows on 2026-08-28 and 5,215 on 2026-09-02 (176 distinct dates, 2026-01-05 … 2026-09-24).

The mapping rule was established from an already-processed adjacent unit rather than inferred from names: for 2026-09-02 the RAW unit and its CLEAN counterpart are content-identical after load, so `CLEAN standard/price/stock_ohlcv_daily/<domain>__<raw basename>.parquet` is a passthrough copy of the RAW unit.

**Mechanism (this is where the R04 report stopped).** It was not a cleaning failure and not a supplier failure:

- sealed releases `R33_FUND_NAV_ASOF_20260831_20260831_092618` and `R39_ASOF_20260831_20260831_164223` **do** contain the 2026-08-31 unit;
- sealed releases `R33_FUND_NAV_ASOF_20260901_20260901_100100` and `R39_ASOF_20260901_20260901_172742` **do** contain the 2026-09-01 unit;
- but every one of the 08-31, 09-01 and 09-02 tip releases was parented to the **same** older release `R33_FUND_NAV_ASOF_20260828_20260828_211339` (215 daily files) and each added only its own unit — 216 files every time. Parent hardlink carry-forward cannot see a unit introduced by a sibling release, so each day survives only in the release that created it and vanishes from every later release.

Numeric proof: parent 215 → 08-31 release 216 (has 08-31) → 09-01 release 216 (has 09-01, lost 08-31) → 09-02 release 216 (has neither). A contiguous chain would have produced 217 and 218.

The exact producer functions are quoted by file and line in `GAP_REPAIR_INPUTS.json#producer_chain`, with the on-disk family copies supplied as bodies: the write side (`save_unit` writes RAW + staging + both sidecars and defines `clean_rel`; `main` writes `STAGING_MANIFEST.json`) and the ingest side (`load_staging` keeps only `status == PASS` items from `08_DAILY_SOURCE_HANDOFF/STAGING_MANIFEST.json`, `ingest_item`/`place_file` place them at `standard/clean_rel`, `hardlink_tree` copies the parent tree, and `PARENT_ID` is a hardcoded constant).

## 5. Remaining blockers and unresolved edges

1. **UE-01 — the R39/R40…R45 driver body is not on disk.** `D:\CURSOR_TASK_ARCHIVE` exists but is empty, and no `post_seal_daily_download_r39*` / `formal_cleaning_r39*` driver exists under `E:\BLACKBOX\脚本` or `E:\BLACKBOX\任务`. The mechanism is fully evidenced from the sealed certificates and the on-disk family copy; the exact parent-selection function that produced the stale parent **cannot be quoted**. This is a named edge, not a guessed cause.
2. **UE-02 — the producer staging sidecars are gone.** Both RAW sidecars point at `stage_path` under the archived R30/R31 task directories, which no longer exist. The CLEAN copy therefore cannot be re-derived from staging; it must be re-ingested from the RAW units that still exist. All ten remaining `STAGING_MANIFEST.json` files under `E:\BLACKBOX\任务` were checked and none references either date.
3. **Repository hygiene, not a data defect:** two of the four RAW units without a CLEAN counterpart (2026-09-10 and 2026-09-24) are superseded duplicates whose later retry **is** in CLEAN. Only 2026-08-31 and 2026-09-01 have exactly one RAW unit and no CLEAN file, so a dedupe rule cannot explain them. Anyone reconciling RAW against CLEAN must not treat the other two as omissions.
4. Reader changes will surface more rejections across the whole plane once applied to anything beyond the synthetic controls. No systematic sweep was run and none should be inferred from a PASS here.
5. Factor values, money_flow and the JQ260 factor library remain: target requirement preserved, historical denial (2026-08-13 receipt) preserved, current access unknown, execution skipped pending changed entitlement, engine admission prohibited.

## 6. Not done, by contract

No cleaning run, no release build, no CACHE write, no substitution schema, no append to a sealed release, no re-download, no CURRENT switch, no purchase or entitlement upgrade, no repeated paid-module probe, no second auth attempt, no global or historical interpreter change, no credential change, no original MASTER flag change, no engine core change.

## 7. Artifacts in this bundle

`ROUND_STATUS.json` · `GPT_CODE_EXECUTION.json` · `JQ_BOUNDED_ACCESS.json` · `HUB_BLOB_VERIFICATION.json` · `SOURCE_ACCESS_UPDATES.json` · `EVIDENCE_CORRECTIONS_R05.json` · `GAP_REPAIR_INPUTS.json` · `SOURCE_BODY_INDEX.json` · `DELTA_REPORT.md` · `candidate_r5/{provider,file_index,errors}.py` · `api_r05_helper_candidate.py` · `source_bodies/` (5 bodies) · `PERMISSION_RECEIPTS/` (2 receipts + redaction declaration)
