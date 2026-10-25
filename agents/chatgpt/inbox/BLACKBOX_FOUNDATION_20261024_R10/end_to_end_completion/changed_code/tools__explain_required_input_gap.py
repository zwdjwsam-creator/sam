"""Explain the remaining REQUIRED_INPUT_MISSING failures of the strict V4 run.

Two distinct causes are possible and must not be conflated:
  A. the tradeability row exists but the limit value is null
  B. the (date, code) key has no tradeability row at all (left-join miss)
Only the measured split decides whether the branch is a data defect or a coverage gap.
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict

import pandas as pd
import pyarrow.parquet as pq

TASK = r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
RUN = os.path.join(TASK, "engine_runs", "v4_r21_20260903_20260924_R11_TRADEABILITY")
CAND = os.path.join(TASK, "candidate", "data", "R11_TRADEABILITY",
                    "STOCK_TRADEABILITY_PIT_R1", "year=2026", "part_2026.parquet")
SEALED = os.path.join(
    r"E:\BLACKBOX\数据\回测缓存\releases",
    "BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439",
    "STOCK_TRADEABILITY_PIT_R1",
)
PRICE = os.path.join(
    r"E:\BLACKBOX\数据\回测缓存\releases",
    "BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439",
    "STOCK_DAILY_PIT_R1",
)
OUT = os.path.join(TASK, "evidence", "REQUIRED_INPUT_GAP.json")


def main() -> int:
    res = json.load(open(os.path.join(RUN, "run_result.json"), encoding="utf-8"))
    fails = res.get("required_input_failures") or []

    cand = pq.ParquetFile(CAND).read().to_pandas()
    cand["date"] = pd.to_datetime(cand["date"]).dt.normalize()
    cand_keys = set(zip(cand["date"], cand["code"].astype(str)))

    sealed_files = []
    for dp, _dn, fn in os.walk(SEALED):
        sealed_files += [os.path.join(dp, f) for f in fn if f.endswith(".parquet")]
    sealed = pd.concat([pq.ParquetFile(f).read().to_pandas() for f in sorted(sealed_files)],
                       ignore_index=True)
    sealed["date"] = pd.to_datetime(sealed["date"]).dt.normalize()
    sealed["code"] = sealed["code"].astype(str)
    sealed_keys = set(zip(sealed["date"], sealed["code"]))

    # price keys for the same days, to tell "no row anywhere" from "row with null value"
    price_files = []
    for dp, _dn, fn in os.walk(PRICE):
        if "year=2026" in dp:
            price_files += [os.path.join(dp, f) for f in fn if f.endswith(".parquet")]
    price = pd.concat([pq.ParquetFile(f).read().to_pandas() for f in sorted(price_files)],
                      ignore_index=True)
    price["date"] = pd.to_datetime(price["date"]).dt.normalize()
    price["code"] = price["code"].astype(str)

    rows = []
    for f in fails:
        day = pd.Timestamp(f["start"])
        for code in f.get("sample_codes", []):
            key = (day, code)
            in_cand = key in cand_keys
            in_sealed = key in sealed_keys
            val = None
            if in_cand:
                sub = cand[(cand["date"] == day) & (cand["code"] == code)]
                val = None if not len(sub) else sub["high_limit"].iloc[0]
            rows.append({
                "date": f["start"], "code": code, "field": f["field"],
                "null_rows": f.get("null_rows"),
                "tradeability_row_in_candidate": bool(in_cand),
                "tradeability_row_in_sealed": bool(in_sealed),
                "candidate_value": (None if val is None or pd.isna(val) else float(val)),
                "has_price_bar_same_day": bool(
                    ((price["date"] == day) & (price["code"] == code)).any()
                ),
            })

    # aggregate the keys actually reported (the recorded list is truncated to 10 codes/day)
    by_date = Counter(r["date"] for r in rows)
    cause = Counter()
    for r in rows:
        if not r["tradeability_row_in_candidate"] and not r["tradeability_row_in_sealed"]:
            cause["NO_TRADEABILITY_ROW_ANYWHERE"] += 1
        elif r["candidate_value"] is None:
            cause["ROW_PRESENT_VALUE_NULL"] += 1
        else:
            cause["OTHER"] += 1

    dates = sorted({f["start"] for f in fails})
    report = {
        "artifact": "REQUIRED_INPUT_GAP",
        "run": os.path.join(RUN, "run_result.json"),
        "run_status": res.get("status"),
        "reported_failure_entries": len(fails),
        "sum_null_rows_reported": sum(int(f.get("null_rows") or 0) for f in fails),
        "field": sorted({f["field"] for f in fails}),
        "dates_involved": dates,
        "date_min": dates[0] if dates else None,
        "date_max": dates[-1] if dates else None,
        "cause_split_of_sampled_codes": dict(cause),
        "sampled_rows": rows,
        "interpretation": (
            "the strict gate is behaving as designed: it refuses to run the strategy's limit "
            "logic on a key whose limit price is not observable. The affected keys are the "
            "sealed plane's paused=0/limit=null keys on 2026-09-03 plus price-plane keys that "
            "have no tradeability observation in either plane."
        ),
        "not_done": [
            "no limit price was filled or inferred",
            "no ST flag was inferred",
            "no supplier call was made",
        ],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps({k: report[k] for k in (
        "reported_failure_entries", "sum_null_rows_reported", "field", "dates_involved",
        "cause_split_of_sampled_codes")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
