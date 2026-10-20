# -*- coding: utf-8 -*-
"""Explicit reader for JQ20 cache products — no glob guessing."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

CACHE_PTR = Path(r"E:\BLACKBOX\数据\回测缓存\CURRENT_CACHE_RELEASE.json")

def _root():
    cur = json.loads(CACHE_PTR.read_text(encoding="utf-8"))
    # CURRENT may use release_root (production) or standard_root (legacy)
    key = "release_root" if cur.get("release_root") else "standard_root"
    return Path(cur[key])

def get_cache_product(product_id: str) -> pd.DataFrame:
    p = _root() / product_id / "data"
    fulls = list(p.glob("*_FULL.parquet"))
    if not fulls:
        fulls = list(p.rglob("*.parquet"))
    if not fulls:
        return pd.DataFrame()
    return pd.read_parquet(fulls[0])

def get_finance_special_statement(statement: str, scope: str = "CONSOLIDATED", asof=None) -> pd.DataFrame:
    statement = statement.upper()
    scope = scope.upper()
    m = {
        ("BALANCE", "CONSOLIDATED"): "JQ20_FINANCE_BALANCE_SHEET_PIT_R1",
        ("BALANCE", "PARENT"): "JQ20_FINANCE_BALANCE_SHEET_PARENT_PIT_R1",
        ("CASHFLOW", "CONSOLIDATED"): "JQ20_FINANCE_CASHFLOW_STATEMENT_PIT_R1",
        ("CASHFLOW", "PARENT"): "JQ20_FINANCE_CASHFLOW_STATEMENT_PARENT_PIT_R1",
        ("INCOME", "CONSOLIDATED"): "JQ20_FINANCE_INCOME_STATEMENT_PIT_R1",
        ("INCOME", "PARENT"): "JQ20_FINANCE_INCOME_STATEMENT_PARENT_PIT_R1",
    }
    pid = m[(statement, scope)]
    df = get_cache_product(pid)
    if asof is not None and not df.empty and "pit_valid_from" in df.columns:
        asof = pd.Timestamp(asof)
        df = df[pd.to_datetime(df["pit_valid_from"], errors="coerce") <= asof]
    return df
