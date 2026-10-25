"""Inventory the retained raw daily gap batches: date coverage and status/limit field completeness.

Read-only. Answers one question only: can tradeability (paused/high_limit/low_limit)
for the engine window be restored from retained authoritative RAW, or is it BLOCKED?
"""
from __future__ import annotations

import json
import os
import re

import pandas as pd
import pyarrow.parquet as pq

RAW = r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P2_stock_daily"
OUT = r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\evidence\RAW_STATUS_FIELD_INVENTORY.json"


def main() -> int:
    rows = []
    for name in sorted(os.listdir(RAW)):
        if not name.endswith(".parquet"):
            continue
        m = re.search(r"gap_(\d{8})", name)
        if not m:
            continue
        path = os.path.join(RAW, name)
        pf = pq.ParquetFile(path)
        cols = pf.schema_arrow.names
        df = pf.read().to_pandas()
        day = pd.to_datetime(df["time"]).dt.normalize()
        rec = {
            "file": name,
            "batch_date": m.group(1),
            "rows": int(len(df)),
            "columns": cols,
            "distinct_dates": [str(d.date()) for d in sorted(day.unique())],
            "date_matches_name": bool(
                len(day.unique()) == 1 and str(day.iloc[0].date()).replace("-", "") == m.group(1)
            ),
        }
        for col in ("paused", "high_limit", "low_limit", "pre_close", "factor"):
            if col in df.columns:
                s = df[col]
                rec[col] = {
                    "present": True,
                    "null": int(s.isna().sum()),
                    "nonnull": int(s.notna().sum()),
                    "n_unique_nonnull": int(pd.Series(s.dropna().unique()).nunique()),
                }
            else:
                rec[col] = {"present": False}
        rows.append(rec)

    days = sorted({r["batch_date"] for r in rows})
    complete_status = [
        r["batch_date"]
        for r in rows
        if r["paused"].get("present")
        and r["high_limit"].get("present")
        and r["low_limit"].get("present")
        and r["paused"]["null"] == 0
        and r["high_limit"]["null"] == 0
        and r["low_limit"]["null"] == 0
    ]
    report = {
        "artifact": "RAW_STATUS_FIELD_INVENTORY",
        "raw_root": RAW,
        "n_gap_batches": len(rows),
        "dates": days,
        "date_min": days[0] if days else None,
        "date_max": days[-1] if days else None,
        "duplicate_batch_dates": sorted({d for d in days if [r["batch_date"] for r in rows].count(d) > 1}),
        "all_name_dates_match_content": all(r["date_matches_name"] for r in rows),
        "dates_with_complete_status_and_limits": complete_status,
        "n_dates_with_complete_status_and_limits": len(complete_status),
        "batches": rows,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps({
        "n_gap_batches": report["n_gap_batches"],
        "date_min": report["date_min"],
        "date_max": report["date_max"],
        "dates": days,
        "dup": report["duplicate_batch_dates"],
        "name_matches_content": report["all_name_dates_match_content"],
        "n_complete_status": len(complete_status),
        "complete": complete_status,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
