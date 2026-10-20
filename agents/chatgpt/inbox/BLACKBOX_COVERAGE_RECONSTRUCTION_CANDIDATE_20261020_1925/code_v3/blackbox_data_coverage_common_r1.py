# -*- coding: utf-8 -*-
"""BLACKBOX Data Coverage Common R1 — CANDIDATE V2 (1940 review fixes).

Not an original-byte restore. Fixes vs V1 (SHA194f012f…):
  - extract errors → UNVERIFIABLE (never OK with errors)
  - no unbounded pandas schema fallback
  - mode only for allowlisted products + FULL_HISTORY contract
  - classify nested cache.coverage for control_plane write_reports
  - RAW/cleaning: year-span inclusive; read errors ≠ confirmed miss
  - calendar: require calendar_date; distinguish empty-window vs uncovered
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

ROOT = Path(r"E:\BLACKBOX")
CACHE_CURRENT = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
CLEANING_CURRENT = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
RAW_P2 = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P2_stock_daily"
CAL_ROOT = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P0_meta" / "calendar_cn_exchange"
CN_TZ = timezone(timedelta(hours=8))

# Products with known date-column contract (do not guess for arbitrary *_PIT_R1).
SUPPORTED_DATE_PRODUCTS: dict[str, dict[str, Any]] = {
    "STOCK_DAILY_PIT_R1": {"date_columns": ("date",), "historical": "FULL_HISTORY", "critical": True},
    "STOCK_DAILY_RAW_PIT_R1": {"date_columns": ("date",), "historical": "FULL_HISTORY", "critical": False},
    "INDEX_DAILY_R1": {"date_columns": ("date",), "historical": "FULL_HISTORY", "critical": True},
    "STOCK_FACTOR_DAILY_R1": {"date_columns": ("date",), "historical": "FULL_HISTORY", "critical": False},
}
RAW_COVERAGE_LEDGER = ROOT / "运行" / "BLACKBOX_RAW_COVERAGE_LEDGER_CURRENT.json"

HISTORICAL_REQUIRED: dict[str, str] = {
    k: v["historical"] for k, v in SUPPORTED_DATE_PRODUCTS.items() if v.get("historical")
}
CRITICAL_BACKTEST_PRODUCTS: set[str] = {
    k for k, v in SUPPORTED_DATE_PRODUCTS.items() if v.get("critical")
}


class CoverageUnverifiable(Exception):
    """Raised when coverage cannot be verified (caller/gate must refuse READY)."""


def now_cn() -> str:
    return datetime.now(CN_TZ).isoformat()


def wjson(path: Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def find_calendar_trade_days() -> Path:
    """Formal calendar authority with explicit fallback contract (no silent latest).

    Order:
      1) versioned asof matching CACHE CURRENT asof
      2) trade_calendar_authority path from BLACKBOX_RAW_COVERAGE_LEDGER_CURRENT.json (if exists)
      3) refuse — do not pick lexicographic latest without authority
    """
    versioned = sorted(CAL_ROOT.glob("calendar_cn_exchange_v2_asof_*/CALENDAR_TRADE_DAYS.parquet"))
    if not versioned:
        raise FileNotFoundError(
            "UNKNOWN_STOP: no calendar_cn_exchange_v2_asof_*/CALENDAR_TRADE_DAYS.parquet under P0_meta"
        )
    asof = None
    try:
        asof = str(cache_current().get("asof") or "").replace("-", "")[:8]
    except Exception:
        asof = None
    if asof:
        matched = [p for p in versioned if asof in p.parts[-2]]
        if matched:
            return matched[-1]
    if RAW_COVERAGE_LEDGER.is_file():
        try:
            body = json.loads(RAW_COVERAGE_LEDGER.read_text(encoding="utf-8"))
            auth = body.get("trade_calendar_authority")
            if auth and Path(auth).is_file():
                return Path(auth)
        except Exception as exc:  # noqa: BLE001
            raise FileNotFoundError(
                f"UNKNOWN_STOP: calendar CURRENT asof unmatched and ledger authority unreadable: {exc}"
            ) from exc
    raise FileNotFoundError(
        "UNKNOWN_STOP: calendar asof unmatched to CACHE CURRENT and no readable "
        "trade_calendar_authority in BLACKBOX_RAW_COVERAGE_LEDGER_CURRENT.json "
        "(refusing lexicographic latest fallback)"
    )


_CALENDAR_DATE_COLS = ("trade_date", "calendar_date")  # formal allowlist only; no first-column fallback


def _calendar_frame(cal_path: Path) -> tuple[pd.DataFrame, str]:
    df = pd.read_parquet(cal_path)
    col = next((c for c in _CALENDAR_DATE_COLS if c in df.columns), None)
    if col is None:
        raise ValueError(
            f"UNKNOWN_STOP: calendar missing formal date column {_CALENDAR_DATE_COLS} in {cal_path}; "
            f"have={list(df.columns)[:12]}"
        )
    return df, col


def load_trade_calendar(start_date: str, end_date: str) -> list[date]:
    """Trade days in [start,end]. Empty list is valid when calendar covers range but all days are non-trade.

    Raises if calendar cannot be read or request falls outside calendar coverage.
    """
    cal_path = find_calendar_trade_days()
    df, col = _calendar_frame(cal_path)
    days = pd.to_datetime(df[col], errors="coerce").dt.normalize().dropna()
    if days.empty:
        raise ValueError(f"UNKNOWN_STOP: calendar empty: {cal_path}")
    cal_min = days.min().date()
    cal_max = days.max().date()
    s = date.fromisoformat(str(start_date)[:10])
    e = date.fromisoformat(str(end_date)[:10])
    if e < s:
        raise ValueError(f"UNKNOWN_STOP: end_date < start_date ({start_date}..{end_date})")
    if s < cal_min or e > cal_max:
        raise ValueError(
            f"UNKNOWN_STOP: request {start_date}..{end_date} outside calendar coverage "
            f"{cal_min}..{cal_max} ({cal_path})"
        )
    out = sorted({d.date() for d in days if s <= d.date() <= e})
    # Legitimate zero trade days (pure weekend/holiday window) → empty list, not error.
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


def _years_inclusive(start_date: str, end_date: str) -> list[int]:
    y0, y1 = int(str(start_date)[:4]), int(str(end_date)[:4])
    if y1 < y0:
        y0, y1 = y1, y0
    return list(range(y0, y1 + 1))


def _to_date_str(v: Any) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v.isoformat()
    ts = pd.to_datetime(v, errors="coerce")
    if pd.isna(ts):
        return None
    return pd.Timestamp(ts).strftime("%Y-%m-%d")


def _unique_dates_from_parquet(fp: Path, date_col: str, start: str | None = None, end: str | None = None) -> set[str]:
    """Date-column projection only. Raises on read failure (no silent skip)."""
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(fp)
    names = pf.schema_arrow.names
    if date_col not in names:
        raise ValueError(f"date column {date_col!r} missing in {fp.name}; have={names[:12]}")
    # column projection via pandas/pyarrow
    table = pf.read(columns=[date_col])
    s = table.column(date_col).to_pandas()
    uniq: set[str] = set()
    for v in s.unique().tolist():
        ds = _to_date_str(v)
        if ds:
            uniq.add(ds)
    if start or end:
        lo = start or "0000-01-01"
        hi = end or "9999-12-31"
        uniq = {d for d in uniq if lo <= d <= hi}
    return uniq


def product_date_coverage(product_path: Path | str, product_id: str | None = None) -> dict[str, Any]:
    """Coverage facts. Any partition read/schema failure → UNVERIFIABLE (not OK)."""
    p = Path(product_path)
    pid = product_id or p.name
    contract = SUPPORTED_DATE_PRODUCTS.get(pid)
    out: dict[str, Any] = {
        "exists": p.exists() and p.is_dir(),
        "path": str(p),
        "product_id": pid,
        "min_date": None,
        "max_date": None,
        "distinct_dates": 0,
        "row_count": 0,
        "year_slices": [],
        "dates": [],
        "date_column": None,
        "coverage_extract_status": "NOT_RUN",
        "errors": [],
        "supported_product": contract is not None,
    }
    if not out["exists"]:
        out["coverage_extract_status"] = "MISSING_PRODUCT"
        return out
    if contract is None:
        out["coverage_extract_status"] = "UNSUPPORTED_PRODUCT"
        out["errors"] = [f"product {pid} not in SUPPORTED_DATE_PRODUCTS contract"]
        return out

    allowed_cols = tuple(contract["date_columns"])
    year_dirs = sorted([x for x in p.iterdir() if x.is_dir() and x.name.startswith("year=")])
    out["year_slices"] = [x.name for x in year_dirs]
    files: list[Path] = []
    if year_dirs:
        for yd in year_dirs:
            files.extend(sorted(yd.glob("*.parquet")))
    else:
        files = sorted(p.glob("*.parquet"))

    if not files:
        out["coverage_extract_status"] = "NO_PARQUET"
        return out

    try:
        import pyarrow.parquet as pq  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        out["coverage_extract_status"] = "UNVERIFIABLE"
        out["errors"] = [f"pyarrow_unavailable:{type(exc).__name__}:{exc}"]
        return out

    dates: set[str] = set()
    rows = 0
    date_col_used: str | None = None
    errors: list[str] = []

    for fp in files:
        try:
            import pyarrow.parquet as pq

            pf = pq.ParquetFile(fp)
            rows += int(pf.metadata.num_rows or 0)
            names = list(pf.schema_arrow.names)
            col = next((c for c in allowed_cols if c in names), None)
            if col is None:
                errors.append(
                    f"{fp.name}:DATE_COLUMN_CONTRACT_MISS allowed={allowed_cols} have={names[:12]}"
                )
                continue
            if date_col_used is None:
                date_col_used = col
            elif date_col_used != col:
                errors.append(f"{fp.name}:DATE_COLUMN_INCONSISTENT {col} vs {date_col_used}")
                continue
            dates |= _unique_dates_from_parquet(fp, col)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{fp.name}:{type(exc).__name__}:{exc}")

    out["row_count"] = rows
    out["date_column"] = date_col_used
    out["errors"] = errors[:20]
    if errors:
        # Partial success must NOT be reported as OK.
        out["coverage_extract_status"] = "UNVERIFIABLE"
        sorted_dates = sorted(dates)
        out["dates"] = sorted_dates
        out["distinct_dates"] = len(sorted_dates)
        if sorted_dates:
            out["min_date"] = sorted_dates[0]
            out["max_date"] = sorted_dates[-1]
        return out

    if date_col_used is None:
        out["coverage_extract_status"] = "DATE_COLUMN_UNKNOWN"
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
    return out


def _year_slices_contiguous(year_slices: list[str], min_date: str, max_date: str) -> bool:
    """Require every calendar year from min..max to appear as year=YYYY (no sparse endpoints)."""
    if not year_slices or not min_date or not max_date:
        return False
    have = set()
    for s in year_slices:
        m = re.match(r"year=(\d{4})$", str(s).strip())
        if m:
            have.add(int(m.group(1)))
    y0, y1 = int(str(min_date)[:4]), int(str(max_date)[:4])
    if y1 < y0:
        return False
    need = set(range(y0, y1 + 1))
    return need.issubset(have)


def _full_history_proven(cov: dict[str, Any]) -> bool:
    """Prove FULL_HISTORY via contiguous year slices + trade-calendar day-set completeness.

    No count/span thresholds. Sparse multi-year samples must fail.
    """
    min_d = cov.get("min_date")
    max_d = cov.get("max_date")
    dates = {str(d)[:10] for d in (cov.get("dates") or [])}
    if not min_d or not max_d or not dates or min_d == max_d:
        return False
    if not _year_slices_contiguous(list(cov.get("year_slices") or []), str(min_d), str(max_d)):
        return False
    try:
        expected = [d.isoformat() for d in load_trade_calendar(str(min_d)[:10], str(max_d)[:10])]
    except Exception:
        return False
    if not expected:
        return False
    return set(expected).issubset(dates)


def infer_mode_for_product(product_id: str, cov: dict[str, Any]) -> str:
    contract = SUPPORTED_DATE_PRODUCTS.get(product_id)
    if contract is None:
        return "UNKNOWN_STOP"
    if not cov.get("exists"):
        return "EMPTY_OR_MISSING"
    status = cov.get("coverage_extract_status")
    if status in (
        "UNVERIFIABLE",
        "DATE_COLUMN_UNKNOWN",
        "DATE_COLUMN_EMPTY",
        "NO_PARQUET",
        "UNSUPPORTED_PRODUCT",
        "NOT_RUN",
    ):
        return "UNKNOWN_STOP"
    if cov.get("errors"):
        return "UNKNOWN_STOP"
    n = int(cov.get("distinct_dates") or 0)
    if n <= 0:
        return "UNKNOWN_STOP"
    if n == 1:
        return "INCREMENTAL_PATCH"

    # FULL_HISTORY only when proven against calendar + contiguous years.
    # Otherwise DAILY_HISTORY (existing consumer enum) — history completeness unproven.
    if contract.get("historical") == "FULL_HISTORY" and _full_history_proven(cov):
        return "FULL_HISTORY"
    return "DAILY_HISTORY"


def _scan_parquets_dates(
    files: list[Path],
    date_cols: tuple[str, ...],
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    present: set[str] = set()
    errors: list[str] = []
    read_ok = 0
    for fp in files:
        try:
            import pyarrow.parquet as pq

            names = list(pq.ParquetFile(fp).schema_arrow.names)
            col = next((c for c in date_cols if c in names), None)
            if col is None:
                errors.append(f"{fp.name}:DATE_COLUMN_CONTRACT_MISS")
                continue
            present |= _unique_dates_from_parquet(fp, col, start_date, end_date)
            read_ok += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{fp.name}:{type(exc).__name__}:{exc}")
    return {
        "present": present,
        "errors": errors,
        "files_ok": read_ok,
        "files_attempted": len(files),
        "unverifiable": bool(errors),
    }


def raw_stock_daily_dates(start_date: str, end_date: str) -> dict[str, Any]:
    expected = [d.isoformat() for d in load_trade_calendar(start_date, end_date)]
    years = _years_inclusive(start_date, end_date)
    files: list[Path] = []
    for y in years:
        files.extend(sorted(RAW_P2.glob(f"stock_daily__*__{y}__*.parquet")))
        # gapfill / incremental naming variants under P2
        files.extend(sorted(RAW_P2.glob(f"*__{y}__*gapfill*.parquet")))
        files.extend(sorted(RAW_P2.glob(f"*incremental*{y}*.parquet")))
    # de-dupe
    files = sorted({fp.resolve(): fp for fp in files}.values(), key=lambda p: p.name)
    scan = _scan_parquets_dates(files, ("date", "time"), start_date, end_date)
    present = scan["present"]
    if scan["unverifiable"]:
        return {
            "raw_root": str(RAW_P2),
            "start": start_date,
            "end": end_date,
            "expected_trade_days": expected,
            "raw_present_trade_days": sorted(present & set(expected)),
            "raw_missing_trade_days": [],
            "raw_gap_count": None,
            "raw_present_count": len(present & set(expected)),
            "expected_count": len(expected),
            "status": "UNVERIFIABLE",
            "errors": scan["errors"][:20],
            "source_partitions_by_date_sample": {},
            "overlap_dates": [],
            "years_scanned": years,
            "files_attempted": scan["files_attempted"],
        }
    missing = [d for d in expected if d not in present]
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
        "status": "COMPLETE" if not missing else "INCOMPLETE",
        "errors": [],
        "source_partitions_by_date_sample": {},
        "overlap_dates": [],
        "years_scanned": years,
        "files_attempted": scan["files_attempted"],
    }


def cleaning_stock_daily_dates(start_date: str, end_date: str) -> dict[str, Any]:
    cur = cleaning_current()
    sd = Path(cur["standard_root"]) / "price" / "stock_ohlcv_daily"
    years = _years_inclusive(start_date, end_date)
    files: list[Path] = []
    if sd.exists():
        for y in years:
            files.extend(sorted(sd.glob(f"*__{y}__*.parquet")))
            files.extend(sorted(sd.glob(f"*gapfill*{y}*.parquet")))
        files = sorted({fp.resolve(): fp for fp in files}.values(), key=lambda p: p.name)
    expected = [d.isoformat() for d in load_trade_calendar(start_date, end_date)]
    if not sd.exists():
        return {
            "path": str(sd),
            "present_trade_days": [],
            "missing_trade_days": [],
            "gap_count": None,
            "status": "UNVERIFIABLE",
            "errors": ["cleaning stock_ohlcv_daily path missing"],
            "years_scanned": years,
        }
    scan = _scan_parquets_dates(files, ("date", "time"), start_date, end_date)
    present = scan["present"]
    if scan["unverifiable"]:
        return {
            "path": str(sd),
            "present_trade_days": sorted(present & set(expected)),
            "missing_trade_days": [],
            "gap_count": None,
            "present_count": len(present & set(expected)),
            "expected_count": len(expected),
            "cleaning_release_id": cur.get("release_id"),
            "standard_path": str(sd),
            "status": "UNVERIFIABLE",
            "errors": scan["errors"][:20],
            "years_scanned": years,
        }
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
        "status": "COMPLETE" if not missing else "INCOMPLETE",
        "errors": [],
        "years_scanned": years,
    }


def cache_stock_daily_dates(start_date: str, end_date: str) -> dict[str, Any]:
    cur = cache_current()
    root = Path(cur["standard_root"])
    prod = root / "STOCK_DAILY_PIT_R1"
    cov = product_date_coverage(prod, "STOCK_DAILY_PIT_R1")
    expected = [d.isoformat() for d in load_trade_calendar(start_date, end_date)]
    if cov.get("coverage_extract_status") != "OK":
        return {
            "product_path": str(prod),
            "dates_in_window": [],
            "missing_trade_days": [],
            "gap_count": None,
            "coverage": cov,
            "coverage_mode": infer_mode_for_product("STOCK_DAILY_PIT_R1", cov),
            "status": "UNVERIFIABLE",
            "errors": cov.get("errors") or [cov.get("coverage_extract_status")],
        }
    have = set(cov.get("dates") or [])
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
        "coverage": cov,
        "coverage_mode": infer_mode_for_product("STOCK_DAILY_PIT_R1", cov),
        "status": "COMPLETE" if not missing else "INCOMPLETE",
        "errors": [],
    }


def compare_coverage(expected: Iterable[str], available: Iterable[str]) -> dict[str, Any]:
    exp = [str(x)[:10] for x in expected]
    have = {str(x)[:10] for x in available}
    missing = [d for d in exp if d not in have]
    return {
        "expected_count": len(exp),
        "available_count": len(exp) - len(missing),
        "missing_trade_days": missing,
        "complete": len(missing) == 0,
    }


def classify_stock_daily(start_date: str, end_date: str) -> dict[str, Any]:
    """Multi-plane STOCK_DAILY diagnosis — nested structure required by control_plane write_reports."""
    try:
        expected_dates = load_trade_calendar(start_date, end_date)
        expected = [d.isoformat() for d in expected_dates]
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
            "coverage_mode": "UNKNOWN_STOP",
            "cache": {"coverage": {}, "status": "UNKNOWN", "gap_count": None},
            "raw": {"status": "UNKNOWN"},
            "cleaning": {"status": "UNKNOWN"},
            "error": str(exc),
        }

    raw = raw_stock_daily_dates(start_date, end_date)
    clean = cleaning_stock_daily_dates(start_date, end_date)
    cache = cache_stock_daily_dates(start_date, end_date)
    cov = cache.get("coverage") or {}
    coverage_mode = cache.get("coverage_mode") or infer_mode_for_product("STOCK_DAILY_PIT_R1", cov)

    planes_unverifiable = any(
        x.get("status") == "UNVERIFIABLE" for x in (raw, clean, cache)
    )

    # Do NOT assert TRUE_MISS / download_required without fully verified scans.
    if planes_unverifiable:
        root_cause = "UNKNOWN_STOP"
        download_required = False
        action = "STOP_COVERAGE_UNVERIFIABLE"
        raw_status = "UNKNOWN"
    else:
        raw_complete = raw.get("raw_gap_count") == 0
        clean_complete = clean.get("gap_count") == 0
        cache_complete = cache.get("gap_count") == 0
        raw_status = "COMPLETE" if raw_complete else "INCOMPLETE"
        if raw_complete and clean_complete and cache_complete:
            root_cause = "OK_MULTI_PLANE"
            download_required = False
            action = "OK_USE_CACHE"
        else:
            # Candidate observation — not authorized redownload.
            root_cause = "CANDIDATE_OBSERVATION_UNVERIFIED_GAP"
            download_required = False
            action = "OBSERVE_DO_NOT_REDOWNLOAD"
            # envelope: min/max must not imply completeness
            if (
                cov.get("min_date")
                and cov.get("max_date")
                and str(cov["min_date"]) <= start_date
                and str(cov["max_date"]) >= end_date
                and not cache_complete
            ):
                root_cause = "ENVELOPE_REVIEW"

    return {
        "dataset": "STOCK_DAILY",
        "requested_start": start_date,
        "requested_end": end_date,
        "expected_trade_days": expected,
        "expected_count": len(expected),
        "raw_status": raw_status,
        "cleaning_status": clean.get("status"),
        "cache_status": cache.get("status"),
        "raw_gap_count": raw.get("raw_gap_count"),
        "cleaning_gap_count": clean.get("gap_count"),
        "cache_gap_count": cache.get("gap_count"),
        "raw_missing_trade_days": raw.get("raw_missing_trade_days"),
        "cleaning_missing_trade_days": clean.get("missing_trade_days"),
        "cache_missing_trade_days": cache.get("missing_trade_days"),
        "coverage_mode": coverage_mode,
        "root_cause": root_cause,
        "download_required": download_required,
        "action": action,
        "authority_ready": not planes_unverifiable,
        # Nested keys required by blackbox_data_coverage_control_plane_build_r1.write_reports
        "cache": {
            "coverage": {
                "min_date": cov.get("min_date"),
                "max_date": cov.get("max_date"),
                "distinct_dates": cov.get("distinct_dates"),
                "row_count": cov.get("row_count"),
                "dates": cov.get("dates"),
                "coverage_extract_status": cov.get("coverage_extract_status"),
                "errors": cov.get("errors"),
            },
            "status": cache.get("status"),
            "gap_count": cache.get("gap_count"),
            "missing_trade_days": cache.get("missing_trade_days"),
            "coverage_mode": coverage_mode,
        },
        "raw": {
            "status": raw.get("status"),
            "gap_count": raw.get("raw_gap_count"),
            "missing_trade_days": raw.get("raw_missing_trade_days"),
            "errors": raw.get("errors"),
            "years_scanned": raw.get("years_scanned"),
        },
        "cleaning": {
            "status": clean.get("status"),
            "gap_count": clean.get("gap_count"),
            "missing_trade_days": clean.get("missing_trade_days"),
            "errors": clean.get("errors"),
            "years_scanned": clean.get("years_scanned"),
        },
        "note_9_1_gap": "Any 2026-09-01 observation is candidate-verify-only; not a redownload authorization",
    }
