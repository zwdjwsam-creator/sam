# 脚本/blackbox_daily_increment_common_r1.py
sha256=348d1f7e6ea18ea8db80cfbd7ed68d5a0c6c3f913e874db65796a2428ee13ec7
size=19082

## imports
```
from __future__ import annotations
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
import pandas as pd
from _base import ROOT
from blackbox_data_absence_gate_r1 import decide as absence_decide
```

## consts
```
CACHE_PTR = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
CLEAN_PTR = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
FACTS = ROOT / "运行" / "BLACKBOX_PRODUCT_CAPABILITY_FACTS_CURRENT.json"
LEDGER = ROOT / "运行" / "BLACKBOX_CACHE_AUTHORITY_AND_PRICE_FRESHNESS_LEDGER_CURRENT.json"
SCOPE = ROOT / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json"
HAND_DECISION = ROOT / "运行" / "HAND_DECISION.json"
RAW_P3 = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P3_finance_pit"
CAL_ROOT = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P0_meta" / "calendar_cn_exchange"
OPS = ROOT / "运行" / "BLACKBOX_R20_20260817_OPERATIONAL_READINESS.json"
RAW_PIT_FIELDS = [
    "date", "code", "open", "high", "low", "close", "volume", "money",
    "signal_date", "data_date", "asset_type", "price_adj_tag", "asof_rule",
    "pit_status", "source_version", "known_at",
]
PRODUCTION_MATRIX_PRODUCTS = [
    "STOCK_DAILY_RAW_PIT_R1",
    "STOCK_DAILY_PIT_R1",
    "ETF_DAILY_PIT_R1",
    "VALUATION_PIT_R1",
]
INDEX_DAILY_NON_BLOCKING = "NON_BLOCKING_KNOWN_EXCEPTION"
```

## resolve_run_target_trade_date L110-L135 (26 lines)
```python
def resolve_run_target_trade_date(
    *,
    cli_date: str | None = None,
    cleaning: dict | None = None,
) -> dict:
    """RUN_TARGET_TRADE_DATE is the only execution authority."""
    d = (cli_date or "").strip()
    if not d and cleaning:
        d = str(cleaning.get("cleaning_as_of") or cleaning.get("daily_asof") or "").strip()
    if not d:
        raise SystemExit("HARD_BLOCK: RUN_TARGET_TRADE_DATE missing")
    ignored = []
    if HAND_DECISION.exists():
        try:
            hand = json.loads(HAND_DECISION.read_text(encoding="utf-8"))
        except Exception:
            hand = {}
        for key in ("finance_asof_target", "stock_asof_target", "daily_asof_target", "asof_target"):
            legacy = str(hand.get(key) or "").strip()
            if legacy and legacy != d:
                ignored.append({"field": key, "value": legacy})
    return {
        "RUN_TARGET_TRADE_DATE": d,
        "LEGACY_TARGET_IGNORED": bool(ignored),
        "legacy_targets": ignored,
    }
```
