# -*- coding: utf-8 -*-
"""量化缺口：12 个被丢文件的应有行数 vs 编译产物在 6 个交易日的实际行数。"""
from __future__ import annotations

import json
import os
import pathlib

import pandas as pd

E2E = pathlib.Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
R3 = E2E / "candidate" / "r15_releases" / "R15_REPLAY_20260924_R3" / "standard" / "price" / "stock_ohlcv_daily"
DAYS = ["2026-07-03", "2026-07-06", "2026-07-07", "2026-07-08", "2026-07-09", "2026-07-10"]


def lp(p):
    s = str(p)
    if s.startswith("\\\\?\\"):
        return s
    if s.startswith("\\\\"):
        return "\\\\?\\UNC\\" + s[2:]
    return "\\\\?\\" + s


def main() -> int:
    files = sorted(R3.glob("*.parquet"))
    dropped = [x for x in files if not x.is_file()]

    per_day_lost = {}
    total_lost = 0
    for f in dropped:
        df = pd.read_parquet(lp(f))
        dcol = "date" if "date" in df.columns else df.columns[0]
        codes = int(df["code"].nunique()) if "code" in df.columns else -1
        rows = int(len(df))
        total_lost += rows
        key = str(df[dcol].iloc[0])[:10] if len(df) else "?"
        per_day_lost.setdefault(key, {"files": 0, "rows": 0, "codes": 0})
        per_day_lost[key]["files"] += 1
        per_day_lost[key]["rows"] += rows
        per_day_lost[key]["codes"] += codes

    print("=== dropped files (would be lost by compiler) ===")
    for d in DAYS:
        v = per_day_lost.get(d, {"files": 0, "rows": 0, "codes": 0})
        print(f"  {d}  files={v['files']}  rows={v['rows']:>6}  codes(sum)={v['codes']}")
    print(f"  TOTAL dropped rows = {total_lost}")

    # 编译产物 6 日实际
    rels = sorted((E2E / "candidate" / "cc_out" / "releases").glob("*"))
    latest = rels[-1] if rels else None
    print(f"\n=== compiled release = {latest.name if latest else 'NONE'} ===")
    qa = latest / "_qa" / "TIP_REBASE_QA.json" if latest else None
    if qa and qa.exists():
        d = json.loads(qa.read_text(encoding="utf-8"))
        for k in ("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "STOCK_FACTOR_DAILY_R1"):
            print(f"  {k:<24} rows_2026 = {d.get('price',{}).get('products',{}).get(k,{}).get('rows_2026')}")

    # 找编译产物里 2026 分区，按日数行
    for cand in sorted((latest / "price" / "STOCK_DAILY_PIT_R1").glob("**/*.parquet")) if latest else []:
        if "2026" in str(cand):
            df = pd.read_parquet(cand, columns=None)
            dcol = "date" if "date" in df.columns else None
            if dcol is None:
                continue
            dd = pd.to_datetime(df[dcol], errors="coerce").dt.strftime("%Y-%m-%d")
            print(f"\n  partition {cand.name}: total rows={len(df)}")
            for day in DAYS:
                sub = df[dd == day]
                print(f"    {day}  rows={len(sub):>6}  codes={sub['code'].nunique() if 'code' in sub.columns else 'n/a'}")
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
