"""Bridge to the ORIGINAL stock minute reader (`STOCK_MINUTE_1M_R1`).

The local plane does carry a minute product; R13's claim that it did not was wrong.
This module does not re-implement anything: it loads
`脚本/blackbox_stock_minute_1m_reader_r1.py` from its real location and calls its real
`fetch_stock_minute_1m(request)` entry point, whose own contract resolves
`数据/清洗成品/CURRENT_CLEANING_RELEASE.json` -> `standard/price/A股_stock_1m`.

Nothing is synthesised here:
  * `PASS` rows are the reader's rows, with its columns and its provenance;
  * `NO_DATA` / `MISSING` / `FAIL` are returned as-is so the caller can BLOCK with the
    reader's reason instead of substituting a daily open;
  * `RAW_NONE` availability is never presented as adjustment.

`duckdb` is the reader's own dependency (it queries the parquet shards with SQL); the task
ships it in `vendor/` so the shared venv is untouched.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import datetime as dt

import pandas as pd

TASK = Path(__file__).resolve().parents[2]
READER = Path(r"E:\BLACKBOX\脚本\blackbox_stock_minute_1m_reader_r1.py")
VENDOR = TASK / "vendor"

_MOD = None
_LOAD_ERROR: Optional[str] = None


def _load():
    global _MOD, _LOAD_ERROR
    if _MOD is not None or _LOAD_ERROR is not None:
        return _MOD
    if str(VENDOR) not in sys.path:
        sys.path.insert(0, str(VENDOR))
    try:
        spec = importlib.util.spec_from_file_location("_bb_stock_minute_reader", READER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        _MOD = mod
    except Exception as exc:  # noqa: BLE001
        _LOAD_ERROR = f"{type(exc).__name__}: {exc}"
    return _MOD


def available() -> Dict[str, Any]:
    mod = _load()
    if mod is None:
        return {"available": False, "error": _LOAD_ERROR, "reader": str(READER)}
    try:
        src = mod.resolve_cleaning_stock_1m_source()
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": f"resolve: {type(exc).__name__}: {exc}"}
    return {
        "available": src.get("status") == "READY",
        "reader": str(READER),
        "product_id": getattr(mod, "PRODUCT_ID", None),
        "source_id": getattr(mod, "SOURCE_ID", None),
        "source_status": src.get("status"),
        "source_dir": src.get("source_dir"),
        "source_pointer": src.get("ptr"),
        "evidence_gaps": src.get("evidence_gaps"),
    }


def _norm_bound(value: Any, *, is_end: bool) -> str:
    """Normalise a JQ-style bound into an explicit timestamp.

    Measured defect in the original reader: `parse_ts('2026-09-15')` resolves a
    date-only string to **15:00:00** (market close), so passing a date-only START
    bound produces an inverted window and the query returns nothing
    (`NO_DATA/EMPTY_AFTER_FILTER`). The reader is left untouched; the caller supplies
    the clock it actually means, which is the adaptation this integration needs.
    """
    if isinstance(value, (dt.datetime, pd.Timestamp)):
        return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M:%S")
    text = str(value).strip()
    if len(text) <= 10:
        return f"{text} {'23:59:59' if is_end else '00:00:00'}"
    return text


def fetch(
    symbols: List[str],
    start: Any,
    end: Any,
    asof: str = "20260924",
    cutoff: Any = None,
    fields: Optional[List[str]] = None,
    request_id: str = "LOCAL_PLANE",
) -> Dict[str, Any]:
    """Call the original reader. Returns its own response dict, unmodified."""
    mod = _load()
    if mod is None:
        return {"status": "FAIL", "reason_code": "READER_IMPORT_FAILED",
                "evidence_gaps": [{"gap": _LOAD_ERROR}], "data": [], "rows": 0,
                "source_paths": [], "source_sha256": {}}
    start_ts = _norm_bound(start, is_end=False)
    end_ts = _norm_bound(end, is_end=True)
    cut_ts = _norm_bound(cutoff if cutoff is not None else end, is_end=True)
    req = {
        "symbols": list(symbols),
        "start_time": start_ts,
        "end_time": end_ts,
        "asof": str(asof),
        "cutoff_time": cut_ts,
        "request_id": str(request_id),
    }
    if fields:
        req["required_columns"] = [c for c in fields if c in
                                   ("timestamp", "open", "high", "low", "close",
                                    "volume", "amount")]
    return mod.fetch_stock_minute_1m(req)
