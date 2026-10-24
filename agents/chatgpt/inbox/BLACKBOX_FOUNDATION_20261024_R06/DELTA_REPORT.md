# R06/10 delta: candidate-only recovery of 2026-08-31 and 2026-09-01

FOUNDATION_ACCEPTANCE=false. ORDER_ALLOWED=false. PRODUCTION_CHANGE_AUTHORIZED=false.
This is a candidate view with parent inheritance. It is not a sealed full release and it is not an engine admission.

## 1. What was executed

The three supplied scripts were staged byte-identically (git blob identity verified against HUB) and executed unedited.

| step | command | exit | result |
| --- | --- | --- | --- |
| fixture suite, literal | `.\runtime\.venv\Scripts\python.exe reviews\R06\test_r06.py` | 1 | FAILED, environment locale only |
| fixture suite, UTF-8 mode | `.\runtime\.venv\Scripts\python.exe -X utf8 reviews\R06\test_r06.py` | 0 | 11/11 PASS |
| bounded repair | `.\runtime\.venv\Scripts\python.exe -X utf8 reviews\R06\r06_gap_repair.py --gap-inputs reviews\R06\GAP_REPAIR_INPUTS_R05.json` | 0 | CANDIDATE_BUILT |
| replay | same command | 0 | ALREADY_BUILT_VERIFIED |
| diagnostic read | R05 `EngineLocalValueProvider` on the candidate registry | 0 | 4 dates visible |

The literal command failed because `test_r06.py` reads a manifest with no `encoding=`, so a cp936 host decodes UTF-8 into mojibake paths and the later `publish_candidate(source_pins)` step cannot open them. No parquet or business data is involved at that point and no supplied code was edited. Re-running the same bytes with the interpreter in UTF-8 mode (PEP 686) fixes the locale default only.

## 2. What is repaired, in the candidate only

Two products, one year partition each, two dates:

| product | parent rows | added 2026-08-31 | added 2026-09-01 | candidate rows | conserved |
| --- | --- | --- | --- | --- | --- |
| STOCK_DAILY_PIT_R1 | 949470 | 5212 | 5214 | 959896 | True |
| STOCK_DAILY_RAW_PIT_R1 | 949470 | 5212 | 5214 | 959896 | True |

The 949470 parent figure was confirmed as the actual partition row count; 959896 is derived from the source and parent tables in code, not asserted as an expected value.

CLEAN side: the whole parent stock-daily directory (232 files) is carried into the candidate view and the two hash-pinned RAW units are added at their evidenced `clean_rel` paths, giving 234 files. The parent directory still holds exactly 232 files and its size/mtime fingerprints are unchanged.

Guards that held: CURRENT pair match, RAW and sidecar hash pins, row counts, duplicate keys, numeric nulls, `fq` all-null, adjacent-unit mapping reproduction, absence of the target dates in the parent, schema coverage with no unknown column, full inheritance, row conservation, source re-check after build, parent-directory stability.

Guards that did not fire: none. No rejection was encountered, so there is no preserved rejection to report in this round.

## 3. What remains dirty or unverified

- STOCK_FACTOR_DAILY_R1 and MARKET_STRUCTURE_DAILY_R1 still lack both dates. The factor product needs at least 250 prior sessions (declared lookback, `ma250`); the structure product declares no lookback but needs one session because `allA_positive_ratio` uses `r1`.
- No price product carries `pre_close`, `is_st`, `paused`, `high_limit` or `low_limit`. Those exist in the RAW cleaning units, and for a narrower window in STOCK_TRADEABILITY_PIT_R1. That product covers 2026-07-13..2026-08-12 plus one 2026-09-03 tip, so tradeability is unbound on both recovered dates.
- A constant `factor=1` with `fq=NULL` in a RAW_NONE unit does not establish an adjusted series. ADJUST_FACTOR_PIT_R1 remains the separate fq=pre product and already covers both dates.
- Inherited products are preserved references, not re-certified claims. No FULL_HISTORY, REQUIRED_FIELDS_OK, gap-free or all-product READY flag is produced.

## 4. The same two-session hole is not limited to stock daily

Using ADJUST_FACTOR_PIT_R1's date set as the session reference (39 sessions from 2026-08-03 to 2026-09-24):

- `STOCK_DAILY_PIT_R1`: missing 2 session(s), max date 2026-09-24, INTERIOR_HOLE — 2026-08-31, 2026-09-01
- `STOCK_DAILY_RAW_PIT_R1`: missing 2 session(s), max date 2026-09-24, INTERIOR_HOLE — 2026-08-31, 2026-09-01
- `STOCK_FACTOR_DAILY_R1`: missing 2 session(s), max date 2026-09-24, INTERIOR_HOLE — 2026-08-31, 2026-09-01
- `MARKET_STRUCTURE_DAILY_R1`: missing 2 session(s), max date 2026-09-24, INTERIOR_HOLE — 2026-08-31, 2026-09-01
- `ETF_DAILY_PIT_R1`: missing 2 session(s), max date 2026-09-24, INTERIOR_HOLE — 2026-08-31, 2026-09-01
- `ETF_FACTOR_DAILY_R1`: missing 2 session(s), max date 2026-09-24, INTERIOR_HOLE — 2026-08-31, 2026-09-01
- `INDEX_DAILY_R1`: missing 2 session(s), max date 2026-09-24, INTERIOR_HOLE — 2026-08-31, 2026-09-01
- `INDEX_FACTOR_DAILY_R1`: missing 2 session(s), max date 2026-09-24, INTERIOR_HOLE — 2026-08-31, 2026-09-01
- `VALUATION_PIT_R1`: missing 8 session(s), max date 2026-09-24, INTERIOR_HOLE — 2026-08-03, 2026-08-04, 2026-08-05, 2026-08-06, 2026-08-07, 2026-08-10, 2026-08-31, 2026-09-01
- `FUND_NAV_PIT_R1`: missing 8 session(s), max date 2026-09-24, INTERIOR_HOLE — 2026-08-24, 2026-08-26, 2026-08-27, 2026-08-31, 2026-09-01, 2026-09-09, 2026-09-10, 2026-09-17
- `ADJUST_FACTOR_PIT_R1`: missing 0 session(s), max date 2026-09-24, INTERIOR_HOLE
- `SW_L1_MEMBERSHIP_PIT_R1`: missing 0 session(s), max date 2026-09-24, INTERIOR_HOLE
- `STOCK_TRADEABILITY_PIT_R1`: missing 30 session(s), max date 2026-09-03, INTERIOR_HOLE

Seven products lose exactly the same two sessions while their own maximum date is 2026-09-24. That signature repeats the sibling-release mechanism recorded in R05 and is not limited to stock daily. VALUATION_PIT_R1 additionally misses 2026-08-03..2026-08-10 and FUND_NAV_PIT_R1 misses six further scattered sessions; those extra holes are recorded and left unadjudicated. This comparison is a date-set fact only. It does not prove the same driver caused every product, and it does not authorise a repair of the other products.

## 5. Publication boundary

`r06_bundle_store.py` was exercised only inside `test_r06.py` fixtures: one commit marker, before-commit failure, after-commit complete generation, stale parent rejection, corruption rejection. It was not invoked on any real store, legacy CURRENT file or business candidate, and no CANDIDATE_CURRENT switch was performed. A candidate manifest alone does not make legacy independent-pointer readers atomic.

No production pointer, seal, certificate, quarantine, ledger or CURRENT file was rewritten. No hardlinked inherited file was opened for writing or had attributes changed. No cleanup of source, parents, temp, old candidates or evidence was performed.

## 6. Evidence corrections in this round

- `finance.STK_MONEY_FLOW` is unknown-permission, not a paid-module denial; the money-flow domain stays blocked because `get_money_flow` carries the explicit paid text.
- `get_extras(paused)` fails on an unsupported info parameter, not on entitlement; `get_price(paused)` is permitted, so the paused route is `get_price`.
- Five `finance.STK_LOCK*/STK_ABNORMAL_CHANGE` names are absent from the installed SDK surface; that is a name/version mismatch whose entitlement is unverified, not denied.
- `get_factor_values` with `roe/ROE/BV/pe_ratio/circ_market_cap` is invalid-factor PROBE_FAIL with no entitlement meaning; the paid conclusion rests on `get_all_factors` and `get_factor_values(market_cap)` only.
- Two unmatched RAW files are selection history, not equivalence. Both versions are preserved and no newest-build rule was applied.
- The CURRENT logical cleaning release is `BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439`; R45 is its parent and the physical provider of `standard/price` through a junction. The repair followed `standard_root` and recorded realpaths rather than choosing a label.

## 7. R07 inputs staged

Complete current compiler body (sha256 `c8ddf805a6ddc998cda507f2aa5c92f27b13a43b5445e5bfed21477c5822f336`, cited hash confirmed equal, not substituted) plus the five registries the compiler writes and the current resolver selects. `p7_gate_common` is reported with its hash and role instead of being uploaded, because it only writes the HAND note. NEXT_UPDATE_BINDINGS covers 12 domain routes with explicit gaps: supplier lag unmeasured, no entitlement change, no target date asserted, 18 catalog products without a physical root under the CURRENT cache release.

## 8. Reproduction

```
cd E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024
.\runtime\.venv\Scripts\python.exe -X utf8 reviews\R06\test_r06.py
.\runtime\.venv\Scripts\python.exe -X utf8 reviews\R06\r06_gap_repair.py --gap-inputs reviews\R06\GAP_REPAIR_INPUTS_R05.json
```

Replay returns `ALREADY_BUILT_VERIFIED` while every artifact still matches its manifest pin (5 artifacts, drift 0) and every source pin still matches (True).
