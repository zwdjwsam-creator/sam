"""Inspect the P1 factor files around the hole: real schema, real date coverage.

The review warns that an integer sequence number must never be read as a date. The first
trace already showed `first_day = 1970-01-01`, which is exactly that symptom. This script
reads the true schema and per-file spans, and separates rows whose `date` is a real
timestamp from rows where it is not, before drawing any conclusion about absence.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
P1 = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P1_adjust_factor")
P6 = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P6_factor_reference\adjust_factor")
OUT = TASK / "evidence" / "FACTOR_SOURCE_SCHEMA.json"
AUG = ("2026-08-10", "2026-09-05")


def describe(root: Path, tag: str) -> dict:
    files = sorted(root.glob("*.parquet"))
    aug_files = [f for f in files if "202608" in f.name or "202609" in f.name]
    picked = aug_files[:3] + aug_files[-3:] if aug_files else files[:2]
    samples = []
    for f in picked:
        d = pd.read_parquet(f)
        samples.append({
            "file": f.name,
            "rows": int(len(d)),
            "columns": list(d.columns),
            "dtypes": {c: str(t) for c, t in d.dtypes.items()},
            "date_head": [str(x) for x in d["date"].head(5)] if "date" in d.columns else None,
            "date_kind": ("INTEGER_SEQUENCE" if "date" in d.columns and
                          pd.api.types.is_integer_dtype(d["date"]) else
                          type(d["date"].iloc[0]).__name__ if "date" in d.columns else None),
        })
    # true event dates across every file, counted via a strict parser
    day_counts: dict[str, int] = {}
    unparsed = 0
    total = 0
    for f in files:
        try:
            d = pd.read_parquet(f, columns=["date"])
        except Exception:  # noqa: BLE001
            continue
        total += len(d)
        if not pd.api.types.is_integer_dtype(d["date"]):
            ts = pd.to_datetime(d["date"], errors="coerce")
            ok = ts.notna()
            unparsed += int((~ok).sum())
            for k, v in ts[ok].dt.strftime("%Y-%m-%d").value_counts().items():
                day_counts[k] = day_counts.get(k, 0) + int(v)
        else:
            unparsed += len(d)
    window = {k: v for k, v in sorted(day_counts.items()) if AUG[0] <= k <= AUG[1]}
    return {
        "tag": tag,
        "root": str(root),
        "n_files": len(files),
        "total_rows": total,
        "rows_with_non_date_encoding": unparsed,
        "n_sessions": len(day_counts),
        "first_day": min(day_counts) if day_counts else None,
        "last_day": max(day_counts) if day_counts else None,
        "window_2026_08_10_to_09_05": window,
        "samples": samples,
    }


def main() -> int:
    out = {"artifact": "FACTOR_SOURCE_SCHEMA",
           "warning": "date columns are parsed strictly; integer values are reported as "
                      "non-date encodings and never converted into calendar days",
           "p1": describe(P1, "P1_adjust_factor"),
           "p6": describe(P6, "P6_factor_reference_adjust_factor")}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    for tag in ("p1", "p6"):
        s = out[tag]
        print(tag, "files", s["n_files"], "rows", s["total_rows"],
              "non_date", s["rows_with_non_date_encoding"],
              "sessions", s["n_sessions"], s["first_day"], "..", s["last_day"])
        print("  window", s["window_2026_08_10_to_09_05"])
    print(json.dumps({k: v["samples"] for k, v in (("p1", out["p1"]), ("p6", out["p6"]))},
                     ensure_ascii=False, indent=1, default=str)[:2200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
