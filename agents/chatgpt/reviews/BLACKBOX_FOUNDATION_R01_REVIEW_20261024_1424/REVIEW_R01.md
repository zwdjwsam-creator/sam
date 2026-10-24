# Independent review of the R01 candidate

Reviewed source: agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R01/candidate/local_plane_provider.py.

## Accepted scope
The registry and the reported real local reads are useful candidate-stage progress. The existing migration fidelity and the 26 original file-list presence checks remain closed. R01 does not establish engine integration, complete requested-window coverage, or all adjustment/PIT semantics.

## Executed counterexamples
The attached standard-library harness extracts the exact R01 methods with AST. Source discovery and Arrow filtering are stubbed to isolate two branches. It performs no Windows, real-dataset, network, engine, or production operation.

```json
{
  "scope": "Exact R01 methods in an isolated standard-library harness; source discovery and Arrow row filtering are stubbed. No Windows, real dataset, network or engine execution.",
  "build_timestamp_misused_as_coverage": {
    "coverage_year": 2014,
    "build_timestamp": "20260612_090000",
    "requested_year": 2026,
    "selected": true,
    "files": [
      "/fixture/bars__2014__20260612_090000.parquet"
    ]
  },
  "unknown_announcement_admitted": {
    "asof": "2026-06-01",
    "announcement_fields_present": false,
    "status": "OK",
    "returned_rows": 1,
    "knowable_at": "UNPROVEN_NO_ANNOUNCEMENT"
  }
}
```

Run the harness with the R01 source path as its sole argument. Its assertions intentionally reproduce the old defects; they are not acceptance assertions for a fixed candidate.

## Additional source findings
- Lines 191-197 read only files[:max_files] and silently ignore read exceptions. Lines 442-458 can still return OK, with truncated describing only returned-row truncation.
- Lines 147-170 treat any eight-digit filename token, including a build date, as coverage. The first counterexample confirms the wrong selection.
- Lines 338-339 accept pre/post adjustment requests, but the subsequent price path does not implement an adjustment before returning OK.
- Lines 332 and 370-379 reduce the request to dates and filter through end-of-day. Intraday request-time safety is not established by a knowable_time_rule string.
- Lines 385-394 retain the last duplicate row; day files are selected before year files, so iteration order does not establish the authoritative revision winner.
- Lines 561-582 admit rows with no announcement date even when an as-of cutoff was supplied. The second counterexample confirms this.
- get_price routes all securities to stock datasets. ETF routing is not proven by the stock-only smoke.
- Static presence of five method names does not establish DataProvider conformance: get_price lacks engine parameters and the candidate returns envelopes rather than DataFrames.
- R01 report says 22 daily rows; SMOKE_RESULTS records 10. Generate current English summaries from one canonical machine result rather than handwritten counts.

These findings concern the candidate and its evidence boundaries, not a claim that historical source data were damaged.

## Budget and language
The user specifies eight remaining cycles. The next task uses budget slot R03/10, while the only completed round report currently observed in HUB is R01. No R02 completion is invented.
All newly uploaded documentation, comments, status messages, and reports must be in English. Preserve literal original source paths, keys, and identifiers exactly when necessary.
