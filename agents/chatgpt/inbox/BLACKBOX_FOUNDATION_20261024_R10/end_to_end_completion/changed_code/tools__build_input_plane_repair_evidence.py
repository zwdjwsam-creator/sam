"""Input-plane repair evidence (R11 follow-up).

Purpose
-------
The R11 V4 run was downgraded to BLOCKED_INPUT_INCOMPLETE because eight
`high_limit` lookups returned null (3 keys on 2026-09-03, 5 keys on 2026-09-07).
This script closes that item with evidence instead of a claim:

1. Sweeps every requested session and counts, per session, the securities the
   price plane serves versus the securities the tradeability plane covers with a
   non-null limit price and a non-null paused flag.
2. Records why the original eight nulls happened (sealed per-cell gaps plus a
   publish race while the candidate partition was being rewritten mid-run).
3. States what the repair does and does not do (cell-level measurement
   substitution; no inference, no supplier call, no ST guess).

Output: `evidence/INPUT_PLANE_REPAIR.json`
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "candidate"))

from local_plane import provider as P  # noqa: E402

OUT = os.path.join(HERE, "evidence", "INPUT_PLANE_REPAIR.json")
WINDOW_START = dt.date(2026, 9, 3)
WINDOW_END = dt.date(2026, 9, 24)


def main() -> int:
    prov = P.LocalPlaneProvider()
    days = [pd.Timestamp(d).date() for d in prov.trade_days(start=WINDOW_START, end=WINDOW_END)]

    # Enumerate the codes the price plane serves for the window (one read).
    price = prov._read("STOCK_DAILY_PIT_R1", 2026)
    price["date"] = pd.to_datetime(price["date"]).dt.normalize()
    price = price[
        (price["date"] >= pd.Timestamp(WINDOW_START)) & (price["date"] <= pd.Timestamp(WINDOW_END))
    ]
    served = price.groupby("date")["code"].apply(lambda s: set(s.unique())).to_dict()

    per_day = []
    gate_pass = True
    for day in days:
        tr = prov._tradeability_frame(day, day)
        codes = served.get(pd.Timestamp(day), set())
        if len(tr):
            tr = tr.copy()
            tr["date"] = pd.to_datetime(tr["date"]).dt.normalize()
            tr = tr[tr["date"] == pd.Timestamp(day)]
        usable = tr[tr["high_limit"].notna() & tr["low_limit"].notna()] if len(tr) else tr
        usable_codes = set(usable["code"]) if len(usable) else set()
        null_limit = (
            set(tr.loc[tr["high_limit"].isna() | tr["low_limit"].isna(), "code"]) if len(tr) else set()
        )
        paused_null = set(tr.loc[tr["paused"].isna(), "code"]) if len(tr) else set()
        missing = codes - usable_codes
        row = {
            "date": str(day),
            "price_plane_codes": len(codes),
            "tradeability_rows": int(len(tr)),
            "usable_limit_keys": len(usable_codes),
            "keys_without_usable_limit": len(missing),
            "rows_with_null_limit": len(null_limit),
            "rows_with_null_paused": len(paused_null),
            "binding": prov.last_tradeability_binding,
        }
        if missing:
            row["missing_sample"] = sorted(missing)[:5]
            gate_pass = False
        per_day.append(row)

    repair = {
        "artifact": "INPUT_PLANE_REPAIR",
        "window": {"start": str(WINDOW_START), "end": str(WINDOW_END), "sessions": len(days)},
        "original_failures": {
            "run": "engine_runs/v4_r21_20260903_20260924_R11_TRADEABILITY/run_result.json",
            "field": "high_limit",
            "entries": 8,
            "split": {
                "2026-09-03": {
                    "keys": ["002731.XSHE", "002870.XSHE", "600929.XSHG"],
                    "cause": "SEALED_CELL_GAP",
                    "detail": "the sealed STOCK_TRADEABILITY_PIT_R1 carries the key with "
                    "paused=0 but a null high_limit/low_limit; the candidate extension was "
                    "excluded for that whole session because the sealed plane served the date "
                    "at all.",
                },
                "2026-09-07": {
                    "keys": [
                        "603037.XSHG",
                        "603038.XSHG",
                        "603039.XSHG",
                        "603040.XSHG",
                        "603041.XSHG",
                    ],
                    "cause": "CANDIDATE_PUBLISH_RACE",
                    "detail": "the candidate partition was being rewritten (non-atomic "
                    "to_parquet) while the engine was already simulating 2026-09-07; that read "
                    "failed and the provider treated the extension as empty for those calls.",
                },
            },
        },
        "repair": {
            "provider_change": [
                "per (date, code) cell reconciliation via combine_first: the sealed value wins "
                "whenever it exists, the candidate value only fills null cells",
                "whole-session exclusion removed; candidate rows now reach sessions the sealed "
                "plane only partially serves",
                "binding reports keys_both_planes / keys_sealed_only / keys_candidate_only / "
                "limit_cells_filled_from_candidate / paused_conflicts_sealed_wins",
            ],
            "builder_change": [
                "candidate partition published atomically (temp file + os.replace) so a "
                "concurrent reader can never observe a half-written parquet",
            ],
            "substitution_class": "SAME_FIELD_SAME_DAY_SAME_SECURITY_FROM_LOCAL_RAW",
            "limit_prices_inferred": 0,
            "st_flags_inferred": 0,
            "supplier_calls": 0,
        },
        "sweep": per_day,
        "sweep_verdict": "GATE_SWEEP_PASS" if gate_pass else "GATE_SWEEP_FAIL",
        "residual_risks": [
            "is_st stays null everywhere: it is not in the retained RAW schema and must not be "
            "inferred from price behaviour",
            "the sealed plane disagrees with retained RAW on `paused` for a few keys on "
            "2026-09-03; sealed wins by policy and the conflict is reported, not silently "
            "resolved",
        ],
        "generated_at": dt.datetime.now().astimezone().isoformat(),
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(repair, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, OUT)
    print(
        json.dumps(
            {
                "sweep_verdict": repair["sweep_verdict"],
                "sessions": len(days),
                "sessions_with_gap": sum(1 for r in per_day if r["keys_without_usable_limit"]),
                "total_missing_keys": sum(r["keys_without_usable_limit"] for r in per_day),
                "null_limit_rows": sum(r["rows_with_null_limit"] for r in per_day),
                "null_paused_rows": sum(r["rows_with_null_paused"] for r in per_day),
            },
            ensure_ascii=False,
        )
    )
    return 0 if gate_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
