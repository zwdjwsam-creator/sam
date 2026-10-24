# BLACKBOX ACCESS AND DOWNLOAD RUNBOOK (R04 addendum, access_resources)

HOST: ZHANGWEI
PARENT: BLACKBOX_FOUNDATION_R04_OF_10_GPT_PATCH_AND_COMPLETE_CONTRACT_HANDOFF_20261024_1455
SCOPE OF THIS DOCUMENT: how an authorized local operator locates an existing credential, starts the correct
runtime, connects, checks entitlement, chooses a bounded date scope and pulls data through the approved
candidate workflow.
FOUNDATION_ACCEPTANCE: false
ORDER_ALLOWED: false
PRODUCTION_CHANGE_AUTHORIZED: false

Nothing in this runbook was executed as a login, probe or download during R04A. Every command below is
either (a) source-proven from a file on this host, or (b) explicitly labelled as needing a callable that
GPT must author.

Secret rule that applies to every step: read a credential only through its loader. Never echo, log,
screenshot, hash, truncate or paste a password, token, cookie, header or signed URL.

---

## 0. Runtime and working directory

```powershell
cd E:\BLACKBOX
E:\BLACKBOX\.venv\Scripts\python.exe -V
```

`E:\BLACKBOX\.venv` is the interpreter the downloader family declares (`depends on jqdatasdk, tushare,
pandas, pyarrow`; both SDK package directories are present). The isolated candidate runtime
`_OPS\FOUNDATION_RECOVERY_20261024\runtime\.venv` is for candidate/engine reads only; do not run
downloaders with it.

---

## 1. Source → credential → loader map

| source_id | supplier | credential locator | loader that actually reads it | current status |
|---|---|---|---|---|
| `SRC_JQDATA_SDK` | JQData | `E:\BLACKBOX\配置\secrets\已验证\聚宽账号.txt` | `脚本\jq_download_base.py::auth()` / `脚本\jq_download_execution_r1.py::parse_cred()` | `CONFIGURED_NOT_VERIFIED` |
| `SRC_TUSHARE_PRO` | Tushare Pro | `E:\BLACKBOX\配置\secrets\已验证\Tushare_TOKEN.txt` | `脚本\blackbox_external_evidence_materialization_r2.py::load_token()` | `HISTORICAL_ACCESS_ONLY` (probe 2026-08-24) |
| `SRC_EXTERNAL_DOC_IMPORT` | sellside / news / company documents | none declared | lane C/D/E collectors | `MANUAL_OR_LICENSED_DOCUMENT_ONLY` |
| `SRC_QMT_TERMINAL` | QMT local terminal | `E:\BLACKBOX\配置\secrets\已验证\QMT账号.txt` | terminal-managed | `DENIED_BY_CURRENT_POLICY` (history build out of scope) |
| `SRC_LOCAL_RELEASES` | local releases | not required | `脚本\run_blackbox_research_os.py` | `VERIFIED_CURRENT_ACCESS` |
| `SRC_HUB_GITHUB` | evidence transport | `C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT` | `tools\upload_r04_delivery.py` | `VERIFIED_CURRENT_ACCESS` |

The engine `env_loader.py` names `JQDATA_USERNAME / JQDATA_PASSWORD / JQDATA_SERVER / JQDATA_PORT /
TUSHARE_TOKEN / TUSHARE_CUSTOM_URL`. Those names belong to the engine, NOT to the updater. An engine
variable being set is not evidence that the downloader can authenticate.

---

## 2. Step 1 — confirm the credential locator (no value printed)

```powershell
$p = "E:\BLACKBOX\配置\secrets\已验证\聚宽账号.txt"
Test-Path $p
(Get-Item $p).Length
(Get-Content $p | Measure-Object -Line).Lines
```

Expected on this host: exists = True, 23 bytes, 2 non-empty lines. Do **not** run `Get-Content` without
`Measure-Object`/counting, and never redirect this file to a log.

Known defect (recorded as R04A loaders fact): the file holds two unlabelled lines, while
`脚本\jq_download_execution_r1.py::parse_cred()` accepts only lines starting with `账号：/账号:` and
`密码：/密码:`. Calling that downloader in its current form raises
`ValueError('凭据文件格式错误，无法解析账号或密码')`. `脚本\jq_download_base.py::auth()` does accept the
unlabelled two-line form (keyed-lines-first, then plain-line fallback).

Therefore:

- **Do not** "fix" the credential file by rewriting it; that changes a secret store outside the
  authorized scope.
- Use the base loader path for a bounded read, or wait for GPT to authorize a loader alignment patch.

---

## 3. Step 2 — connect and verify the session (bounded, one call)

A bounded authentication check with the base loader exists as a code path but has no contracted CLI. The
missing callable is: *"authenticate through `jq_download_base.auth()` and print
`jqdatasdk.get_query_count()` only"* — GPT must author it before it is used. Until then this step is
`DYNAMIC_RESOLUTION_NOT_VERIFIED`: the loader and the file are statically verified, the runtime result is
not.

When such a callable is authorized, it must:

1. import `jqdatasdk`, call `auth()` (no password argument, locator-resolved),
2. print only `total` / `spare` from `get_query_count()`,
3. exit non-zero on any exception,
4. write nothing under `数据\`, `运行\` or `研究系统\`.

Tushare equivalent: `tushare.pro_api(load_token())` followed by exactly one cheap endpoint
(`stock_basic`, `limit=5`) and a status record — not a table sweep.

---

## 4. Step 3 — pick a bounded date scope

The declared scope authority is:

```powershell
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\blackbox_full_data_update_scope_refresh_r1.py
Get-Content E:\BLACKBOX\运行\BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json
```

`HIST_END` / `asof` in that CURRENT file is the only legal upper bound for a pull. `脚本\jq_download_base.py`
also enforces a quota guard (`quota_left`, `quota_ok`) and a subprocess timeout for `get_price`;
a bounded window means one dataset, one short date range, one code list already known from
`DATA_ACQUISITION_MATRIX.json`.

---

## 5. Step 4 — run the approved lane, not a new downloader

The six-lane daily entry point (source-proven CLI):

```powershell
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode status
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode run --date 20260924 --lane A
```

Accepted modes: `run`, `status`, `resume`, `publish_identity`. Flags: `--date`, `--run`, `--lane`,
`--skip-jq`, `--skip-t-external`, `--skip-sellside-if-done`, `--p0a-selftest`,
`--identity-backup-dir` (required for `publish_identity`).

The Research OS wrapper is:

```powershell
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_research_os.py --mode daily_incremental
```

Lane A (`A_JQ_INCREMENTAL`) only *refreshes scope and verifies* the scope/cleaning/cache triple
(`scope_refresh_script`, `cleaning_current`, `cache_current`). It does not itself download.
The download body lives in `脚本\jq_download_execution_r1.py` (modes: `start`, `resume`) plus
`脚本\jq_download_base.py` / `脚本\_download_batch.py`. There is **no** single contracted
"download one date range for one dataset" command today; that is the missing callable GPT must author
before any pull, so that a pull cannot become an arbitrary sweep.

Post-download, the formal orchestrator is:

```powershell
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\blackbox_daily_increment_orchestrator_r1.py
```

It chains the ETF NAV plane, the cleaning/cache chain and the scope refresh. It runs *after* a download and
must not be used to imply that a download happened.

---

## 6. Step 5 — close the plane honestly

```powershell
Get-Content E:\BLACKBOX\研究系统\数据平面\CURRENT\DAILY_DATA_MANIFEST_CURRENT.json
```

A day is complete only with: download complete for the permitted domains → cleaning CURRENT → alignment and
anti-lookahead pass → CACHE CURRENT → manifest → research. `thin canary` results must never be published as
a FULL product. If a domain is permission-blocked, record it in the full table rather than retrying.

---

## 7. Known gaps an operator must not paper over

1. **CLEAN omission, 2026-08-31 and 2026-09-01.** RAW holds both units
   (`stock_daily__incremental_gap_20260831_20260831__full__20260831_155057.parquet`, 5,212 rows;
   `stock_daily__incremental_gap_20260901_20260901__full__20260901_161813.parquet`, 5,214 rows).
   CLEAN and CACHE contain neither date for any code. The reason is not proven. Do not re-download these
   days to "fix" it: the RAW is already there, so the defect is in the cleaning step, and a re-download
   would spend quota to hide a pipeline bug.
2. **Factor value plane.** No value plane exists. AMEND_R3 declares the full library required,
   the daily child rule seals the same domains as permission-skipped, and the engine gate still forbids
   factor-value ingestion. This is an authority conflict, not a technician decision.
3. **FUND NAV.** The approved route is `get_extras(info='unit_net_value' / 'acc_net_value')`.
   `finance.FUND_NET_VALUE` returned 0 rows and `refactor_net_value` is unsupported; neither observation
   proves the supplier lacks the data, and neither authorizes an unrestricted whole-table query.
4. **Index weights.** Managed snapshot semantics: check the latest source snapshot; do not run an
   unconditional full-history download.

---

## 8. What is explicitly forbidden in this task

No new login attempt, no quota consumption, no paid API probe, no business-data download, no global
dependency install, no secret migration or rewriting, no browser cookie extraction, no QMT brokerage access,
no production CURRENT switch, no purchase or subscription, no rewriting of original contracts or already
downloaded data.

If a step cannot be completed without one of the above, stop and record the blocker with the exact
missing callable or configuration for GPT.
