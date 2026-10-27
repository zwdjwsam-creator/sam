# ZHANGWEI - R4 correction: 600621 was still suspended on 2026-10-27

at: 2026-10-27T20:47:05+0800
supersedes: the "suspended-then-reopened" reading in DIAGNOSIS_R4.json

## Corrected fact

600621.XSHG 华鑫股份 was halted for **two full sessions, 2026-10-26 and 2026-10-27**,
and resumed on **2026-10-28**. So 2026-10-27 had no trading at all.

- 2026-10-26 halt announcement: controlling shareholder 仪电集团 planning a share
  transfer that could change control; halt expected not to exceed two trading days.
  (公告编号 临2026-034, 上海证券报 / 中国证券报)
- 2026-10-27 framework agreement: 286,000,000 shares (26.99%) to 国盛集团 and 国茂控股
  at 13.85 CNY each, 3.966 billion CNY total; controlling shareholder becomes
  国盛集团, ultimate controller unchanged (上海市国资委); resume from the 2026-10-28 open.

## What the supplier did

It flagged the first halt day correctly (`paused=1`, band pinned to pre_close, zero
volume) and missed the second: `paused=0` with a normal +/-10% band, yet zero trades,
zero money and null open/high/low. Across all 17 sessions and 1,098 accepted batches
this shape appears exactly once, so it is not systemic.

Correct classification: **SUSPENDED_UNFLAGGED_BY_SUPPLIER**, a no-trade session. It is
not missing data, not a coverage gap, not a supplier outage, and it does not corrupt
any accepted row. The reported close 14.90 is the carried-over last print and must not
be consumed as a 10-27 close, return or mark.

## Why the gate must change

`LIVE_BAR_NULL` can never be satisfied when the supplier's own pause flag is wrong, so
one code halts a product and a day. A data-only discriminator is available and does not
need announcements: close == pre_close, volume == money == 0, and null open/high/low.
Recommend classifying that shape as NO_TRADE_SESSION_SUPPLIER_UNFLAGGED, recording it
per code and session, keeping the other 79 rows, and continuing with no fill. Keep the
hard stop for non-zero volume with a null price, a null close, or a band inconsistent
with pre_close.

## Scope effect

2026-10-28 is the resumption and sits outside the 17-session plan, which ends 10-27, so
the next increment is the first that can see post-transfer price action. The 13.85
transfer price is 7.05% below the 14.90 last close - arithmetic only, not a view.

## Process note

I closed the original diagnosis on supplier data alone and did not look up the
announcement. That was the miss. The original `DIAGNOSIS_R4.json` bytes are untouched;
this addendum carries the correction.

Artifact: `DIAGNOSIS_R4_ADDENDUM_600621.json` (7732 B, `89d4136089b829be0e4dcd06e8e4fdde0ed5a28bc11a163b899a89b6ee2d13da`)
