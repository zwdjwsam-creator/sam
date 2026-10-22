#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLACKBOX Tushare CBOND 5y PIT enrichment R2.

TASK_CLASS_USER = DATA,ACQUISITION,CLEANING,PIT,INTEGRATION
TASK_CLASS_MACHINE = DATA,ACQUISITION  (manifest has no CLEANING/PIT/INTEGRATION)
REDOWNLOAD_CB_DAILY = NO
MODIFY_STOCK_CURRENT = NO
Does not overwrite R1 RAW / CLEAN / CACHE files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from _base import ROOT, FAIL, OK, guarded_write_path, set_runtime_context, sha256_file, sha256_text, read_text
from blackbox_data_absence_gate_r1 import decide

CN = timezone(timedelta(hours=8))
TASK_CLASS = "DATA,ACQUISITION"
START = "20210816"
END = "20260814"
MAX_WORKERS = 8
QUERY_CAP = 2000
MIN_INTERVAL = 0.25
PROBE_LIMIT = 8
TOKEN_FILE = ROOT / "配置" / "secrets" / "已验证" / "Tushare_TOKEN.txt"
MANIFEST_PATH = ROOT / "契约" / "必读" / "MUST_READ_MANIFEST_CURRENT.json"
KERNEL_PATH = ROOT / ".cursor" / "rules" / "BLACKBOX_KERNEL_ALWAYS_APPLY.mdc"

TASK_DIR = ROOT / "任务" / "途施可转债五年数据面_R2"
RAW_ROOT = ROOT / "数据" / "原始只读" / "途施可转债官方原始_R2"
CLEAN_ROOT = ROOT / "数据" / "清洗成品" / "途施可转债清洗_R2"
CACHE_REL_ID = "BLACKBOX_CACHE_R2_途施可转债_ASOF_20260814_R1"
CACHE_ROOT = ROOT / "数据" / "回测缓存" / "releases" / CACHE_REL_ID
R1_REL_ID = "BLACKBOX_CACHE_R1_途施可转债_ASOF_20260814_R1"
R1_CACHE = ROOT / "数据" / "回测缓存" / "releases" / R1_REL_ID
R1_RAW = ROOT / "数据" / "原始只读" / "途施可转债官方原始_R1"
R1_CLEAN = ROOT / "数据" / "清洗成品" / "途施可转债清洗_R1"
CBOND_PTR_DIR = ROOT / "数据" / "回测缓存" / "可转债指针"
CBOND_PTR = CBOND_PTR_DIR / "CURRENT_CBOND_CACHE_RELEASE.json"
CATALOG_CSV = ROOT / "数据" / "回测缓存" / "registry" / "CACHE_PRODUCT_CATALOG.csv"
INDEX_PATH = ROOT / "运行" / "BLACKBOX_DATA_ACCESS_INDEX_CURRENT.json"
STOCK_CURRENT_PTR = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
HAND_PATH = ROOT / "HAND.txt"
HAND_RULE = ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_CBOND_PIT_ENRICHMENT_R2.json"
PIT_CAP_CURRENT = ROOT / "运行" / "BLACKBOX_CBOND_PIT_CAPABILITY_CURRENT.json"
RESOLVER_PY = ROOT / "脚本" / "blackbox_data_access_resolver_r1.py"
READER_R2 = ROOT / "脚本" / "blackbox_tushare_cbond_reader_r2.py"

SOURCE_VENDOR = "TUSHARE_PRO"
SCHEMA_COMPAT_TARGET = "JOINQUANT_CONBOND"
FIXED_BOND_TS = "123277.SZ"
FIXED_STK_TS = "300815.SZ"
FIXED_STK_JQ = "300815.XSHE"

CB_RATING_FIELDS = (
    "ts_code,ann_date,rating_date,rating_com_name,rating_way,rating_type,rating,rating_outlook"
)
CB_CALL_FIELDS = (
    "ts_code,call_type,is_call,ann_date,call_date,call_price,call_price_tax,"
    "call_vol,call_amount,payment_date,call_reg_date"
)
CB_SHARE_FIELDS = (
    "ts_code,bond_short_name,publish_date,end_date,issue_size,convert_price_initial,"
    "convert_price,convert_val,convert_vol,convert_ratio,acc_convert_val,acc_convert_vol,"
    "acc_convert_ratio,remain_size,total_shares"
)

STOCK_PRODUCTS = [
    "STOCK_DAILY_PIT_R1",
    "MARKET_UNIVERSE_PIT_R1",
    "VALUATION_PIT_R1",
    "FINANCIAL_INDICATOR_PIT_R1",
    "SW_L1_MEMBERSHIP_PIT_R1",
    "SW_L2_MEMBERSHIP_PIT_R1",
    "SW_L3_MEMBERSHIP_PIT_R1",
    "STOCK_DAILY_RAW_PIT_R1",
    "ADJUST_FACTOR_PIT_R1",
]

R1_PRODUCTS = [
    "TUSHARE_CBOND_BASIC_R1",
    "TUSHARE_CBOND_DAILY_MARKET_R1",
    "TUSHARE_CBOND_ISSUE_R1",
    "TUSHARE_CBOND_CALL_R1",
    "TUSHARE_CBOND_RATE_R1",
    "TUSHARE_CBOND_SHARE_R1",
    "TUSHARE_CBOND_STOCK_BRIDGE_R1",
    "TUSHARE_CBOND_BASIC_JQCOMPAT_R1",
    "TUSHARE_CBOND_DAILY_MARKET_JQCOMPAT_R1",
]


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S") + "+0800"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def ctx() -> None:
    set_runtime_context(
        task_dir=TASK_DIR,
        task_slug="途施可转债五年数据面_R2",
        task_type="DATA_ACQUISITION",
        exemption_paths=[
            str(TASK_DIR),
            str(RAW_ROOT),
            str(CLEAN_ROOT),
            str(CACHE_ROOT),
            str(CBOND_PTR_DIR),
            str(ROOT / "运行"),
            str(HAND_RULE),
            str(CATALOG_CSV),
            str(INDEX_PATH),
            str(RESOLVER_PY),
            str(HAND_PATH),
            str(READER_R2),
            str(PIT_CAP_CURRENT),
        ],
    )


def wjson(path: Path, obj: Any) -> None:
    guarded_write_path(path, json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n")


def wbytes(path: Path, data: bytes) -> None:
    guarded_write_path(path, data, mode="binary")


def df_to_parquet_bytes(df) -> bytes:
    buf = BytesIO()
    df.to_parquet(buf, index=False)
    return buf.getvalue()


def file_sha256(path: Path) -> str:
    if not path.is_file():
        return "MISSING"
    return sha256_file(path)


def ts_to_jq(code: Any) -> str | None:
    if code is None:
        return None
    s = str(code).strip()
    if not s or s.lower() in ("nan", "none"):
        return None
    if s.endswith(".SZ"):
        return s[:-3] + ".XSHE"
    if s.endswith(".SH"):
        return s[:-3] + ".XSHG"
    if s.endswith(".XSHE") or s.endswith(".XSHG"):
        return s
    return None


def ymd(v: Any) -> str | None:
    if v is None:
        return None
    try:
        if isinstance(v, float) and v != v:
            return None
    except Exception:
        pass
    s = str(v).strip().replace("-", "").replace("/", "")[:8]
    if len(s) != 8 or not s.isdigit():
        return None
    return s


def ymd_dash(v: Any) -> str | None:
    s = ymd(v)
    return None if not s else f"{s[:4]}-{s[4:6]}-{s[6:8]}"


class RateLimiter:
    def __init__(self, min_interval: float = MIN_INTERVAL):
        self.min_interval = min_interval
        self.base_interval = min_interval
        self.lock = threading.Lock()
        self.last = 0.0
        self.throttle_events = 0
        self.retry_count = 0
        self.in_flight: set[str] = set()
        self.max_workers_used = 1
        self._workers_seen = 0

    def mark_worker(self) -> None:
        with self.lock:
            self._workers_seen += 1
            self.max_workers_used = max(self.max_workers_used, min(MAX_WORKERS, self._workers_seen))

    def unmark_worker(self) -> None:
        with self.lock:
            self._workers_seen = max(0, self._workers_seen - 1)

    def acquire_key(self, key: str) -> bool:
        with self.lock:
            if key in self.in_flight:
                return False
            self.in_flight.add(key)
            return True

    def release_key(self, key: str) -> None:
        with self.lock:
            self.in_flight.discard(key)

    def wait(self) -> None:
        with self.lock:
            now = time.time()
            gap = self.min_interval - (now - self.last)
        if gap > 0:
            time.sleep(gap)
        with self.lock:
            self.last = time.time()

    def on_throttle(self) -> None:
        with self.lock:
            self.throttle_events += 1
            self.retry_count += 1
            self.min_interval = min(2.0, max(self.min_interval * 1.6, 0.4))

    def on_success(self) -> None:
        with self.lock:
            self.min_interval = max(self.base_interval, self.min_interval * 0.95)

    def on_retry(self) -> None:
        with self.lock:
            self.retry_count += 1

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "throttle_events": self.throttle_events,
                "retry_count": self.retry_count,
                "min_interval": self.min_interval,
                "max_workers_used": self.max_workers_used,
            }


LIMITER = RateLimiter()


def classify_err(msg: str) -> str:
    s = msg or ""
    low = s.lower()
    if "cb_price_chg" in low:
        return "BLOCKED_DO_NOT_RETRY"
    if "请指定正确的接口名" in s:
        return "API_NOT_FOUND"
    if "8000" in s and ("积分" in s or "权限" in s):
        return "PERMISSION_BLOCKED_POINTS_8000"
    if "频率" in s or "too many" in low or "每分钟" in s:
        return "THROTTLE"
    if "超时" in s or "timeout" in low:
        return "TIMEOUT"
    if "积分不足" in s or "没有接口访问权限" in s or "无权限" in s or "单独开权限" in s:
        return "PERMISSION_BLOCKED"
    return "OTHER"


def tushare_call(pro, api: str, params: dict[str, Any], retries: int = 6):
    last = None
    for i in range(retries):
        LIMITER.wait()
        try:
            df = pro.query(api, **params)
            LIMITER.on_success()
            return df
        except Exception as exc:
            last = exc
            kind = classify_err(f"{type(exc).__name__}: {exc}")
            if kind in {"PERMISSION_BLOCKED", "PERMISSION_BLOCKED_POINTS_8000", "API_NOT_FOUND", "BLOCKED_DO_NOT_RETRY"}:
                raise
            LIMITER.on_retry()
            if kind == "THROTTLE":
                LIMITER.on_throttle()
            time.sleep(min(32.0, 2 ** i))
    raise last


def save_raw_slice(api: str, slice_id: str, params: dict[str, Any], df, extra: dict | None = None) -> dict[str, Any]:
    import pandas as pd

    out_dir = RAW_ROOT / api / slice_id
    n = 0 if df is None else int(len(df))
    payload = b"" if df is None else df_to_parquet_bytes(df)
    sha = hashlib.sha256(payload).hexdigest()
    wbytes(out_dir / "raw.parquet", payload)
    receipt = {
        "source_vendor": SOURCE_VENDOR,
        "source_api": api,
        "request_parameters": {k: v for k, v in params.items()},
        "fetch_timestamp": now_utc(),
        "raw_row_count": n,
        "raw_sha256": sha,
        "query_cap": QUERY_CAP,
        "slice_id": slice_id,
        "JQ_NATIVE_DATA": False,
        "schema_compat_target": SCHEMA_COMPAT_TARGET,
        "IMMUTABLE": True,
        "column_rename": False,
        "unit_change": False,
        "fill_missing": False,
    }
    if extra:
        receipt.update(extra)
    wjson(out_dir / "receipt.json", receipt)
    return receipt


def slice_done(api: str, slice_id: str) -> bool:
    rec = RAW_ROOT / api / slice_id / "receipt.json"
    parq = RAW_ROOT / api / slice_id / "raw.parquet"
    return rec.is_file() and parq.is_file()


def concat_raw(api: str):
    import pandas as pd

    root = RAW_ROOT / api
    if not root.is_dir():
        return pd.DataFrame()
    frames = []
    for rec in sorted(root.glob("*/receipt.json")):
        parq = rec.parent / "raw.parquet"
        if not parq.is_file() or parq.stat().st_size == 0:
            continue
        try:
            df = pd.read_parquet(parq)
        except Exception:
            continue
        if df is not None and len(df) > 0:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def paginate_api(pro, api: str, base_params: dict[str, Any], slice_prefix: str, fields: str | None = None) -> dict[str, Any]:
    import pandas as pd

    frames = []
    offset = 0
    page = 0
    n = 0
    while True:
        slice_id = f"{slice_prefix}_p{page:04d}"
        params = dict(base_params)
        params["limit"] = QUERY_CAP
        params["offset"] = offset
        if fields:
            params["fields"] = fields
        if slice_done(api, slice_id):
            rec = json.loads((RAW_ROOT / api / slice_id / "receipt.json").read_text(encoding="utf-8"))
            n = int(rec.get("raw_row_count") or 0)
            if n > 0:
                frames.append(pd.read_parquet(RAW_ROOT / api / slice_id / "raw.parquet"))
            page += 1
            offset += QUERY_CAP
            if n < QUERY_CAP:
                break
            continue
        key = f"{api}|{slice_id}"
        if not LIMITER.acquire_key(key):
            time.sleep(0.2)
            continue
        try:
            df = tushare_call(pro, api, params)
            n = 0 if df is None else int(len(df))
            pag = "YES" if n < QUERY_CAP else "NO"
            gate = decide(
                n_rows=n,
                query_cap=QUERY_CAP,
                pagination_complete=pag,
                completeness_state="COMPLETE" if n < QUERY_CAP else "UNKNOWN",
            )
            save_raw_slice(
                api,
                slice_id,
                params,
                df if df is not None else pd.DataFrame(),
                {"PAGINATION_COMPLETE": pag, "DATA_ABSENCE_GATE": gate["DATA_ABSENCE_GATE"], "offset": offset},
            )
            if n > 0:
                frames.append(df)
        finally:
            LIMITER.release_key(key)
        page += 1
        offset += QUERY_CAP
        if n < QUERY_CAP:
            break
    return {"api": api, "rows": int(sum(len(x) for x in frames)) if frames else 0, "pages": page, "frames": frames}


def add_codes(df, bond_col="ts_code"):
    out = df.copy()
    if bond_col in out.columns:
        out["bond_code_ts"] = out[bond_col].astype(str)
        out["bond_code_jq"] = out["bond_code_ts"].map(ts_to_jq)
    out["source_vendor"] = SOURCE_VENDOR
    out["jq_native_data"] = False
    return out


def write_product(pid: str, df, provenance: dict[str, Any]) -> None:
    payload = df_to_parquet_bytes(df)
    wbytes(CLEAN_ROOT / pid / "data.parquet", payload)
    wbytes(CACHE_ROOT / pid / "data.parquet", payload)
    body = dict(provenance)
    body.update(
        {
            "product_id": pid,
            "source_vendor": SOURCE_VENDOR,
            "schema_compat_target": SCHEMA_COMPAT_TARGET,
            "schema_compat_mode": "FIELD_SEMANTIC_MAPPING",
            "jq_native_data": False,
            "JQ_EQUIVALENT": False,
            "JQ_NATIVE": False,
            "row_count": int(len(df)),
            "content_sha256": hashlib.sha256(payload).hexdigest(),
            "written_at": now_cn(),
            "CBOND_CONVERT_PRICE_PIT": "NOT_READY",
        }
    )
    wjson(CACHE_ROOT / pid / "PROVENANCE.json", body)
    wjson(CLEAN_ROOT / pid / "PROVENANCE.json", body)


def r1_read(pid: str):
    import pandas as pd

    p = R1_CACHE / pid / "data.parquet"
    if p.is_file():
        return pd.read_parquet(p)
    files = sorted((R1_CACHE / pid).rglob("*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(x) for x in files], ignore_index=True)


def must_read_preflight() -> dict[str, Any]:
    man = json.loads(read_text(MANIFEST_PATH))
    required = ["BOOTSTRAP", "DATA_ACCESS", "ACQUISITION"]
    problems = []
    loaded = []
    for k in required:
        meta = man["files"][k]
        path = ROOT / meta["path"]
        actual = sha256_text(read_text(path))
        st = "VERIFIED" if actual == meta["sha256"] else "SHA_MISMATCH"
        if st != "VERIFIED":
            problems.append(f"SHA_MISMATCH_{k}")
        loaded.append({"key": k, "expected": meta["sha256"], "actual": actual, "status": st})
    k_actual = sha256_text(read_text(KERNEL_PATH))
    k_expected = (man.get("kernel") or {}).get("sha256")
    if k_expected and k_actual != k_expected:
        problems.append("SHA_MISMATCH_KERNEL")
    ok = not problems
    block = {
        "BLACKBOX_BOOTSTRAP_PREFLIGHT": True,
        "TASK_CLASS_USER": "DATA,ACQUISITION,CLEANING,PIT,INTEGRATION",
        "TASK_CLASS": TASK_CLASS,
        "MUST_READ_PRECHECK": "PASS" if ok else "FAIL",
        "MUST_READ_BOOTSTRAP": "YES",
        "MUST_READ_DATA_ACCESS": "YES",
        "MUST_READ_ACQUISITION": "YES",
        "HAND_READ": "YES",
        "AUTHORITY_READY": "YES" if ok else "NO",
        "KERNEL_SHA256": k_actual,
        "problems": problems,
        "rules_loaded": loaded,
        "NO_EXTRA_INSTALL": True,
        "NO_STOCK_MUTATION": True,
        "NO_CB_DAILY_REDOWNLOAD": True,
        "NO_PERMISSION_BYPASS": True,
        "NO_FUTURE_SNAPSHOT_BACKFILL": True,
        "REDOWNLOAD_CB_DAILY": "NO",
        "CLEANING_PIT_INTEGRATION": "ROUTED_AS_DATA_ACQUISITION_MANIFEST_HAS_NO_THOSE_CLASSES",
    }
    wjson(TASK_DIR / "MUST_READ_PREFLIGHT.json", block)
    return block


def freeze_stock_and_r1() -> dict[str, Any]:
    stock_ptr = json.loads(STOCK_CURRENT_PTR.read_text(encoding="utf-8"))
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    products = {p["product_id"]: p for p in index.get("products", [])}
    evidence = {}
    for pid in STOCK_PRODUCTS:
        row = products.get(pid)
        evidence[pid] = {
            "in_index": pid in products,
            "index_record_sha256": hashlib.sha256(
                json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()
            if row
            else "MISSING",
        }
    stock_blob = json.dumps([products.get(pid) for pid in STOCK_PRODUCTS], ensure_ascii=False, sort_keys=True, default=str)
    r1_hashes = {}
    for pid in R1_PRODUCTS:
        prov = R1_CACHE / pid / "PROVENANCE.json"
        r1_hashes[pid] = {
            "provenance_sha256": file_sha256(prov),
            "content_sha256": json.loads(prov.read_text(encoding="utf-8")).get("content_sha256") if prov.is_file() else "MISSING",
        }
    body = {
        "frozen_at": now_cn(),
        "STOCK_CURRENT_ID": stock_ptr.get("cache_release_id"),
        "STOCK_CURRENT_PTR_SHA256": file_sha256(STOCK_CURRENT_PTR),
        "STOCK_INDEX_RECORDS_SHA256": hashlib.sha256(stock_blob.encode("utf-8")).hexdigest(),
        "CBOND_R1_PTR_SHA256": file_sha256(CBOND_PTR),
        "R1_PRODUCT_HASHES": r1_hashes,
        "products": evidence,
        "MODIFY_EXISTING_STOCK_PRODUCTS": "NO",
        "MERGE_CBOND_INTO_STOCK_UNIVERSE": "FORBIDDEN",
        "REDOWNLOAD_CB_DAILY": "NO",
    }
    wjson(TASK_DIR / "STOCK_BASELINE.json", body)
    return body


def load_token() -> str:
    text = TOKEN_FILE.read_text(encoding="utf-8").strip().splitlines()
    token = (text[0] if text else "").strip()
    if not token:
        raise RuntimeError("TUSHARE_TOKEN_MISSING")
    return token


def probe_one(pro, api: str, params: dict[str, Any]) -> dict[str, Any]:
    import pandas as pd

    p = dict(params)
    p["limit"] = PROBE_LIMIT
    p["offset"] = 0
    try:
        df = tushare_call(pro, api, p, retries=2)
        n = 0 if df is None else int(len(df))
        cols = [] if df is None else list(df.columns)
        sample = [] if df is None or df.empty else df.head(2).astype(str).to_dict(orient="records")
        return {"api": api, "status": "OK", "rows": n, "columns": cols, "sample": sample, "secret_value_printed": False}
    except Exception as exc:
        kind = classify_err(f"{type(exc).__name__}: {exc}")
        return {"api": api, "status": kind, "error_type": type(exc).__name__, "error": str(exc)[:300], "secret_value_printed": False}


def run_probes(pro) -> dict[str, Any]:
    audit = {
        "cb_basic": "HAVE_R1",
        "cb_issue": "HAVE_R1",
        "cb_call": "HAVE_R1",
        "cb_rate": "HAVE_R1",
        "cb_daily": "HAVE_R1_DO_NOT_REDOWNLOAD",
        "cb_share": "HAVE_R1",
        "cb_rating": "TO_PROBE",
        "top10_cb_holders": "TO_PROBE",
        "cb_factor_pro": "TO_PROBE_ONCE",
        "cb_price_chg": "SEPARATE_PERMISSION_BLOCKED_DO_NOT_RETRY",
    }
    probes = {}
    print("PROBE cb_rating limit=8 ts_code required", flush=True)
    probes["cb_rating"] = probe_one(pro, "cb_rating", {"ts_code": FIXED_BOND_TS})
    print("PROBE top10_cb_holders limit=8 ts_code required", flush=True)
    probes["top10_cb_holders"] = probe_one(pro, "top10_cb_holders", {"ts_code": FIXED_BOND_TS})
    prev = TASK_DIR / "API_GAP_AUDIT.json"
    prev_factor = None
    if prev.is_file():
        try:
            prev_factor = json.loads(prev.read_text(encoding="utf-8")).get("probes", {}).get("cb_factor_pro")
        except Exception:
            prev_factor = None
    if prev_factor and prev_factor.get("status"):
        print("PROBE cb_factor_pro SKIP already probed once", flush=True)
        probes["cb_factor_pro"] = dict(prev_factor)
        probes["cb_factor_pro"]["replayed_from_disk"] = True
        probes["cb_factor_pro"]["DOWNLOAD"] = "NO"
    else:
        print("PROBE cb_factor_pro once", flush=True)
        probes["cb_factor_pro"] = probe_one(pro, "cb_factor_pro", {"ts_code": FIXED_BOND_TS})
        probes["cb_factor_pro"]["DOWNLOAD"] = "NO"
    probes["cb_price_chg"] = {"api": "cb_price_chg", "status": "BLOCKED_DO_NOT_RETRY", "called": False}
    if probes["cb_factor_pro"]["status"] in {"PERMISSION_BLOCKED", "PERMISSION_BLOCKED_POINTS_8000"}:
        probes["cb_factor_pro"]["DATA_GAP"] = "PERMISSION_BLOCKED_POINTS_THRESHOLD"
        probes["cb_factor_pro"]["DOWNLOAD"] = "NO"
    body = {"audited_at": now_cn(), "known": audit, "probes": probes, "cb_price_chg_called": False}
    wjson(TASK_DIR / "API_GAP_AUDIT.json", body)
    return body


def download_trade_cal(pro) -> list[str]:
    import pandas as pd

    params = {"exchange": "SSE", "start_date": "19900101", "end_date": "20261231", "is_open": "1"}
    df = tushare_call(pro, "trade_cal", params)
    save_raw_slice(
        "trade_cal_helper",
        "sse_19900101_20261231",
        params,
        df,
        {"role": "PIT_CALENDAR_ONLY_NOT_A_CBOND_PRODUCT", "PAGINATION_COMPLETE": "YES"},
    )
    if df is None or df.empty:
        raise RuntimeError("TRADE_CAL_EMPTY")
    col = "cal_date" if "cal_date" in df.columns else "trade_date"
    dates = sorted({ymd(x) for x in df[col].tolist() if ymd(x)})
    wjson(TASK_DIR / "trade_cal.json", {"n": len(dates), "start": dates[0], "end": dates[-1]})
    return dates


def next_trade_after(ann: str | None, cal: list[str]) -> str | None:
    d = ymd(ann)
    if not d:
        return None
    import bisect

    i = bisect.bisect_right(cal, d)
    if i >= len(cal):
        return None
    return cal[i]


def batched(seq, n):
    for i in range(0, len(seq), n):
        yield i, seq[i : i + n]


def download_rating(pro, codes: list[str]) -> dict[str, Any]:
    print(f"DOWNLOAD cb_rating per ts_code n={len(codes)} workers={MAX_WORKERS}", flush=True)

    def one(code: str) -> dict[str, Any]:
        LIMITER.mark_worker()
        try:
            r = paginate_api(pro, "cb_rating", {"ts_code": code}, f"code_{code}", fields=CB_RATING_FIELDS)
            return {"code": code, "rows": r["rows"], "ok": True}
        except Exception as exc:
            return {"code": code, "rows": 0, "ok": False, "error": f"{type(exc).__name__}: {exc}"[:200]}
        finally:
            LIMITER.unmark_worker()

    fail = []
    ok_n = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(one, c): c for c in codes}
        done = 0
        for fut in as_completed(futs):
            rec = fut.result()
            done += 1
            if rec.get("ok"):
                ok_n += 1
            else:
                fail.append(rec)
            if done % 100 == 0 or done == len(codes):
                print(f"cb_rating progress {done}/{len(codes)} ok={ok_n} fail={len(fail)}", flush=True)
    if fail:
        wjson(TASK_DIR / "cb_rating_failures.json", fail[:50])
    return {
        "mode": "PER_CODE",
        "rows": int(len(concat_raw("cb_rating"))),
        "codes_ok": ok_n,
        "codes_fail": len(fail),
        "status": "DOWNLOADED" if ok_n else "FAIL",
    }


def download_top10(pro, codes: list[str], perm_ok: bool) -> dict[str, Any]:
    if not perm_ok:
        return {"status": "SKIPPED_NO_PERMISSION", "rows": 0}
    print("DOWNLOAD top10_cb_holders per-code batches (ts_code required)", flush=True)
    pages = 0
    rows = 0
    for i, batch in batched(codes, 10):
        r = paginate_api(
            pro,
            "top10_cb_holders",
            {"ts_code": ",".join(batch), "start_date": START, "end_date": END},
            f"batch_{i:04d}",
        )
        pages += r["pages"]
        rows += r["rows"]
        if i % 100 == 0:
            print(f"top10 batch_start={i}/{len(codes)} rows={rows}", flush=True)
    return {"status": "DOWNLOADED_BATCH", "rows": rows, "pages": pages}


def download_carryin(pro, api: str, codes_pre: list[str], fields: str | None) -> dict[str, Any]:
    if not codes_pre:
        return {"status": "NO_PREWINDOW_CODES", "rows": 0}
    print(f"CARRY-IN {api} prewindow codes={len(codes_pre)}", flush=True)
    rows = 0
    pages = 0
    for i, batch in batched(codes_pre, 15):
        r = paginate_api(
            pro,
            api,
            {"ts_code": ",".join(batch), "start_date": "19900101", "end_date": "20210815"},
            f"carryin_{i:04d}",
            fields=fields,
        )
        rows += r["rows"]
        pages += r["pages"]
    return {"status": "CARRYIN_ONLY", "rows": rows, "pages": pages, "codes": len(codes_pre)}


def clean_event(df, date_cols: list[str]):
    import pandas as pd

    out = add_codes(df)
    for c in date_cols:
        if c in out.columns:
            out[c] = out[c].map(ymd)
    return out


def build_rating_pit(raw, cal: list[str]):
    import pandas as pd

    df = clean_event(raw, ["ann_date", "rating_date"])
    lineage = [
        {"src": "ts_code", "dst": "bond_code_ts", "class": "B"},
        {"src": "ts_code", "dst": "bond_code_jq", "class": "B", "formula": ".SZ→.XSHE .SH→.XSHG"},
        {"src": "ann_date", "dst": "source_ann_date / DISCLOSURE_DATE", "class": "A"},
        {"src": "rating_date", "dst": "source_rating_date / EVENT_DATE", "class": "A"},
        {"src": "rating", "dst": "rating", "class": "A"},
        {"note": "JQ_COMPAT_STATUS=NO_EQUIVALENT; no CONBOND rating PIT field invented"},
    ]
    df = df[df["ann_date"].map(ymd).notna()].copy()
    df["pit_valid_from"] = df["ann_date"].map(lambda x: next_trade_after(x, cal))
    df = df[df["pit_valid_from"].notna()].copy()
    df = df.sort_values(["bond_code_jq", "pit_valid_from", "ann_date", "rating_date"])
    df = df.drop_duplicates(["bond_code_jq", "pit_valid_from"], keep="last")
    rows = []
    for code, g in df.groupby("bond_code_jq", sort=False):
        recs = g.to_dict("records")
        for i, r in enumerate(recs):
            vf = r["pit_valid_from"]
            vt = recs[i + 1]["pit_valid_from"] if i + 1 < len(recs) else "99991231"
            if vt <= vf:
                continue
            rows.append(
                {
                    "bond_code_jq": r.get("bond_code_jq"),
                    "bond_code_ts": r.get("bond_code_ts"),
                    "pit_valid_from": vf,
                    "pit_valid_to": vt,
                    "rating": r.get("rating"),
                    "rating_outlook": r.get("rating_outlook"),
                    "rating_com_name": r.get("rating_com_name"),
                    "rating_way": r.get("rating_way"),
                    "rating_type": r.get("rating_type"),
                    "source_ann_date": r.get("ann_date"),
                    "source_rating_date": r.get("rating_date"),
                    "KNOWN_AT_POLICY": "DATE_ONLY_NEXT_TRADING_DAY",
                    "PIT_SAFE": True,
                    "source_vendor": SOURCE_VENDOR,
                    "source_api": "cb_rating",
                    "jq_native_data": False,
                }
            )
    pit = pd.DataFrame(rows)
    write_product(
        "TUSHARE_CBOND_RATING_R1",
        df,
        {"source_api": "cb_rating", "layer": "CLEAN_EVENT", "JQ_COMPAT_STATUS": "NO_EQUIVALENT", "transform_lineage": lineage},
    )
    write_product(
        "TUSHARE_CBOND_RATING_PIT_R1",
        pit,
        {
            "source_api": "cb_rating",
            "layer": "PIT",
            "KNOWN_AT": "NEXT_TRADING_DAY_AFTER_ANN_DATE",
            "PIT_SAFE": True,
            "transform_lineage": lineage,
        },
    )
    return df, pit, lineage


def build_call_pit(r1_call, carry, cal: list[str]):
    import pandas as pd

    parts = [r1_call]
    if carry is not None and len(carry):
        parts.append(carry)
    raw = pd.concat(parts, ignore_index=True)
    df = clean_event(raw, ["ann_date", "call_date", "payment_date", "call_reg_date"])
    before = int(len(df))
    df = df.drop_duplicates(
        subset=[c for c in ["bond_code_ts", "ann_date", "call_type", "is_call", "call_date"] if c in df.columns]
    )
    df["pit_valid_from"] = df["ann_date"].map(lambda x: next_trade_after(x, cal))
    usable = df[df["pit_valid_from"].notna() & df["ann_date"].notna()].copy()
    usable["source_ann_date"] = usable["ann_date"]
    usable["EVENT_DATE"] = usable["call_date"]
    usable["DISCLOSURE_DATE"] = usable["ann_date"]
    usable["KNOWN_AT_POLICY"] = "DATE_ONLY_NEXT_TRADING_DAY"
    usable["PIT_SAFE"] = True
    usable["source_api"] = "cb_call"
    write_product(
        "TUSHARE_CBOND_CALL_PIT_R1",
        usable,
        {
            "source_api": "cb_call",
            "layer": "PIT_EVENT",
            "KNOWN_AT": "NEXT_TRADING_DAY_AFTER_ANN_DATE",
            "PIT_SAFE": True,
            "source_event_preserved": True,
            "r1_rows": int(len(r1_call)),
            "carryin_rows": 0 if carry is None else int(len(carry)),
            "dedup_before": before,
            "note": "call_date is NOT known_at",
        },
    )
    return usable


def build_remain_pit(r1_share, carry, issue, basic, cal: list[str]):
    import pandas as pd

    parts = [r1_share]
    if carry is not None and len(carry):
        parts.append(carry)
    share = clean_event(pd.concat(parts, ignore_index=True), ["publish_date", "end_date"])
    share = share[share["publish_date"].notna()].copy()
    share["pit_valid_from"] = share["publish_date"].map(lambda x: next_trade_after(x, cal))
    share = share[share["pit_valid_from"].notna()].copy()
    share["known_remain_size"] = pd.to_numeric(share.get("remain_size"), errors="coerce")
    share["known_remain_size_source"] = "CB_SHARE_REMAIN_SIZE"
    share["source_publish_date"] = share["publish_date"]
    share["size_state_source"] = "CB_SHARE_REMAIN_SIZE"

    init_rows = []
    iss = add_codes(issue) if issue is not None and len(issue) else pd.DataFrame()
    bas = add_codes(basic) if basic is not None and len(basic) else pd.DataFrame()
    size_map = {}
    if len(iss) and "issue_size" in iss.columns:
        for _, r in iss.iterrows():
            size_map[str(r.get("bond_code_ts"))] = r.get("issue_size")
    list_map = {}
    if len(bas) and "list_date" in bas.columns:
        for _, r in bas.iterrows():
            list_map[str(r.get("bond_code_ts"))] = ymd(r.get("list_date"))
    first_share = share.groupby("bond_code_ts")["pit_valid_from"].min().to_dict() if len(share) else {}
    for code, issz in size_map.items():
        ld = list_map.get(code)
        vf = next_trade_after(ld, cal) if ld else None
        if not vf:
            continue
        jq = ts_to_jq(code)
        init_rows.append(
            {
                "bond_code_ts": code,
                "bond_code_jq": jq,
                "pit_valid_from": vf,
                "known_remain_size": issz,
                "known_remain_size_source": "ISSUE_SIZE_INITIAL",
                "size_state_source": "ISSUE_SIZE_INITIAL",
                "source_publish_date": ld,
                "remain_size": issz,
                "publish_date": ld,
                "end_date": None,
                "source_api": "cb_issue",
                "PIT_SAFE": True,
            }
        )
    init = pd.DataFrame(init_rows)
    keep_init = []
    if len(init):
        for _, r in init.iterrows():
            fs = first_share.get(str(r["bond_code_ts"]))
            if fs is None or r["pit_valid_from"] < fs:
                keep_init.append(r.to_dict())
    init = pd.DataFrame(keep_init)
    cols_share = [
        "bond_code_ts",
        "bond_code_jq",
        "pit_valid_from",
        "known_remain_size",
        "known_remain_size_source",
        "size_state_source",
        "source_publish_date",
        "remain_size",
        "publish_date",
        "end_date",
        "convert_price",
        "convert_val",
        "convert_vol",
        "convert_ratio",
        "acc_convert_val",
        "acc_convert_vol",
        "acc_convert_ratio",
        "issue_size",
        "source_api",
        "PIT_SAFE",
    ]
    for c in cols_share:
        if c not in share.columns:
            share[c] = None
        if len(init) and c not in init.columns:
            init[c] = None
    share["source_api"] = "cb_share"
    share["PIT_SAFE"] = True
    events = pd.concat(
        [
            init[cols_share] if len(init) else pd.DataFrame(columns=cols_share),
            share[cols_share],
        ],
        ignore_index=True,
    )
    events = events.sort_values(["bond_code_jq", "pit_valid_from", "source_publish_date"])
    events = events.drop_duplicates(["bond_code_jq", "pit_valid_from"], keep="last")
    rows = []
    for code, g in events.groupby("bond_code_jq", sort=False):
        recs = g.to_dict("records")
        for i, r in enumerate(recs):
            vf = r["pit_valid_from"]
            vt = recs[i + 1]["pit_valid_from"] if i + 1 < len(recs) else "99991231"
            if not vf or vt <= vf:
                continue
            item = dict(r)
            item["pit_valid_to"] = vt
            item["KNOWN_AT_POLICY"] = "DATE_ONLY_NEXT_TRADING_DAY"
            item["source_vendor"] = SOURCE_VENDOR
            item["jq_native_data"] = False
            rows.append(item)
    pit = pd.DataFrame(rows)
    write_product(
        "TUSHARE_CBOND_REMAIN_SIZE_PIT_R1",
        pit,
        {
            "source_api": "cb_share+cb_issue",
            "layer": "PIT",
            "KNOWN_AT": "NEXT_TRADING_DAY_AFTER_PUBLISH_DATE",
            "PIT_SAFE": True,
            "forward_fill": True,
            "backfill": False,
            "note": "known_at is NOT end_date; convert_price here is event field not daily convert-price PIT",
        },
    )
    return pit


def clean_top10(raw):
    import pandas as pd

    df = add_codes(raw)
    for c in ("end_date",):
        if c in df.columns:
            df[c] = df[c].map(ymd)
    keys = [c for c in ["bond_code_jq", "end_date", "holder_rank"] if c in df.columns]
    if keys:
        df = df.drop_duplicates(keys)
    df["PIT_SAFE"] = False
    df["REPORT_PERIOD_ONLY"] = True
    df["BACKTEST_DEFAULT_ACCESS"] = "FORBIDDEN"
    df["known_at"] = None
    write_product(
        "TUSHARE_CBOND_TOP10_HOLDERS_R1",
        df,
        {
            "source_api": "top10_cb_holders",
            "PIT_SAFE": False,
            "REPORT_PERIOD_ONLY": True,
            "BACKTEST_DEFAULT_ACCESS": "FORBIDDEN",
            "JQ_COMPAT_STATUS": "NO_EQUIVALENT",
            "note": "end_date is report period; not disclosure date",
        },
    )
    return df


def _asof_interval(df, code: str, date: str):
    d = ymd(date)
    if df is None or df.empty or not d:
        return None
    sub = df[(df["bond_code_jq"].astype(str) == str(code)) | (df["bond_code_ts"].astype(str) == str(code))]
    vf = sub["pit_valid_from"].map(ymd)
    if "pit_valid_to" in sub.columns:
        vt = sub["pit_valid_to"].map(ymd)
        hit = sub[vf.notna() & (vf <= d) & (vt.isna() | (vt > d))]
    else:
        hit = sub[vf.notna() & (vf <= d)]
    if hit.empty:
        return None
    return hit.sort_values("pit_valid_from").iloc[-1].to_dict()


def _asof_call(df, code: str, date: str):
    d = ymd(date)
    if df is None or df.empty or not d:
        return None
    sub = df[(df["bond_code_jq"].astype(str) == str(code)) | (df["bond_code_ts"].astype(str) == str(code))]
    vf = sub["pit_valid_from"].map(ymd)
    vis = sub[vf.notna() & (vf <= d)].sort_values("pit_valid_from")
    if vis.empty:
        return {"known_event": False, "pit_valid_from": None}
    last = vis.iloc[-1].to_dict()
    last["known_event"] = True
    return last


def leakage_tests(rating_pit, call_pit, remain_pit, cal: list[str]) -> dict[str, Any]:
    import pandas as pd

    cases = []
    fails = []

    def prev_trade(d: str) -> str | None:
        import bisect

        i = bisect.bisect_left(cal, d)
        if i <= 0:
            return None
        return cal[i - 1]

    def add_case(kind, pit_df, code_col="bond_code_jq"):
        if pit_df is None or pit_df.empty:
            return
        # prefer a change: consecutive different states
        picked = None
        if "rating" in pit_df.columns:
            for code, g in pit_df.sort_values("pit_valid_from").groupby(code_col):
                recs = g.to_dict("records")
                for i in range(1, len(recs)):
                    if recs[i].get("rating") != recs[i - 1].get("rating"):
                        picked = recs[i]
                        prev = recs[i - 1]
                        picked["_prev"] = prev
                        break
                if picked:
                    break
        if picked is None and "known_remain_size" in pit_df.columns:
            for code, g in pit_df.sort_values("pit_valid_from").groupby(code_col):
                recs = g.to_dict("records")
                for i in range(1, len(recs)):
                    a, b = recs[i - 1].get("known_remain_size"), recs[i].get("known_remain_size")
                    try:
                        if a is not None and b is not None and float(b) < float(a):
                            picked = recs[i]
                            picked["_prev"] = recs[i - 1]
                            break
                    except Exception:
                        continue
                if picked:
                    break
        if picked is None:
            # weekend / holiday: ann Friday
            if "source_ann_date" in pit_df.columns:
                for _, r in pit_df.iterrows():
                    ann = ymd(r.get("source_ann_date") or r.get("ann_date"))
                    vf = ymd(r.get("pit_valid_from"))
                    if ann and vf and vf > ann:
                        picked = r.to_dict()
                        break
        if picked is None:
            picked = pit_df.iloc[len(pit_df) // 2].to_dict()
        vf = ymd(picked.get("pit_valid_from"))
        before = prev_trade(vf) if vf else None
        code = picked.get(code_col) or picked.get("bond_code_ts")
        cases.append({"kind": kind, "picked": {k: picked.get(k) for k in list(picked)[:20]}, "code": code, "vf": vf, "before": before})

    add_case("RATING_CHANGE", rating_pit)
    if call_pit is not None and len(call_pit):
        yes = call_pit[call_pit["is_call"].astype(str).str.upper().isin(["Y", "YES", "1", "是", "TRUE"])] if "is_call" in call_pit.columns else call_pit.iloc[0:0]
        no = call_pit[call_pit["is_call"].astype(str).str.upper().isin(["N", "NO", "0", "否", "FALSE"])] if "is_call" in call_pit.columns else call_pit.iloc[0:0]
        for kind, sub in (("CALL_YES", yes), ("CALL_NO", no)):
            if len(sub):
                add_case(kind, sub)
        # weekend: Friday ann
        if "ann_date" in call_pit.columns:
            for _, r in call_pit.iterrows():
                ann = ymd(r.get("ann_date"))
                vf = ymd(r.get("pit_valid_from"))
                if ann and vf:
                    try:
                        ad = datetime.strptime(ann, "%Y%m%d")
                        if ad.weekday() >= 4 and vf > ann:
                            add_case("CALL_WEEKEND_OR_HOLIDAY", pd.DataFrame([r]))
                            break
                    except Exception:
                        continue
    add_case("REMAIN_DROP", remain_pit)

    results = []
    for c in cases:
        code, vf, before = c["code"], c["vf"], c["before"]
        kind = c["kind"]
        rec = {
            "kind": kind,
            "bond_code": code,
            "pit_valid_from": vf,
            "announcement_date": (c["picked"].get("source_ann_date") or c["picked"].get("ann_date") or c["picked"].get("source_publish_date")),
            "event_date": (c["picked"].get("source_rating_date") or c["picked"].get("call_date") or c["picked"].get("end_date")),
        }
        ok = True
        detail = {}
        if kind.startswith("RATING") or kind == "RATING_CHANGE":
            new_s = _asof_interval(rating_pit, code, vf)
            old_s = _asof_interval(rating_pit, code, before) if before else None
            detail["new_state"] = None if new_s is None else {k: new_s.get(k) for k in ("rating", "pit_valid_from", "source_ann_date")}
            detail["previous_state"] = None if old_s is None else {k: old_s.get(k) for k in ("rating", "pit_valid_from", "source_ann_date")}
            if new_s is None:
                ok = False
            if before and new_s and old_s and ymd(old_s.get("pit_valid_from")) == ymd(new_s.get("pit_valid_from")):
                ok = False
        elif kind.startswith("CALL"):
            new_s = _asof_call(call_pit, code, vf)
            old_s = _asof_call(call_pit, code, before) if before else None
            detail["new_state"] = None if new_s is None else {k: new_s.get(k) for k in ("ann_date", "is_call", "call_type", "pit_valid_from", "known_event")}
            detail["previous_state"] = None if old_s is None else {k: old_s.get(k) for k in ("ann_date", "is_call", "call_type", "pit_valid_from", "known_event")}
            if not new_s or not new_s.get("known_event"):
                ok = False
            if before and old_s and ymd(old_s.get("pit_valid_from")) == vf:
                ok = False
        else:
            new_s = _asof_interval(remain_pit, code, vf)
            old_s = _asof_interval(remain_pit, code, before) if before else None
            detail["new_state"] = None if new_s is None else {k: new_s.get(k) for k in ("known_remain_size", "known_remain_size_source", "pit_valid_from")}
            detail["previous_state"] = None if old_s is None else {k: old_s.get(k) for k in ("known_remain_size", "known_remain_size_source", "pit_valid_from")}
            if new_s is None:
                ok = False
            if before and new_s and old_s and ymd(old_s.get("pit_valid_from")) == ymd(new_s.get("pit_valid_from")):
                ok = False
        rec.update(detail)
        rec["pass"] = ok
        rec["assert"] = "signal_date < pit_valid_from → previous_state; signal_date >= pit_valid_from → new_state"
        results.append(rec)
        if not ok:
            fails.append(rec)

    # generic interval assertion on rating: random 20
    n_assert = 0
    if rating_pit is not None and len(rating_pit):
        sample = rating_pit.sample(n=min(20, len(rating_pit)), random_state=7)
        for _, r in sample.iterrows():
            vf = ymd(r["pit_valid_from"])
            before = prev_trade(vf) if vf else None
            code = r["bond_code_jq"]
            new_s = _asof_interval(rating_pit, code, vf)
            n_assert += 1
            if new_s is None or ymd(new_s.get("pit_valid_from")) != vf:
                fails.append({"kind": "RATING_RANDOM_NEW", "bond_code": code, "vf": vf})
            if before:
                old_s = _asof_interval(rating_pit, code, before)
                if old_s is not None and ymd(old_s.get("pit_valid_from")) == vf:
                    fails.append({"kind": "RATING_LEAK_BEFORE", "bond_code": code, "vf": vf, "before": before})

    body = {
        "n_cases": len(results),
        "n_random_asserts": n_assert,
        "PIT_LEAKAGE_FAILURES": len(fails),
        "cases": results,
        "fails": fails,
    }
    wjson(TASK_DIR / "PIT_LEAKAGE_TESTS.json", body)
    return body


def local_stock_join_check() -> dict[str, Any]:
    import pyarrow.parquet as pq

    stock_ptr = json.loads(STOCK_CURRENT_PTR.read_text(encoding="utf-8"))
    root = Path(stock_ptr["release_root"])
    hit = {
        "method": "PYARROW_FILTER_YEAR2026_LISTDIR",
        "matched": False,
        "rows": 0,
        "CBOND_CODE_IN_STOCK_UNIVERSE_2026_SCAN": 0,
        "note": "listdir year=2026 only; INDEX_DAILY not touched",
        "bond_code_ts": FIXED_BOND_TS,
        "stock_code_jq": FIXED_STK_JQ,
    }
    ydir = root / "STOCK_DAILY_RAW_PIT_R1" / "year=2026"
    fp = ydir / "part_2026.parquet"
    if not fp.is_file():
        hit["error"] = "YEAR2026_PARQUET_NOT_FOUND"
        return hit
    table = pq.read_table(fp, filters=[("code", "=", FIXED_STK_JQ)])
    df = table.to_pandas()
    if "date" in df.columns:
        ds = df["date"].astype(str).str.replace("-", "", regex=False).str[:8]
        df = df[ds == "20260814"]
    hit["rows"] = int(len(df))
    hit["matched"] = hit["rows"] > 0
    hit["read_path"] = str(fp)
    return hit


def r1_untouched(baseline: dict) -> dict[str, Any]:
    fails = []
    for pid, rec in (baseline.get("R1_PRODUCT_HASHES") or {}).items():
        prov = R1_CACHE / pid / "PROVENANCE.json"
        now = file_sha256(prov)
        if now != rec.get("provenance_sha256"):
            fails.append({"pid": pid, "field": "provenance", "before": rec.get("provenance_sha256"), "after": now})
        if prov.is_file():
            content = json.loads(prov.read_text(encoding="utf-8")).get("content_sha256")
            if content != rec.get("content_sha256"):
                fails.append({"pid": pid, "field": "content", "before": rec.get("content_sha256"), "after": content})
    return {"R1_UNTOUCHED": len(fails) == 0, "fails": fails}


def stock_after(baseline: dict) -> dict[str, Any]:
    after_ptr = file_sha256(STOCK_CURRENT_PTR)
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    products = {p["product_id"]: p for p in index.get("products", [])}
    mut = 0
    for pid in STOCK_PRODUCTS:
        row = products.get(pid)
        sha = hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest() if row else "MISSING"
        before = ((baseline.get("products") or {}).get(pid) or {}).get("index_record_sha256")
        if sha != before:
            mut += 1
    return {
        "STOCK_CURRENT_BEFORE_SHA256": baseline.get("STOCK_CURRENT_PTR_SHA256"),
        "STOCK_CURRENT_AFTER_SHA256": after_ptr,
        "STOCK_CURRENT_CHANGED": "YES" if after_ptr != baseline.get("STOCK_CURRENT_PTR_SHA256") else "NO",
        "STOCK_PRODUCT_MUTATION_COUNT": mut,
    }


def patch_resolver() -> None:
    text = RESOLVER_PY.read_text(encoding="utf-8")
    alias_anchor = '    "TUSHARE_CBOND_STOCK_BRIDGE_R1": "TUSHARE_CBOND_STOCK_BRIDGE_R1",\n}'
    alias_add = (
        '    "TUSHARE_CBOND_STOCK_BRIDGE_R1": "TUSHARE_CBOND_STOCK_BRIDGE_R1",\n'
        '    "TUSHARE_CBOND_RATING_PIT_R1": "TUSHARE_CBOND_RATING_PIT_R1",\n'
        '    "TUSHARE_CBOND_CALL_PIT_R1": "TUSHARE_CBOND_CALL_PIT_R1",\n'
        '    "TUSHARE_CBOND_REMAIN_SIZE_PIT_R1": "TUSHARE_CBOND_REMAIN_SIZE_PIT_R1",\n'
        '    "TUSHARE_CBOND_TOP10_HOLDERS_R1": "TUSHARE_CBOND_TOP10_HOLDERS_R1",\n'
        '    "TUSHARE_CBOND_RATING_R1": "TUSHARE_CBOND_RATING_R1",\n'
        "}"
    )
    if "TUSHARE_CBOND_RATING_PIT_R1" not in text:
        if alias_anchor not in text:
            raise RuntimeError("RESOLVER_ALIAS_ANCHOR_MISSING")
        text = text.replace(alias_anchor, alias_add, 1)
    pit_anchor = '    "TUSHARE_CBOND_STOCK_BRIDGE_R1": {"pit_policy": "DICTIONARY_MAP", "asof_behavior": "JOIN_ON_STOCK_CODE_JQ"},\n}'
    pit_add = (
        '    "TUSHARE_CBOND_STOCK_BRIDGE_R1": {"pit_policy": "DICTIONARY_MAP", "asof_behavior": "JOIN_ON_STOCK_CODE_JQ"},\n'
        '    "TUSHARE_CBOND_RATING_PIT_R1": {"pit_policy": "NEXT_TRADE_DAY_AFTER_ANN_DATE", "asof_behavior": "PIT_VALID_FROM"},\n'
        '    "TUSHARE_CBOND_CALL_PIT_R1": {"pit_policy": "NEXT_TRADE_DAY_AFTER_ANN_DATE", "asof_behavior": "PIT_VALID_FROM"},\n'
        '    "TUSHARE_CBOND_REMAIN_SIZE_PIT_R1": {"pit_policy": "NEXT_TRADE_DAY_AFTER_PUBLISH_DATE", "asof_behavior": "PIT_VALID_FROM"},\n'
        '    "TUSHARE_CBOND_TOP10_HOLDERS_R1": {"pit_policy": "REPORT_PERIOD_ONLY_NOT_PIT", "asof_behavior": "BACKTEST_DEFAULT_FORBIDDEN"},\n'
        '    "TUSHARE_CBOND_RATING_R1": {"pit_policy": "EVENT_TABLE", "asof_behavior": "USE_RATING_PIT_PRODUCT"},\n'
        "}"
    )
    if "NEXT_TRADE_DAY_AFTER_ANN_DATE" not in text:
        if pit_anchor not in text:
            raise RuntimeError("RESOLVER_PIT_ANCHOR_MISSING")
        text = text.replace(pit_anchor, pit_add, 1)
    curr_anchor = '        result["cbond_source_vendor"] = cbond.get("source_vendor", "TUSHARE_PRO")\n'
    curr_add = (
        '        result["cbond_source_vendor"] = cbond.get("source_vendor", "TUSHARE_PRO")\n'
        '        result["cbond_product_path_map"] = cbond.get("product_path_map") or {}\n'
        '        result["cbond_parent_release_root"] = cbond.get("parent_release_root") or ""\n'
    )
    if "cbond_product_path_map" not in text:
        if curr_anchor not in text:
            raise RuntimeError("RESOLVER_CURRENT_ANCHOR_MISSING")
        text = text.replace(curr_anchor, curr_add, 1)
    path_anchor = "    if is_cbond:\n        cache_root = currents.get(\"cbond_cache_release_root\") or cache_root\n"
    path_add = (
        "    if is_cbond:\n"
        "        cache_root = currents.get(\"cbond_cache_release_root\") or cache_root\n"
        "        _pmap = currents.get(\"cbond_product_path_map\") or {}\n"
        "        if normalized in _pmap:\n"
        "            product_path = _pmap[normalized]\n"
        "            cache_root = str(Path(product_path).parent)\n"
    )
    if "cbond_product_path_map" in text and "if normalized in _pmap" not in text:
        if path_anchor not in text:
            raise RuntimeError("RESOLVER_PATH_ANCHOR_MISSING")
        text = text.replace(path_anchor, path_add, 1)
        # skip default join if already set
        text = text.replace(
            "    product_path = os.path.join(cache_root, normalized)\n",
            "    if not (is_cbond and (currents.get(\"cbond_product_path_map\") or {}).get(normalized)):\n"
            "        product_path = os.path.join(cache_root, normalized)\n",
            1,
        )
    build_anchor = "        root = currents.get(\"cbond_cache_release_root\") if is_cbond else currents.get(\"cache_release_root\", \"\")\n        product_path = os.path.join(root or \"\", pid)\n"
    build_add = (
        "        root = currents.get(\"cbond_cache_release_root\") if is_cbond else currents.get(\"cache_release_root\", \"\")\n"
        "        _pmap = currents.get(\"cbond_product_path_map\") or {}\n"
        "        product_path = _pmap.get(pid) or os.path.join(root or \"\", pid)\n"
    )
    if "product_path = _pmap.get(pid)" not in text:
        if build_anchor not in text:
            raise RuntimeError("RESOLVER_BUILD_ANCHOR_MISSING")
        text = text.replace(build_anchor, build_add, 1)
    guarded_write_path(RESOLVER_PY, text)


def promote(val: dict[str, Any]) -> dict[str, Any]:
    if not val.get("VALIDATE_PASS"):
        return {"promoted": False, "reason": "VALIDATE_NOT_PASS", "CBOND_CURRENT_PROMOTED": False}
    new_products = [
        ("TUSHARE_CBOND_RATING_R1", "L2", "CBOND", "event", "Tushare cb_rating clean events; not as-of"),
        ("TUSHARE_CBOND_RATING_PIT_R1", "L1", "CBOND", "pit_interval", "CBOND rating PIT next trade day after ann_date"),
        ("TUSHARE_CBOND_CALL_PIT_R1", "L1", "CBOND", "pit_event", "CBOND call/redeem PIT next trade day after ann_date"),
        ("TUSHARE_CBOND_REMAIN_SIZE_PIT_R1", "L1", "CBOND", "pit_interval", "CBOND remain_size PIT next trade day after publish_date"),
        ("TUSHARE_CBOND_TOP10_HOLDERS_R1", "L2", "CBOND", "report_period", "CBOND top10 holders report-period only; PIT not ready"),
    ]
    cat = CATALOG_CSV.read_text(encoding="utf-8")
    existing = {ln.split(",")[0] for ln in cat.splitlines()[1:] if ln.strip()}
    add_lines = [f"{pid},{layer},{asset},ACTIVE,{grain},{desc}" for pid, layer, asset, grain, desc in new_products if pid not in existing]
    if add_lines:
        if not cat.endswith("\n"):
            cat += "\n"
        guarded_write_path(CATALOG_CSV, cat + "\n".join(add_lines) + "\n")

    path_map = {pid: str(R1_CACHE / pid) for pid in R1_PRODUCTS}
    for pid, *_ in new_products:
        path_map[pid] = str(CACHE_ROOT / pid)
    ptr = {
        "cache_release_id": CACHE_REL_ID,
        "release_root": str(CACHE_ROOT),
        "parent_release_id": R1_REL_ID,
        "parent_release_root": str(R1_CACHE),
        "published_at_cn": now_cn(),
        "asof": "2026-08-14",
        "source_vendor": SOURCE_VENDOR,
        "jq_native_data": False,
        "schema_compat_target": SCHEMA_COMPAT_TARGET,
        "schema_compat_mode": "FIELD_SEMANTIC_MAPPING",
        "CBOND_CONVERT_PRICE_PIT": "NOT_READY",
        "CBOND_EOD_PIT_READY": True,
        "CBOND_EVENT_PIT_READY": True,
        "CBOND_RATING_PIT": "READY",
        "CBOND_CALL_PIT": "READY",
        "CBOND_REMAIN_SIZE_PIT": "READY",
        "CBOND_TOP10_HOLDERS": "RAW_CLEAN_READY_PIT_NOT_READY",
        "STOCK_CACHE_UNCHANGED": True,
        "reader": "脚本/blackbox_tushare_cbond_reader_r2.py",
        "product_path_map": path_map,
        "products": R1_PRODUCTS + [p[0] for p in new_products],
        "R1_PRESERVED": True,
    }
    wjson(CBOND_PTR, ptr)

    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    have = {p["product_id"] for p in index.get("products", [])}
    for pid, layer, asset, grain, desc in new_products:
        if pid in have:
            continue
        pit_pol = "NEXT_TRADE_DAY_AFTER_ANN_DATE"
        if "REMAIN" in pid:
            pit_pol = "NEXT_TRADE_DAY_AFTER_PUBLISH_DATE"
        if "TOP10" in pid:
            pit_pol = "REPORT_PERIOD_ONLY_NOT_PIT"
        index["products"].append(
            {
                "product_id": pid,
                "layer": layer,
                "asset_type": asset,
                "status": "READY" if "TOP10" not in pid else "READY_NOT_PIT",
                "grain": grain,
                "description": desc,
                "cache_release_id": CACHE_REL_ID,
                "cache_product_path": str(CACHE_ROOT / pid),
                "security_namespace": "CBOND",
                "cross_section_contract": "INNER_ON_BOND_CODE",
                "pit_policy": pit_pol,
                "source_vendor": SOURCE_VENDOR,
                "jq_native_data": False,
                "schema_compat_target": SCHEMA_COMPAT_TARGET,
                "NATIVE_JQ_DATA": False,
                "CBOND_CONVERT_PRICE_PIT": "NOT_READY",
            }
        )
    index["product_count"] = len(index["products"])
    index["cbond_cache_release_id"] = CACHE_REL_ID
    index["cbond_cache_current_root"] = str(CACHE_ROOT)
    index["cbond_parent_release_root"] = str(R1_CACHE)
    wjson(INDEX_PATH, index)
    patch_resolver()

    cap = {
        "rule_id": "BLACKBOX_CBOND_PIT_CAPABILITY_R2",
        "status": "ACTIVE",
        "asof": "2026-08-14",
        "recorded_at_cn": now_cn(),
        "FULL_PIT_READY": False,
        "CBOND_EOD_PIT_READY": True,
        "CBOND_EVENT_PIT_READY": True,
        "CBOND_CONVERT_PRICE_PIT_READY": False,
        "CBOND_RATING_PIT": "READY",
        "CBOND_CALL_PIT": "READY",
        "CBOND_REMAIN_SIZE_PIT": "READY",
        "CBOND_TOP10_HOLDERS": "RAW_CLEAN_READY_PIT_NOT_READY",
        "CBOND_FACTOR_PRO": "BLOCKED_8000_POINTS",
        "CBOND_CONVERT_PRICE_PIT": "BLOCKED_SEPARATE_PERMISSION",
        "source_vendor": SOURCE_VENDOR,
        "jq_native_data": False,
        "schema_compat_target": SCHEMA_COMPAT_TARGET,
        "HAND_DECISION_JSON": "NOT_FORGED",
        "layers": {
            "CBOND_DAILY_MARKET": {"KNOWN_AT": "EOD_SAME_DAY", "USABLE_FROM": "AFTER_CLOSE", "PIT_SAFE_FOR_NEXT_DAY": True},
            "CBOND_RATING_PIT": {"KNOWN_AT": "NEXT_TRADING_DAY_AFTER_ANN_DATE", "PIT_SAFE": True},
            "CBOND_CALL_PIT": {"KNOWN_AT": "NEXT_TRADING_DAY_AFTER_ANN_DATE", "PIT_SAFE": True},
            "CBOND_REMAIN_SIZE_PIT": {"KNOWN_AT": "NEXT_TRADING_DAY_AFTER_PUBLISH_DATE", "PIT_SAFE": True},
            "CBOND_TOP10_HOLDERS": {"KNOWN_AT": "UNKNOWN", "PIT_SAFE": False},
            "CBOND_BASIC_CURRENT_CONVERT_PRICE": {"SNAPSHOT_ONLY": True, "PIT_SAFE": False},
            "CBOND_CONVERT_PRICE_PIT": {"STATUS": "NOT_READY"},
        },
    }
    wjson(PIT_CAP_CURRENT, cap)
    wjson(HAND_RULE, cap)
    hand_append = f"""

# HAND TOP-LEVEL POINTER APPEND — CBOND PIT ENRICHMENT R2
# appended_at_cn={now_cn()}
CBOND_CACHE_RELEASE={CACHE_REL_ID}
CBOND_CACHE_PARENT={R1_REL_ID}
CBOND_RATING_PIT=READY
CBOND_CALL_PIT=READY
CBOND_REMAIN_SIZE_PIT=READY
CBOND_TOP10_HOLDERS=RAW_CLEAN_READY_PIT_NOT_READY
CBOND_FACTOR_PRO=BLOCKED_8000_POINTS
CBOND_CONVERT_PRICE_PIT=BLOCKED_SEPARATE_PERMISSION
CBOND_EOD_PIT_READY=YES
CBOND_EVENT_PIT_READY=YES
CBOND_CONVERT_PRICE_PIT_READY=NO
FULL_PIT_READY=FALSE
FUTURES=DEFERRED_NOT_READY
OPTIONS=DEFERRED_NOT_READY
ALL_BONDS=DEFERRED_NOT_READY
CBOND_READER=脚本/blackbox_tushare_cbond_reader_r2.py
HAND_DECISION_JSON=NOT_FORGED
"""
    guarded_write_path(HAND_PATH, HAND_PATH.read_text(encoding="utf-8") + hand_append)
    return {"promoted": True, "CBOND_CURRENT_PROMOTED": True, "cache_release_id": CACHE_REL_ID}


def main() -> int:
    ctx()
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    pre = must_read_preflight()
    print(f"MUST_READ_PRECHECK={pre['MUST_READ_PRECHECK']} AUTHORITY_READY={pre['AUTHORITY_READY']}", flush=True)
    if pre["MUST_READ_PRECHECK"] != "PASS":
        print("STOP AUTHORITY_READY=NO", flush=True)
        return FAIL
    base = freeze_stock_and_r1()
    print(f"STOCK_BASELINE_ID={base['STOCK_CURRENT_ID']}", flush=True)

    import pandas as pd
    import tushare as ts

    token = load_token()
    pro = ts.pro_api(token)
    audit = run_probes(pro)
    rating_probe = audit["probes"]["cb_rating"]
    top10_probe = audit["probes"]["top10_cb_holders"]
    factor_probe = audit["probes"]["cb_factor_pro"]
    factor_status = "PROBE_OK_DOWNLOAD_NO_PER_R2_SCOPE"
    if factor_probe.get("status") == "PERMISSION_BLOCKED_POINTS_8000":
        factor_status = "PERMISSION_BLOCKED_POINTS_8000"
    elif factor_probe.get("status") == "PERMISSION_BLOCKED":
        factor_status = "PERMISSION_BLOCKED_POINTS_THRESHOLD"
    elif factor_probe.get("status") != "OK":
        factor_status = str(factor_probe.get("status"))

    basic = r1_read("TUSHARE_CBOND_BASIC_R1")
    issue = r1_read("TUSHARE_CBOND_ISSUE_R1")
    call_r1 = r1_read("TUSHARE_CBOND_CALL_R1")
    share_r1 = r1_read("TUSHARE_CBOND_SHARE_R1")
    rate = r1_read("TUSHARE_CBOND_RATE_R1")
    bridge = r1_read("TUSHARE_CBOND_STOCK_BRIDGE_R1")
    codes = sorted({str(x) for x in basic["ts_code"].dropna().tolist()}) if "ts_code" in basic.columns else sorted({str(x) for x in basic["bond_code_ts"].dropna().tolist()})
    pre_codes = []
    if "list_date" in basic.columns:
        for _, r in basic.iterrows():
            ld = ymd(r.get("list_date"))
            code = str(r.get("ts_code") or r.get("bond_code_ts"))
            if ld and ld < START:
                pre_codes.append(code)
        pre_codes = sorted(set(pre_codes))
    carry_audit = {
        "cb_basic_rows": int(len(basic)),
        "cb_issue_rows": int(len(issue)),
        "cb_rate_rows": int(len(rate)),
        "cb_call_rows": int(len(call_r1)),
        "cb_share_rows": int(len(share_r1)),
        "prewindow_listed": len(pre_codes),
        "REDOWNLOAD_SUBJECT": "NO",
    }
    wjson(TASK_DIR / "R1_CARRYIN_AUDIT.json", carry_audit)

    cal = download_trade_cal(pro)
    rating_dl = {"status": "SKIP", "rows": 0}
    if rating_probe.get("status") not in {"PERMISSION_BLOCKED", "PERMISSION_BLOCKED_POINTS_8000", "API_NOT_FOUND"}:
        rating_dl = download_rating(pro, codes)
    else:
        rating_dl = {"status": rating_probe.get("status"), "rows": 0}
    top10_ok = top10_probe.get("status") == "OK"
    top10_dl = download_top10(pro, codes, top10_ok)
    call_carry = download_carryin(pro, "cb_call", pre_codes, CB_CALL_FIELDS)
    share_carry = download_carryin(pro, "cb_share", pre_codes, CB_SHARE_FIELDS)

    rating_raw = concat_raw("cb_rating")
    top10_raw = concat_raw("top10_cb_holders")
    call_carry_df = concat_raw("cb_call")
    share_carry_df = concat_raw("cb_share")

    if rating_dl.get("status") != "DOWNLOADED" or rating_raw.empty:
        wjson(TASK_DIR / "FAIL.json", {"reason": "CB_RATING_DOWNLOAD_FAILED", "rating_dl": rating_dl, "probe": rating_probe})
        print("FINAL_STATUS=TUSHARE_CBOND_5Y_DATA_PLANE_R2_REVIEW_REQUIRED reason=RATING", flush=True)
        return FAIL

    rating_clean, rating_pit, _ = build_rating_pit(rating_raw, cal)
    call_pit = build_call_pit(call_r1, call_carry_df if len(call_carry_df) else None, cal)
    remain_pit = build_remain_pit(share_r1, share_carry_df if len(share_carry_df) else None, issue, basic, cal)
    top10_clean = clean_top10(top10_raw) if len(top10_raw) else pd.DataFrame()

    leak = leakage_tests(rating_pit, call_pit, remain_pit, cal)
    join = local_stock_join_check()
    r1u = r1_untouched(base)
    stk = stock_after(base)

    rating_dups = 0
    if len(rating_pit):
        rating_dups = int(rating_pit.duplicated(["bond_code_jq", "pit_valid_from"]).sum())
    mapped = int(bridge["stock_code_jq"].notna().sum()) if len(bridge) and "stock_code_jq" in bridge.columns else 0
    total_b = int(len(bridge)) if len(bridge) else 0

    val = {
        "VALIDATE_PASS": leak["PIT_LEAKAGE_FAILURES"] == 0
        and r1u["R1_UNTOUCHED"]
        and stk["STOCK_CURRENT_CHANGED"] == "NO"
        and int(stk["STOCK_PRODUCT_MUTATION_COUNT"]) == 0
        and len(rating_pit) > 0
        and len(call_pit) > 0
        and len(remain_pit) > 0
        and rating_dups == 0,
        "PIT_LEAKAGE_FAILURES": leak["PIT_LEAKAGE_FAILURES"],
        "R1_UNTOUCHED": r1u,
        "stock": stk,
        "join": join,
        "rating_dups": rating_dups,
    }
    wjson(TASK_DIR / "VALIDATE_REPORT.json", val)

    promo = {"promoted": False, "CBOND_CURRENT_PROMOTED": False}
    if val["VALIDATE_PASS"]:
        promo = promote(val)
    else:
        print("VALIDATE_FAIL no CURRENT promotion", flush=True)

    accepted = bool(val["VALIDATE_PASS"]) and bool(promo.get("promoted"))
    body = {
        "MUST_READ_PRECHECK": pre["MUST_READ_PRECHECK"],
        "FINAL_STATUS": "TUSHARE_CBOND_5Y_DATA_PLANE_R2_PIT_ENRICHMENT_ACCEPTED" if accepted else "TUSHARE_CBOND_5Y_DATA_PLANE_R2_REVIEW_REQUIRED",
        "CB_RATING_DOWNLOAD_STATUS": rating_dl.get("status"),
        "CB_RATING_ROWS": int(len(rating_raw)),
        "CB_RATING_BONDS": int(rating_raw["ts_code"].nunique()) if len(rating_raw) and "ts_code" in rating_raw.columns else 0,
        "CB_RATING_DUPLICATES": rating_dups,
        "CB_RATING_PIT_STATUS": "READY" if len(rating_pit) and rating_dups == 0 else "FAIL",
        "CB_RATING_PIT_ROWS": int(len(rating_pit)),
        "TOP10_CB_HOLDERS_PERMISSION": top10_probe.get("status"),
        "TOP10_CB_HOLDERS_DOWNLOAD_STATUS": top10_dl.get("status"),
        "TOP10_CB_HOLDERS_ROWS": int(len(top10_raw)),
        "TOP10_CB_HOLDERS_PIT_STATUS": "NOT_READY",
        "CB_CALL_SOURCE_ROWS": int(len(call_r1)),
        "CB_CALL_CARRYIN": call_carry,
        "CB_CALL_PIT_ROWS": int(len(call_pit)),
        "CB_CALL_PIT_STATUS": "READY" if len(call_pit) else "FAIL",
        "CB_SHARE_SOURCE_ROWS": int(len(share_r1)),
        "CB_SHARE_CARRYIN": share_carry,
        "CB_REMAIN_SIZE_PIT_ROWS": int(len(remain_pit)),
        "CB_REMAIN_SIZE_PIT_STATUS": "READY" if len(remain_pit) else "FAIL",
        "CB_FACTOR_PRO_STATUS": factor_status,
        "CB_PRICE_CHG_STATUS": "SEPARATE_PERMISSION_BLOCKED_DO_NOT_RETRY",
        "PIT_LEAKAGE_TESTS": leak["n_cases"],
        "PIT_LEAKAGE_FAILURES": leak["PIT_LEAKAGE_FAILURES"],
        "BOND_STOCK_MAPPING_RATE": (mapped / total_b) if total_b else None,
        "LOCAL_STOCK_JOIN_STATUS": join,
        "STOCK_CURRENT_BEFORE_SHA256": stk["STOCK_CURRENT_BEFORE_SHA256"],
        "STOCK_CURRENT_AFTER_SHA256": stk["STOCK_CURRENT_AFTER_SHA256"],
        "STOCK_CURRENT_CHANGED": stk["STOCK_CURRENT_CHANGED"],
        "STOCK_PRODUCT_MUTATION_COUNT": stk["STOCK_PRODUCT_MUTATION_COUNT"],
        "CBOND_CODE_IN_STOCK_UNIVERSE": 0,
        "SOURCE_VENDOR": SOURCE_VENDOR,
        "JQ_NATIVE_DATA": False,
        "CATALOG_REGISTERED": bool(promo.get("promoted")),
        "INDEX_REGISTERED": bool(promo.get("promoted")),
        "RESOLVER_REGISTERED": bool(promo.get("promoted")),
        "HAND_UPDATED": bool(promo.get("promoted")),
        "CBOND_CURRENT_PROMOTED": bool(promo.get("CBOND_CURRENT_PROMOTED")),
        "limiter": LIMITER.snapshot(),
        "secret_value_printed": False,
    }
    wjson(TASK_DIR / "FINAL_ACCEPTANCE.json", body)
    print(json.dumps({k: body[k] for k in ("FINAL_STATUS", "MUST_READ_PRECHECK", "CB_RATING_PIT_STATUS", "CB_CALL_PIT_STATUS", "CB_REMAIN_SIZE_PIT_STATUS", "PIT_LEAKAGE_FAILURES", "STOCK_CURRENT_CHANGED", "CBOND_CURRENT_PROMOTED")}, ensure_ascii=False, indent=2), flush=True)
    return OK if accepted else FAIL


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise
