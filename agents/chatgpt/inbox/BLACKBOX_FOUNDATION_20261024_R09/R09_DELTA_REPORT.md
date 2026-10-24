# R09/10 delivery — control successors, desktop entry result, six-layer matrix

Round R09/10 (one future execution delivery remains after this one).
Reviewer package: `agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R09_CONTROL_INTEGRATION_20261024_2100`.
Host: ZHANGWEI desktop. No network acquisition, no download, no production edit, no CURRENT switch.

## 1. Review package accepted as pinned

All six reviewer files were fetched and hashed. Every SHA256 and byte count matches
`R09_IMPLEMENTATION_PACKAGE.json` (`all_match = true`; see `R09_CONTROL_AND_ENTRY_RESULTS.json`).

## 2. Successor build from the four exact original bodies

`build_r09_control_successor.py --packet <R08 body export>` produced
`_OPS/FOUNDATION_RECOVERY_20261024/candidate/r09/control_successor`.

| target | build SHA256 | reviewer expected | match |
|---|---|---|---|
| `blackbox_must_read_preflight_r1.py` | `0d7b039e…f99525f` | `0d7b039e…f99525f` | yes |
| `blackbox_request_window_data_capability_resolver_r1.py` | `f847a918…d23fcfb7` | same | yes |
| `pre_ingestion_gate.py` | `365784a5…90f4c512` | same | yes |
| `blackbox_daily_increment_publish_gate_r1.py` | `c4600d14…2fba1160` | same | yes |

Source pins are the four recorded originals; `production_modified = false` in the build manifest.
Nothing was installed into the production tree.

## 3. Offline controls re-run on this desktop

`test_r09_controls.py` → `status = PASS`, **38/38** controls, `supplier_calls = 0`,
`production_writes = 0`, `FOUNDATION_ACCEPTANCE = false`.
Recorded stdout: `reviews/R09/control_2100/DESKTOP_CONTROLS_STDOUT.txt`.
This reproduces the review host's control set; it is still control evidence, not engine admission.

## 4. Ordered candidate entry on this desktop: STOP at stage 1

`r09_control_runtime.py` exited 3 with:

```
status=STOP  error=ValueError  reason=MUST_READ_PREFLIGHT_FAILED
FileNotFoundError: [Errno 2] No usable temporary directory found
```

Exact cause (full traceback in `DESKTOP_ORDERED_ENTRY.txt`, reproduction in `_diag_child.py`):

```
blackbox_must_read_preflight_r1.py:17  from _base import *
E:\BLACKBOX\脚本\_base.py:30           ("ALLOW_TEMPFILE_DELETE", Path(tempfile.gettempdir()), None),
tempfile._get_default_tempdir()        probes by CREATING a file
audit guard                            denies O_CREAT  ->  no usable temp dir  ->  import fails
```

This is an incompatibility between the reviewed guard and the real `_base` import chain, not a
preflight logic defect. Per the review instruction the guard was **not** relaxed: no exception was
added, no `_base` edit, no production patch. Stage 1 therefore remains `STOP`, and the ordered entry
has **not** passed on this desktop.

Consequence for the reviewer: either the guard needs a reviewer-authorized, narrowly scoped exception
for the import-time temp-directory probe, or `_base.py:30` must stop calling `tempfile.gettempdir()`
at import. Both are decisions outside this round's authority.

## 5. Stages 2–4 executed with a disclosed stage-1 substitution

To keep the round useful without pretending stage 1 passed, `diagnose_stages_2_4_stage1_blocked.py`
substitutes only the stage-1 callback with a marker and runs stages 2/3/4 against real sources. The
output is labelled `R09_STAGES_2_4_DIAGNOSTIC_WITH_STAGE1_SUBSTITUTED; NOT_A_PASSED_ORDERED_ENTRY`.

- Stage 2 (pinned binding): R08 manifest `89d2a903…`, CURRENT cache/cleaning pair, selected price and
  factor artifacts, and four applicable rule/lesson bodies all re-hashed before read.
- Stage 3 (bounded read): price vs factor over `(date, code)` — 949 470 parent keys → 959 896 candidate
  keys, **0 lost keys, 0 lost `close` observations**; `000001.XSHE` 2026-08-31 close `11.72` and
  2026-09-01 close `11.92` served from the **candidate override**, factor identical; canonical
  399303.XSHE adapter returns 5 242 rows (diagnostic only, no RAW fallback, no PIT or master admission).
- Stage 4 (negative controls): synthetic shadow admission parses exactly once
  (`REAL_MARKET_DATA` → `REAL_DATA_NOT_AUTHORIZED`), live publisher call rejected before its matrix
  (`R09_SUCCESSOR_DRY_RUN_ONLY`), supplier calls 0.

Important: the read was served by the candidate override, **not** by CURRENT. CURRENT still lacks
2026-08-31 and 2026-09-01 for stock price/factor.

## 6. Six-layer matrix — no layer borrows another layer's PASS

`SIX_LAYER_EVIDENCE_MATRIX.json`. Each layer carries its own figures, its own SHA-pinned evidence and
its own `does_not_prove` list.

| layer | status | decisive figures |
|---|---|---|
| L1 copied assets | `PRESENT_AND_PINNED_WITHIN_MANIFEST_SCOPE` | 4 files / 219 098 719 B on disk; 3 R08 artifacts (factor 959 896 rows, structure 178, unobserved grid 34 477); 234 vs 232 candidate/parent daily; 51 inherited products by reference, **0 copies created** |
| L2 classified assets | `CLASSIFIED_WITH_DECLARED_GAPS` | 14 canonical products classified with per-product date range/rows/coverage; catalog 42 rows (L1 25 / L2 12 / L3 2 / META 2; ACTIVE 38); `MARKET_STRUCTURE_DAILY_R1` dirty: SW_UNVERIFIED, PIT_UNIVERSE_UNRESOLVED |
| L3 usable read requests | `CANDIDATE_READ_PASS__CURRENT_READ_NOT_SERVED` | 959 896 keys, 0 lost, 0 lost `close`; two request rows served; index adapter 5 242 rows diagnostic only |
| L4 formal engine admission | `NOT_ADMITTED` | `RUNTIME_INCOMPLETE_FOR_ENGINE_STARTUP`; 8 missing packages; `bullet-trade` not installed; wiring `SOURCE_REFERENCE_ONLY_NOT_EXECUTED` |
| L5 incremental RAW staging | `UNITS_PRESENT_AND_PINNED__NO_NEW_ACQUISITION` | 6 pinned RAW units for the two dates (ETF 1 623 / 1 624 rows, valuation, adjust_factor ×2) + 4 stock RAW/sidecar pins; 0 new units; append-only preserved |
| L6 publication / latest freshness | `CURRENT_UNCHANGED__NOT_GLOBALLY_FRESH` | CURRENT pair unchanged (`b2ce53f0…`, `9abad90c…`); release asof 2026-09-24; capability generation `TIP_REBASE_ASOF_20260924_20260925_034907`; per-domain gaps remain; `SEAL.json` carries no product or generation identity; live publish `FORBIDDEN` |

Cross-layer rules restated: candidate read PASS does not upgrade CURRENT; presence does not upgrade
usability; usability does not upgrade admission; RAW presence does not upgrade publication.

## 7. Four unresolved ownership/receipt items — narrowed, not re-downloaded

`FOUR_UNRESOLVED_ITEMS_NARROWED.json` + byte-exact bodies in `NARROWING_SOURCE_BODIES.json`.
Only existing inventories and the exact current consumers were read; no global scan, no acquisition.

1. **Universe / tradeability producer ownership.** Both are ACTIVE catalog rows (L1/STOCK) and are
   read by `blackbox_data_access_resolver_r1.py` (:125–127 name map, :210–211 PIT policy) and by
   `blackbox_external_market_evidence_data_agent_r1.py` (:228, :405). No writer exists in
   `脚本`, the cache-compiler task, or `研究系统/数据平面`. Content is stale by declared asof:
   `MARKET_UNIVERSE_PIT_R1` max 2026-07-20; `STOCK_TRADEABILITY_PIT_R1` max 2026-09-03 with 15
   missing sessions; CURRENT declares `TRADEABILITY_EFFECTIVE_ASOF=2026-09-03`,
   `inherited_0903_until_security_state_tip`. Open: name the producer interface. Do not rebuild.
2. **Adjust-factor refresh receipt.** The receipt exists at product level:
   `ADJUST_FACTOR_PIT_R1/COVERAGE.json` with `reason=BACKWARD_DIRTY_FULL_HISTORY_REPLACE`,
   `tip_extended_at=2026-09-24T19:56:50+00:00`, exact `tip_source`
   `adjust_factor_stock__incremental_20260924__20260925_030214.parquet`, `n_rows=12 182 523`,
   `date_max=2026-09-24`, `n_rows_year_2026=863 710`; coverage 3 097/3 097 sessions, 0 read errors.
   Open: per-date RAW→Cleaning→Cache linkage and the meaning of the 12 degraded 2026 dates.
3. **SW L2/L3 route generation and content.** `TIP_COMPILER.inject_sw` owns the routes. All three
   CURRENT pointers resolve, exist, are non-thin, and their derived content max equals
   `formal_data_asof = 2026-09-24`: L1 12 587 795 membership / 90 046 structure, L2 12 575 466 /
   351 502, L3 12 564 290 / 825 939, 13 partition years each, `gate_pass=true`, `thin_days=0`.
   Open: the candidate inherits these by name reference only (`PRESERVED_REFERENCE_NOT_REVERIFIED`).
4. **Reader generation binding.** `CURRENT_CACHE_RELEASE.cache_release_id` is the FUND_NAV release,
   while the `RELEASE.json` inside that same `release_root` carries the TIP_REBASE id;
   `MANIFEST.json` names FUND_NAV with parent TIP_REBASE and `products_added=[FUND_NAV_PIT_R1]`;
   `CURRENT_CLEANING_RELEASE.release_id` is R33_FUND_NAV while `parent_release_id` is R45_DAILY_TIP
   and its `quarantine_root`/`ledger_path` live under R45; `SEAL.json` is 70 bytes of
   `accepted`+`sealed_at`. Generation identity therefore depends on the reader path. Open: declare
   the pointer as the only generation authority and make the seal carry it.

## 8. Boundaries kept

`FOUNDATION_ACCEPTANCE=false`, `ORDER_ALLOWED=false`, `PRODUCTION_CHANGE_AUTHORIZED=false`,
`CURRENT_SWITCH_ALLOWED=false`, `NEW_DATA_ACQUISITION_AUTHORIZED=false`, network calls 0,
downloads 0, source-absence claims 0.

## 9. What R10 still has to decide

1. Whether the guarded preflight may receive a reviewer-authorized narrow exception for the
   import-time temp-directory probe (or `_base.py:30` is changed); until then the ordered entry
   cannot pass on this host.
2. Whether L3 candidate usability plus the L5 RAW units are sufficient to authorize a
   candidate-only promotion rehearsal, or CURRENT must stay untouched.
3. Which of the four narrowed items are accepted as settled and which need a named owner.
4. Whether missing engine runtime packages are in scope for R10 at all.

This delivery does not accept the foundation, does not publish, and does not claim engine admission.
