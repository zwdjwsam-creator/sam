# -*- coding: utf-8 -*-
"""证明：长路径下 is_file() 静默丢文件；\\?\ 前缀可读。并给出编译器可见数对比。"""
from __future__ import annotations

import os
import pathlib
import sys

P = pathlib.Path(
    r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
    r"\candidate\r15_releases\R15_REPLAY_20260924_R3\standard\price\stock_ohlcv_daily"
)


def lp(p):
    s = str(p)
    if s.startswith("\\\\?\\"):
        return s
    if s.startswith("\\\\"):
        return "\\\\?\\UNC\\" + s[2:]
    return "\\\\?\\" + s


def main() -> int:
    files = sorted(P.glob("*.parquet"))
    print(f"tree_report schema=BLACKBOX_LONGPATH_PROBE_R1")
    print(f"LongPathsEnabled(read via registry not here) ; os.name={os.name}")
    print(f"files_on_disk            = {len(files)}")
    print(f"max_path_len             = {max(len(str(x)) for x in files)}")

    vis = [x for x in files if x.is_file()]
    print(f"is_file() visible        = {len(vis)}")
    print(f"is_file() dropped        = {len(files) - len(vis)}")

    ok_pref = 0
    bad = []
    for x in files:
        try:
            os.stat(lp(x))
            ok_pref += 1
        except OSError as e:
            bad.append((len(str(x)), x.name, type(e).__name__))
    print(f"stat(\\?\ prefixed) OK    = {ok_pref}")
    print(f"stat(\\?\ prefixed) FAIL  = {len(bad)}")
    for b in bad[:5]:
        print(f"   FAIL len={b[0]} {b[2]} {b[1][:60]}")

    # 编译器实际可见（模拟 find_parquets）
    rglob_vis = sorted([p for p in P.rglob("*.parquet") if p.is_file()])
    print(f"find_parquets() returns  = {len(rglob_vis)}   <-- compiler sees this")

    # 直接 pandas 读长路径 via prefix
    import pandas as pd
    dropped = [x for x in files if not x.is_file()]
    if dropped:
        d0 = dropped[0]
        try:
            df = pd.read_parquet(lp(d0))
            print(f"read_parquet(\\?\ on dropped[0]) rows={len(df)} codes={df['code'].nunique() if 'code' in df.columns else 'n/a'} file={d0.name[:50]}")
        except Exception as e:
            print(f"read_parquet(\\?\ ) FAIL {type(e).__name__}: {str(e)[:100]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
