# -*- coding: utf-8 -*-
"""BLACKBOX Data Coverage Common R1 — CANDIDATE RECONSTRUCTION (20261020_1925).

NOT a claim of byte-identical restore of the original empty production stubs.
Rebuilt from live callers:
  - blackbox_data_access_resolver_r1.py
  - blackbox_data_coverage_control_plane_build_r1.py
  - blackbox_data_coverage_diagnose_r1.py
and from sealed ledger/QA shapes under E:\\BLACKBOX\\运行.

Hard rules encoded here:
  - trade calendar from formal parquet (no Mon–Fri approximation)
  - do not treat min/max alone as middle completeness
  - date-column projection only (no unbounded full-table materialization)
  - unsupported / ambiguous → UNKNOWN_STOP / explicit refusal (never fake READY)
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

ROOT = Path(r"E:\BLACKBOX")
CACHE_CURRENT = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
CLEANING_CURRENT = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
RAW_P2 = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P2_stock_daily"
CAL_ROOT = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P0_meta"
CN_TZ = timezone(timedelta(hours=8))

# Products that must not regress from FULL_HISTORY to thin patch (from prior ledger).
HISTORICAL_REQUIRED: dict[str, str] = {
    "STOCK_DAILY_PIT_R1": "FULL_HISTORY",
    "STOCK_DAILY_RAW_PIT_R1": "FULL_HISTORY",
    "INDEX_DAILY_R1": "FULL_HISTORY",
    "STOCK_FACTOR_DAILY_R1": "FULL_HISTORY",
}
CRITICAL_BACKTEST_PRODUCTS: set[str] = {
    "STOCK_DAILY_PIT_R1",
    "INDEX_DAILY_R1",
}

DATE_COL_CANDIDATES = ("date", "trade_date", "data_date", "calendar_date", "time")


def now_cn() -> str:
    return datetime.now(CN_TZ).isoformat()


def wjson(path: Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def find_calendar_trade_days() -> Path:
    """Authority calendar parquet path (versioned asof preferred)."""
    versioned = sorted(CAL_ROOT.glob("calendar_cn_exchange*/calendar_cn_exchange_v2_asof_*/CALENDAR_TRADE_DAYS.parquet"))
    if versioned:
        return versioned[-1]
    flat = sorted(CAL_ROOT.rglob("CALENDAR_TRADE_DAYS.parquet"))
    if not flat:
        raise FileNotFoundError("CALENDAR_TRADE_DAYS.parquet missing under P0_meta")
    return flat[-1]


def load_trade_calendar(start_date: str, end_date: str) -> list[date]:
    """Return formal exchange trade days in [start_date, end_date] inclusive."""
    cal_path = find_calendar_trade_days()
    df = pd.read_parquet(cal_path)
    col = "calendar_date" if "calendar_date" in df.columns else None
    if col is None:
        for c in DATE_COL_CANDIDATES:
            if c in df.columns:
                col = c
                break
    if col is None:
        col = df.columns[0]
    days = pd.to_datetime(df[col], errors="coerce").dt.normalize().dropna().dt.date
    s = date.fromisoformat(str(start_date)[:10])
    e = date.fromisoformat(str(end_date)[:10])
    out = sorted({d for d in days if s <= d <= e})
    if not out and s <= e:
        # Calendar file present but empty window → refuse weekday faking
        raise ValueError(
            f"UNKNOWN_STOP: trade calendar yielded 0 days for {start_date}..{end_date} from {cal_path}"
        )
    return out


def cache_current() -> dict[str, Any]:
    body = json.loads(CACHE_CURRENT.read_text(encoding="utf-8"))
    root = body.get("release_root") or body.get("standard_root")
    return {
        "cache_release_id": body.get("cache_release_id"),
        "standard_root": root,
        "release_root": root,
        "asof": body.get("asof") or body.get("cache_asof"),
        "source_cleaning_release": body.get("source_cleaning_release"),
        "raw": body,
    }


def cleaning_current() -> dict[str, Any]:
    body = json.loads(CLEANING_CURRENT.read_text(encoding="utf-8"))
    return {
        "release_id": body.get("release_id") or body.get("cleaning_release_id"),
        "standard_root": body.get("standard_root"),
        "asof": body.get("daily_asof") or body.get("cleaning_as_of"),
        "raw": body,
    }


def _pick_date_col(columns: Iterable[str]) -> str | None:
    cols = list(columns)
    for c in DATE_COL_CANDIDATES:
        if c in cols:
            return c
    for c in cols:
        if "date" in str(c).lower():
            return str(c)
    return None


def _unique_dates_from_parquet(fp: Path, start: str | None = None, end: str | None = None) -> set[str]:
    """Project date column only; optional window filter after unique extract."""
    try:
        import pyarrow.parquet as pq

        schema_names = pq.ParquetFile(fp).schema_arrow.names
    except Exception:
        schema_names = list(pd.read_parquet(fp).head(0).columns)
    col = _pick_date_col(schema_names)
    if col is None:
        return set()
    s = pd.read_parquet(fp, columns=[col])[col]
    days = pd.to_datetime(s, errors="coerce").dt.strftime("%Y-%m-%d").dropna()
    uniq = set(days.unique().tolist())
    if start or end:
        lo = start or "0000-01-01"
        hi = end or "9999-12-31"
        uniq = {d for d in uniq if lo <= d <= hi}
    return uniq


def product_date_coverage(product_path: Path | str) -> dict[str, Any]:
    """Coverage facts for a cache product directory (hive year=… / parquet).

    Returns dates list when a date column is discoverable. Never invents dates.
    Does not equate directory existence with FULL coverage.
    """
    p = Path(product_path)
    out: dict[str, Any] = {
        "exists": p.exists() and p.is_dir(),
        "path": str(p),
        "min_date": None,
        "max_date": None,
        "distinct_dates": 0,
        "row_count": 0,
        "year_slices": [],
        "dates": [],
        "date_column": None,
        "coverage_extract_status": "NOT_RUN",
    }
    if not out["exists"]:
        out["coverage_extract_status"] = "MISSING_PRODUCT"
        return out

    year_dirs = sorted([x for x in p.iterdir() if x.is_dir() and x.name.startswith("year=")])
    out["year_slices"] = [x.name for x in year_dirs]

    files: list[Path] = []
    if year_dirs:
        for yd in year_dirs:
            files.extend(sorted(yd.glob("*.parquet")))
    else:
        files = sorted(p.rglob("*.parquet"))

    if not files:
        out["coverage_extract_status"] = "NO_PARQUET"
        return out

    dates: set[str] = set()
    rows = 0
    date_col = None
    errors: list[str] = []
    for fp in files:
        try:
            import pyarrow.parquet as pq

            meta = pq.ParquetFile(fp).metadata
            rows += int(meta.num_rows or 0)
            names = pq.ParquetFile(fp).schema_arrow.names
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{fp.name}:{type(exc).__name__}")
            continue
        if date_col is None:
            date_col = _pick_date_col(names)
        if date_col is None or date_col not in names:
            continue
        try:
            dates |= _unique_dates_from_parquet(fp)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{fp.name}:{type(exc).__name__}")

    out["row_count"] = rows
    out["date_column"] = date_col
    if date_col is None:
        out["coverage_extract_status"] = "DATE_COLUMN_UNKNOWN"
        out["errors"] = errors[:8]
        return out

    sorted_dates = sorted(dates)
    out["dates"] = sorted_dates
    out["distinct_dates"] = len(sorted_dates)
    if sorted_dates:
        out["min_date"] = sorted_dates[0]
        out["max_date"] = sorted_dates[-1]
        out["coverage_extract_status"] = "OK"
    else:
        out["coverage_extract_status"] = "DATE_COLUMN_EMPTY"
    if errors:
        out["errors"] = errors[:8]
    return out


def infer_mode_for_product(product_id: str, cov: dict[str, Any]) -> str:
    if not cov.get("exists"):
        return "EMPTY_OR_MISSING"
    status = cov.get("coverage_extract_status")
    if status in ("DATE_COLUMN_UNKNOWN", "DATE_COLUMN_EMPTY", "NO_PARQUET"):
        return "UNKNOWN_STOP"
    n = int(cov.get("distinct_dates") or 0)
    if n <= 0:
        return "UNKNOWN_STOP"
    required = HISTORICAL_REQUIRED.get(product_id)
    if n == 1:
        return "INCREMENTAL_PATCH" if required else "ASOF_SNAPSHOT_HISTORY"
    # multi-day
    if required == "FULL_HISTORY":
        return "FULL_HISTORY"
    if product_id.endswith("_PIT_R1") or "DAILY" in product_id:
        return "DAILY_HISTORY"
    return "ASOF_SNAPSHOT_HISTORY"


def raw_stock_daily_dates(start_date: str, end_date: str) -> dict[str, Any]:
    """RAW plane coverage vs formal trade calendar for STOCK_DAILY window."""
    expected = [str(d) for d in load_trade_calendar(start_date, end_date)]
    present: set[str] = set()
    # Prefer year files whose year overlaps the window
    years = {int(str(start_date)[:4]), int(str(end_date)[:4])}
    files: list[Path] = []
    for y in sorted(years):
        files.extend(sorted(RAW_P2.glob(f"stock_daily__*__{y}__*.parquet")))
    if not files:
        # fall back: any parquet under P2 (still date-column only)
        files = sorted(RAW_P2.glob("stock_daily__*.parquet"))
    # Deduplicate by stem year-batch keeping newest timestamp suffix
    # Overlaps allowed; we union dates (OVERLAP_ALLOWED semantics).
    overlap_dates: set[str] = set()
    seen_by_file: dict[str, set[str]] = {}
    for fp in files:
        try:
            ds = _unique_dates_from_parquet(fp, start_date, end_date)
        except Exception:
            continue
        for d in ds:
            if d in present:
                overlap_dates.add(d)
            present.add(d)
        seen_by_file[fp.name] = ds

    missing = [d for d in expected if d not in present]
    sample = {k: sorted(v)[:5] for k, v in list(seen_by_file.items())[:6]}
    return {
        "raw_root": str(RAW_P2),
        "start": start_date,
        "end": end_date,
        "expected_trade_days": expected,
        "raw_present_trade_days": sorted(present & set(expected)),
        "raw_missing_trade_days": missing,
        "raw_gap_count": len(missing),
        "raw_present_count": len(present & set(expected)),
        "expected_count": len(expected),
        "source_partitions_by_date_sample": sample,
        "overlap_dates": sorted(overlap_dates)[:50],
    }


def cleaning_stock_daily_dates(start_date: str, end_date: str) -> dict[str, Any]:
    cur = cleaning_current()
    sd = Path(cur["standard_root"]) / "price" / "stock_ohlcv_daily"
    years = {int(str(start_date)[:4]), int(str(end_date)[:4])}
    files: list[Path] = []
    for y in sorted(years):
        files.extend(sorted(sd.glob(f"*__{y}__*.parquet")))
    if not files and sd.exists():
        files = sorted(sd.glob("*.parquet"))
    present: set[str] = set()
    for fp in files:
        try:
            present |= _unique_dates_from_parquet(fp, start_date, end_date)
        except Exception:
            continue
    expected = [str(d) for d in load_trade_calendar(start_date, end_date)]
    missing = [d for d in expected if d not in present]
    return {
        "path": str(sd),
        "present_trade_days": sorted(present & set(expected)),
        "missing_trade_days": missing,
        "gap_count": len(missing),
        "present_count": len(present & set(expected)),
        "expected_count": len(expected),
        "cleaning_release_id": cur.get("release_id"),
        "standard_path": str(sd),
    }


def cache_stock_daily_dates(start_date: str, end_date: str) -> dict[str, Any]:
    cur = cache_current()
    root = Path(cur["standard_root"])
    prod = root / "STOCK_DAILY_PIT_R1"
    cov = product_date_coverage(prod)
    have = set(cov.get("dates") or [])
    expected = [str(d) for d in load_trade_calendar(start_date, end_date)]
    in_win = sorted(d for d in expected if d in have)
    missing = [d for d in expected if d not in have]
    return {
        "product_path": str(prod),
        "dates_in_window": in_win,
        "missing_trade_days": missing,
        "gap_count": len(missing),
        "min_date": cov.get("min_date"),
        "max_date": cov.get("max_date"),
        "distinct_dates": cov.get("distinct_dates"),
        "coverage_mode": infer_mode_for_product("STOCK_DAILY_PIT_R1", cov),
    }


def compare_coverage(expected: Iterable[str], available: Iterable[str]) -> dict[str, Any]:
    exp = [str(x) for x in expected]
    have = set(str(x) for x in available)
    missing = [d for d in exp if d not in have]
    return {
        "expected_count": len(exp),
        "available_count": len(exp) - len(missing),
        "missing_trade_days": missing,
        "complete": len(missing) == 0,
    }


def classify_stock_daily(start_date: str, end_date: str) -> dict[str, Any]:
    """Multi-plane STOCK_DAILY diagnosis for a request window."""
    try:
        expected = [str(d) for d in load_trade_calendar(start_date, end_date)]
    except Exception as exc:  # noqa: BLE001
        return {
            "dataset": "STOCK_DAILY",
            "requested_start": start_date,
            "requested_end": end_date,
            "root_cause": "UNKNOWN_STOP",
            "raw_status": "UNKNOWN",
            "download_required": False,
            "action": "STOP_FIX_TRADE_CALENDAR",
            "authority_ready": False,
            "error": str(exc),
        }

    raw = raw_stock_daily_dates(start_date, end_date)
    clean = cleaning_stock_daily_dates(start_date, end_date)
    cache = cache_stock_daily_dates(start_date, end_date)

    raw_complete = raw["raw_gap_count"] == 0
    clean_complete = clean["gap_count"] == 0
    cache_complete = cache["gap_count"] == 0

    if not raw_complete:
        root_cause = "TRUE_MISS_AFTER_ALL_PLANES" if (not clean_complete and not cache_complete) else "PARTIAL_WINDOW_GAP"
        raw_status = "INCOMPLETE"
    else:
        raw_status = "COMPLETE"
        if not clean_complete:
            root_cause = "PARTIAL_WINDOW_GAP"
        elif not cache_complete:
            root_cause = "PARTIAL_WINDOW_GAP"
        else:
            root_cause = "OK_MULTI_PLANE"

    # Envelope: min/max alone must not imply middle completeness — already enforced via day set.
    envelope_ok = True
    if cache.get("min_date") and cache.get("max_date"):
        if cache["min_date"] <= start_date and cache["max_date"] >= end_date and not cache_complete:
            envelope_ok = False
            if root_cause == "OK_MULTI_PLANE":
                root_cause = "ENVELOPE_REVIEW"

    return {
        "dataset": "STOCK_DAILY",
        "requested_start": start_date,
        "requested_end": end_date,
        "expected_trade_days": expected,
        "expected_count": len(expected),
        "raw_status": raw_status,
        "cleaning_status": "COMPLETE" if clean_complete else "INCOMPLETE",
        "cache_status": "COMPLETE" if cache_complete else "INCOMPLETE",
        "raw_gap_count": raw["raw_gap_count"],
        "cleaning_gap_count": clean["gap_count"],
        "cache_gap_count": cache["gap_count"],
        "raw_missing_trade_days": raw["raw_missing_trade_days"],
        "cleaning_missing_trade_days": clean["missing_trade_days"],
        "cache_missing_trade_days": cache["missing_trade_days"],
        "cache_mode": cache.get("coverage_mode"),
        "envelope_min_max_insufficient": (not envelope_ok),
        "root_cause": root_cause,
        "download_required": bool(not raw_complete),
        "action": (
            "OK_USE_CACHE"
            if root_cause == "OK_MULTI_PLANE"
            else ("STOP_RAW_GAP" if not raw_complete else "STOP_FIX_DOWNSTREAM_PLANE")
        ),
        "authority_ready": True,
    }
