# 脚本/blackbox_index_weight_governance_r1.py
sha256=3c49a663b69582277ed68cde470131b93a174f692db3332b2279ee2d1861ee8a
size=67528

## imports
```
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import pandas as pd
```

## consts
```
ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "Scripts" / "python.exe"
TASK_ID = "BLACKBOX_ETF_INDEX_WEIGHT_DATA_LAYER_AND_INCREMENT_GOVERNANCE_R1"
TASK = ROOT / "任务" / TASK_ID
RAW_DIR = (
    ROOT
    / "数据"
    / "原始只读"
    / "JQData_9999_official_raw"
    / "P3_index"
    / "index_weights_code_preserved__asof_20260702__repair_v1"
)
P3_INDEX = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P3_index"
TRACK_DIR = (
    ROOT
    / "数据"
    / "原始只读"
    / "JQData_9999_official_raw"
    / "P4_fund_etf"
    / "fund_tracking_index_mapping"
)
LEDGER = ROOT / "运行" / "BLACKBOX_JQ_ACCESSIBLE_DATASET_LEDGER_CURRENT.json"
INDEX_PATH = ROOT / "运行" / "BLACKBOX_DATA_ACCESS_INDEX_CURRENT.json"
FACTS = ROOT / "运行" / "BLACKBOX_PRODUCT_CAPABILITY_FACTS_CURRENT.json"
SIDECAR = ROOT / "运行" / "BLACKBOX_SIDECAR_CACHE_PRODUCTS_CURRENT.json"
DAILY_RULE = ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_R1.json"
DAILY_CUR = ROOT / "运行" / "BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json"
CATALOG = ROOT / "数据" / "回测缓存" / "registry" / "CACHE_PRODUCT_CATALOG.csv"
CACHE_CURRENT = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
ORCH = ROOT / "脚本" / "blackbox_daily_increment_orchestrator_r1.py"
CODE_RE = re.compile(r"^\d{6}\.(XSHG|XSHE)$")
OVERSEAS_KW = ("德国", "纳斯达克", "纳指", "日经", "恒生", "标普", "道琼斯", "欧洲", "美国", "香港", "H股")
COMMODITY_KW = ("黄金", "白银", "原油", "豆粕", "有色", "商品", "能源", "黄金ETF")
```

## daily_check L1096-L1165 (70 lines)
```python
def daily_check(target: str, probe: dict | None = None, qa: dict | None = None, live: bool = False) -> dict:
    qa = qa or {}
    probe = probe or {}
    local_max = qa.get("latest_2026_snapshot")
    if not local_max and SIDECAR.is_file():
        path = Path((load_json(SIDECAR).get("products") or {}).get("INDEX_WEIGHT_PIT_R1", {}).get("cache_product_path") or "")
        covp = path / "COVERAGE.json"
        if covp.is_file():
            local_max = load_json(covp).get("LOCAL_MAX_SNAPSHOT")
    source_latest = None
    semantics = probe.get("SOURCE_UPDATE_SEMANTICS") or "UNKNOWN"
    if live:
        try:
            sys.path.insert(0, str(ROOT / "脚本"))
            import jq_download_base as jdb  # noqa: WPS433
            import jqdatasdk as jq  # noqa: WPS433
            jdb.auth()
            w = jq.get_index_weights("000300.XSHG", date=target)
            df = w.reset_index() if hasattr(w, "reset_index") else w
            if "date" in getattr(df, "columns", []):
                source_latest = str(pd.to_datetime(df["date"], errors="coerce").max().date())
        except Exception as e:  # noqa: BLE001
            source_latest = None
            semantics = semantics or "UNKNOWN"
            live_err = type(e).__name__
        else:
            live_err = None
    else:
        live_err = None
        if probe.get("probe_rows"):
            ok = [r for r in probe["probe_rows"] if r.get("ok") and r.get("index_code") == "000300.XSHG"]
            if ok:
                source_latest = max(r.get("source_snapshot_date") or "" for r in ok) or None
    update_token = "NO"
    source_refresh_status = "OK"
    if source_latest and local_max and source_latest > local_max:
        update_required = True
        update_token = "YES"
        reason = "NEW_SOURCE_SNAPSHOT"
    elif source_latest and local_max and source_latest <= local_max:
        update_required = False
        update_token = "NO"
        reason = "NO_NEW_SOURCE_SNAPSHOT"
    elif not source_latest:
        update_required = False
        probe_failed = bool(probe.get("failed")) or (live and live_err)
        if probe_failed or (semantics == "UNKNOWN" and not source_latest):
            update_token = "UNKNOWN"
            source_refresh_status = "UNKNOWN_SOURCE_UNREACHABLE"
            reason = "SOURCE_UNREACHABLE_UPDATE_NOT_PROVEN"
        else:
            update_token = "NO"
            reason = "NO_NEW_SOURCE_SNAPSHOT"
    return {
        "INDEX_WEIGHT_MANAGED_BY_DAILY_INCREMENT": "YES",
        "SOURCE_UPDATE_SEMANTICS": semantics,
        "SOURCE_REFRESH_STATUS": source_refresh_status,
        "LOCAL_LATEST_SNAPSHOT": local_max,
        "SOURCE_LATEST_SNAPSHOT": source_latest,
        "INDEX_WEIGHT_LOCAL_MAX_SNAPSHOT": local_max,
        "INDEX_WEIGHT_SOURCE_LATEST_SNAPSHOT": source_latest,
        "LOCAL_SNAPSHOT_AVAILABLE": bool(local_max),
        "SOURCE_REFRESH_FAILED": source_refresh_status == "UNKNOWN_SOURCE_UNREACHABLE",
        "UPDATE_REQUIRED": update_token,
        "INDEX_WEIGHT_UPDATE_REQUIRED": update_token,
        "reason": reason,
        "run_target_date": target,
        "live_error": live_err,
        "CACHE_CURRENT_SWITCHED": False,
    }
```
