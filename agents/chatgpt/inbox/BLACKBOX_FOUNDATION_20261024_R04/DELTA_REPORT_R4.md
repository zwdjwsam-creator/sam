# R04/10 delta report — GPT safety patch executed, complete applicable contract handoff

Budget slot 4/10. Cycles remaining after this delivery: 6. Predecessor R03.
`FOUNDATION_ACCEPTANCE=false`, `ORDER_ALLOWED=false`, `formal_backtest_active=false`,
`PRODUCTION_CHANGE_AUTHORIZED=false`.

## 1. What GPT authored and what the operator did

GPT authored the patch (`build_r04_patch.py`), the manifest (`PATCH_INPUTS.json`) and the independent
verifier (`verify_safety_patch.py`). The operator only staged the exact bytes, verified them, executed the two
commands in order, and recorded the results. No business rule was invented, no source was edited to force PASS.

| step | result |
|---|---|
| staged patch bytes vs HUB git blob sha1 | 4/4 MATCH |
| R03 normalized sha256 vs GPT manifest | 5/5 MATCH |
| generator (`build_r04_patch.py`, exit 0) | `PATCH_CREATED`; R03 preserved |
| generator second invocation (guard) | exit 1 `DESTINATION_ALREADY_EXISTS` |
| verifier (`verify_safety_patch.py`, exit 0) | `PASS`, nine synthetic checks |
| generated r4 hashes vs GPT-recorded outputs | 5/5 MATCH |
| changed files | `provider.py`, `engine_adapter.py` only |

## 2. Native adapter evidence (diagnostic, not admission)

`EngineLocalValueProvider` (candidate r4) was imported as the engine leaf subclass and instanced on the isolated
runtime (`Python 3.12.10`, `isinstance(obj, DataProvider) == True`, `strict_partial=True`).

- `get_price("000001.XSHE","2026-06-01","2026-06-03", fq="none", fill_paused=False)` -> real DataFrame,
  `DatetimeIndex`, columns `open,close,high,low,volume,money`, 3 rows, status OK, closes 10.64/10.73/10.64.
- `get_index_stocks` -> `ENGINE_INDEX_CONTRACT_PENDING`; `get_split_dividend` -> `ENGINE_EVENT_CONTRACT_PENDING`.
- `get_all_securities("stock")` -> 5222-row DataFrame (still ignores its date argument; see `R04-C08`).
- Request beyond the observed watermark -> `COVERAGE_INCOMPLETE`.

The original R03 test suite was not modified to conceal the intentionally blocked methods.

## 3. Contract/source handoff

`CONTRACT_SOURCE_MANIFEST.json`: 98 declared items, 98 resolved, 0 missing, 0 over the 400 KB body limit,
92 staged for upload, 5 already identical in HUB and referenced by blob instead of re-uploaded
(handbook, full update scope, coverage non-regression gate, `RULE_ID_INDEX_0930`, `CONTRACT_SCOPE_1145`).

Source sets: engine MASTER rule library (30 bodies incl. all admission matrices and dictionaries),
engine contract/clock sources, engine interface and consumer source (18 files incl. `data/api.py`,
`core/engine.py`, `providers/base.py`, `providers/jqdata.py`, dividend tests), update/publication contracts,
AI-entry and memory indexes.

Honesty fields: `sha256` is not a read claim. Every item carries `agent_read_status`
(FULL / PARTIAL / NOT_READ). Items marked NOT_READ were hashed, structurally parsed and staged verbatim,
not read end to end by the operator.

## 4. Conflict register

`CONTRACT_CONFLICTS.json`: 13 rows, all open, `resolution_owner=GPT`. The eight required topics are covered by
`R04-C01`..`R04-C09`, plus four operator-observed defects (`R04-C10` plane gap, `R04-C11` tail clipping,
`R04-C12` suspended-bar semantics, `R04-C13` R03 static registry annotation).

Hard evidence behind the required topics:

- `R04-C02`: `close`, `factor` and `pre_close` are `required_for_matching=true` for stock daily/1m; the reader
  admits only requested fields. Plane check shows `factor` constant 1.0 and `fq` NULL.
- `R04-C03`: handbook closed the table on `fq_pre_post` while the engine default is `fq="pre"`.
- `R04-C04`: handoff declares completion-time semantics NOT_DEFINED; `jq_clock.py` defines 240 labels
  (09:31-11:30, 13:01-15:00); reader checks dates only.
- `R04-C06`: engine expects `{date, security_type, scale_factor, bonus_pre_tax, per_base}` with `per_base=10`
  for A shares; the plane stores 45 raw per-10-share columns and the candidate does no conversion.
- `R04-C08`: `index_components` is stored per index-year with `asof_date`; the reader reads only the final two
  entries and ignores dated eligibility.
- `R04-C09`: the three publication defects stay open and were not re-run.

## 5. Structure correction

`SYSTEM_STRUCTURE_R4.json`: 23 nodes, 21 edges, 0 dangling endpoints. Every node has `node_id`; every edge is
labelled `FILE_EXISTS` / `STATIC_CALL_EDGE` / `RUNTIME_OBSERVED_EDGE` / `DESIRED_EDGE` / `UNRESOLVED_EDGE`.
`local_parquet` is now a declared node. The registry-builder input is recorded as the R01 registry JSON
(`build_registry_r3.py:80`), not a fresh CURRENT resolution; a fresh CURRENT cleaning/cache read was performed
in this build and compared with the registry layer roots (both match).

## 6. Evidence label correction

See `EVIDENCE_LABEL_CORRECTION_R4.md`. Only R03 checks 8 and 9 used real data; the intraday and event examples
were fixture-based and are relabelled as such without rewriting the R03 report.

## 7. Not done by design

No factory registration, no full engine invocation, no adjustment formula, no corporate-action conversion, no
CURRENT pointer change, no incremental update, no engine core instantiation, no global/historical environment
repair.

## 8. Exact next gaps

`NEXT_MISSING_EVIDENCE_R4.json`: factory injection path, an implemented clock/session contract, adjustment
formula authority, validated per-dataset incremental cursor, index-membership eligibility, A-share announcement
authority, and the lane-updater modules reached by `run_blackbox_research_os.py`.
