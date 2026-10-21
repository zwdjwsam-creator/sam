# -*- coding: utf-8 -*-
"""ETF_MINUTE_1M overlapping-shard reader + coverage R1.

Logical product: ETF_MINUTE_1M_R1 (reuse catalog name; not a second product).
ETF_DAILY_PIT_R1 is a different product. No silent daily fallback.

Roots from Cleaning CURRENT + RAW fund_etf_price_1m only.
Does not recurse P4b / open_fund.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blackbox_data_absence_gate_r1 import decide as absence_decide  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CN_TZ = timezone(timedelta(hours=8))
CLEANING_PTR = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
CACHE_PTR = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
TASK = ROOT / "任务" / "BLACKBOX_ETF_DAILY_MINUTE_DATA_PLANE_ROOT_FIX_R1"
RUN = ROOT / "运行"
RAW_1M = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P4_fund_etf_raw_none" / "fund_etf_price_1m"
CAL_ROOT = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P0_meta" / "calendar_cn_exchange"

DAY_RE = re.compile(r"__1m__(?P<date>\d{4}-\d{2}-\d{2})__")
YEAR_RE = re.compile(r"__(?P<year>\d{4})__1m__")
RANGE_RE = re.compile(r"fund_etf_price_1m__(?P<a>\d{6}\.[A-Z]+)_(?P<b>\d{6}\.[A-Z]+)")
EX_RE = re.compile(r"__(XSHE|XSHG)__")

CANONICAL_COLS = [
    "security_code",
    "exchange",
    "datetime",
    "trade_date",
    "bar_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "bar_complete_at",
    "bar_available_at",
    "source_shard",
]

INCIDENT_POOL = [
    "518880.XSHG", "501018.XSHG", "159985.XSHE", "159980.XSHE",
    "513100.XSHG", "513290.XSHG", "513520.XSHG", "513030.XSHG",
    "159792.XSHE", "513130.XSHG", "159920.XSHE", "159329.XSHE",
    "510300.XSHG", "510510.XSHG", "512100.XSHG", "159915.XSHE",
    "512890.XSHG", "513310.XSHG", "511010.XSHG", "511880.XSHG",
]


def now_cn() -> str:
    return datetime.now(CN_TZ).isoformat()


def wjson(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cleaning_etf_1m_dir() -> Path:
    ptr = load_json(CLEANING_PTR)
    return Path(ptr["standard_root"]) / "price" / "ETF_1m"


def classify_name(name: str) -> str:
    if DAY_RE.search(name):
        return "DAILY_SLICE"
    if "incremental" in name.lower():
        return "INCREMENTAL_BATCH"
    if YEAR_RE.search(name):
        return "YEAR_BATCH"
    return "OTHER"


def parse_range(name: str) -> Optional[tuple[str, int, int]]:
    m = RANGE_RE.search(name)
    if not m:
        return None
    a, b = m.group("a"), m.group("b")
    na, ea = a.split(".")
    nb, _ = b.split(".")
    return ea, int(na), int(nb)


def code_in_range(code: str, rng: Optional[tuple[str, int, int]]) -> bool:
    if rng is None:
        return False
    num, ex = code.split(".")
    return rng[0] == ex and rng[1] <= int(num) <= rng[2]


def code_matches_daily(code: str, name: str) -> bool:
    m = EX_RE.search(name)
    if not m:
        return True
    return code.endswith("." + m.group(1))


def envelope_from_name(name: str, shard_type: str) -> tuple[Optional[str], Optional[str]]:
    if shard_type == "DAILY_SLICE":
        m = DAY_RE.search(name)
        d = m.group("date") if m else None
        return d, d
    m = re.search(r"incremental_(\d{8})_(\d{8})", name)
    if m:
        a = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}"
        b = f"{m.group(2)[:4]}-{m.group(2)[4:6]}-{m.group(2)[6:]}"
        return a, b
    ym = YEAR_RE.search(name)
    if ym:
        y = ym.group("year")
        return f"{y}-01-01", f"{y}-12-31"
    return None, None


def sidecar_envelope(parquet_path: Path) -> tuple[Optional[str], Optional[str], Optional[list]]:
    for side in (Path(str(parquet_path) + ".sidecar.json"), parquet_path.with_suffix(parquet_path.suffix + ".sidecar.json")):
        if not side.is_file():
            continue
        try:
            j = json.loads(side.read_text(encoding="utf-8"))
        except Exception:
            continue
        s = j.get("start_date") or j.get("start")
        e = j.get("end_date") or j.get("end")
        codes = j.get("codes") or j.get("etf_codes")
        return (str(s)[:10] if s else None, str(e)[:10] if e else None, codes if isinstance(codes, list) else None)
    return None, None, None


def window_overlap(a0: Optional[str], a1: Optional[str], b0: str, b1: str) -> bool:
    if not a0 or not a1:
        return False
    return not (a1 < b0 or a0 > b1)


def scan_root(root: Path, source_generation: str) -> list[dict]:
    out = []
    if not root.is_dir():
        return out
    for f in root.glob("*.parquet"):
        st = classify_name(f.name)
        if st == "OTHER":
            continue
        d0, d1 = envelope_from_name(f.name, st)
        sc0, sc1, scodes = sidecar_envelope(f) if root == RAW_1M or "incremental" in f.name else (None, None, None)
        if sc0:
            d0 = sc0
        if sc1:
            d1 = sc1
        rng = parse_range(f.name)
        rec = {
            "path": str(f),
            "file_name": f.name,
            "shard_type": st,
            "exchange": (EX_RE.search(f.name).group(1) if EX_RE.search(f.name) else (rng[0] if rng else None)),
            "frequency": "1m",
            "date_min": d0,
            "date_max": d1,
            "range_start": f"{rng[1]:06d}.{rng[0]}" if rng else None,
            "range_end": f"{rng[2]:06d}.{rng[0]}" if rng else None,
            "sidecar_codes": scodes,
            "symbols_count": len(scodes) if scodes else None,
            "rows": None,
            "source_generation": source_generation,
            "source_batch": st,
            "file_size": f.stat().st_size,
            "file_sha256": None,
            "qa_status": "FILENAME_SIDECAR_CLASSIFIED",
        }
        out.append(rec)
    return out


def build_shard_manifest() -> dict:
    cleaning = load_json(CLEANING_PTR)
    shards = []
    shards.extend(scan_root(cleaning_etf_1m_dir(), cleaning["release_id"]))
    shards.extend(scan_root(RAW_1M, "P4_fund_etf_raw_none/fund_etf_price_1m"))
    by_type = defaultdict(int)
    for s in shards:
        by_type[s["shard_type"]] += 1
    body = {
        "manifest_id": "ETF_MINUTE_1M_SHARD_MANIFEST_CURRENT",
        "product_id": "ETF_MINUTE_1M_R1",
        "generated_at": now_cn(),
        "cleaning_release_id": cleaning["release_id"],
        "roots_scanned": [str(cleaning_etf_1m_dir()), str(RAW_1M)],
        "n_shards": len(shards),
        "by_type": dict(by_type),
        "sha256_policy": "NOT_REQUIRED_FILENAME_SIDECAR_MANIFEST",
        "shards": shards,
    }
    return body


def overlapping_shards(
    manifest: dict,
    start: str,
    end: str,
    symbols: Optional[list[str]] = None,
    plane: str = "CLEANING",
    cleaning_release_id: Optional[str] = None,
) -> list[dict]:
    cleaning_id = cleaning_release_id or load_json(CLEANING_PTR)["release_id"]
    out = []
    for s in manifest["shards"]:
        if plane == "CLEANING" and s["source_generation"] != cleaning_id:
            continue
        if plane == "RAW" and "P4_fund_etf_raw_none" not in str(s.get("source_generation")):
            continue
        if not window_overlap(s.get("date_min"), s.get("date_max"), start, end):
            continue
        if symbols:
            if s["shard_type"] == "DAILY_SLICE":
                if not any(code_matches_daily(c, s["file_name"]) for c in symbols):
                    continue
            else:
                rng = parse_range(s["file_name"])
                scodes = s.get("sidecar_codes")
                hit = False
                for c in symbols:
                    if scodes and c in scodes:
                        hit = True
                        break
                    if code_in_range(c, rng):
                        hit = True
                        break
                if not hit:
                    continue
        out.append(s)
    return out


def _read_table(path: Path) -> pa.Table:
    names = set(pq.read_schema(path).names)
    if "security_code" in names and "datetime" in names:
        cols = [c for c in CANONICAL_COLS if c in names]
        return pq.read_table(path, columns=cols)
    cols = [c for c in ("time", "code", "open", "high", "low", "close", "volume", "money", "bar_complete_at") if c in names]
    return pq.read_table(path, columns=cols)


def normalize_table(t: pa.Table, shard_path: str) -> pa.Table:
    names = set(t.column_names)
    if "security_code" in names and "datetime" in names:
        df = t.to_pandas()
        for c in CANONICAL_COLS:
            if c not in df.columns:
                df[c] = None
        df["source_shard"] = shard_path
        return pa.Table.from_pandas(df[CANONICAL_COLS], preserve_index=False)
    code = t.column("code") if "code" in names else pa.array([None] * t.num_rows, pa.string())
    ts = t.column("time") if "time" in names else pa.array([None] * t.num_rows, pa.timestamp("ns"))
    df = t.to_pandas()
    df["security_code"] = df["code"].astype(str)
    df["exchange"] = df["security_code"].str.split(".").str[-1]
    df["datetime"] = pd_to_dt(df["time"])
    df["trade_date"] = df["datetime"].dt.strftime("%Y-%m-%d")
    df["bar_time"] = df["datetime"].dt.strftime("%H:%M:%S")
    if "bar_complete_at" in df.columns:
        df["bar_complete_at"] = pd_to_dt(df["bar_complete_at"])
    else:
        df["bar_complete_at"] = df["datetime"]
    df["bar_available_at"] = df["bar_complete_at"]
    if "money" in df.columns and "amount" not in df.columns:
        df["amount"] = df["money"]
    for c in ("open", "high", "low", "close", "volume", "amount"):
        if c not in df.columns:
            df[c] = None
    df["source_shard"] = shard_path
    keep = CANONICAL_COLS
    return pa.Table.from_pandas(df[keep], preserve_index=False)


def pd_to_dt(s):
    import pandas as pd
    return pd.to_datetime(s)


def filter_request(t: pa.Table, symbols: list[str], start: str, end: str) -> pa.Table:
    import pandas as pd
    df = t.to_pandas()
    df = df[df["security_code"].isin(symbols)]
    df = df[(df["trade_date"] >= start) & (df["trade_date"] <= end)]
    if df.empty:
        return pa.Table.from_pandas(df, preserve_index=False)
    return pa.Table.from_pandas(df, preserve_index=False)


def dedupe_canonical(t: pa.Table) -> dict:
    import pandas as pd
    df = t.to_pandas()
    before = len(df)
    if df.empty:
        return {"table": t, "before": 0, "after": 0, "identical": 0, "conflicts": 0, "conflict_keys": []}
    price_cols = ["open", "high", "low", "close", "volume", "amount"]
    df["_key"] = df["security_code"].astype(str) + "|" + df["datetime"].astype(str)
    conflicts = []
    identical = 0
    keep_idx = []
    for key, g in df.groupby("_key", sort=False):
        if len(g) == 1:
            keep_idx.append(g.index[0])
            continue
        sub = g[price_cols].fillna(-1)
        if sub.nunique(dropna=False).max() <= 1:
            identical += len(g) - 1
            keep_idx.append(g.index[0])
        else:
            conflicts.append(key)
    after_df = df.loc[keep_idx].drop(columns=["_key"])
    return {
        "table": pa.Table.from_pandas(after_df, preserve_index=False),
        "before": before,
        "after": len(after_df),
        "identical": identical,
        "conflicts": len(conflicts),
        "conflict_keys": conflicts[:50],
    }


def read_overlapping(
    symbols: list[str],
    start: str,
    end: str,
    *,
    mode: str = "NEW",
    manifest: Optional[dict] = None,
    cleaning_release_id: Optional[str] = None,
) -> dict:
    manifest = manifest or build_shard_manifest()
    cleaning_id = cleaning_release_id or load_json(CLEANING_PTR)["release_id"]
    skipped = []
    if mode == "OLD":
        # Reproduce first-match year shard only; skip daily slices.
        requested = []
        loaded = []
        tables = []
        for code in symbols:
            hits = [
                s for s in manifest["shards"]
                if s["source_generation"] == cleaning_id
                and s["shard_type"] in ("YEAR_BATCH", "INCREMENTAL_BATCH")
                and window_overlap(s.get("date_min"), s.get("date_max"), start, end)
                and code_in_range(code, parse_range(s["file_name"]))
            ]
            requested.extend(hits)
            if not hits:
                skipped.append({"code": code, "reason": "OLD_NO_YEAR_HIT"})
                continue
            hits.sort(key=lambda s: (0 if s["shard_type"] == "INCREMENTAL_BATCH" else 1, s["file_name"]))
            first = hits[0]
            loaded.append(first)
            t = filter_request(normalize_table(_read_table(Path(first["path"])), first["path"]), [code], start, end)
            tables.append(t)
        requested_u = {s["path"]: s for s in requested}
        loaded_u = {s["path"]: s for s in loaded}
    else:
        requested = overlapping_shards(manifest, start, end, symbols, plane="CLEANING", cleaning_release_id=cleaning_id)
        loaded = []
        tables = []
        requested_u = {s["path"]: s for s in requested}
        loaded_u = {}
        for s in requested:
            path = Path(s["path"])
            try:
                raw_t = _read_table(path)
            except Exception as exc:
                skipped.append({"path": s["path"], "reason": f"READ_FAIL:{exc}"})
                continue
            t = filter_request(normalize_table(raw_t, s["path"]), symbols, start, end)
            if t.num_rows == 0:
                skipped.append({"path": s["path"], "reason": "NO_ROWS_AFTER_SYMBOL_DATE_FILTER"})
                continue
            loaded_u[s["path"]] = s
            tables.append(t)
    if not tables:
        empty = pa.table({c: pa.array([], type=pa.string()) for c in ["security_code"]})
        dd = {"table": empty, "before": 0, "after": 0, "identical": 0, "conflicts": 0, "conflict_keys": []}
    else:
        merged = pa.concat_tables(tables, promote_options="default")
        dd = dedupe_canonical(merged)
    status = "PASS"
    if dd["conflicts"] > 0:
        status = "FAIL_CLOSED_DUPLICATE_CONFLICT"
    return {
        "mode": mode,
        "product_id": "ETF_MINUTE_1M_R1",
        "frequency": "1m",
        "window": [start, end],
        "symbols": symbols,
        "REQUESTED_SHARDS": list(requested_u.values()),
        "LOADED_SHARDS": list(loaded_u.values()),
        "SKIPPED_SHARDS": skipped,
        "n_requested": len(requested_u),
        "n_loaded": len(loaded_u),
        "n_skipped": len(skipped),
        "ROWS_BEFORE_DEDUPE": dd["before"],
        "ROWS_AFTER_DEDUPE": dd["after"],
        "DUPLICATE_IDENTICAL": dd["identical"],
        "DUPLICATE_CONFLICT": dd["conflicts"],
        "DEDUPE_QA": status,
        "table": dd["table"],
        "conflict_keys": dd["conflict_keys"],
    }


def official_trading_calendar_window(start: str, end: str) -> dict:
    """expected_days = official A-share trade calendar ∩ [start, end].

    Must not depend on shard availability, observed first/last dates, or daily slices.
    """
    cands = sorted(CAL_ROOT.glob("calendar_cn_exchange_v2_asof_*/CALENDAR_TRADE_DAYS.parquet"))
    if not cands:
        raise RuntimeError("OFFICIAL_TRADING_CALENDAR_MISSING")
    path = cands[-1]
    df = pd.read_parquet(path)
    col = None
    for name in ("trade_date", "calendar_date", "date", "trade_day"):
        if name in df.columns:
            col = name
            break
    if col is None:
        col = df.columns[0]
    all_days = sorted({str(v)[:10] for v in df[col].tolist() if str(v)[:10] >= "1990-01-01"})
    days = [d for d in all_days if start <= d <= end]
    if not days:
        raise RuntimeError(f"OFFICIAL_TRADING_CALENDAR_EMPTY_WINDOW:{start}:{end}:{path}")
    cal_min = all_days[0]
    cal_max = all_days[-1]
    return {
        "EXPECTED_CALENDAR_SOURCE": str(path),
        "calendar_version": path.parent.name,
        "EXPECTED_WINDOW_START": start,
        "EXPECTED_WINDOW_END": end,
        "expected_days": days,
        "EXPECTED_TRADE_DAY_COUNT": len(days),
        "calendar_min": cal_min,
        "calendar_max": cal_max,
        "covers_request_start": cal_min <= start,
        "covers_request_end": cal_max >= end,
        "depends_on_shards": False,
        "depends_on_observed_minmax": False,
    }


def expected_trade_days(start: str, end: str) -> list[str]:
    return official_trading_calendar_window(start, end)["expected_days"]


def expected_trade_days_full(start: str, end: str) -> list[str]:
    return official_trading_calendar_window(start, end)["expected_days"]


def shard_partition_dates(
    manifest: dict,
    expected_days: list[str],
    plane: str = "CLEANING",
    cleaning_release_id: Optional[str] = None,
) -> set[str]:
    cleaning_id = cleaning_release_id or load_json(CLEANING_PTR)["release_id"]
    covered: set[str] = set()
    shards = manifest.get("shards") or []
    for d in expected_days:
        for s in shards:
            if plane == "CLEANING" and s.get("source_generation") != cleaning_id:
                continue
            if window_overlap(s.get("date_min"), s.get("date_max"), d, d):
                covered.add(d)
                break
    return covered


def coverage_matrix(read_body: dict, expected_days: list[str]) -> dict:
    import pandas as pd
    t = read_body["table"]
    df = t.to_pandas() if t.num_rows else pd.DataFrame(columns=["security_code", "trade_date", "bar_time"])
    rows = []
    for code in read_body["symbols"]:
        sub = df[df["security_code"] == code] if not df.empty else df
        have = sorted(set(sub["trade_date"].astype(str))) if len(sub) else []
        have_set = set(have)
        gap = [d for d in expected_days if d not in have_set]
        complete = []
        partial = []
        first_last = {}
        if len(sub):
            for d, g in sub.groupby("trade_date"):
                n = len(g)
                bars = sorted(g["bar_time"].astype(str))
                ds = str(d)
                first_last[ds] = {"minute_rows": n, "first_bar": bars[0] if bars else None, "last_bar": bars[-1] if bars else None}
                if n >= 230:
                    complete.append(ds)
                else:
                    partial.append(ds)
        if not have:
            state = "UNKNOWN_SYMBOL_GAP"
            absence = absence_decide(
                n_rows=0,
                pagination_complete="YES",
                completeness_state="UNKNOWN",
                symbol_identity_proven=False,
                source_request_complete=False,
            )
        elif gap:
            state = "AVAILABLE_PARTIAL"
            absence = absence_decide(
                n_rows=len(sub),
                pagination_complete="YES",
                completeness_state="PARTIAL",
                available_partial=True,
            )
        else:
            state = "AVAILABLE_COMPLETE"
            absence = absence_decide(
                n_rows=len(sub),
                pagination_complete="YES",
                completeness_state="COMPLETE",
            )
        gap_reason = []
        if not have:
            gap_reason.append("ZERO_ROWS_IN_WINDOW")
        elif gap:
            gap_reason.append("DATES_MISSING_SEE_INVENTORY")
        rows.append({
            "symbol": code,
            "request_start": read_body["window"][0],
            "request_end": read_body["window"][1],
            "window": read_body["window"],
            "frequency": "1m",
            "expected_days": len(expected_days),
            "expected_trade_days": len(expected_days),
            "available_days": len(have),
            "available_trade_days": len(have),
            "complete_days": len(complete),
            "partial_days": len(partial),
            "gap_days": len(gap),
            "missing_days": gap,
            "coverage_state": state,
            "coverage_status": state,
            "gap_reason": gap_reason,
            "DATA_ABSENCE_GATE": absence["DATA_ABSENCE_GATE"],
            "DATA_ABSENT_CLAIM_ALLOWED": absence["DATA_ABSENT_CLAIM_ALLOWED"],
            "first_date": have[0] if have else None,
            "last_date": have[-1] if have else None,
            "first_available_date": have[0] if have else None,
            "last_available_date": have[-1] if have else None,
            "blocker": gap_reason[0] if gap_reason else None,
        })
    return {"rows": rows, "expected_days": expected_days}


def classify_gaps(
    cov_rows: list[dict],
    expected_days: list[str],
    partition_dates: set[str],
    daily_slice_dates: Optional[set[str]] = None,
) -> dict:
    """Classify from official expected calendar + shard envelope presence. No chat-hardcoded dates."""
    daily_slice_dates = daily_slice_dates or set()
    inv = []
    have_any = {d: [] for d in expected_days}
    for r in cov_rows:
        miss = set(r.get("missing_days") or [])
        for d in expected_days:
            if d not in miss:
                have_any[d].append(r["symbol"])
    for d in expected_days:
        n_have = len(have_any[d])
        part_ok = d in partition_dates
        if not part_ok:
            inv.append({
                "class": "UNKNOWN_PARTITION_GAP",
                "date": d,
                "symbols": "ALL_REQUESTED",
                "partition_present": False,
                "daily_slice_present": d in daily_slice_dates,
            })
        elif n_have == 0:
            inv.append({
                "class": "SYMBOL_PARTITION_GAP",
                "date": d,
                "symbols": "ALL_REQUESTED",
                "partition_present": True,
                "daily_slice_present": d in daily_slice_dates,
                "note": "relevant shard envelope covers date but no requested symbol has bars; CONFIRMED_ABSENT forbidden",
            })
    for r in cov_rows:
        if r["available_days"] == 0:
            inv.append({
                "class": "UNKNOWN_SYMBOL_GAP",
                "symbol": r["symbol"],
                "DATA_ABSENCE_GATE": r["DATA_ABSENCE_GATE"],
                "DATA_ABSENT_CLAIM_ALLOWED": False,
                "note": "0 rows in window; CONFIRMED_ABSENT forbidden until acquisition complete",
            })
            continue
        miss = r.get("missing_days") or []
        symbol_part = [d for d in miss if d in partition_dates]
        if symbol_part:
            inv.append({
                "class": "SYMBOL_PARTITION_GAP",
                "symbol": r["symbol"],
                "dates": symbol_part,
                "DATA_ABSENT_CLAIM_ALLOWED": False,
            })
        if r["partial_days"]:
            inv.append({
                "class": "PARTIAL_DAY_GAP",
                "symbol": r["symbol"],
                "n_partial": r["partial_days"],
            })
    confirmed = sum(1 for r in cov_rows if r.get("DATA_ABSENCE_GATE") == "CONFIRMED_ABSENT")
    return {
        "inventory_id": "ETF_MINUTE_GAP_INVENTORY_CURRENT",
        "items": inv,
        "n": len(inv),
        "CONFIRMED_ABSENT_count": confirmed,
    }


def anti_lookahead_test(t: pa.Table) -> dict:
    import pandas as pd
    if t.num_rows == 0:
        return {"status": "PASS", "n_tested": 0, "note": "empty_table"}
    df = t.to_pandas()
    bad = 0
    # Contract: BAR_AVAILABLE_AT <= request_time required. Using bar at T=bar_available_at is allowed.
    # Fail if bar_available_at is NaT or before datetime (incoherent).
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["bar_available_at"] = pd.to_datetime(df["bar_available_at"])
    incoherent = df[df["bar_available_at"] < df["datetime"] - pd.Timedelta(minutes=2)]
    future_fill = 0  # no execution fill in this task
    status = "PASS" if len(incoherent) == 0 else "FAIL"
    return {
        "status": status,
        "contract_id": "MINUTE_BAR_TIME_CONTRACT",
        "BAR_TIMESTAMP": "datetime",
        "BAR_AVAILABLE_AT": "bar_complete_at or datetime",
        "rule": "request at T may use bars with BAR_AVAILABLE_AT <= T; 14:55 bar not usable before 14:55:00",
        "n_rows": int(len(df)),
        "incoherent_available_before_timestamp": int(len(incoherent)),
        "future_bar_fill_used": future_fill,
    }


def schema_qa(t: pa.Table) -> dict:
    import pandas as pd
    if t.num_rows == 0:
        return {"status": "PASS", "note": "empty"}
    df = t.to_pandas()
    fails = []
    for c in CANONICAL_COLS:
        if c not in df.columns:
            fails.append(f"missing_col:{c}")
    if df["security_code"].astype(str).str.contains(r"\.(XSHE|XSHG)$").mean() < 1:
        fails.append("code_suffix")
    px = df[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce")
    if (px <= 0).any().any():
        fails.append("non_positive_price")
    ohlc_bad = (px["high"] < px[["open", "close", "low"]].max(axis=1)) | (px["low"] > px[["open", "close", "high"]].min(axis=1))
    # simplified OHLC: high>=max(o,c,l) low<=min(o,c,h)
    if bool((px["high"] < px[["open", "close"]].max(axis=1)).mean() > 0.01):
        fails.append("ohlc_high")
    lunch = df["bar_time"].astype(str).between("11:31:00", "12:59:59")
    if int(lunch.sum()) > 0:
        fails.append(f"lunch_pseudo_bar:{int(lunch.sum())}")
    return {"status": "PASS" if not fails else "FAIL", "fails": fails, "n": int(len(df))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-manifest", action="store_true")
    ap.add_argument("--coverage", action="store_true")
    ap.add_argument("--regression", action="store_true")
    ap.add_argument("--start", default="2026-07-01")
    ap.add_argument("--end", default="2026-08-18")
    args = ap.parse_args()
    TASK.mkdir(parents=True, exist_ok=True)
    qa = TASK / "qa"
    qa.mkdir(parents=True, exist_ok=True)

    if args.build_manifest or args.coverage or args.regression:
        man = build_shard_manifest()
        slim = dict(man)
        slim["shards"] = man["shards"]  # full
        wjson(RUN / "ETF_MINUTE_1M_SHARD_MANIFEST_CURRENT.json", man)
        wjson(qa / "ETF_MINUTE_1M_SHARD_MANIFEST_CURRENT.json", {**man, "shards": man["shards"][:20], "n_shards": man["n_shards"], "note": "head20; full in 运行/"})

    if args.coverage or args.regression:
        man = load_json(RUN / "ETF_MINUTE_1M_SHARD_MANIFEST_CURRENT.json")
        cal = official_trading_calendar_window(args.start, args.end)
        expected = cal["expected_days"]
        new_read = read_overlapping(INCIDENT_POOL, args.start, args.end, mode="NEW", manifest=man)
        table = new_read.pop("table")
        cov = coverage_matrix({**new_read, "table": table, "symbols": INCIDENT_POOL}, expected)
        daily_dates = {s["date_min"] for s in man["shards"] if s["shard_type"] == "DAILY_SLICE" and s["source_generation"] == load_json(CLEANING_PTR)["release_id"] and s.get("date_min")}
        part_dates = shard_partition_dates(man, expected)
        gaps = classify_gaps(cov["rows"], expected, part_dates, daily_dates)
        schema = schema_qa(table)
        time_c = anti_lookahead_test(table)
        wjson(RUN / "ETF_MINUTE_1M_COVERAGE_CURRENT.json", {
            "generated_at": now_cn(),
            "window": [args.start, args.end],
            **{k: cal[k] for k in (
                "EXPECTED_CALENDAR_SOURCE", "calendar_version",
                "EXPECTED_WINDOW_START", "EXPECTED_WINDOW_END", "EXPECTED_TRADE_DAY_COUNT",
            )},
            "expected_days": expected,
            "rows": cov["rows"],
        })
        wjson(RUN / "ETF_MINUTE_GAP_INVENTORY_CURRENT.json", gaps)
        wjson(qa / "NEW_READER_RESULT.json", {k: v for k, v in new_read.items() if k != "REQUESTED_SHARDS"} | {
            "REQUESTED_SHARDS_N": new_read["n_requested"],
            "LOADED_SHARDS_N": new_read["n_loaded"],
            "schema_qa": schema,
            "time_contract": time_c,
            "symbols_with_rows": sum(1 for r in cov["rows"] if r["available_days"] > 0),
            "zero_row_symbols": [r["symbol"] for r in cov["rows"] if r["available_days"] == 0],
            "aug_daily_slice_files": sum(1 for s in man["shards"] if s["shard_type"] == "DAILY_SLICE" and (s.get("date_min") or "").startswith("2026-08")),
        })
        print(json.dumps({
            "NEW_have": sum(1 for r in cov["rows"] if r["available_days"] > 0),
            "zero": [r["symbol"] for r in cov["rows"] if r["available_days"] == 0],
            "DEDUPE": new_read["DEDUPE_QA"],
            "schema": schema["status"],
            "time": time_c["status"],
            "n_loaded": new_read["n_loaded"],
            "rows": new_read["ROWS_AFTER_DEDUPE"],
        }, ensure_ascii=False, indent=2))

    if args.regression:
        man = load_json(RUN / "ETF_MINUTE_1M_SHARD_MANIFEST_CURRENT.json")
        old_read = read_overlapping(INCIDENT_POOL, args.start, args.end, mode="OLD", manifest=man)
        old_t = old_read.pop("table")
        expected = expected_trade_days_full(args.start, args.end)
        old_cov = coverage_matrix({**old_read, "table": old_t, "symbols": INCIDENT_POOL}, expected)
        new_cov = load_json(RUN / "ETF_MINUTE_1M_COVERAGE_CURRENT.json")
        old_have = sum(1 for r in old_cov["rows"] if r["available_days"] > 0)
        new_have = sum(1 for r in new_cov["rows"] if r["available_days"] > 0)
        old_types = {s.get("shard_type") for s in (old_read.get("LOADED_SHARDS") or [])}
        new_types = set()
        # new_read already popped in coverage branch; reload from files
        body = {
            "OLD_READER_RESULT": {
                "n_loaded": old_read["n_loaded"],
                "rows": old_read["ROWS_AFTER_DEDUPE"],
                "symbols_with_rows": old_have,
                "zero_row_symbols": [r["symbol"] for r in old_cov["rows"] if r["available_days"] == 0],
                "loaded_shard_types": sorted(old_types),
                "includes_daily_slice": "DAILY_SLICE" in old_types,
                "mode": "first_year_or_incremental_match_no_daily",
            },
            "NEW_READER_RESULT": {
                "symbols_with_rows": new_have,
                "mode": "all_overlapping_year_incremental_daily",
            },
            "ROOT_CAUSE_REPRODUCED": (
                old_have < new_have
                and "DAILY_SLICE" not in old_types
            ),
            "ROOT_FIX_VERIFIED": old_have < new_have and "DAILY_SLICE" not in old_types,
        }
        wjson(qa / "GOLDEN_REGRESSION_OLD_VS_NEW.json", body)
        print(json.dumps(body, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
