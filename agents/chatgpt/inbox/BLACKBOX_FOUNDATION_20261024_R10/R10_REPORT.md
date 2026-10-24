# R10 — final planned round: operating entry activated and measured

Round: R10/10 (final planned execution round). Host: ZHANGWEI. Date: 2026-10-24.
Consumes: `agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R10_OPERATING_ENTRY_20261024_2230`.

```
FULL_GOAL_MET=false
FOUNDATION_ACCEPTANCE=false
ORDER_ALLOWED=false
CURRENT_SWITCH_ALLOWED=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
```

No supplier call, no login, no download, no write to business data, no CURRENT switch, no publication,
no engine start, no order. R09's acceptance is recorded as *bounded ordered candidate verification only*.

## 1. Package intake — every pin matched

7/7 supplied files reproduced at their declared sha256 and byte size, staged unchanged into
`reviews/R10/operating_entry/` (the path the operations guide names). All 4 evidence inputs were staged as
local copies and each recomputed **canonical-JSON** sha256 matched its declared value:

| input | declared = recomputed |
|---|---|
| matrix | `1d4963e9…92d2901` |
| dependency | `ac51fe94…a6355db7` |
| bindings | `7ac4cb53…87f26891` |
| acquisition | `5640c889…b807e49250` |

Originals were not edited; the byte-level copies differ from originals only in serialisation, which is why the
pin is semantic rather than byte-level for these four.

## 2. Offline controls: 24/24 on this host

`test_blackbox_operate_r10.py` → exit 0, **24 controls PASS** (same count as the reviewer host). They cover
synthetic Arrow reads, key/field rejection, stale parent/calendar rejection, unknown schema/route rejection,
duplicate evidence-key rejection, and guarded engine-import side effects / auth / construction.

## 3. Real desktop operations — all five surfaces exercised

Every operation ran the genuine CACHE must-read preflight: `MUST_READ_PRECHECK = PASS`, `problems = []`,
kernel `b05a6995…` (1167 B, 21 lines), both rules `VERIFIED`. No STOP was converted.

**catalog** (exit 0): 41 entities joined — matches the reviewer's verified 41. **13 explicit product↔updater
joins**, 28 products explicitly `UNBOUND_IN_THIS_EVIDENCE_JOIN`. No prefix-guessed route was activated.
`serving_authority` is `REQUEST_NOT_EVALUATED` for all 41. The three review corrections ride in the output:
INDEX canonical full history supersedes the old H1 minute-derivation instruction, the universe's historical
window is not a current trade filter, and ADJUST_FACTOR's sidecar is not an acquisition receipt.
Field ownership carries 5 products; 11 dependency edges; target-date rule present.

**describe** (5 products, exit 0 each): RAW_NONE stock, adjustment factor, universe, index, and the fund-like
virtual view. Each returns recorded schema + provenance + update route, and each keeps `serving_authority`
at `REQUEST_NOT_EVALUATED`. Unknown product → `STOP PRODUCT_NOT_IN_REVIEWED_CATALOG`, exit 3.

**query** (exit 0): `STOCK_DAILY_RAW_PIT_R1`, `000001.XSHE`, 2026-08-28→2026-09-02, `close` →
`BOUNDED_OBSERVATIONS_SERVED`, **4 expected keys / 4 returned keys**, four finite observations
(11.65 / 11.72 / 11.92 / 11.91), with parent-CURRENT pair, calendar and the candidate partition all pinned.
This is a bounded candidate RAW_NONE read: not a universe, not a listing date, not an adjustment factor, not
tradeability or PIT eligibility, and not engine admission.

**update-plan** (6 products, exit 0 each): `CONTRACT_PLAN_ONLY; NO_SUPPLIER_CALL_OR_WRITER`, with the
9-step execution order verbatim. Concrete bindings are shown (e.g. tradeability: `SRC_JQDATA_SDK`,
`get_price(fields=['paused','high_limit','low_limit']) + get_extras('is_st') + finance.STK_STATUS_CHANGE/STK_LIST`,
credential locator id only, watermark `2026-07-13..2026-08-12 plus one 2026-09-03 tip`). The word "download gap"
stays a record to reconcile, never an authorization.

**six real negative controls** (each exit 3, each `SOURCE_ABSENCE_CLAIM_ALLOWED=false`):
`REQUEST_OUTSIDE_PINNED_CALENDAR; NO_SOURCE_ABSENCE_CLAIM`, `UNSUPPORTED_FIELD`, `CANONICAL_CODE_REQUIRED`,
`PRODUCT_READER_NOT_ACTIVATED; NO_RAW_FALLBACK`, `REQUEST_WINDOW_LIMIT_31_DAYS`, `INVALID_CODE_COUNT`.

## 4. Engine import — a real outcome, not a list inference

`engine_import_probe_r10.py --desktop-import` → exit 0, verdict **`IMPORT_ATTEMPTED_FORBIDDEN_SIDE_EFFECT`**,
blocked event `os.mkdir`.

What did succeed: all three pinned sources matched their declared sha256; `bullet_trade.core.engine`,
`bullet_trade.data.api` and `bullet_trade.data.providers.base` imported inside the guarded child; imported
module paths resolved inside the pinned root; `BacktestEngine`, `DataProvider` and `get_price` are present;
nothing was constructed, no provider registered, no auth call, no network, no order.

Why a clean import cannot be claimed, located exactly (additive read-only diagnostic; no guard relaxed, no
package installed):

```
bullet_trade/core/globals.py:421   log = Logger()                 # module level
bullet_trade/core/globals.py:156   os.makedirs(log_dir, exist_ok=True)   # arg0 = "./logs"
bullet_trade/core/__init__.py:12   from .globals import g, log
```

The `mkdtemp`-style error the reviewer warned about is **not** involved: this is a genuine import-time
directory-creation side effect, swallowed by the engine's own `except Exception: pass`. So the honest
statement is *import structurally complete, import-time write attempted and denied* — **not** a missing
dependency, and **not** a proven startup failure. `formal_engine_admission = NOT_ADMITTED`; unguarded start,
provider wiring, PIT/session/matching contracts and any backtest remain unproven.

## 5. Full-goal decision — `FULL_GOAL_MET=false`

Met this round: a reviewed local operating entry that runs on real evidence; catalog/describe/query/update-plan
all working; 41 entities and 13 updater joins reproduced; one bounded read with complete keys; six real
rejections; one real engine-import outcome with its exact event and frame.

Still unmet (7 material predicates, each with its evidence):

1. adjustment source→cache lineage and symbol/field completeness — sidecar 12,182,523 vs physical 12,266,026
   (Δ 83,503) unresolved; the 2026-09-01 session carries 11 rows; per-date lineage rows absent.
2. universe/tradeability producer and coverage contract — `PRODUCER_UNBOUND_IN_REVIEWED_EVIDENCE`; universe
   window ends 2026-07-20; tradeability spans 2026-07-13..2026-09-03 with 15 missing sessions.
3. empty required virtual-view members — `FUND_DAILY_PIT_R1` and `FUND_FACTOR_DAILY_R1` have 0 parquet;
   `FUND_LIKE_ASSET_VIEW_R1` holds only `VIEW.json`, so an empty required member must not read as ETF-only.
4. product-specific current-cache gaps — 11 measured products with missing sessions; 2026-08-31 and
   2026-09-01 absent from stock/ETF/index/valuation/fund-NAV planes in the mounted release.
5. genuine engine admission and runtime — see §4.
6. executable incremental/publication readiness — contracts are navigation only; no checkpoint advance,
   append-only RAW receipt, publication or freshness proof was executed or is authorized.
7. rule-body generation binding — historical/generation-specific bodies stay as history; the stale capability
   generation remains rejected, not relabelled.

Explicitly not claimed: that the original data is absent, that data was lost in migration, that a one-symbol
query proves the five-part goal, or that latest full-system updates are complete. Physical copy fidelity was
accepted separately in R08 and was **not** re-tested by copying, re-downloading or re-cleaning the preserved source.

## 6. Boundaries honoured

Every artifact still carries `FOUNDATION_ACCEPTANCE=false`, `ORDER_ALLOWED=false`,
`CURRENT_SWITCH_ALLOWED=false`, `NEW_DATA_ACQUISITION_AUTHORIZED=false`. No business file, seal, pointer,
rule body, CURRENT release or credential was modified. This round consumed the last planned slot; no
further round is self-authorized by this report.
