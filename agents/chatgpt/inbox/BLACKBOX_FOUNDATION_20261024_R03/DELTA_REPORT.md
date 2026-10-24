# R03 DELTA REPORT -- runtime, provider correctness, engine-contract adapter

Round: R03 / 10. Budget slot: 3/10. Remaining after delivery: 7.
Predecessor visible in HUB: BLACKBOX_FOUNDATION_20261024_R01. R02 completion was not
observed in HUB and is not invented here.
FOUNDATION_ACCEPTANCE = false. ORDER_ALLOWED = false. Production write = none.

## 1. Dedicated runtime (blocker from R01 removed)

R01 could not import the engine contract because system Python 3.12 has no pandas and the
historical `.venv` points at a foreign path. This cycle creates an isolated runtime under the
recovery tree and installs only what the reader and the safe contract test need.

- Executable: `runtime\.venv\Scripts\python.exe`
- Python 3.12.10, pandas 2.3.3, pyarrow 21.0.0, numpy 2.5.4
- Lock: `runtime/REQUIREMENTS_LOCK.txt`; commands: `RUNTIME_COMMAND.md`
- Global Python, the historical `.venv`, production configuration and account files untouched.

## 2. Independent review findings: resolution status

`agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R01_REVIEW_20261024_1424/REVIEW_R01.md`

| Review finding | Resolution in R03 | Evidence |
|---|---|---|
| lines 191-197 read only `files[:max_files]`, exceptions silently ignored | accounting splits selected / attempted / loaded / unreadable / schema-conflicted / budget-skipped; any non-empty failure set forces PARTIAL with a code | checks 2 |
| lines 442-458 could still return OK with truncation hidden | row truncation and file-budget overflow both enter `incomplete_reasons` | checks 2 |
| lines 147-170 any 8-digit token, including build date, treated as coverage | build stamps `YYYYMMDD_HHMMSS` are stripped first; selection uses parquet footer time statistics; filename hints are only a fallback for unreadable footers | checks 1, 10 |
| lines 338-339 accept pre/post but no adjustment applied | `fq=pre/post` rejected with `ADJUST_MODE_UNEVIDENCED`; RAW_NONE identity preserved, factor never relabelled | checks 4, 7 |
| lines 332 / 370-379 reduce to dates, knowable rule is only a string | request timestamps keep time and CN timezone; daily bars become known at 15:00 of their trade date, intraday labels are bar ends; supplied `asof` narrows the cutoff; events without an announcement are withheld under `asof` | checks 3, 8 |
| lines 385-394 keep last iterated row, day files before year files | deterministic merge on `(specificity_rank, build stamp, source name)`; equal-rank disagreements surface as `revisions.conflicts`; reversed enumeration returns an identical frame | checks 5 |
| lines 561-582 admit rows with no announcement date under an as-of gate | rows without announcement are withheld and counted (`withheld_unknown_announcement`) | checks 3 |
| get_price routes all securities to stock datasets | routing from SECURITY_MASTER type: stock / ETF / index each to its own dataset; futures, mixed and unknown codes rejected explicitly | checks 6 |
| static method-name presence is not conformance | adapter subclasses the real `DataProvider` loaded as a leaf module and returns DataFrames / engine lists; every declared parameter honoured or rejected | checks 7, 9 |
| R01 report says 22 daily rows, SMOKE_RESULTS records 10 | canonical calendar-derived expectation is 21 and the current read returns 21 with proven coverage; both prior numbers are recorded as superseded | checks 8 |

The two counterexamples shipped with the review are reproduced in the new suite as
checks 1 (build stamp is not coverage) and 3 (unknown announcement cannot pass an as-of gate),
with the expectations inverted as instructed.

## 3. Correctness changes in the reader

1. **Coverage.** `runtime/file_index_<dataset>_<layer>.json` is built once from parquet footer
   time statistics (min/max over row groups) and cached against a directory-mtime signature.
   Requests do not re-enumerate the dataset tree. Observed bounds: stock daily `2014-01-02 ..
   2026-09-24`, stock 1m `2026-09-11 .. 2026-09-24`, ETF daily `2026-07-30 .. 2026-09-24`.
2. **Version identity.** Same family + same coverage means versions, newest build wins. Same
   family with *different* coverage means complementary segments, both kept. This is the defect
   that turned a 22-row answer into 10 rows in R01.
3. **Read accounting.** Every failure mode is counted and named; "OK" is impossible when a
   selected file failed, a budget skipped files, rows were truncated, coverage is unproven, a
   required field has nulls, or revisions conflict.
4. **Time.** Request timestamps are preserved with time and `+08:00`; a bare date means the whole
   trade day (end-of-day availability), an explicit timestamp clips later bars. `asof` narrows
   further. Intraday first bar is 09:31, consistent with end-labelled bars.
5. **Adjustment.** Only `fq=none` is served. `pre/post` and `pre_factor_ref_date` are rejected;
   `prefer_engine` / `force_no_engine` are rejected because no fallback is bound.
6. **Pause semantics.** `skip_paused` / `fill_paused` require bar-level pause evidence in the
   loaded segments; batch segments omit it, so the request is rejected instead of guessed.
   `fill_paused=True` with real paused rows is rejected as not implemented (no synthetic fills).
7. **Field admission.** Per-field null ratios with field-specific admission; required OHLCV
   nulls block success, optional fields report `FIELD_NULL_IN_SEGMENT`. A missing `factor`
   column stays null and is never replaced by 1.0.
8. **Registry scope.** Universal 2014 starts and the global cleaning-as-of cursor are gone.
   Nine datasets carry observed watermarks from real statistics; the rest are explicitly
   `NOT_OBSERVED_THIS_CYCLE` / `NO_TIME_AXIS_OBSERVED` with `declared_range = null`.
   `increment_cursor = null` everywhere -- no updater offset is invented.

## 4. Engine-contract adapter

- Subclass of the real `bullet_trade.data.providers.base.DataProvider`, loaded by file path so no
  trading or download initialisation runs (`eng.base` in SYSTEM_STRUCTURE).
- `get_price` returns the engine layout: `DatetimeIndex` named `time`, flat field columns for a
  single code, `MultiIndex (field, code)` for multiple codes, long `time/code/...` form for
  `panel=False`.
- `count` is derived from the trading calendar for daily frequencies; intraday `count` is
  rejected. `skip_paused`, `fill_paused`, `pre_factor_ref_date`, `prefer_engine`,
  `force_no_engine` are honoured or rejected -- never silently ignored.
- `get_trade_days` returns `datetime` list, `get_all_securities` a code-indexed DataFrame,
  `get_index_stocks` a code list, `get_split_dividend` the documented unified event schema
  (`security/date/security_type/scale_factor/bonus_pre_tax/per_base`, source ratios retained).
- Rejections raise `ProviderReject`; partial results are returned with `df.attrs["bb_status"]`,
  `df.attrs["bb_reasons"]` and full provenance, so a partial frame cannot masquerade as complete.

## 5. Verification result (machine, canonical)

`TEST_RESULTS.json`: 10 checks, 10 passed, 0 failed. Runtime pandas 2.3.3 / pyarrow 21.0.0.
All narrative numbers in this report are taken from that file.

Real-data evidence:
- stock daily `000001.XSHE` 2026-06-01..2026-06-30: 21 rows, status OK, expected 21, missing
  dates none, 38 files selected / 38 loaded, 13 duplicate rows resolved, no conflict.
- stock 1m `000001.XSHE` 2026-09-11 09:30..09:45: 10 bars, last bar 09:40, later bars excluded.
- ex-rights as-of gate: 2 events in the window, 1 admitted (announced 2025-12-20), 1 withheld
  (no announcement) under `asof=2026-01-10`.

## 6. Unresolved edges (honest limits)

1. `data/api.py::_create_provider` has no local-value branch (jqdata / tushare / qmt / miniqmt /
   remote-qmt only). The adapter is conformant but not selectable by the engine yet; registering
   a branch is a production change reserved for a later round.
2. Adjusted price semantics remain unimplemented: batch segments carry `factor = null`, so any
   pre/post conversion would fabricate values. The engine default `fq='pre'` therefore cannot be
   served by this candidate.
3. No per-dataset increment cursor exists; the updater has not published one.
4. Full engine invocation (backtest run) was not executed; `formal_backtest_active` and
   `engine_core_active` remain false by instruction.
5. The cache plane (`CURRENT_CACHE_RELEASE`) and factor value plane are not bound to this reader.

## 7. Next smallest step

Toward engine integration: add one read-only provider branch in `data/api.py` behind an explicit
configuration switch (default unchanged) and prove `set_data_provider("blackbox_local_value")`
through `data/api.py::get_price` in an isolated unit test -- still no core activation.
Toward a real latest-data incremental update: derive and publish one per-dataset cursor from the
observed watermark of the stock daily plane, then run a single-day bounded incremental append in
a candidate release, never writing into sealed/CURRENT.
