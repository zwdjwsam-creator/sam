"""Trace the 12 sparse factor sessions from the CACHE back to the SOURCE layer.

Question: is `ADJUST_FACTOR_PIT_R1` sparse because the authoritative input is sparse, or
because the builder dropped a forward-carry it was supposed to perform?

Layers read (read-only, necessary columns only):
  L0 CACHE  releases/.../ADJUST_FACTOR_PIT_R1   (date, code, factor)
  L1 P1     RAW P1_adjust_factor/*.parquet      (date, code, factor)  <- declared source
  L2 P6     RAW P6_factor_reference/adjust_factor/*.parquet         <- reference layer
  L3 staged R15 copies, when present

Nothing is derived, filled or repaired here: the output is row counts per session per
layer plus the exact (date, code) keys missing in the CACHE but present upstream.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
OUT = TASK / "evidence" / "FACTOR_SOURCE_TRACE.json"

CACHE = Path(r"E:\BLACKBOX\数据\回测缓存\releases"
             r"\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439"
             r"\ADJUST_FACTOR_PIT_R1\data\year=2026")
P1 = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P1_adjust_factor")
P6 = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P6_factor_reference\adjust_factor")
SPARSE = ["2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21",
          "2026-08-24", "2026-08-25", "2026-08-26", "2026-08-27", "2026-08-28",
          "2026-09-01", "2026-09-02"]
DENSE_REF = ["2026-08-31", "2026-09-03", "2026-09-04"]


def read_any(root: Path, cols=("date", "code", "factor")) -> pd.DataFrame:
    files = sorted(root.glob("*.parquet"))
    if not files:
        return pd.DataFrame(columns=list(cols))
    frames = []
    for f in files:
        try:
            d = pd.read_parquet(f)
        except Exception:  # noqa: BLE001
            continue
        keep = [c for c in cols if c in d.columns]
        if "date" not in keep:
            continue
        frames.append(d[keep])
    if not frames:
        return pd.DataFrame(columns=list(cols))
    out = pd.concat(frames, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
    out = out.dropna(subset=["date"])
    if "code" in out.columns:
        out["code"] = out["code"].astype(str)
    if "factor" in out.columns:
        out["factor"] = pd.to_numeric(out["factor"], errors="coerce")
    return out


def per_day(df: pd.DataFrame) -> dict:
    if not len(df):
        return {}
    return {str(k): int(v) for k, v in
            df.groupby(df["date"].dt.strftime("%Y-%m-%d")).size().items()}


def file_kinds(root: Path) -> dict:
    kinds = {}
    for f in sorted(root.glob("*.parquet")):
        name = f.name
        if "incremental" in name:
            kind = "incremental"
        elif "batch" in name:
            kind = "batch"
        elif "history" in name or "full" in name:
            kind = "history"
        else:
            kind = "other"
        kinds[kind] = kinds.get(kind, 0) + 1
    return kinds


def main() -> int:
    cache = read_any(CACHE)
    p1 = read_any(P1)
    p6 = read_any(P6)

    cache_days = per_day(cache)
    p1_days = per_day(p1)
    p6_days = per_day(p6)

    rows = []
    for day in SPARSE + DENSE_REF:
        c_n = cache_days.get(day, 0)
        p1_n = p1_days.get(day, 0)
        p6_n = p6_days.get(day, 0)
        c_codes = set(cache.loc[cache["date"] == day, "code"]) if c_n else set()
        p1_codes = set(p1.loc[p1["date"] == day, "code"]) if p1_n else set()
        rows.append({
            "date": day,
            "cache_rows": c_n,
            "p1_rows": p1_n,
            "p6_rows": p6_n,
            "p1_minus_cache_codes": len(p1_codes - c_codes),
            "cache_minus_p1_codes": len(c_codes - p1_codes),
            "verdict": ("INPUT_PRESENT_UPSTREAM" if p1_n > c_n else
                        "INPUT_ABSENT_UPSTREAM" if p1_n == 0 and c_n == 0 else
                        "CACHE_MATCHES_SOURCE" if p1_n == c_n else "CACHE_EXCEEDS_SOURCE"),
        })

    # the key question: is P1 an incremental (changed-only) product?
    sample = p1[(p1["date"].dt.strftime("%Y-%m-%d") == SPARSE[0])]
    factor_values = (sample["factor"].value_counts().head(5).to_dict()
                     if "factor" in sample.columns and len(sample) else {})

    out = {
        "artifact": "FACTOR_SOURCE_TRACE",
        "question": "is the sparse CACHE caused by a sparse authoritative source, or by a "
                    "missing carry in the builder?",
        "layers": {
            "cache": {"root": str(CACHE), "sessions": len(cache_days),
                      "rows": int(len(cache))},
            "p1": {"root": str(P1), "file_kinds": file_kinds(P1),
                   "sessions": len(p1_days), "rows": int(len(p1)),
                   "first_day": min(p1_days) if p1_days else None,
                   "last_day": max(p1_days) if p1_days else None},
            "p6": {"root": str(P6), "file_kinds": file_kinds(P6),
                   "sessions": len(p6_days), "rows": int(len(p6)),
                   "first_day": min(p6_days) if p6_days else None,
                   "last_day": max(p6_days) if p6_days else None},
        },
        "per_session": rows,
        "p1_sample_day": {"date": SPARSE[0], "rows": int(len(sample)),
                          "distinct_factor_values": {str(k): int(v) for k, v in
                                                     factor_values.items()}},
        "p1_is_incremental_only": file_kinds(P1).get("incremental", 0) > 0 and \
        file_kinds(P1).get("history", 0) == 0,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"layers": {k: {kk: vv for kk, vv in v.items() if kk != "root"}
                                 for k, v in out["layers"].items()},
                      "p1_is_incremental_only": out["p1_is_incremental_only"],
                      "per_session": rows}, ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
