"""Is P1 a real adjustment series? Batch vs incremental, and the CACHE's own shape.

The incremental files are all-1.0. Before calling that a defect, the batch files (the
historical corpus) and the CACHE product itself must be measured on the same axis:
distinct factor values per session.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
P1 = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P1_adjust_factor")
CACHE = Path(r"E:\BLACKBOX\数据\回测缓存\releases"
             r"\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439"
             r"\ADJUST_FACTOR_PIT_R1\data\year=2026")
OUT = TASK / "evidence" / "FACTOR_SERIES_NATURE.json"


def batch_profile() -> list[dict]:
    rows = []
    for f in sorted(P1.glob("adjust_factor_stock__batch_*.parquet")):
        try:
            d = pd.read_parquet(f)
        except Exception:  # noqa: BLE001
            continue
        if "factor" not in d.columns:
            continue
        fv = pd.to_numeric(d["factor"], errors="coerce")
        rows.append({"file": f.name, "rows": int(len(d)),
                     "factor_distinct": int(fv.nunique()),
                     "factor_min": float(fv.min()), "factor_max": float(fv.max()),
                     "all_ones": bool(fv.nunique() == 1 and float(fv.iloc[0]) == 1.0)})
    return rows


def main() -> int:
    batches = batch_profile()
    cache = pd.concat([pd.read_parquet(f) for f in sorted(CACHE.glob("*.parquet"))],
                      ignore_index=True)
    cache["date"] = pd.to_datetime(cache["date"], errors="coerce").dt.normalize()
    cache["factor"] = pd.to_numeric(cache["factor"], errors="coerce")
    per_day = (cache.groupby(cache["date"].dt.strftime("%Y-%m-%d"))
               .agg(rows=("factor", "size"), distinct=("factor", "nunique"),
                    ones=("factor", lambda s: int((s.round(6) == 1.0).sum())))
               .reset_index().rename(columns={"date": "session"}))
    per_day["ones_share"] = (per_day["ones"] / per_day["rows"]).round(4)
    varied = per_day[per_day["distinct"] > 1]
    all_ones = per_day[per_day["distinct"] == 1]
    out = {
        "artifact": "FACTOR_SERIES_NATURE",
        "batch_files": len(batches),
        "batch_all_ones": int(sum(1 for b in batches if b["all_ones"])),
        "batch_varied": int(sum(1 for b in batches if not b["all_ones"])),
        "batch_sample": batches[:3] + batches[-3:],
        "cache_sessions": int(len(per_day)),
        "cache_sessions_single_value": int(len(all_ones)),
        "cache_sessions_varied": int(len(varied)),
        "cache_varied_sessions": varied.tail(12).to_dict("records"),
        "cache_all_ones_sessions": [str(x) for x in all_ones["session"].tail(12)],
        "cache_per_day": per_day.to_dict("records"),
        "reading": {
            "p1_batch_carries_real_factors": any(not b["all_ones"] for b in batches),
            "p1_incremental_carries_real_factors": False,
            "consequence": "the incremental plane cannot be the adjustment authority: it is "
                           "a constant 1.0 for every code, which is exactly the forbidden "
                           "constant fallback if consumed as a factor",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "cache_per_day"},
                     ensure_ascii=False, indent=1, default=str)[:2600])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
