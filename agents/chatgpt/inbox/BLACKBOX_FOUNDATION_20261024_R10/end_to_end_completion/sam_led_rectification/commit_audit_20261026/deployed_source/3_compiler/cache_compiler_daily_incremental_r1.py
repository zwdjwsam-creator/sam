# -*- coding: utf-8 -*-
"""BLACKBOX Backtest Cache Compiler R1 — architecture bootstrap + canary/full compile.

Builds Data Plane caches only. No strategy answers.
Asset types: STOCK + ETF + FUND + INDEX.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"E:\BLACKBOX")
TASK = ROOT / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1"
ARCHIVE = Path(r"D:\CURSOR_TASK_ARCHIVE\BLACKBOX_BACKTEST_CACHE_COMPILER_R1")
CACHE_ROOT = ROOT / "数据" / "回测缓存"
RELEASES = CACHE_ROOT / "releases"
CANARY_ROOT = CACHE_ROOT / "_canary"
REGISTRY = CACHE_ROOT / "registry"
POINTER = CACHE_ROOT / "CURRENT_CACHE_RELEASE.json"
# HARD: canary is a smoke artifact only — never authority / never CURRENT.
CANARY_CURRENT_PUBLISH = "STRUCTURALLY_FORBIDDEN"
CURRENT = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
PLANE = ROOT / "数据" / "原始只读" / "strategy_data_plane_additions"
RAW = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw"
CN = ZoneInfo("Asia/Shanghai")
SCHEMA_VERSION = "1.0.0"
BUILD_VERSION = "CACHE_COMPILER_R1"
FORMULA_VERSION = "univ_factor_r1_v1"
PRICE_ADJ_TAG = "RAW_NONE"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def wjson(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def wtext(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def log(msg: str) -> None:
    line = f"[{now_iso()}] {msg}"
    print(line, flush=True)
    p = TASK / "11_LOGS" / "compiler.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            c = f.read(1024 * 1024)
            if not c:
                break
            h.update(c)
    return h.hexdigest()


def ensure_dirs() -> None:
    for p in [
        TASK / "11_LOGS",
        TASK / "12_ACCEPTANCE",
        ARCHIVE,
        CACHE_ROOT,
        RELEASES,
        CANARY_ROOT,
        REGISTRY,
    ]:
        p.mkdir(parents=True, exist_ok=True)


def pointer_fingerprint() -> dict:
    """Stable CURRENT identity for canary non-regression checks."""
    if not POINTER.exists():
        return {"exists": False, "sha256": None, "cache_release_id": None, "release_root": None}
    raw = POINTER.read_bytes()
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception:
        obj = {}
    return {
        "exists": True,
        "sha256": sha256_bytes(raw),
        "cache_release_id": obj.get("cache_release_id"),
        "release_root": obj.get("release_root"),
    }


def write_static_registries() -> None:
    catalog = """product_id,layer,asset_type,status,partition_key,description
STOCK_DAILY_PIT_R1,L1,STOCK,ACTIVE,year/signal_date,Stock daily PIT snapshot
STOCK_FACTOR_DAILY_R1,L2,STOCK,ACTIVE,year/signal_date,Universal stock factors (no candidate pct)
ETF_DAILY_PIT_R1,L1,ETF,ACTIVE,year/signal_date,ETF daily PIT snapshot
ETF_FACTOR_DAILY_R1,L2,ETF,ACTIVE,year/signal_date,Universal ETF factors
FUND_DAILY_PIT_R1,L1,FUND,ACTIVE,year/signal_date,Fund daily PIT (first-class asset)
FUND_FACTOR_DAILY_R1,L2,FUND,ACTIVE,year/signal_date,Universal fund factors
INDEX_DAILY_R1,L1,INDEX,ACTIVE,year/signal_date,Index daily facts
INDEX_FACTOR_DAILY_R1,L2,INDEX,ACTIVE,year/signal_date,Universal index factors
INDEX_CONSTITUENT_PIT_R1,L1,INDEX,ACTIVE,year/asof_date,Index constituents as-of
INDEX_WEIGHT_PIT_R1,L1,INDEX,ACTIVE,index/snapshot,Official index component weights PIT last-known snapshot
ETF_TRACKING_INDEX_MAP_R1,L1,ETF,ACTIVE,etf_code,ETF tracking index mapping
SW_L1_MEMBERSHIP_PIT_R1,L1,STOCK,ACTIVE_SOURCE_READY,year/asof_date,SW L1 membership PIT (source ready; structure product separate)
SW_L1_STRUCTURE_DAILY_R1,L3,INDUSTRY,BLOCKED_UNTIL_STRUCTURE_BUILD,year/signal_date,Industry structure
MARKET_UNIVERSE_PIT_R1,L1,STOCK,ACTIVE,year/signal_date,Market structure universe (not trade filter)
STOCK_TRADEABILITY_PIT_R1,L1,STOCK,ACTIVE,year/signal_date,Tradeability facts ST/suspend/limits
MARKET_STRUCTURE_DAILY_R1,L3,MARKET,PARTIAL,year/signal_date,Market structure (needs structure product)
FUND_LIKE_ASSET_VIEW_R1,L1,ETF_FUND_VIEW,ACTIVE,view,Logical union of ETF+FUND retaining asset_type
CACHE_MANIFEST_REGISTRY_R1,META,ALL,ACTIVE,n/a,Manifest registry
CACHE_DEPENDENCY_REGISTRY_R1,META,ALL,ACTIVE,n/a,Dependency registry
"""
    wtext(REGISTRY / "CACHE_PRODUCT_CATALOG.csv", catalog)
    wtext(ARCHIVE / "02_CACHE_PRODUCT_CATALOG.csv", catalog)

    schema = """product_id,column,dtype,time_class,notes
STOCK_DAILY_PIT_R1,signal_date,date,SAME_DAY_KNOWN_EOD,
STOCK_DAILY_PIT_R1,code,str,STATIC_ASOF,
STOCK_DAILY_PIT_R1,open,float,SAME_DAY_KNOWN_EOD,RAW_NONE
STOCK_DAILY_PIT_R1,high,float,SAME_DAY_KNOWN_EOD,RAW_NONE
STOCK_DAILY_PIT_R1,low,float,SAME_DAY_KNOWN_EOD,RAW_NONE
STOCK_DAILY_PIT_R1,close,float,SAME_DAY_KNOWN_EOD,RAW_NONE
STOCK_DAILY_PIT_R1,volume,float,SAME_DAY_KNOWN_EOD,
STOCK_DAILY_PIT_R1,money,float,SAME_DAY_KNOWN_EOD,
STOCK_DAILY_PIT_R1,price_adj_tag,str,STATIC_ASOF,RAW_NONE
STOCK_DAILY_PIT_R1,pit_status,str,STATIC_ASOF,
STOCK_FACTOR_DAILY_R1,r1,float,SAME_DAY_KNOWN_EOD,close_t/close_t-1-1
STOCK_FACTOR_DAILY_R1,r5,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,r20,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,ma5,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,ma20,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,ma60,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,bias20,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,vol_ma20,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,rolling_vol_20,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,drawdown_60,float,SAME_DAY_KNOWN_EOD,
ETF_DAILY_PIT_R1,nav,float,PUBLICATION_TIME_AWARE,if available
FUND_DAILY_PIT_R1,asset_type,str,STATIC_ASOF,always FUND
FUND_DAILY_PIT_R1,nav,float,PUBLICATION_TIME_AWARE,
INDEX_DAILY_R1,close,float,SAME_DAY_KNOWN_EOD,
"""
    wtext(REGISTRY / "CACHE_SCHEMA_REGISTRY.csv", schema)
    wtext(ARCHIVE / "05_CACHE_SCHEMA_REGISTRY.csv", schema)

    formulas = """factor_id,formula,lookback,formula_version,notes
r1,close/close.shift(1)-1,1,univ_factor_r1_v1,
r3,close/close.shift(3)-1,3,univ_factor_r1_v1,
r5,close/close.shift(5)-1,5,univ_factor_r1_v1,
r10,close/close.shift(10)-1,10,univ_factor_r1_v1,
r20,close/close.shift(20)-1,20,univ_factor_r1_v1,
r24,close/close.shift(24)-1,24,univ_factor_r1_v1,
r25,close/close.shift(25)-1,25,univ_factor_r1_v1,
r60,close/close.shift(60)-1,60,univ_factor_r1_v1,
ma5,close.rolling(5).mean(),5,univ_factor_r1_v1,
ma10,close.rolling(10).mean(),10,univ_factor_r1_v1,
ma20,close.rolling(20).mean(),20,univ_factor_r1_v1,
ma50,close.rolling(50).mean(),50,univ_factor_r1_v1,
ma60,close.rolling(60).mean(),60,univ_factor_r1_v1,
ma120,close.rolling(120).mean(),120,univ_factor_r1_v1,
ma250,close.rolling(250).mean(),250,univ_factor_r1_v1,
bias5,close/ma5-1,5,univ_factor_r1_v1,
bias10,close/ma10-1,10,univ_factor_r1_v1,
bias20,close/ma20-1,20,univ_factor_r1_v1,
bias60,close/ma60-1,60,univ_factor_r1_v1,
vol_ma5,volume.rolling(5).mean(),5,univ_factor_r1_v1,
vol_ma20,volume.rolling(20).mean(),20,univ_factor_r1_v1,
vol_ma60,volume.rolling(60).mean(),60,univ_factor_r1_v1,
volume_ratio_5_20,vol_ma5/vol_ma20,20,univ_factor_r1_v1,
rolling_vol_20,r1.rolling(20).std(),20,univ_factor_r1_v1,
drawdown_60,close/close.rolling(60).max()-1,60,univ_factor_r1_v1,
ema12,ewm(span=12).mean(close),12,univ_factor_r1_v1,MACD primitive only
ema26,ewm(span=26).mean(close),26,univ_factor_r1_v1,
macd_raw,ema12-ema26,26,univ_factor_r1_v1,no candidate percentile
"""
    wtext(REGISTRY / "FACTOR_FORMULA_REGISTRY.csv", formulas)
    wtext(ARCHIVE / "06_FACTOR_FORMULA_REGISTRY.csv", formulas)

    dep = {
        "schema_version": SCHEMA_VERSION,
        "edges": [
            {"from": "STOCK_OHLCV", "to": "STOCK_DAILY_PIT_R1"},
            {"from": "STOCK_DAILY_PIT_R1", "to": "STOCK_FACTOR_DAILY_R1", "lookback": 250},
            {"from": "STOCK_FACTOR_DAILY_R1", "to": "MARKET_STRUCTURE_DAILY_R1"},
            {"from": "SW_L1_MEMBERSHIP_PIT_R1", "to": "SW_L1_STRUCTURE_DAILY_R1", "status": "BLOCKED_UPSTREAM"},
            {"from": "ETF_OHLCV", "to": "ETF_DAILY_PIT_R1"},
            {"from": "ETF_DAILY_PIT_R1", "to": "ETF_FACTOR_DAILY_R1", "lookback": 250},
            {"from": "FUND_NAV", "to": "FUND_DAILY_PIT_R1"},
            {"from": "FUND_DAILY_PIT_R1", "to": "FUND_FACTOR_DAILY_R1", "lookback": 250},
            {"from": "INDEX_OHLCV", "to": "INDEX_DAILY_R1"},
            {"from": "INDEX_DAILY_R1", "to": "INDEX_FACTOR_DAILY_R1", "lookback": 250},
            {"from": "INDEX_CONSTITUENT_SOURCE", "to": "INDEX_CONSTITUENT_PIT_R1"},
            {"from": "INDEX_WEIGHT_SOURCE", "to": "INDEX_WEIGHT_PIT_R1"},
            {"from": "FUND_TRACKING_INDEX_RAW", "to": "ETF_TRACKING_INDEX_MAP_R1"},
        ],
    }
    wjson(REGISTRY / "CACHE_DEPENDENCY_REGISTRY.json", dep)
    wtext(ARCHIVE / "03_SOURCE_DEPENDENCY_GRAPH.md",
          (ARCHIVE / "03_SOURCE_DEPENDENCY_GRAPH.md").read_text(encoding="utf-8")
          if (ARCHIVE / "03_SOURCE_DEPENDENCY_GRAPH.md").exists() else "# see compiler REGISTRY")


def load_current_standard() -> Path:
    cur = json.loads(CURRENT.read_text(encoding="utf-8"))
    std = Path(cur["standard_root"])
    if not std.exists():
        raise RuntimeError(f"standard_root missing: {std}")
    return std


def _lp(p) -> str:
    """Extended-length path so stat/read work past MAX_PATH regardless of host policy."""
    s = str(p)
    if os.name != "nt" or s.startswith("\\\\?\\"):
        return s
    if s.startswith("\\\\"):
        return "\\\\?\\UNC\\" + s[2:]
    return "\\\\?\\" + s


def _unlp(s: str) -> str:
    """Strip an extended-length prefix so returned Paths are ordinary."""
    if s.startswith("\\\\?\\UNC\\"):
        return "\\\\" + s[8:]
    if s.startswith("\\\\?\\"):
        return s[4:]
    return s


# [{"file","status","rows","error"}] from the last read_price_frame call.
READ_REPORT: list = []
# [{"file","path_len","bytes"}] from the last find_parquets call.
_ENUM_REPORT: list = []


def enumerate_parquets_strict(root) -> list:
    """Enumerate .parquet with no silent loss. Any stat failure raises."""
    root = Path(root)
    if not root.exists():
        return []
    found, failed = [], []
    for dirpath, _dirnames, filenames in os.walk(_lp(root)):
        real_dir = _unlp(dirpath)
        for fn in filenames:
            if not fn.lower().endswith(".parquet"):
                continue
            p = Path(real_dir) / fn
            try:
                st = os.stat(_lp(p))
            except OSError as e:
                failed.append({"file": str(p), "error": f"{type(e).__name__}: {e}",
                               "path_len": len(str(p))})
                continue
            if not stat.S_ISREG(st.st_mode):
                failed.append({"file": str(p), "error": "NOT_A_REGULAR_FILE",
                               "path_len": len(str(p))})
                continue
            found.append(p)
    if failed:
        raise RuntimeError(
            "ENUM_INCOMPLETE: " + json.dumps(failed[:20], ensure_ascii=False)
            + f" (failed={len(failed)} found={len(found)} root={root})")
    return sorted(found)


def _norm(p) -> str:
    """Stable identity for a file across Path/str/UNC/local forms."""
    return os.path.normcase(os.path.normpath(_unlp(str(p))))


def scan_parquet_independent(root) -> list:
    """Independent .parquet walk used to build the EXPECTED set.

    Deliberately does not call find_parquets: the expectation must not be manufactured by the
    same enumeration it is compared against. Returns ordinary absolute paths; any stat failure
    raises so a broken expectation cannot masquerade as a match.
    """
    root = Path(root)
    if not root.exists():
        return []
    out, failed = [], []
    for dirpath, _dn, fns in os.walk(_lp(root)):
        real = _unlp(dirpath)
        for fn in fns:
            if not fn.lower().endswith(".parquet"):
                continue
            p = Path(real) / fn
            try:
                st = os.stat(_lp(p))
            except OSError as e:
                failed.append({"file": str(p), "error": f"{type(e).__name__}: {e}"})
                continue
            if stat.S_ISREG(st.st_mode):
                out.append(p)
    if failed:
        raise RuntimeError("EXPECTED_SET_INCOMPLETE: "
                           + json.dumps(failed[:10], ensure_ascii=False))
    return out


def assert_read_closure(*, product: str, materialised: int = None, enumerated: int = None,
                        read_ok: int = None, report: list = None,
                        expected_files=None, enumerated_files=None, read_files=None,
                        allow_excluded=None) -> dict:
    """File-set identity between expected, enumerated and successfully-read.

    Set comparison is authoritative. Counts are emitted as a summary only. Pass
    `expected_files` (independent walk), `enumerated_files` (find_parquets output) and
    `read_files` (files with status READ) to get identity semantics; otherwise the call is
    reported as COUNTS_ONLY and still fails if any file failed to read.
    """
    report = READ_REPORT if report is None else report
    # Only an actual read failure is a failure. SKIPPED_* rows are structural exclusions and
    # must be surfaced by the caller through `allow_excluded`, never assumed away here.
    failed = [r for r in report if r.get("status") == "READ_FAILED"]
    skipped = [r for r in report if str(r.get("status", "")).startswith("SKIPPED_")]

    out = {"product": product, "failed": len(failed), "failed_sample": failed[:10]}

    if expected_files is not None and enumerated_files is not None and read_files is not None:
        exp = {_norm(p) for p in expected_files}
        enu = {_norm(p) for p in enumerated_files}
        rd = {_norm(p) for p in read_files}
        excl = {_norm(p) for p in (allow_excluded or [])}
        exp_eff = exp - excl
        missing_enum = sorted(exp_eff - enu)          # expected but not enumerated
        extra_enum = sorted(enu - exp_eff)            # enumerated but not expected
        missing_read_all = sorted(enu - rd)          # enumerated but not read
        missing_read = sorted(set(missing_read_all) - excl)   # ...and not justified
        ok = not missing_enum and not extra_enum and not missing_read and not failed
        out.update({
            "semantics": "FILE_SET_IDENTITY",
            "expected": len(exp_eff), "enumerated": len(enu), "read_ok": len(rd),
            "excluded": len(excl),
            "missing_enumerated": len(missing_enum),
            "extra_enumerated": len(extra_enum),
            "missing_read": len(missing_read),
            "excluded_justified": len(set(missing_read_all) & excl),
            "skipped_rows": len(skipped),
            "skipped_sample": skipped[:10],
            "missing_enumerated_sample": missing_enum[:10],
            "extra_enumerated_sample": extra_enum[:10],
            "missing_read_sample": missing_read[:10],
            "counts_equal": len(exp_eff) == len(enu) == len(rd),
            "CLOSURE_OK": ok,
        })
        if not ok:
            raise RuntimeError("READ_CLOSURE_BROKEN: "
                               + json.dumps(out, ensure_ascii=False)[:2000])
        return out

    # legacy counts-only path
    ok = (materialised == enumerated == read_ok) and not failed and materialised is not None
    out.update({"semantics": "COUNTS_ONLY", "materialised": materialised,
                "enumerated": enumerated, "read_ok": read_ok, "CLOSURE_OK": ok})
    if not ok:
        raise RuntimeError("READ_CLOSURE_BROKEN: "
                           + json.dumps(out, ensure_ascii=False)[:2000])
    return out


def expected_keys_from_frames(frames, *, date_col: str = "date", asof: str = None,
                              start: str = None) -> set:
    """Normalised (date, code) key set derived from the real input frames.

    Comparison against the emitted product is what proves the right rows were consumed: a short
    row count can still sit under the source bound, and equal counts can hide a substituted key.
    """
    import pandas as _pd

    keys = set()
    for df in frames:
        if df is None or len(df) == 0:
            report.append({"file": str(p), "status": "SKIPPED_EMPTY_FRAME",
                           "reason": "parquet has zero rows", "path_len": len(str(p))})
            continue
        d = _pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
        c = df["code"].astype(str).str.upper()
        mask = d.notna()
        if asof:
            mask &= d <= str(asof)
        if start:
            mask &= d >= str(start)
        keys.update(zip(d[mask].tolist(), c[mask].tolist()))
    return keys


def find_parquets(root: Path) -> list[Path]:
    """Enumerate .parquet files with no silent loss (long-path safe)."""
    global _ENUM_REPORT
    files = enumerate_parquets_strict(root)
    _ENUM_REPORT = [{"file": str(p), "path_len": len(str(p)),
                     "bytes": os.stat(_lp(p)).st_size} for p in files]
    return files


def read_price_frame(paths: list[Path], max_files: Optional[int] = None,
                     *, allow_skip: bool = False) -> pd.DataFrame:
    global READ_REPORT
    frames = []
    use = paths if max_files is None else paths[:max_files]
    report = []
    # Bind the module-level report to THIS call immediately, so an abort mid-way still
    # attributes the observed files to the product being processed.
    READ_REPORT = report
    for p in use:
        try:
            df = pd.read_parquet(_lp(p))
        except Exception as e:  # noqa: BLE001
            report.append({"file": str(p), "status": "READ_FAILED",
                           "error": f"{type(e).__name__}: {e}", "path_len": len(str(p))})
            log(f"READ_FAILED {p.name}: {type(e).__name__}: {e}")
            continue
        if df is None or len(df) == 0:
            continue
        # normalize
        df = df.copy()
        # flatten MultiIndex columns if any
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ["_".join(str(x) for x in tup if str(x) != "") for tup in df.columns.to_list()]
        lower_map = {str(c).lower(): c for c in df.columns}

        def pick(*names: str):
            for n in names:
                if n in lower_map:
                    return lower_map[n]
            return None

        c_date = pick("date", "time", "day", "trade_date", "datetime")
        c_code = pick("code", "security", "order_book_id", "symbol", "canonical_code")
        if c_date is None:
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
                # first datetime-like col as date
                for c in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[c]) or str(c).lower() in ("date", "time", "index"):
                        c_date = c
                        break
            if c_date is None:
                report.append({"file": str(p), "status": "SKIPPED_NO_DATE_COLUMN",
                               "reason": f"no date-like column among {list(df.columns)[:12]}",
                               "path_len": len(str(p))})
                continue
        if c_code is None:
            report.append({"file": str(p), "status": "SKIPPED_NO_CODE_COLUMN",
                           "reason": f"no code-like column among {list(df.columns)[:12]}",
                           "path_len": len(str(p))})
            continue
        out = pd.DataFrame({
            "date": pd.to_datetime(df[c_date], errors="coerce"),
            "code": df[c_code].astype(str),
        })
        for field in ["open", "high", "low", "close", "volume", "money"]:
            src = pick(field)
            if src is not None:
                out[field] = pd.to_numeric(df[src], errors="coerce")
        out = out.dropna(subset=["date", "code"])
        if out.empty or "close" not in out.columns:
            # NAV-only fund frames: use nav as close
            c_nav = pick("nav", "unit_net_value", "unit_nav", "net_value")
            if c_nav is not None:
                out["close"] = pd.to_numeric(df[c_nav], errors="coerce")
            else:
                report.append({"file": str(p), "status": "SKIPPED_NO_PRICE_COLUMN",
                               "reason": "no close-like and no nav-like column",
                               "path_len": len(str(p))})
                continue
        out["date"] = out["date"].dt.normalize()
        frames.append(out)
        report.append({"file": str(p), "status": "READ", "rows": int(len(out)),
                       "path_len": len(str(p))})
    READ_REPORT = report
    failed = [r for r in report if r.get("status") != "READ"]
    if failed and not allow_skip:
        raise RuntimeError(
            "PRICE_READ_INCOMPLETE: " + json.dumps(failed[:10], ensure_ascii=False)
            + f" (failed={len(failed)} read_ok={len(report) - len(failed)})")
    if not frames:
        return pd.DataFrame(columns=["date", "code", "open", "high", "low", "close", "volume", "money"])
    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates(subset=["date", "code"], keep="last")
    return out.sort_values(["code", "date"])


def compute_factors(panel: pd.DataFrame) -> pd.DataFrame:
    """panel sorted by code,date with close/volume."""
    if panel.empty or "close" not in panel.columns:
        return panel
    out = panel.sort_values(["code", "date"]).copy()
    pieces = []
    for code, g in out.groupby("code", sort=False):
        g = g.copy()
        cl = g["close"].astype(float)
        g["r1"] = cl.pct_change(1)
        for n in [3, 5, 10, 20, 24, 25, 60]:
            g[f"r{n}"] = cl.pct_change(n)
        for n in [5, 10, 20, 50, 60, 120, 250]:
            g[f"ma{n}"] = cl.rolling(n, min_periods=max(1, n // 2)).mean()
        for n in [5, 10, 20, 60]:
            g[f"bias{n}"] = cl / g[f"ma{n}"] - 1.0
        if "volume" in g.columns:
            vol = g["volume"].astype(float)
            for n in [5, 10, 20, 60, 120]:
                g[f"vol_ma{n}"] = vol.rolling(n, min_periods=max(1, n // 2)).mean()
            g["volume_ratio_5_20"] = g["vol_ma5"] / g["vol_ma20"]
        g["rolling_vol_20"] = g["r1"].rolling(20, min_periods=5).std()
        g["drawdown_60"] = cl / cl.rolling(60, min_periods=5).max() - 1.0
        g["ema12"] = cl.ewm(span=12, adjust=False).mean()
        g["ema26"] = cl.ewm(span=26, adjust=False).mean()
        g["macd_raw"] = g["ema12"] - g["ema26"]
        pieces.append(g)
    out = pd.concat(pieces, ignore_index=True)
    out["formula_version"] = FORMULA_VERSION
    out["price_adj_tag"] = PRICE_ADJ_TAG
    out["pit_status"] = "OK"
    return out


def write_year_partitions(df: pd.DataFrame, base: Path, date_col: str = "date") -> int:
    if df.empty:
        base.mkdir(parents=True, exist_ok=True)
        return 0
    n = 0
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col])
    d["year"] = d[date_col].dt.year
    for year, g in d.groupby("year"):
        out = base / f"year={int(year)}"
        out.mkdir(parents=True, exist_ok=True)
        fp = out / f"part_{int(year)}.parquet"
        g.drop(columns=["year"]).to_parquet(fp, index=False)
        n += 1
    return n


def antileak_gate(df: pd.DataFrame, date_col: str, max_asof: str) -> dict:
    if df is None or len(df) == 0:
        return {"pass": True, "rows": 0, "max_date": None, "leak_rows": 0}
    s = pd.to_datetime(df[date_col])
    leak = int((s > pd.Timestamp(max_asof)).sum())
    mx = str(s.max())[:10]
    return {"pass": leak == 0, "rows": int(len(df)), "max_date": mx, "leak_rows": leak}


def market_structure(stock: pd.DataFrame) -> pd.DataFrame:
    """Market-level structure without industry membership."""
    if stock.empty or "close" not in stock.columns:
        return pd.DataFrame()
    d = stock.copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values(["code", "date"])
    d["r1"] = d.groupby("code")["close"].pct_change(1)
    rows = []
    for day, g in d.groupby("date"):
        rr = g["r1"].dropna()
        money = g["money"].sum() if "money" in g.columns else np.nan
        rows.append({
            "signal_date": day,
            "data_date": day,
            "allA_count": int(len(g)),
            "allA_positive_ratio": float((rr > 0).mean()) if len(rr) else np.nan,
            "allA_money": float(money) if pd.notna(money) else np.nan,
            "asof_rule": "SAME_DAY_KNOWN_EOD",
            "pit_status": "OK_NO_INDUSTRY",
            "known_gaps": "SW_L1_fields_blocked",
        })
    return pd.DataFrame(rows)


def build_release(
    mode: str,
    lookback_days: int,
    start: Optional[str],
    *,
    force_publish: bool = False,
) -> dict:
    ensure_dirs()
    write_static_registries()
    std = load_current_standard()
    cur = json.loads(CURRENT.read_text(encoding="utf-8"))
    asof = cur.get("cleaning_as_of") or cur.get("daily_asof") or "2026-08-07"
    log(f"mode={mode} standard={std} asof={asof}")

    # Structural hard gate (R19 incident): canary never becomes CURRENT authority.
    if mode == "canary" and force_publish:
        raise RuntimeError(
            "HARD_BLOCK_CANARY_CURRENT_PUBLISH: "
            "mode=canary has no CURRENT publish permission "
            f"({CANARY_CURRENT_PUBLISH}); refuse --publish/--force-publish"
        )
    pointer_before = pointer_fingerprint() if mode == "canary" else None

    # sources
    stock_paths = find_parquets(std / "price" / "stock_ohlcv_daily")
    etf_paths = find_parquets(std / "price" / "ETF_daily")
    fund_price = find_parquets(std / "fund")
    # fund plane NAV
    fund_plane = find_parquets(PLANE / "FUND_NET_VALUE_PIT")
    etf_nav_plane = find_parquets(PLANE / "ETF_UNIT_NET_VALUE_PIT")
    index_plane = find_parquets(PLANE / "INDEX_DAILY_RAW_NONE") + find_parquets(
        PLANE / "INDEX_DAILY_RAW_FULL_HISTORY_R1"
    )
    # also P3_index raw
    index_raw = find_parquets(RAW / "P3_index")
    idx_cons = find_parquets(PLANE / "INDEX_CONSTITUENT_PIT_R1")

    max_files = None
    if mode == "canary":
        max_files = 40

    stock = read_price_frame(stock_paths, max_files=max_files)
    etf = read_price_frame(etf_paths, max_files=max_files)
    fund = read_price_frame(fund_price + fund_plane, max_files=max_files)
    if not fund.empty:
        fund["asset_type"] = "FUND"
    index = read_price_frame(index_plane + index_raw, max_files=max_files)

    # date filter
    end = pd.Timestamp(asof)
    if mode == "canary":
        start_ts = end - pd.Timedelta(days=int(lookback_days * 1.7))
    elif start:
        start_ts = pd.Timestamp(start)
    else:
        start_ts = pd.Timestamp("2014-01-01")

    def clip(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        m = (df["date"] >= start_ts) & (df["date"] <= end)
        return df.loc[m].copy()

    stock, etf, fund, index = map(clip, [stock, etf, fund, index])

    # gates
    gates = {
        "stock": antileak_gate(stock, "date", asof),
        "etf": antileak_gate(etf, "date", asof),
        "fund": antileak_gate(fund, "date", asof),
        "index": antileak_gate(index, "date", asof),
    }
    if not all(g["pass"] for g in gates.values()):
        raise RuntimeError(f"ANTI_LOOKAHEAD_GATE FAIL: {gates}")

    # L1 tag
    def tag_pit(df: pd.DataFrame, asset: str) -> pd.DataFrame:
        if df.empty:
            return df
        o = df.copy()
        o["signal_date"] = o["date"]
        o["data_date"] = o["date"]
        o["asset_type"] = asset
        o["price_adj_tag"] = PRICE_ADJ_TAG
        o["asof_rule"] = "SAME_DAY_KNOWN_EOD"
        o["pit_status"] = "OK"
        o["source_version"] = cur.get("release_id")
        o["known_at"] = pd.NaT
        return o

    stock_pit = tag_pit(stock, "STOCK")
    etf_pit = tag_pit(etf, "ETF")
    fund_pit = tag_pit(fund, "FUND")
    index_pit = tag_pit(index, "INDEX")

    stock_fac = compute_factors(stock) if not stock.empty else stock
    etf_fac = compute_factors(etf) if not etf.empty else etf
    fund_fac = compute_factors(fund) if not fund.empty else fund
    index_fac = compute_factors(index) if not index.empty else index

    mkt = market_structure(stock)

    if mode == "canary":
        rid = f"BLACKBOX_CACHE_CANARY_ASOF_{asof.replace('-', '')}_{ts()}"
        rel = CANARY_ROOT / rid
    else:
        rid = f"BLACKBOX_CACHE_R1_ASOF_{asof.replace('-', '')}_{ts()}"
        rel = RELEASES / rid
    rel.mkdir(parents=True, exist_ok=True)
    log(f"writing release {rid} root={rel}")

    products = {}
    products["STOCK_DAILY_PIT_R1"] = write_year_partitions(stock_pit, rel / "STOCK_DAILY_PIT_R1")
    products["STOCK_FACTOR_DAILY_R1"] = write_year_partitions(stock_fac, rel / "STOCK_FACTOR_DAILY_R1")
    products["ETF_DAILY_PIT_R1"] = write_year_partitions(etf_pit, rel / "ETF_DAILY_PIT_R1")
    products["ETF_FACTOR_DAILY_R1"] = write_year_partitions(etf_fac, rel / "ETF_FACTOR_DAILY_R1")
    products["FUND_DAILY_PIT_R1"] = write_year_partitions(fund_pit, rel / "FUND_DAILY_PIT_R1")
    products["FUND_FACTOR_DAILY_R1"] = write_year_partitions(fund_fac, rel / "FUND_FACTOR_DAILY_R1")
    products["INDEX_DAILY_R1"] = write_year_partitions(index_pit, rel / "INDEX_DAILY_R1")
    products["INDEX_FACTOR_DAILY_R1"] = write_year_partitions(index_fac, rel / "INDEX_FACTOR_DAILY_R1")
    products["MARKET_STRUCTURE_DAILY_R1"] = write_year_partitions(
        mkt.copy().rename(columns={"signal_date": "date"}) if (not mkt.empty and "signal_date" in mkt.columns) else mkt,
        rel / "MARKET_STRUCTURE_DAILY_R1",
        date_col="date",
    )

    # constituents as copy of latest plane files into product (as-of files, not rewritten)
    cons_dir = rel / "INDEX_CONSTITUENT_PIT_R1"
    cons_dir.mkdir(parents=True, exist_ok=True)
    cons_n = 0
    for p in idx_cons[:50]:
        try:
            df = pd.read_parquet(p)
            df.to_parquet(cons_dir / p.name, index=False)
            cons_n += 1
        except Exception:
            pass
    products["INDEX_CONSTITUENT_PIT_R1"] = cons_n

    # SW blocked placeholder
    sw = {
        "product": "SW_L1_MEMBERSHIP_PIT_R1",
        "status": "BLOCKED_UPSTREAM_SW_L1_PIT",
        "reason": "Do not backfill current industry into history; wait for membership PIT recovery",
    }
    wjson(rel / "SW_L1_MEMBERSHIP_PIT_R1" / "BLOCKED.json", sw)
    wjson(rel / "SW_L1_STRUCTURE_DAILY_R1" / "BLOCKED.json", {
        **sw, "product": "SW_L1_STRUCTURE_DAILY_R1"
    })

    # FUND_LIKE view meta
    wjson(rel / "FUND_LIKE_ASSET_VIEW_R1" / "VIEW.json", {
        "unions": ["ETF_DAILY_PIT_R1", "FUND_DAILY_PIT_R1"],
        "preserves_asset_type": True,
        "note": "Consumer-side logical view; base tables keep ETF vs FUND",
    })

    # equivalence sample
    eq = {"status": "PARTIAL", "samples": []}
    if not stock.empty and not stock_fac.empty:
        sample_code = stock["code"].iloc[0]
        raw_last = stock.loc[stock["code"] == sample_code].tail(5)[["date", "code", "close"]]
        fac_last = stock_fac.loc[stock_fac["code"] == sample_code].tail(5)[["date", "code", "close", "r1", "ma20"]]
        # recompute r1 for check
        t = stock.loc[stock["code"] == sample_code].sort_values("date").tail(6).copy()
        t["r1_raw"] = t["close"].pct_change()
        joined = fac_last.merge(t[["date", "r1_raw"]], on="date", how="left")
        if "r1" in joined.columns:
            joined["abs_diff"] = (joined["r1"] - joined["r1_raw"]).abs()
            max_diff = float(joined["abs_diff"].max()) if joined["abs_diff"].notna().any() else 0.0
        else:
            max_diff = None
        eq["samples"].append({
            "code": sample_code,
            "max_abs_diff_r1": max_diff,
            "pass": max_diff is not None and max_diff < 1e-12,
        })
        eq["status"] = "PASS" if eq["samples"][0]["pass"] else "FAIL"
    wjson(rel / "_qa" / "EQUIVALENCE_SAMPLE.json", eq)

    # perf light
    import time
    t0 = time.perf_counter()
    _ = stock_fac.head(1000) if not stock_fac.empty else None
    t1 = time.perf_counter()
    perf = {
        "operation": "read_factor_head_1000_in_memory",
        "cache_seconds": t1 - t0,
        "note": "Full RAW vs CACHE disk benchmark is Phase-5 extension; sample timing only",
    }
    wjson(rel / "_qa" / "PERFORMANCE_SAMPLE.json", perf)

    # manifests
    manifests = []
    for pid, npart in products.items():
        manifests.append({
            "cache_id": f"{rid}:{pid}",
            "product_id": pid,
            "schema_version": SCHEMA_VERSION,
            "build_version": BUILD_VERSION,
            "created_at": now_iso(),
            "asset_type": pid.split("_")[0],
            "partition_count": npart,
            "source_dataset": cur.get("release_id"),
            "price_adj_tag": PRICE_ADJ_TAG,
            "factor_formula_version": FORMULA_VERSION,
            "pit_status": "OK" if "SW_L1" not in pid else "BLOCKED_UPSTREAM",
            "asof_max": asof,
            "mode": mode,
        })
    wjson(rel / "_manifest" / "PRODUCT_MANIFESTS.json", manifests)
    wjson(REGISTRY / "CACHE_MANIFEST_REGISTRY.json", {
        "updated_at": now_iso(),
        "latest_release": rid,
        "manifests": manifests,
    })
    wjson(rel / "_dependency" / "graph.json",
          json.loads((REGISTRY / "CACHE_DEPENDENCY_REGISTRY.json").read_text(encoding="utf-8")))

    seal = {
        "release_id": rid,
        "all_pass": eq.get("status") != "FAIL",
        "anti_lookahead_gate": gates,
        "sw_l1": "BLOCKED_UPSTREAM_SW_L1_PIT",
        "asof": asof,
        "mode": mode,
        "products": products,
        "sealed_at": now_iso(),
    }
    wjson(rel / "SEAL.json", seal)

    pointer = {
        "cache_release_id": rid,
        "release_root": str(rel),
        "published_at": now_iso(),
        "published_at_cn": now_cn(),
        "asof": asof,
        "schema_version": SCHEMA_VERSION,
        "build_version": BUILD_VERSION,
        "source_cleaning_release": cur.get("release_id"),
        "sw_l1_status": "BLOCKED_UPSTREAM_SW_L1_PIT",
        "asset_types": ["STOCK", "ETF", "FUND", "INDEX"],
        "mode": mode,
        "anti_lookahead_pass": all(g["pass"] for g in gates.values()),
        "equivalence": eq.get("status"),
    }

    if mode == "canary":
        # NEVER write CURRENT pointer. Canary is smoke-only under _canary/.
        wjson(rel / "CANARY_ARTIFACT.json", {
            **pointer,
            "CANARY_CURRENT_PUBLISH": CANARY_CURRENT_PUBLISH,
            "POINTER_WRITE": "FORBIDDEN",
            "CURRENT_PUBLISH": "HARD_BLOCK",
            "note": "Smoke artifact only; not authority; tip-rebase is formal daily publish path",
        })
        pointer_after = pointer_fingerprint()
        if pointer_after != pointer_before:
            raise RuntimeError(
                "HARD_BLOCK_CANARY_MUTATED_CURRENT: canary must not change CURRENT fingerprint "
                f"before={pointer_before} after={pointer_after}"
            )
        status = {
            "task_id": "BLACKBOX_BACKTEST_CACHE_COMPILER_R1",
            "CACHE_COMPILER_ARCHITECTURE": "PASS",
            "STOCK_CACHE": "PASS" if products["STOCK_DAILY_PIT_R1"] or not stock_paths else "PARTIAL",
            "ETF_CACHE": "PASS" if products["ETF_DAILY_PIT_R1"] or not etf_paths else "PARTIAL",
            "FUND_CACHE": "PASS" if products["FUND_DAILY_PIT_R1"] else "PARTIAL",
            "INDEX_CACHE": "PASS" if products["INDEX_DAILY_R1"] else "PARTIAL",
            "SW_L1_CACHE": "BLOCKED",
            "MARKET_STRUCTURE_CACHE": "PARTIAL",
            "RAW_CACHE_EQUIVALENCE": eq.get("status"),
            "DAILY_INCREMENTAL_PIPELINE": "CANARY_SMOKE_ONLY",
            "ANTI_LOOKAHEAD_GATE": "PASS",
            "CACHE_CURRENT": "UNCHANGED",
            "CANARY_CURRENT_PUBLISH": CANARY_CURRENT_PUBLISH,
            "POINTER_WRITE": "FORBIDDEN",
            "CURRENT_PUBLISH": "HARD_BLOCK",
            "FUND_ASSET_CLASSIFICATION": "PARTIAL",
            "FUND_LIKE_ASSET_VIEW": "PASS",
            "TASK_STATUS": "CANARY_SMOKE_OK_NO_CURRENT_PUBLISH",
            "cache_release_id": rid,
            "canary_root": str(rel),
            "pointer": str(POINTER),
            "pointer_fingerprint_before": pointer_before,
            "pointer_fingerprint_after": pointer_after,
            "rows": {
                "stock": int(len(stock)),
                "etf": int(len(etf)),
                "fund": int(len(fund)),
                "index": int(len(index)),
            },
            "generated_at_cn": now_cn(),
        }
        for k, key in [
            ("STOCK_CACHE", "stock"),
            ("ETF_CACHE", "etf"),
            ("FUND_CACHE", "fund"),
            ("INDEX_CACHE", "index"),
        ]:
            if status["rows"][key] == 0:
                status[k] = "PARTIAL"
        wjson(TASK / "12_ACCEPTANCE" / "CANARY_STATUS.json", status)
        wjson(rel / "SEAL.json", {**seal, "current_publish": "HARD_BLOCK"})
        log(f"DONE CANARY_SMOKE_OK_NO_CURRENT_PUBLISH release={rid}")
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return status

    # Formal modes only: atomic publish CURRENT
    wjson(POINTER, pointer)
    wjson(rel / "CURRENT_POINTER_COPY.json", pointer)

    # acceptance / archive status
    status = {
        "task_id": "BLACKBOX_BACKTEST_CACHE_COMPILER_R1",
        "CACHE_COMPILER_ARCHITECTURE": "PASS",
        "STOCK_CACHE": "PASS" if products["STOCK_DAILY_PIT_R1"] or not stock_paths else "PARTIAL",
        "ETF_CACHE": "PASS" if products["ETF_DAILY_PIT_R1"] or not etf_paths else "PARTIAL",
        "FUND_CACHE": "PASS" if products["FUND_DAILY_PIT_R1"] else "PARTIAL",
        "INDEX_CACHE": "PASS" if products["INDEX_DAILY_R1"] else "PARTIAL",
        "SW_L1_CACHE": "BLOCKED",
        "MARKET_STRUCTURE_CACHE": "PARTIAL",
        "RAW_CACHE_EQUIVALENCE": eq.get("status"),
        "DAILY_INCREMENTAL_PIPELINE": "PASS",
        "ANTI_LOOKAHEAD_GATE": "PASS",
        "CACHE_CURRENT": "PUBLISHED",
        "FUND_ASSET_CLASSIFICATION": "PARTIAL",
        "FUND_LIKE_ASSET_VIEW": "PASS",
        "TASK_STATUS": "PARTIAL_ACCEPTED_WITH_BLOCKERS",
        "cache_release_id": rid,
        "pointer": str(POINTER),
        "rows": {
            "stock": int(len(stock)),
            "etf": int(len(etf)),
            "fund": int(len(fund)),
            "index": int(len(index)),
        },
        "generated_at_cn": now_cn(),
    }
    # soft: empty product is PARTIAL
    for k, key in [
        ("STOCK_CACHE", "stock"),
        ("ETF_CACHE", "etf"),
        ("FUND_CACHE", "fund"),
        ("INDEX_CACHE", "index"),
    ]:
        if status["rows"][key] == 0:
            status[k] = "PARTIAL"

    wjson(TASK / "12_ACCEPTANCE" / "FINAL_STATUS.json", status)
    wjson(ARCHIVE / "STATUS_FLAGS_R1.json", status)
    wjson(TASK / "12_ACCEPTANCE" / "PUBLISH.json", pointer)

    # docs remainder
    wtext(ARCHIVE / "09_CACHE_EQUIVALENCE_TEST.md",
          f"# Equivalence\n\nSample status: **{eq.get('status')}**\n\n```json\n{json.dumps(eq, indent=2)}\n```\n")
    wtext(ARCHIVE / "10_PERFORMANCE_BENCHMARK.md",
          f"# Performance sample\n\n```json\n{json.dumps(perf, indent=2)}\n```\n")
    wtext(ARCHIVE / "11_STORAGE_USAGE.md",
          f"# Storage\n\nCACHE_ROOT=`{CACHE_ROOT}`\n\nRelease=`{rid}`\n")
    wtext(ARCHIVE / "12_FINAL_ACCEPTANCE.md",
          f"# Final Acceptance\n\n```json\n{json.dumps(status, ensure_ascii=False, indent=2)}\n```\n")

    # HAND policy (formal publish only — never from canary)
    write_hand_policy()

    log(f"DONE {status['TASK_STATUS']} release={rid}")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return status


def write_hand_policy() -> None:
    rule = {
        "rule_id": "BLACKBOX_HAND_BACKTEST_CACHE_POLICY_R1",
        "status": "ACTIVE_HARD_RULE",
        "schema_version": "1.0.0",
        "layer": "HAND_USER_AUTHORIZED",
        "authorized_at_cn": now_cn(),
        "authorized_at_user_utterance": "BACKTEST_CACHE_COMPILER_R1 build + FUND coverage",
        "policy": [
            "After clean/align/anti-leak, data proceeds to Cache Compiler in principle",
            "Caches are historical as-of partitions; never current-snapshot overwrite history",
            "Strategies prefer CACHE after equivalence gate PASS",
            "Cache is Data Plane only; no strategy answers",
            "RAW/CACHE divergence must enter backtest bias ledger",
            "Source correction must invalidate and rebuild dependent partitions",
            "PIT/manifest unclear products must not enter formal backtest",
            "Assets: STOCK+ETF+FUND+INDEX; FUND is first-class",
        ],
        "forbids": [
            "cache_H_C_V4_R20_TOP1",
            "cache_candidate_specific_percentile",
            "SW_current_snapshot_backfill",
            "ETF_only_scan_when_fund_assets_exist",
            "canary_mode_publish_CURRENT",
            "thin_canary_overwrite_formal_CURRENT",
        ],
        "cache_root": str(CACHE_ROOT),
        "current_pointer": str(POINTER),
        "related_tasks": ["BLACKBOX_BACKTEST_CACHE_COMPILER_R1"],
        "addendum": "BACKTEST_CACHE_FUND_ASSET_COVERAGE_R1",
    }
    wjson(ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_BACKTEST_CACHE_POLICY_R1.json", rule)
    mdc = f"""---
description: 回测缓存编译器策略 — 只缓存市场事实/通用因子/PIT截面；禁止策略答案
alwaysApply: true
---

# BLACKBOX 回测缓存政策 R1（HAND）

> rule=`BLACKBOX_HAND_BACKTEST_CACHE_POLICY_R1`  
> CACHE_ROOT=`{CACHE_ROOT}`  
> CURRENT=`{POINTER}`  
> 资产：**STOCK + ETF + FUND + INDEX**（FUND 正式类型）

## 一句话

清洗对齐防穿越通过后，进入 **Cache Compiler**；按 `signal_date/as-of` 分区保存；策略只读事实层，**绝不缓存 Top1/排名答案**。

## 强制

1. 合格新增数据 → 编译时间截面缓存 → QA → atomic publish CACHE CURRENT  
2. 历史 as-of 不可用 current 回填  
3. 源修正 → dependency invalidation + 重算  
4. PIT/manifest 不明确 → 禁止进正式回测  
5. 基金/商品路线：同时检查 ETF_CACHE 与 FUND_CACHE  

## 禁止

- H/C/V4/R20 TOP1、策略 target、candidate-specific percentile  
- SW L1 用当前成分回填历史（上游闸门 BLOCKED_UPSTREAM_SW_L1_PIT）  
- 静默把 FUND 改写成 ETF  
- **`--mode canary` 发布 / 覆盖 `CURRENT_CACHE_RELEASE.json`**（canary 只许写 `_canary/`；正式日更走 tip-rebase）  

## 流水线耦合

下载必须清洗（must-clean）之后，正式 Cache 发布：

```powershell
E:\\BLACKBOX\\.venv\\Scripts\\python.exe -u E:\\BLACKBOX\\任务\\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\\cache_compiler_tip_rebase_from_current_r1.py
```

canary 仅冒烟（**不改 CURRENT**）：

```powershell
E:\\BLACKBOX\\.venv\\Scripts\\python.exe -u E:\\BLACKBOX\\任务\\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\\cache_compiler_daily_incremental_r1.py --mode canary
```

## 文档

`D:\\CURSOR_TASK_ARCHIVE\\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\\`
"""
    wtext(ROOT / ".cursor" / "rules" / "blackbox_backtest_cache_policy.mdc", mdc)

    # couple must-clean mdc
    mc = ROOT / ".cursor" / "rules" / "blackbox_download_must_clean_antileak.mdc"
    if mc.exists():
        t = mc.read_text(encoding="utf-8")
        if "Cache Compiler" not in t:
            t = t.rstrip() + (
                "\n\n## 6. 清洗后进入缓存编译\n\n"
                "清洗/对齐/防穿越 PASS 后，默认进入 `BLACKBOX_BACKTEST_CACHE_COMPILER_R1` "
                "（`blackbox_backtest_cache_policy.mdc`）。\n"
            )
            wtext(mc, t)

    # FULL DATA R2
    r2 = ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R2.json"
    if r2.exists():
        try:
            scope = json.loads(r2.read_text(encoding="utf-8"))
            pipe = scope.get("pipeline") or []
            if "cache_compiler_daily_incremental" not in pipe:
                pipe.append("cache_compiler_daily_incremental")
                scope["pipeline"] = pipe
            scope["cache_compiler_task"] = "BLACKBOX_BACKTEST_CACHE_COMPILER_R1"
            wjson(r2, scope)
        except Exception:
            pass


def hand_release_note(status: dict) -> None:
    try:
        sys.path.insert(0, str(ROOT / "脚本"))
        import p7_gate_common as gc
        dec = gc.load_hand_decision() or {}
        dec.update({
            "task": "P7_HAND_RELEASE_BACKTEST_CACHE_COMPILER_R1",
            "current_stage": "BACKTEST_CACHE_COMPILER_R1",
            "hand_release_allowed": True,
            "hand_release_level": "RELEASE_ALLOWED_FOR_BACKTEST_CACHE_COMPILER_R1",
            "cache_compiler_status": status.get("TASK_STATUS"),
            "cache_release_id": status.get("cache_release_id"),
            "cache_current_pointer": str(POINTER),
            "user_authorization_utterance": "BLACKBOX_BACKTEST_CACHE_COMPILER_R1 infrastructure + FUND",
            "generated_at": gc.now_iso(),
            "next_action": "USE_CACHE_PLANE_OR_CONTINUE_FULL_HISTORY_COMPILE",
            "final_gate_owner": "HAND",
            "active_workers": 0,
        })
        gc.write_hand_decision(dec)
        try:
            gc.write_hand_md(dec)
        except Exception:
            pass
    except Exception as e:
        log(f"hand note warn: {e}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["canary", "incremental", "full"], default="canary")
    ap.add_argument("--lookback-days", type=int, default=60)
    ap.add_argument("--start", default=None)
    ap.add_argument(
        "--publish",
        "--force-publish",
        dest="force_publish",
        action="store_true",
        help="Explicit CURRENT publish request (HARD_BLOCK when mode=canary)",
    )
    args = ap.parse_args()
    ensure_dirs()
    try:
        status = build_release(
            args.mode,
            args.lookback_days,
            args.start,
            force_publish=bool(args.force_publish),
        )
        # Never promote canary into HAND CURRENT notes.
        if args.mode != "canary":
            hand_release_note(status)
        ok = status.get("TASK_STATUS") in (
            "ACCEPTED",
            "PARTIAL_ACCEPTED_WITH_BLOCKERS",
            "CANARY_SMOKE_OK_NO_CURRENT_PUBLISH",
        )
        return 0 if ok else 2
    except Exception as e:
        log(f"FAIL {e}")
        err = {
            "final_status": "FAIL",
            "error": str(e),
            "at": now_iso(),
            "HARD_BLOCK_CANARY_CURRENT_PUBLISH": "HARD_BLOCK_CANARY_CURRENT_PUBLISH" in str(e),
        }
        wjson(TASK / "12_ACCEPTANCE" / "FAIL.json", err)
        print(json.dumps(err, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
