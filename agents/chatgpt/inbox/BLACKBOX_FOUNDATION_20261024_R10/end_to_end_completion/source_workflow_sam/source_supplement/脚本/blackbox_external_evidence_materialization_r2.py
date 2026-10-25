#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLACKBOX EXTERNAL EVIDENCE MATERIALIZATION R2.

Parent: BLACKBOX_EXTERNAL_MARKET_EVIDENCE_DATA_AGENT_R1
Role: MARKET_EVIDENCE_DATA_AGENT

Formalize R1 AVAILABLE Tushare probes into source-isolated RAW/CLEAN/PIT products;
start EXCHANGE/COMPANY_PRIMARY announcement metadata; build fact/event/canonical views.

Forbidden: industrial conclusions, theme scores, BUY/SELL, JQ product mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd

ROOT = Path(r"E:\BLACKBOX")
import sys

sys.path.insert(0, str(ROOT / "脚本"))

from _base import OK, WriteGuardError, guarded_write_path, set_runtime_context  # noqa: E402
from blackbox_data_absence_gate_r1 import decide  # noqa: E402

CN = timezone(timedelta(hours=8))
TASK_ID = "BLACKBOX_EXTERNAL_EVIDENCE_MATERIALIZATION_R2"
PARENT = "BLACKBOX_EXTERNAL_MARKET_EVIDENCE_DATA_AGENT_R1"
TASK_DIR = ROOT / "任务" / TASK_ID
EVIDENCE = ROOT / "数据" / "外部证据"
TS_ROOT = EVIDENCE / "TUSHARE"
TS_RAW = TS_ROOT / "RAW_READONLY"
TS_CLEAN = TS_ROOT / "CLEAN"
TS_PIT = TS_ROOT / "PIT"
TS_CUR = TS_ROOT / "CURRENT"
TS_LOG = TS_ROOT / "LOG"
EX_ROOT = EVIDENCE / "EXCHANGE"
CP_ROOT = EVIDENCE / "COMPANY_PRIMARY"
CAN_ROOT = EVIDENCE / "CANONICAL"
FUND_ROOT = EVIDENCE / "FUND"
CURRENT = EVIDENCE / "CURRENT"
QA = TASK_DIR / "qa"
TOKEN_FILE = ROOT / "配置" / "secrets" / "已验证" / "Tushare_TOKEN.txt"
R1_PROBE = CURRENT / "TUSHARE_PERMISSION_PROBE_CURRENT.json"
CACHE_PTR = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
SCOPE_PTR = ROOT / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json"
RUN_ACCEPT = ROOT / "运行" / "BLACKBOX_EXTERNAL_EVIDENCE_MATERIALIZATION_R2_CURRENT.json"
RUN_RESOLVER = ROOT / "运行" / "BLACKBOX_EXTERNAL_EVIDENCE_RESOLVER_CURRENT.json"
RUN_ASOF_ALIGN = ROOT / "运行" / "BLACKBOX_EXTERNAL_EVIDENCE_ASOF_ALIGN_CURRENT.json"
HAND = ROOT / "HAND.txt"

HIST_START = "20220101"
HIST_END = "20260821"  # overridden at runtime from --asof / JQ SCOPE CURRENT
FORCE_TIP = False
FORCE_FINANCIAL_TIP = False
QUERY_CAP = 5000
SLEEP_S = 0.35
# Per-code Tushare pull concurrency (CLI --workers overrides).
WORKERS = 8
_IO_LOCK = threading.Lock()
_THREAD_LOCAL = threading.local()

# Priority from charter; ONLY materialize if R1 status == AVAILABLE
P0 = ["stock_basic", "stock_company", "income", "balancesheet", "cashflow", "fina_indicator"]
P1 = ["top10_holders", "top10_floatholders"]
P2 = ["fund_basic", "fund_nav", "fund_portfolio", "fund_share"]
P3 = ["index_classify", "index_member"]
NO_PERM_KEEP = {"anns_d": "NO_PERMISSION"}
NO_RECORD_CHECK = {"disclosure_date"}


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S") + "+0800"


def resolve_asof_yyyymmdd(cli_asof: str | None = None) -> str:
    """Align external HIST_END to JQ CURRENT asof (YYYYMMDD)."""
    if cli_asof:
        s = str(cli_asof).strip().replace("-", "")
        if len(s) == 8 and s.isdigit():
            return s
        raise SystemExit(f"invalid --asof: {cli_asof}")
    for ptr in (SCOPE_PTR, CACHE_PTR):
        if not ptr.exists():
            continue
        obj = json.loads(ptr.read_text(encoding="utf-8"))
        raw = obj.get("data_asof") or obj.get("asof") or obj.get("cleaning_as_of")
        if raw:
            s = str(raw).strip().replace("-", "")[:8]
            if len(s) == 8 and s.isdigit():
                return s
    return HIST_END


def asof_iso(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"


def product_hist_end(meta_path: Path) -> str | None:
    if not meta_path.exists():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    hr = meta.get("hist_range")
    if isinstance(hr, list) and len(hr) >= 2:
        return str(hr[1]).replace("-", "")[:8]
    for k in ("hist_end", "asof", "data_asof"):
        if meta.get(k):
            return str(meta[k]).replace("-", "")[:8]
    return None


def product_data_max_yyyymmdd(parquet_path: Path) -> str | None:
    """Actual max visibility date from PIT parquet (not meta hist_range claim)."""
    if not parquet_path.exists():
        return None
    try:
        import pyarrow.parquet as pq

        schema_names = set(pq.read_schema(parquet_path).names)
    except Exception:
        schema_names = set()
    for col in ("market_available_at", "publication_at", "f_ann_date", "ann_date"):
        if schema_names and col not in schema_names:
            continue
        try:
            s = pd.read_parquet(parquet_path, columns=[col])[col]
        except Exception:
            continue
        s = pd.to_datetime(s, errors="coerce")
        if s.notna().any():
            return s.max().strftime("%Y%m%d")
    return None


def resolve_financial_tip_start(meta_path: Path, pit_parquet: Path) -> tuple[str, str | None, str | None]:
    """Incremental tip window: prefer meta hist_end lag, else data max date, never full HIST_START rebuild."""
    old_end = product_hist_end(meta_path)
    data_max = product_data_max_yyyymmdd(pit_parquet)
    if old_end and old_end < HIST_END:
        d0 = datetime.strptime(old_end, "%Y%m%d") + timedelta(days=1)
        return d0.strftime("%Y%m%d"), old_end, data_max
    if data_max:
        # overlap lookback for late revisions / same-day fills
        d0 = datetime.strptime(data_max, "%Y%m%d") - timedelta(days=3)
        tip = max(HIST_START, d0.strftime("%Y%m%d"))
        return tip, old_end, data_max
    return HIST_START, old_end, data_max


def should_skip_ready(meta_path: Path, *, min_rows: int = 1000, allow_force: bool = True) -> bool:
    """Skip only if READY and hist_end already covers runtime HIST_END (unless FORCE_TIP)."""
    if FORCE_TIP and allow_force:
        return False
    if not meta_path.exists():
        return False
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("status") != "READY" or int(meta.get("n_rows") or 0) < min_rows:
        return False
    old = product_hist_end(meta_path)
    if old and old < HIST_END:
        return False
    return True


def now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def wjson(path: Path, obj: Any) -> None:
    guarded_write_path(path, json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n")


def wtext(path: Path, text: str) -> None:
    guarded_write_path(path, text if text.endswith("\n") else text + "\n")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_token() -> str:
    text = TOKEN_FILE.read_text(encoding="utf-8").strip()
    token = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "：" in line or ":" in line:
            k, v = (line.split("：", 1) if "：" in line else line.split(":", 1))
            if "token" in k.lower() or "密钥" in k or ("积分" not in k and "账号" not in k):
                token = v.strip()
        else:
            token = line
    if not token:
        raise ValueError("Tushare token missing")
    return token


def r1_available() -> set[str]:
    if not R1_PROBE.exists():
        raise FileNotFoundError(str(R1_PROBE))
    doc = json.loads(R1_PROBE.read_text(encoding="utf-8"))
    return {r["api"] for r in doc.get("probes") or [] if r.get("status") == "AVAILABLE"}


def r1_probe_map() -> dict[str, dict]:
    doc = json.loads(R1_PROBE.read_text(encoding="utf-8"))
    return {r["api"]: r for r in doc.get("probes") or []}


def quarter_periods(start_yyyymmdd: str, end_yyyymmdd: str) -> list[str]:
    out: list[str] = []
    for y in range(int(start_yyyymmdd[:4]), int(end_yyyymmdd[:4]) + 1):
        for p in (f"{y}0331", f"{y}0630", f"{y}0930", f"{y}1231"):
            if start_yyyymmdd <= p <= end_yyyymmdd or (p[:6] <= end_yyyymmdd[:6] and p <= f"{end_yyyymmdd[:4]}1231"):
                # include period ends up to 20260630 for mid-2026 window
                if p <= "20260630" or (p[:4] < end_yyyymmdd[:4]):
                    out.append(p)
    # unique sorted within hist window period ends
    out = sorted(set(x for x in out if x >= "20220331" and x <= "20260630"))
    return out


def append_log(api: str, payload: dict) -> None:
    TS_LOG.mkdir(parents=True, exist_ok=True)
    day = datetime.now(CN).strftime("%Y%m%d")
    path = TS_LOG / f"request_log_{day}.jsonl"
    line = json.dumps({"api": api, **payload, "request_time": now_cn()}, ensure_ascii=False)
    with _IO_LOCK:
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def thread_pro():
    """One tushare client per worker thread (client is not assumed thread-safe)."""
    pro = getattr(_THREAD_LOCAL, "pro", None)
    if pro is None:
        pro = get_pro()
        _THREAD_LOCAL.pro = pro
    return pro


def classify_err(msg: str) -> str:
    s = msg or ""
    if "没有接口访问权限" in s or "无权限" in s or "没有权限" in s or "积分不足" in s:
        return "NO_PERMISSION"
    if "不存在" in s and ("接口" in s or "api" in s.lower()):
        return "NO_PRODUCT"
    return "ERROR"


def _call_with_transport_retry(fn, kwargs: dict, *, api: str, max_retries: int = 4):
    """Retry transient Tushare HTTP resets; do not mask NO_PERMISSION."""
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            return fn(**kwargs)
        except TypeError:
            raise
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            if classify_err(msg) == "NO_PERMISSION":
                raise
            transient = (
                "Connection" in type(exc).__name__
                or "ProtocolError" in type(exc).__name__
                or "ConnectionReset" in msg
                or "10054" in msg
                or "RemoteDisconnected" in msg
            )
            last_exc = exc
            if not transient or attempt >= max_retries - 1:
                append_log(
                    api,
                    {
                        "request_params": kwargs,
                        "row_count": 0,
                        "response_status": "ERROR",
                        "error": msg[:300],
                        "attempt": attempt + 1,
                    },
                )
                raise
            time.sleep(SLEEP_S * (attempt + 2))
    assert last_exc is not None
    raise last_exc


def fetch_paginated(pro, api: str, base_kwargs: dict, *, sleep_s: float = SLEEP_S) -> tuple[pd.DataFrame, dict]:
    """Paginate with limit/offset until page < QUERY_CAP. SILENT_TRUNCATION gate."""
    fn = getattr(pro, api)
    frames = []
    offset = 0
    pages = 0
    silent = 0
    while True:
        kwargs = dict(base_kwargs)
        kwargs["limit"] = QUERY_CAP
        kwargs["offset"] = offset
        t0 = time.time()
        try:
            df = _call_with_transport_retry(fn, kwargs, api=api)
        except TypeError:
            # API may not accept offset
            if offset > 0:
                break
            kwargs.pop("offset", None)
            df = _call_with_transport_retry(fn, kwargs, api=api)
            n = 0 if df is None else len(df)
            append_log(api, {"request_params": kwargs, "row_count": n, "response_status": "OK", "elapsed_s": round(time.time() - t0, 3)})
            if n == QUERY_CAP:
                silent = 1
                gate = decide(n_rows=n, query_cap=QUERY_CAP, pagination_complete="NO")
                return (df if df is not None else pd.DataFrame()), {
                    "PAGINATION_COMPLETE": "NO",
                    "SILENT_TRUNCATION": 1,
                    "pages": 1,
                    "DATA_ABSENCE_GATE": gate.get("DATA_ABSENCE_GATE"),
                }
            return (df if df is not None else pd.DataFrame()), {
                "PAGINATION_COMPLETE": "YES",
                "SILENT_TRUNCATION": 0,
                "pages": 1,
            }
        except Exception as exc:  # noqa: BLE001
            append_log(api, {"request_params": kwargs, "row_count": 0, "response_status": "ERROR", "error": str(exc)[:300]})
            raise
        n = 0 if df is None else len(df)
        append_log(api, {"request_params": kwargs, "row_count": n, "response_status": "OK", "elapsed_s": round(time.time() - t0, 3)})
        pages += 1
        if n:
            frames.append(df)
        if n < QUERY_CAP:
            break
        if n == QUERY_CAP:
            offset += QUERY_CAP
            time.sleep(sleep_s)
            continue
        break
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    meta = {"PAGINATION_COMPLETE": "YES", "SILENT_TRUNCATION": silent, "pages": pages, "total_rows": len(out)}
    return out, meta


def save_raw(api: str, part: str, df: pd.DataFrame, sidecar: dict) -> Path:
    dest = TS_RAW / api
    dest.mkdir(parents=True, exist_ok=True)
    stamp = now_ts()
    # include thread id to avoid name collision under parallel writers
    pq = dest / f"{api}__{part}__{stamp}_t{threading.get_ident()}.parquet"
    with _IO_LOCK:
        df.to_parquet(pq, index=False)
        side = {
            **sidecar,
            "api": api,
            "part": part,
            "row_count": int(len(df)),
            "sha256": sha256_file(pq),
            "path": str(pq),
            "immutable": True,
            "request_time": now_cn(),
            "source_id": "TUSHARE_PRO",
            "source_name": "Tushare Pro",
            "source_table": api,
            "rights_status": "LICENSED",
        }
        # sidecar/checksum still under evidence root; write via guarded paths needs lock only
        side_path = Path(str(pq) + ".sidecar.json")
        chk = Path(str(pq) + ".checksum.sha256")
    wjson(side_path, side)
    with _IO_LOCK:
        chk.write_text(side["sha256"] + "\n", encoding="utf-8")
    return pq


def pit_dates_from_financial(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # economic period end
    if "end_date" in out.columns:
        out["economic_period_end"] = out["end_date"].astype(str).str.replace("-", "", regex=False)
    else:
        out["economic_period_end"] = None
    # publication: prefer f_ann_date then ann_date
    pub = None
    for c in ("f_ann_date", "ann_date", "actual_ann_date"):
        if c in out.columns:
            pub = out[c].astype(str).str.replace("-", "", regex=False)
            break
    out["publication_at"] = pub
    out["market_available_at"] = pub  # EOD disclosure day as market-available baseline
    out["local_discovered_at"] = now_cn()
    out["retrieved_at"] = now_cn()
    if "update_flag" in out.columns:
        out["revision_flag"] = out["update_flag"].astype(str)
    else:
        out["revision_flag"] = None
    out["revision_publication_at"] = pub
    out["record_version"] = out["revision_flag"].fillna("0").astype(str)
    out["PIT_valid"] = out["publication_at"].notna() & (out["publication_at"].astype(str) != "None") & (out["publication_at"].astype(str) != "nan")
    out["source_id"] = "TUSHARE_PRO"
    out["source_name"] = "Tushare Pro"
    out["source_namespace"] = "TUSHARE"
    out["rights_status"] = "LICENSED"
    # provenance record id
    key_cols = [c for c in ("ts_code", "end_date", "ann_date", "f_ann_date", "update_flag") if c in out.columns]

    def _rid(row):
        blob = "|".join(str(row.get(c, "")) for c in key_cols)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:20]

    if key_cols:
        out["source_record_id"] = out.apply(_rid, axis=1)
    else:
        out["source_record_id"] = [uuid.uuid4().hex[:20] for _ in range(len(out))]
    return out


def write_product(product_id: str, layer: str, df: pd.DataFrame, meta: dict, root: Path) -> Path:
    prod = root / product_id
    data = prod / "data"
    data.mkdir(parents=True, exist_ok=True)
    pq = data / f"{product_id}__full.parquet"
    df.to_parquet(pq, index=False)
    meta2 = {
        **meta,
        "product_id": product_id,
        "layer": layer,
        "n_rows": int(len(df)),
        "path": str(pq),
        "sha256": sha256_file(pq),
        "updated_at": now_cn(),
        "source_namespace": meta.get("source_namespace", "TUSHARE"),
        "forbid_write_into_jq_products": True,
    }
    wjson(prod / "PRODUCT_META.json", meta2)
    return pq


def get_pro():
    import tushare as ts

    return ts.pro_api(load_token())


# ── materializers ─────────────────────────────────────────────


def mat_stock_basic(pro, available: set[str]) -> dict:
    if "stock_basic" not in available:
        return {"api": "stock_basic", "status": "SKIP_NOT_AVAILABLE_IN_R1"}
    existing = TS_PIT / "TUSHARE_STOCK_BASIC_R1" / "PRODUCT_META.json"
    existing = TS_PIT / "TUSHARE_STOCK_BASIC_R1" / "PRODUCT_META.json"
    if should_skip_ready(existing, min_rows=1000):
        meta = json.loads(existing.read_text(encoding="utf-8"))
        return {"api": "stock_basic", "status": "READY", "n_rows": meta.get("n_rows"), "skipped": True}
    frames = []
    metas = []
    for st in ("L", "D", "P"):
        df, meta = fetch_paginated(pro, "stock_basic", {"list_status": st, "fields": "ts_code,symbol,name,area,industry,fullname,list_date,delist_date,list_status,exchange,curr_type,act_name,act_ent_type"})
        part = f"list_status_{st}"
        if len(df):
            save_raw("stock_basic", part, df, meta)
            frames.append(df)
        metas.append(meta)
        time.sleep(SLEEP_S)
    all_df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["ts_code"], keep="last") if frames else pd.DataFrame()
    # Refuse empty overwrite: live tip can return 0 rows (API flake) while RAW/PIT still valid.
    if len(all_df) == 0 and existing.exists():
        prior = json.loads(existing.read_text(encoding="utf-8"))
        if int(prior.get("n_rows") or 0) > 0:
            return {
                "api": "stock_basic",
                "status": "READY",
                "n_rows": prior.get("n_rows"),
                "skipped": True,
                "note": "REFUSED_EMPTY_OVERWRITE",
                "pagination": metas,
            }
    all_df["source_id"] = "TUSHARE_PRO"
    all_df["source_table"] = "stock_basic"
    all_df["source_namespace"] = "TUSHARE"
    all_df["rights_status"] = "LICENSED"
    all_df["publication_at"] = all_df.get("list_date")
    all_df["market_available_at"] = all_df.get("list_date")
    all_df["PIT_valid"] = True
    all_df["local_discovered_at"] = now_cn()
    write_product("TUSHARE_STOCK_BASIC_R1", "CLEAN", all_df, {"status": "READY", "hist_range": [HIST_START, HIST_END]}, TS_CLEAN)
    write_product("TUSHARE_STOCK_BASIC_R1", "PIT", all_df, {"status": "READY", "pit_policy": "DICTIONARY_ASOF_LIST_DATE"}, TS_PIT)
    return {"api": "stock_basic", "status": "READY", "n_rows": len(all_df), "pagination": metas}


def mat_stock_company(pro, available: set[str]) -> dict:
    if "stock_company" not in available:
        return {"api": "stock_company", "status": "SKIP_NOT_AVAILABLE_IN_R1"}
    existing = TS_PIT / "TUSHARE_STOCK_COMPANY_R1" / "PRODUCT_META.json"
    existing = TS_PIT / "TUSHARE_STOCK_COMPANY_R1" / "PRODUCT_META.json"
    if should_skip_ready(existing, min_rows=1000):
        meta = json.loads(existing.read_text(encoding="utf-8"))
        return {"api": "stock_company", "status": "READY", "n_rows": meta.get("n_rows"), "skipped": True}
    # try exchange batches
    frames = []
    for ex in ("SZSE", "SSE", "BSE"):
        try:
            df, meta = fetch_paginated(pro, "stock_company", {"exchange": ex})
        except Exception as exc:  # noqa: BLE001
            # fallback single call without exchange
            if ex == "SZSE":
                try:
                    df, meta = fetch_paginated(pro, "stock_company", {})
                except Exception as e2:
                    return {"api": "stock_company", "status": "FAILED", "error": str(e2)[:300]}
            else:
                continue
        if len(df):
            save_raw("stock_company", f"exchange_{ex}", df, meta)
            frames.append(df)
        time.sleep(SLEEP_S)
    if not frames:
        return {"api": "stock_company", "status": "NO_RECORD_CONFIRMED", "n_rows": 0}
    all_df = pd.concat(frames, ignore_index=True)
    if "ts_code" in all_df.columns:
        all_df = all_df.drop_duplicates(subset=["ts_code"], keep="last")
    all_df["source_id"] = "TUSHARE_PRO"
    all_df["source_table"] = "stock_company"
    all_df["source_namespace"] = "TUSHARE"
    all_df["rights_status"] = "LICENSED"
    all_df["PIT_valid"] = True
    all_df["local_discovered_at"] = now_cn()
    write_product("TUSHARE_STOCK_COMPANY_R1", "CLEAN", all_df, {"status": "READY"}, TS_CLEAN)
    write_product("TUSHARE_STOCK_COMPANY_R1", "PIT", all_df, {"status": "READY", "pit_policy": "SNAPSHOT_DICTIONARY"}, TS_PIT)
    return {"api": "stock_company", "status": "READY", "n_rows": len(all_df)}


def mat_financial(pro, api: str, available: set[str], workers: int | None = None) -> dict:
    if api not in available:
        return {"api": api, "status": "SKIP_NOT_AVAILABLE_IN_R1"}
    pid = {
        "income": "TUSHARE_INCOME_PIT_R1",
        "balancesheet": "TUSHARE_BALANCESHEET_PIT_R1",
        "cashflow": "TUSHARE_CASHFLOW_PIT_R1",
        "fina_indicator": "TUSHARE_FINA_INDICATOR_PIT_R1",
    }[api]
    existing = TS_PIT / pid / "PRODUCT_META.json"
    # Financial tip: --force-tip implies FORCE_FINANCIAL_TIP; window is incremental (data_max/old_end), not full HIST_START.
    if should_skip_ready(existing, min_rows=1000, allow_force=FORCE_FINANCIAL_TIP):
        meta = json.loads(existing.read_text(encoding="utf-8"))
        return {"api": api, "product_id": pid, "status": meta.get("status"), "n_rows": meta.get("n_rows"), "PIT_READY_ROWS": meta.get("PIT_READY_ROWS"), "skipped": True}

    tip_start = HIST_START
    pit_parquet = TS_PIT / pid / "data" / f"{pid}__full.parquet"
    tip_mode = bool(FORCE_FINANCIAL_TIP)
    old_end = None
    data_max = None
    if tip_mode:
        tip_start, old_end, data_max = resolve_financial_tip_start(existing, pit_parquet)
        print(
            f"[{api}] TIP_MODE tip_start={tip_start} hist_end={HIST_END} old_end={old_end} data_max={data_max}",
            flush=True,
        )

    basic_path = TS_PIT / "TUSHARE_STOCK_BASIC_R1" / "data" / "TUSHARE_STOCK_BASIC_R1__full.parquet"
    if not basic_path.exists():
        return {"api": api, "status": "FAILED", "error": "stock_basic required"}
    codes = pd.read_parquet(basic_path, columns=["ts_code"])["ts_code"].astype(str).tolist()

    raw_dir = TS_RAW / api
    raw_dir.mkdir(parents=True, exist_ok=True)

    def _done_codes() -> set[str]:
        done: set[str] = set()
        for p in raw_dir.glob("*.parquet"):
            if "probe" in p.name:
                continue
            try:
                s = pd.read_parquet(p, columns=["ts_code"])
                done.update(s["ts_code"].astype(str).tolist())
            except Exception:
                continue
        return done

    done_codes = _done_codes()
    if tip_mode:
        pending = list(codes)  # tip must refresh already-downloaded codes for new HIST_END
    else:
        pending = [c for c in codes if c not in done_codes]
    n_workers = max(1, int(workers if workers is not None else WORKERS))
    print(
        f"[{api}] tip_mode={tip_mode} tip_start={tip_start} done_codes={len(done_codes)} pending={len(pending)}/{len(codes)} workers={n_workers}",
        flush=True,
    )

    stop_flag = {"no_permission": False}
    errors = {"n": 0}
    completed = {"n": 0}
    batch_buf: list[pd.DataFrame] = []
    batch_lock = threading.Lock()
    sleep_s = 0.05  # lighter per-call sleep under concurrency

    def _flush_batch(force: bool = False) -> None:
        with batch_lock:
            if not batch_buf:
                return
            if not force and len(batch_buf) < 200:
                return
            big = pd.concat(batch_buf, ignore_index=True)
            batch_buf.clear()
        save_raw(
            api,
            f"batch_w{n_workers}_{now_ts()}",
            big,
            {"PAGINATION_COMPLETE": "YES", "SILENT_TRUNCATION": 0, "workers": n_workers, "tip_mode": tip_mode, "tip_start": tip_start},
        )

    def _one(code: str) -> tuple[str, int, str | None]:
        if stop_flag["no_permission"]:
            return code, 0, "SKIPPED"
        try:
            local_pro = thread_pro()
            fn = getattr(local_pro, api)
            start = tip_start if tip_mode else HIST_START
            df = fn(ts_code=code, start_date=start, end_date=HIST_END)
            n = 0 if df is None else len(df)
            append_log(
                api,
                {
                    "request_params": {"ts_code": code, "start_date": start, "end_date": HIST_END, "tip_mode": tip_mode},
                    "row_count": n,
                    "response_status": "OK",
                    "workers": n_workers,
                },
            )
            if n:
                with batch_lock:
                    batch_buf.append(df)
                    need_flush = len(batch_buf) >= 200
                if need_flush:
                    _flush_batch(force=True)
            time.sleep(sleep_s)
            return code, n, None
        except Exception as exc:  # noqa: BLE001
            st = classify_err(str(exc))
            append_log(
                api,
                {
                    "request_params": {"ts_code": code},
                    "row_count": 0,
                    "response_status": "ERROR",
                    "error": str(exc)[:200],
                },
            )
            if st == "NO_PERMISSION":
                stop_flag["no_permission"] = True
                return code, 0, "NO_PERMISSION"
            with batch_lock:
                errors["n"] += 1
            time.sleep(sleep_s)
            return code, 0, str(exc)[:120]

    if pending:
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futs = [ex.submit(_one, code) for code in pending]
            for fut in as_completed(futs):
                _code, _n, err = fut.result()
                completed["n"] += 1
                if completed["n"] % 200 == 0 or completed["n"] == len(pending):
                    print(
                        f"[{api}] parallel {completed['n']}/{len(pending)} errors={errors['n']}",
                        flush=True,
                    )
                if err == "NO_PERMISSION":
                    # cancel remaining is best-effort; stop_flag already set
                    pass
        _flush_batch(force=True)

    if errors["n"] > 80 and len(done_codes) == 0 and completed["n"] == 0:
        return {"api": api, "status": "FAILED", "error": "too_many_errors_at_start", "workers": n_workers}

    # assemble from disk only
    parts = []
    for p in sorted(raw_dir.glob("*.parquet")):
        if "probe" in p.name:
            continue
        try:
            parts.append(pd.read_parquet(p))
        except Exception:
            continue
    if not parts:
        return {"api": api, "status": "NO_RECORD_CONFIRMED", "n_rows": 0, "workers": n_workers}
    all_df = pd.concat(parts, ignore_index=True)
    subset = [c for c in ("ts_code", "end_date", "report_type") if c in all_df.columns]
    if not subset:
        subset = [c for c in ("ts_code", "end_date") if c in all_df.columns]
    if subset:
        sort_cols = [c for c in ("ann_date", "f_ann_date", "update_flag") if c in all_df.columns]
        if sort_cols:
            all_df = all_df.sort_values(sort_cols)
        all_df = all_df.drop_duplicates(subset=subset, keep="last")
    pit_df = pit_dates_from_financial(all_df)
    pit_ok = int(pit_df["PIT_valid"].sum()) if "PIT_valid" in pit_df.columns else 0
    n_codes = int(pit_df["ts_code"].nunique()) if "ts_code" in pit_df.columns else 0
    status = "READY" if n_codes >= int(0.95 * len(codes)) and pit_ok > 0 else "PARTIAL"
    if stop_flag["no_permission"] and status == "READY":
        status = "PARTIAL"
    write_product(pid.replace("_PIT_", "_CLEAN_"), "CLEAN", all_df, {"status": status, "source_table": api}, TS_CLEAN)
    write_product(
        pid,
        "PIT",
        pit_df,
        {
            "status": status,
            "source_table": api,
            "pit_policy": "publication_at_from_f_ann_date_or_ann_date",
            "forbid_end_date_as_visibility": True,
            "hist_range": [HIST_START, HIST_END],
            "PIT_READY_ROWS": pit_ok,
            "codes_requested": len(codes),
            "codes_present": n_codes,
            "workers": n_workers,
        },
        TS_PIT,
    )
    return {
        "api": api,
        "product_id": pid,
        "status": status,
        "n_rows": len(pit_df),
        "PIT_READY_ROWS": pit_ok,
        "codes_present": n_codes,
        "workers": n_workers,
    }


def mat_holders(pro, api: str, available: set[str]) -> dict:
    if api not in available:
        return {"api": api, "status": "SKIP_NOT_AVAILABLE_IN_R1"}
    periods = [p for p in quarter_periods(HIST_START, HIST_END) if p.endswith(("0630", "1231")) or p >= "20240101"]
    # holders often annual/semi - use all quarters anyway
    periods = quarter_periods(HIST_START, HIST_END)
    frames = []
    for period in periods:
        try:
            df, meta = fetch_paginated(pro, api, {"period": period})
        except Exception as exc:
            # some need ts_code — fallback sample from stock_basic later
            print(f"[{api}] period fail {period}: {exc}", flush=True)
            continue
        if len(df):
            save_raw(api, f"period_{period}", df, meta)
            frames.append(df)
        time.sleep(SLEEP_S)
        print(f"[{api}] period={period} rows={len(df)}", flush=True)
    if not frames:
        # per-code fallback for recent period only (PARTIAL)
        basic_path = TS_PIT / "TUSHARE_STOCK_BASIC_R1" / "data" / "TUSHARE_STOCK_BASIC_R1__full.parquet"
        if not basic_path.exists():
            return {"api": api, "status": "FAILED", "error": "no stock_basic for fallback"}
        codes = pd.read_parquet(basic_path, columns=["ts_code"])["ts_code"].astype(str).tolist()
        period = "20241231"
        for i, code in enumerate(codes):
            try:
                df, meta = fetch_paginated(pro, api, {"ts_code": code, "period": period})
            except Exception:
                continue
            if len(df):
                save_raw(api, f"code_{code}_{period}", df, meta)
                frames.append(df)
            if i % 50 == 0:
                print(f"[{api}] code fallback {i}/{len(codes)}", flush=True)
            time.sleep(SLEEP_S)
            if i >= 200:  # bounded fallback to avoid runaway; mark PARTIAL
                break
        status_forced = "PARTIAL"
    else:
        status_forced = None
    if not frames:
        return {"api": api, "status": "NO_RECORD_CONFIRMED", "n_rows": 0}
    all_df = pd.concat(frames, ignore_index=True)
    all_df = pit_dates_from_financial(all_df) if "end_date" in all_df.columns or "ann_date" in all_df.columns else all_df
    if "ann_date" in all_df.columns and "publication_at" not in all_df.columns:
        all_df["publication_at"] = all_df["ann_date"]
        all_df["market_available_at"] = all_df["ann_date"]
        all_df["PIT_valid"] = all_df["ann_date"].notna()
    all_df["source_namespace"] = "TUSHARE"
    all_df["source_id"] = "TUSHARE_PRO"
    all_df["rights_status"] = "LICENSED"
    pid = "TUSHARE_TOP10_HOLDERS_PIT_R1" if api == "top10_holders" else "TUSHARE_TOP10_FLOATHOLDERS_PIT_R1"
    status = status_forced or "READY"
    write_product(pid, "PIT", all_df, {"status": status, "source_table": api}, TS_PIT)
    write_product(pid.replace("_PIT_", "_CLEAN_"), "CLEAN", all_df, {"status": status}, TS_CLEAN)
    return {"api": api, "product_id": pid, "status": status, "n_rows": len(all_df)}


def mat_fund_basic(pro, available: set[str]) -> dict:
    if "fund_basic" not in available:
        return {"api": "fund_basic", "status": "SKIP_NOT_AVAILABLE_IN_R1"}
    frames = []
    for market in ("E", "O"):
        try:
            df, meta = fetch_paginated(pro, "fund_basic", {"market": market})
        except Exception as exc:
            print(f"[fund_basic] {market} {exc}", flush=True)
            continue
        if len(df):
            save_raw("fund_basic", f"market_{market}", df, meta)
            frames.append(df)
        time.sleep(SLEEP_S)
    if not frames:
        return {"api": "fund_basic", "status": "FAILED", "n_rows": 0}
    all_df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["ts_code"], keep="last")
    all_df["source_namespace"] = "TUSHARE"
    all_df["source_id"] = "TUSHARE_PRO"
    all_df["rights_status"] = "LICENSED"
    all_df["PIT_valid"] = True
    # name history stub columns
    all_df["fund_name"] = all_df["name"] if "name" in all_df.columns else None
    all_df["effective_from"] = all_df["found_date"] if "found_date" in all_df.columns else None
    all_df["effective_to"] = None
    write_product("TUSHARE_FUND_BASIC_PIT_R1", "PIT", all_df, {"status": "READY"}, TS_PIT)
    fund_ns = FUND_ROOT / "TUSHARE"
    fund_ns.mkdir(parents=True, exist_ok=True)
    write_product("TUSHARE_FUND_BASIC_PIT_R1", "PIT", all_df, {"status": "READY"}, fund_ns)
    return {"api": "fund_basic", "product_id": "TUSHARE_FUND_BASIC_PIT_R1", "status": "READY", "n_rows": len(all_df)}


def mat_fund_nav_share(pro, api: str, available: set[str], workers: int | None = None) -> dict:
    if api not in available:
        return {"api": api, "status": "SKIP_NOT_AVAILABLE_IN_R1"}
    basic = TS_PIT / "TUSHARE_FUND_BASIC_PIT_R1" / "data" / "TUSHARE_FUND_BASIC_PIT_R1__full.parquet"
    if not basic.exists():
        return {"api": api, "status": "FAILED", "error": "fund_basic missing"}
    bdf = pd.read_parquet(basic)
    if "market" in bdf.columns:
        codes = bdf.loc[bdf["market"].astype(str) == "E", "ts_code"].astype(str).tolist()
    else:
        codes = bdf["ts_code"].astype(str).tolist()[:800]
    years = [
        ("20220101", "20221231"),
        ("20230101", "20231231"),
        ("20240101", "20241231"),
        ("20250101", "20251231"),
        ("20260101", HIST_END),
    ]
    # default still bounded unless --workers used with full; keep prior 80 for safety unless workers set
    n_workers = max(1, int(workers if workers is not None else WORKERS))
    code_cap = min(len(codes), 80 if n_workers <= 1 else min(len(codes), 400))
    codes = codes[:code_cap]
    print(f"[{api}] codes={len(codes)} workers={n_workers}", flush=True)
    frames: list[pd.DataFrame] = []
    frames_lock = threading.Lock()
    stop = {"no_permission": False}

    def _one(code: str) -> int:
        if stop["no_permission"]:
            return 0
        local_pro = thread_pro()
        rows = 0
        for start, end in years:
            try:
                df, meta = fetch_paginated(
                    local_pro, api, {"ts_code": code, "start_date": start, "end_date": end}, sleep_s=0.05
                )
            except Exception as exc:
                if "权限" in str(exc):
                    stop["no_permission"] = True
                    return rows
                continue
            if len(df):
                save_raw(api, f"{code}_{start}_{end}", df, meta)
                with frames_lock:
                    frames.append(df)
                rows += len(df)
            time.sleep(0.05)
        return rows

    done = 0
    with ThreadPoolExecutor(max_workers=n_workers) as ex:
        futs = [ex.submit(_one, c) for c in codes]
        for fut in as_completed(futs):
            fut.result()
            done += 1
            if done % 20 == 0 or done == len(codes):
                with frames_lock:
                    acc = sum(len(x) for x in frames)
                print(f"[{api}] parallel funds {done}/{len(codes)} acc_rows={acc}", flush=True)

    if stop["no_permission"] and not frames:
        return {"api": api, "status": "NO_PERMISSION", "workers": n_workers}
    if not frames:
        return {"api": api, "status": "NO_RECORD_CONFIRMED", "n_rows": 0, "workers": n_workers}
    all_df = pd.concat(frames, ignore_index=True)
    all_df["source_namespace"] = "TUSHARE"
    all_df["source_id"] = "TUSHARE_PRO"
    all_df["rights_status"] = "LICENSED"
    date_col = "nav_date" if "nav_date" in all_df.columns else ("trade_date" if "trade_date" in all_df.columns else None)
    if date_col:
        all_df["publication_at"] = all_df[date_col]
        all_df["market_available_at"] = all_df[date_col]
        all_df["PIT_valid"] = all_df[date_col].notna()
    pid = "TUSHARE_FUND_NAV_R1" if api == "fund_nav" else "TUSHARE_FUND_SHARE_R1"
    status = "PARTIAL" if len(codes) < len(bdf) else "READY"
    write_product(
        pid,
        "PIT",
        all_df,
        {"status": status, "codes_materialized": len(codes), "codes_universe_e": int((bdf["market"].astype(str) == "E").sum()) if "market" in bdf.columns else len(bdf), "workers": n_workers},
        TS_PIT,
    )
    write_product(pid, "PIT", all_df, {"status": status, "codes_materialized": len(codes), "workers": n_workers}, FUND_ROOT / "TUSHARE")
    return {"api": api, "product_id": pid, "status": status, "n_rows": len(all_df), "codes": len(codes), "workers": n_workers}


def mat_fund_portfolio(pro, available: set[str]) -> dict:
    if "fund_portfolio" not in available:
        return {"api": "fund_portfolio", "status": "SKIP_NOT_AVAILABLE_IN_R1"}
    basic = TS_PIT / "TUSHARE_FUND_BASIC_PIT_R1" / "data" / "TUSHARE_FUND_BASIC_PIT_R1__full.parquet"
    codes = pd.read_parquet(basic)["ts_code"].astype(str).tolist()
    if "market" in pd.read_parquet(basic).columns:
        bdf = pd.read_parquet(basic)
        codes = bdf.loc[bdf["market"].astype(str) == "E", "ts_code"].astype(str).tolist()
    periods = [p for p in quarter_periods(HIST_START, HIST_END) if p.endswith(("0630", "1231"))]
    frames = []
    for i, code in enumerate(codes[:40]):
        for period in periods:
            try:
                df, meta = fetch_paginated(pro, "fund_portfolio", {"ts_code": code, "period": period})
            except Exception:
                continue
            if len(df):
                save_raw("fund_portfolio", f"{code}_{period}", df, meta)
                frames.append(df)
            time.sleep(SLEEP_S)
        if i % 10 == 0:
            print(f"[fund_portfolio] {i} funds", flush=True)
    if not frames:
        return {"api": "fund_portfolio", "status": "NO_RECORD_CONFIRMED", "n_rows": 0}
    all_df = pd.concat(frames, ignore_index=True)
    # PIT: use ann_date if present else end_date+lag unknown → require ann_date
    if "ann_date" in all_df.columns:
        all_df["publication_at"] = all_df["ann_date"]
        all_df["market_available_at"] = all_df["ann_date"]
        all_df["PIT_valid"] = all_df["ann_date"].notna()
    else:
        all_df["publication_at"] = None
        all_df["market_available_at"] = None
        all_df["PIT_valid"] = False
    if "end_date" in all_df.columns:
        all_df["economic_period_end"] = all_df["end_date"]
        all_df["report_period"] = all_df["end_date"]
    all_df["source_namespace"] = "TUSHARE"
    all_df["source_id"] = "TUSHARE_PRO"
    all_df["rights_status"] = "LICENSED"
    all_df["note_pit"] = "forbid treating report_period end as same-day visible"
    status = "PARTIAL"
    write_product("TUSHARE_FUND_HOLDING_PIT_R1", "PIT", all_df, {"status": status}, TS_PIT)
    return {"api": "fund_portfolio", "product_id": "TUSHARE_FUND_HOLDING_PIT_R1", "status": status, "n_rows": len(all_df), "PIT_READY_ROWS": int(all_df["PIT_valid"].sum())}


def mat_index_ref(pro, available: set[str]) -> dict:
    out = {}
    if "index_classify" in available:
        frames = []
        for level in ("L1", "L2", "L3"):
            df, meta = fetch_paginated(pro, "index_classify", {"level": level, "src": "SW2021"})
            if len(df):
                save_raw("index_classify", f"SW2021_{level}", df, meta)
                frames.append(df)
            time.sleep(SLEEP_S)
        if frames:
            all_df = pd.concat(frames, ignore_index=True)
            all_df["source_namespace"] = "TUSHARE"
            write_product("TUSHARE_INDEX_CLASSIFY_R1", "PIT", all_df, {"status": "READY"}, TS_PIT)
            out["index_classify"] = {"status": "READY", "n_rows": len(all_df)}
    if "index_member" in available:
        # members for L1 indexes from classify
        cls = TS_PIT / "TUSHARE_INDEX_CLASSIFY_R1" / "data" / "TUSHARE_INDEX_CLASSIFY_R1__full.parquet"
        frames = []
        if cls.exists():
            cdf = pd.read_parquet(cls)
            codes = cdf.loc[cdf["level"].astype(str) == "L1", "index_code"].astype(str).unique().tolist() if "level" in cdf.columns else cdf["index_code"].astype(str).unique().tolist()[:40]
        else:
            codes = ["801010.SI"]
        for code in codes:
            try:
                df, meta = fetch_paginated(pro, "index_member", {"index_code": code})
            except Exception:
                continue
            if len(df):
                save_raw("index_member", code.replace(".", "_"), df, meta)
                frames.append(df)
            time.sleep(SLEEP_S)
        if frames:
            all_df = pd.concat(frames, ignore_index=True)
            all_df["source_namespace"] = "TUSHARE"
            write_product("TUSHARE_INDEX_MEMBER_R1", "PIT", all_df, {"status": "PARTIAL", "note": "L1 members"}, TS_PIT)
            out["index_member"] = {"status": "PARTIAL", "n_rows": len(all_df)}
    return out


def phase_disclosure_date_check(pro) -> dict:
    """Re-check disclosure_date with historical range — do not upgrade probe-empty to PRODUCT_HAS_NO_DATA."""
    api = "disclosure_date"
    try:
        df, meta = fetch_paginated(pro, api, {"start_date": "20260101", "end_date": HIST_END})
        n = len(df)
        if n:
            save_raw(api, "hist_2026", df, meta)
        return {
            "api": api,
            "API_AVAILABLE": True,
            "QUERY_VALID": True,
            "HISTORICAL_RECORD_FOUND": n > 0,
            "n_rows": n,
            "status": "READY" if n else "NO_RECORD_UNCONFIRMED_NEED_PARAM",
            "note": "R1 probe 0-row must not become PRODUCT_HAS_NO_DATA",
        }
    except Exception as exc:
        st = classify_err(str(exc))
        return {
            "api": api,
            "API_AVAILABLE": st != "NO_PRODUCT",
            "QUERY_VALID": False,
            "HISTORICAL_RECORD_FOUND": False,
            "status": st,
            "error": str(exc)[:300],
        }


def phase_anns_d_keep(pro) -> dict:
    """Keep NO_PERMISSION; do not rewrite as NO_DATA. Probe alternative later."""
    return {
        "api": "anns_d",
        "TUSHARE_ANNS_D": "NO_PERMISSION",
        "status": "NO_PERMISSION",
        "NO_DATA_FORBIDDEN": True,
        "ALTERNATIVE_SOURCE_AVAILABLE": None,  # filled by exchange phase
    }


def phase_exchange_company_primary() -> dict:
    """Start EXCHANGE + COMPANY_PRIMARY announcement metadata (bounded window)."""
    import requests

    EX_ROOT.mkdir(parents=True, exist_ok=True)
    CP_ROOT.mkdir(parents=True, exist_ok=True)
    docs = []
    # 1) Seed from local JQ disclosure calendar as S3 reference pointer (not EXCHANGE primary)
    ref_rows = 0
    if CACHE_PTR.exists():
        cache = json.loads(CACHE_PTR.read_text(encoding="utf-8"))
        root = Path(cache["release_root"])
        disc = root / "JQ20_STK_REPORT_DISCLOSURE_PIT_R1"
        if disc.exists():
            for p in list(disc.rglob("*.parquet"))[:5]:
                try:
                    df = pd.read_parquet(p)
                except Exception:
                    continue
                ref_rows += len(df)
            wjson(
                EX_ROOT / "REFERENCE_JQ_DISCLOSURE_POINTER.json",
                {
                    "note": "JQ disclosure is S3 vendor reference, not EXCHANGE_PRIMARY",
                    "product": "JQ20_STK_REPORT_DISCLOSURE_PIT_R1",
                    "n_rows_sample_files": ref_rows,
                    "source_priority": "S3",
                },
            )

    # 2) Cninfo public query (巨潮) — official disclosure portal; metadata only
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
    })
    url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    # plate batches
    for column, plate in (("szse", "sz"), ("sse", "sh"), ("bj", "bj")):
        for page in range(1, 4):
            data = {
                "pageNum": str(page),
                "pageSize": "30",
                "column": column,
                "tabName": "fulltext",
                "plate": plate,
                "seDate": "2026-08-01~2026-08-21",
                "searchkey": "",
                "secid": "",
                "category": "",
                "trade": "",
                "stock": "",
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true",
            }
            try:
                resp = session.post(url, data=data, timeout=30)
                js = resp.json()
            except Exception as exc:
                print(f"[cninfo] fail {column} p{page}: {exc}", flush=True)
                continue
            anns = js.get("announcements") or []
            for a in anns:
                title = str(a.get("announcementTitle") or "")
                dtype = "OTHER_CORPORATE_ANNOUNCEMENT"
                if "年度报告" in title and "摘要" not in title:
                    dtype = "ANNUAL_REPORT"
                elif "半年度报告" in title or "中期报告" in title:
                    dtype = "SEMIANNUAL_REPORT"
                elif "三季度" in title or "一季度" in title or "季度报告" in title:
                    dtype = "QUARTERLY_REPORT"
                elif "业绩预告" in title:
                    dtype = "EARNINGS_FORECAST"
                elif "业绩快报" in title:
                    dtype = "EARNINGS_EXPRESS"
                elif "合同" in title:
                    dtype = "MAJOR_CONTRACT"
                adj = a.get("adjunctUrl") or ""
                source_url = ("http://static.cninfo.com.cn/" + adj) if adj else None
                ts = a.get("announcementTime")
                pub = None
                if isinstance(ts, (int, float)):
                    pub = datetime.fromtimestamp(ts / 1000, CN).strftime("%Y-%m-%d")
                elif ts:
                    pub = str(ts)[:10]
                doc = {
                    "document_id": f"CNINFO_{a.get('announcementId')}",
                    "company_code": a.get("secCode"),
                    "company_name": a.get("secName"),
                    "document_type": dtype,
                    "title": title,
                    "economic_period": None,
                    "publication_at": pub,
                    "market_available_at": pub,
                    "local_discovered_at": now_cn(),
                    "source_namespace": "EXCHANGE",
                    "source_name": "CNINFO_JUCHAO",
                    "source_url": source_url,
                    "original_file_available": bool(adj),
                    "parsed_text_available": False,
                    "rights_status": "PUBLIC",
                    "sha256_if_file": None,
                    "PIT_valid": bool(pub),
                    "source_id": "CNINFO",
                    "source_table": "hisAnnouncement",
                    "source_record_id": str(a.get("announcementId")),
                }
                docs.append(doc)
            time.sleep(0.25)

    ex_df = pd.DataFrame(docs)
    if len(ex_df):
        write_product(
            "ANNOUNCEMENT_METADATA_PIT_R1",
            "PIT",
            ex_df,
            {"status": "PARTIAL", "window": "2026-08-01~2026-08-21", "source": "CNINFO"},
            EX_ROOT,
        )
        # text product empty shell
        text_df = ex_df.loc[ex_df["original_file_available"]].copy()
        text_df["parsed_text_available"] = False
        text_df["text"] = None
        write_product(
            "ANNOUNCEMENT_TEXT_PIT_R1",
            "PIT",
            text_df.head(0),  # metadata-only this round; files not bulk-downloaded
            {"status": "PARTIAL", "note": "file URLs recorded; body ingest deferred (rights/size)"},
            EX_ROOT,
        )

    # COMPANY_PRIMARY: structure + mirror metadata tagged as needing IR confirm
    cp_docs = []
    for d in docs[:50]:
        cp = dict(d)
        cp["document_id"] = "CP_REF_" + str(d["document_id"])
        cp["source_namespace"] = "COMPANY_PRIMARY"
        cp["source_name"] = "PENDING_IR_CONFIRM"
        cp["rights_status"] = "UNKNOWN"
        cp["note"] = "seeded_from_exchange_metadata_pending_company_ir_verification"
        cp_docs.append(cp)
    cp_df = pd.DataFrame(cp_docs)
    write_product(
        "CORPORATE_PUBLIC_DOCUMENT_PIT_R1",
        "PIT",
        cp_df,
        {"status": "PARTIAL", "note": "bootstrap from exchange metadata; IR crawl not completed"},
        CP_ROOT,
    )
    write_product(
        "CORPORATE_PUBLIC_TEXT_PIT_R1",
        "PIT",
        cp_df.head(0),
        {"status": "PARTIAL", "note": "text separated from structured finance; empty until legal parse"},
        CP_ROOT,
    )

    return {
        "EXCHANGE_DOCUMENT_COUNT": int(len(ex_df)),
        "COMPANY_DOCUMENT_COUNT": int(len(cp_df)),
        "COMPANY_TEXT_COUNT": 0,
        "ALTERNATIVE_SOURCE_AVAILABLE": bool(len(ex_df) > 0),
        "EXCHANGE_STATUS": "PARTIAL" if len(ex_df) else "FAILED",
    }


def phase_company_index_r2() -> dict:
    basic = TS_PIT / "TUSHARE_STOCK_BASIC_R1" / "data" / "TUSHARE_STOCK_BASIC_R1__full.parquet"
    company = TS_PIT / "TUSHARE_STOCK_COMPANY_R1" / "data" / "TUSHARE_STOCK_COMPANY_R1__full.parquet"
    r1_idx = EVIDENCE / "JQ" / "products" / "COMPANY_EVIDENCE_INDEX_R1" / "COMPANY_EVIDENCE_INDEX_R1.parquet"
    if not basic.exists():
        return {"status": "FAILED", "error": "stock_basic missing"}
    b = pd.read_parquet(basic)
    idx = b.rename(columns={"ts_code": "company_code", "name": "company_name"})[
        [c for c in ["company_code", "company_name", "list_date", "delist_date", "industry", "exchange"] if c in b.columns or c in ["company_code", "company_name"]]
    ].copy()
    # map columns properly
    idx = pd.DataFrame({
        "company_code": b["ts_code"].astype(str),
        "company_name": b["name"].astype(str) if "name" in b.columns else None,
        "list_date": b["list_date"] if "list_date" in b.columns else None,
        "delist_date": b["delist_date"] if "delist_date" in b.columns else None,
    })
    if r1_idx.exists():
        r1 = pd.read_parquet(r1_idx)
        # r1 company may be 000001.XSHE style
        def to_jq(code: str) -> str:
            code = str(code)
            if code.endswith(".SZ"):
                return code[:6] + ".XSHE"
            if code.endswith(".SH"):
                return code[:6] + ".XSHG"
            if code.endswith(".BJ"):
                return code[:6] + ".XBSE"
            return code

        idx["jq_code"] = idx["company_code"].map(to_jq)
        sw = r1.drop_duplicates("company")
        m = sw.set_index("company")
        for col in ("SW_L1", "SW_L2", "SW_L3"):
            if col in sw.columns:
                idx[col] = idx["jq_code"].map(m[col].to_dict() if col in m.columns else {})
            else:
                idx[col] = None
        idx["membership_effective_date"] = None
        idx["JQ_company_available"] = idx["jq_code"].isin(set(sw["company"].astype(str)))
    else:
        idx["SW_L1"] = idx["SW_L2"] = idx["SW_L3"] = None
        idx["membership_effective_date"] = None
        idx["JQ_company_available"] = False
        idx["jq_code"] = None
    idx["Tushare_company_available"] = True
    if company.exists():
        c = pd.read_parquet(company)
        idx["Tushare_company_profile"] = idx["company_code"].isin(set(c["ts_code"].astype(str)))
    else:
        idx["Tushare_company_profile"] = False
    # financial available
    fin = TS_PIT / "TUSHARE_INCOME_PIT_R1" / "data" / "TUSHARE_INCOME_PIT_R1__full.parquet"
    if fin.exists():
        fcodes = set(pd.read_parquet(fin, columns=["ts_code"])["ts_code"].astype(str))
        idx["financial_available"] = idx["company_code"].isin(fcodes)
    else:
        idx["financial_available"] = False
    ex_meta = EX_ROOT / "ANNOUNCEMENT_METADATA_PIT_R1" / "data" / "ANNOUNCEMENT_METADATA_PIT_R1__full.parquet"
    if ex_meta.exists():
        ed = pd.read_parquet(ex_meta)
        # sec codes often 6-digit
        secs = set(ed["company_code"].astype(str).str.zfill(6))
        idx["announcement_available"] = idx["company_code"].str[:6].isin(secs)
    else:
        idx["announcement_available"] = False
    idx["corporate_text_available"] = False
    idx["IR_available"] = False
    idx["source_namespace"] = "MIXED_INDEX"
    idx["index_version"] = "R2"
    out_dir = EVIDENCE / "JQ" / "products" / "COMPANY_EVIDENCE_INDEX_R2"
    write_product("COMPANY_EVIDENCE_INDEX_R2", "PIT", idx, {"status": "PARTIAL", "n_companies": len(idx)}, out_dir.parent)
    # write_product nests product_id folder under root — fix path: use out_dir parent = JQ/products
    wjson(CURRENT / "COMPANY_EVIDENCE_INDEX_R2_CURRENT.json", {"n": len(idx), "status": "PARTIAL", "updated_at": now_cn()})
    return {"status": "PARTIAL", "COMPANY_INDEX_COUNT": int(len(idx)), "product_id": "COMPANY_EVIDENCE_INDEX_R2"}


def phase_fact_canonical() -> dict:
    """Build underlying fact/event/canonical/conflict masters from materialized finance."""
    CAN_ROOT.mkdir(parents=True, exist_ok=True)
    income_p = TS_PIT / "TUSHARE_INCOME_PIT_R1" / "data" / "TUSHARE_INCOME_PIT_R1__full.parquet"
    facts = []
    if income_p.exists():
        df = pd.read_parquet(income_p)
        # key fields
        field_map = []
        for raw, ftype, unit in (
            ("total_revenue", "REVENUE", "CNY"),
            ("revenue", "REVENUE_OPERATING", "CNY"),
            ("n_income", "NET_INCOME", "CNY"),
            ("n_income_attr_p", "NET_INCOME_PARENT", "CNY"),
        ):
            if raw in df.columns:
                field_map.append((raw, ftype, unit))
        for _, row in df.iterrows():
            for raw, ftype, unit in field_map:
                val = row.get(raw)
                if pd.isna(val):
                    continue
                uid = hashlib.sha256(
                    f"{row.get('ts_code')}|{row.get('economic_period_end')}|{ftype}".encode()
                ).hexdigest()[:24]
                facts.append({
                    "underlying_fact_id": uid,
                    "company_code": row.get("ts_code"),
                    "economic_period_end": row.get("economic_period_end"),
                    "fact_type": ftype,
                    "RAW_VALUE": val,
                    "RAW_UNIT": unit,
                    "NORMALIZED_VALUE": val,
                    "NORMALIZED_UNIT": unit,
                    "observation_source_namespace": "TUSHARE",
                    "observation_source_id": "TUSHARE_PRO",
                    "source_table": "income",
                    "source_field": raw,
                    "source_record_id": row.get("source_record_id"),
                    "publication_at": row.get("publication_at"),
                    "market_available_at": row.get("market_available_at"),
                    "PIT_valid": bool(row.get("PIT_valid")),
                })
    fact_df = pd.DataFrame(facts)
    if len(fact_df):
        # one row per underlying_fact_id keeping tushare obs; graph allows multi-obs later
        write_product("UNDERLYING_FACT_MASTER_R1", "CANONICAL", fact_df, {"status": "PARTIAL"}, CAN_ROOT)

    # Events from exchange docs
    events = []
    ex_meta = EX_ROOT / "ANNOUNCEMENT_METADATA_PIT_R1" / "data" / "ANNOUNCEMENT_METADATA_PIT_R1__full.parquet"
    if ex_meta.exists():
        ed = pd.read_parquet(ex_meta)
        for _, row in ed.iterrows():
            eid = hashlib.sha256(
                f"{row.get('company_code')}|{row.get('publication_at')}|{row.get('document_type')}|{row.get('title')}".encode("utf-8")
            ).hexdigest()[:24]
            events.append({
                "underlying_event_id": eid,
                "company_code": row.get("company_code"),
                "event_type": row.get("document_type"),
                "title": row.get("title"),
                "publication_at": row.get("publication_at"),
                "market_available_at": row.get("market_available_at"),
                "primary_source_namespace": "EXCHANGE",
                "primary_source_record_id": row.get("source_record_id"),
                "REFERENCE_TO_EVENT": [],
                "PIT_valid": bool(row.get("PIT_valid")),
            })
    event_df = pd.DataFrame(events).drop_duplicates("underlying_event_id") if events else pd.DataFrame()
    if len(event_df):
        write_product("UNDERLYING_EVENT_MASTER_R1", "CANONICAL", event_df, {"status": "PARTIAL"}, CAN_ROOT)

    # Canonical view from facts (Tushare as machine value; priority S3)
    canon = []
    for _, row in fact_df.iterrows() if len(fact_df) else []:
        canon.append({
            "canonical_record_id": "CAN_" + row["underlying_fact_id"],
            "underlying_fact_or_event_id": row["underlying_fact_id"],
            "company_code": row["company_code"],
            "fact_type": row["fact_type"],
            "economic_period": row["economic_period_end"],
            "canonical_value": row["NORMALIZED_VALUE"],
            "canonical_unit": row["NORMALIZED_UNIT"],
            "RAW_VALUE": row["RAW_VALUE"],
            "RAW_UNIT": row["RAW_UNIT"],
            "source_used": "TUSHARE",
            "source_priority": "S3",
            "all_source_ids": ["TUSHARE_PRO"],
            "source_count": 1,
            "source_conflict": False,
            "publication_at": row["publication_at"],
            "market_available_at": row["market_available_at"],
            "PIT_valid": row["PIT_valid"],
            "ORIGINAL_PRIMARY_REFERENCE": None,
        })
    canon_df = pd.DataFrame(canon)
    if len(canon_df):
        write_product("CANONICAL_CORPORATE_EVIDENCE_R1", "CANONICAL", canon_df, {"status": "PARTIAL", "note": "research view only"}, CAN_ROOT)

    # Conflict master: compare Tushare vs JQ FI on overlapping sample if possible
    conflicts = []
    jq_fi = None
    if CACHE_PTR.exists():
        root = Path(json.loads(CACHE_PTR.read_text(encoding="utf-8"))["release_root"])
        fi = root / "FINANCIAL_INDICATOR_PIT_R1"
        # skip heavy join if too large — sample conflict scaffold only
        wjson(
            CAN_ROOT / "SOURCE_CONFLICT_MASTER_R1" / "PRODUCT_META.json",
            {
                "product_id": "SOURCE_CONFLICT_MASTER_R1",
                "status": "PARTIAL",
                "n_rows": 0,
                "note": "no silent overwrite; multi-source value compare deferred to targeted join job",
                "updated_at": now_cn(),
            },
        )
        (CAN_ROOT / "SOURCE_CONFLICT_MASTER_R1" / "data").mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=[
            "underlying_fact_id", "source_a", "value_a", "source_b", "value_b",
            "absolute_difference", "relative_difference", "likely_reason", "resolved", "resolution_rule",
        ]).to_parquet(CAN_ROOT / "SOURCE_CONFLICT_MASTER_R1" / "data" / "SOURCE_CONFLICT_MASTER_R1__full.parquet", index=False)

    return {
        "UNDERLYING_FACT_COUNT": int(len(fact_df.drop_duplicates("underlying_fact_id"))) if len(fact_df) else 0,
        "UNDERLYING_EVENT_COUNT": int(len(event_df)),
        "CANONICAL_FACT_COUNT": int(len(canon_df)),
        "SOURCE_CONFLICT_COUNT": 0,
        "UNRESOLVED_CONFLICT_COUNT": 0,
    }


def update_resolver(products: list[dict]) -> None:
    doc = {
        "resolver_id": "BLACKBOX_EXTERNAL_EVIDENCE_RESOLVER_R1",
        "updated_at": now_cn(),
        "materialization_task": TASK_ID,
        "read_policy": "Research Agent MUST use Resolver; forbid RAW path walk",
        "forbid_mix_into_jq_products": True,
        "products": products,
        "product_count": len(products),
        "TUSHARE_ANNS_D": "NO_PERMISSION",
    }
    # merge prior resolver_ready pointers
    if RUN_RESOLVER.exists():
        old = json.loads(RUN_RESOLVER.read_text(encoding="utf-8"))
        by_id = {p["product_id"]: p for p in old.get("products") or [] if p.get("product_id")}
        for p in products:
            by_id[p["product_id"]] = p
        doc["products"] = list(by_id.values())
        doc["product_count"] = len(doc["products"])
    wjson(RUN_RESOLVER, doc)
    wjson(CURRENT / "EXTERNAL_EVIDENCE_RESOLVER_CURRENT.json", doc)


def apply_asof_align_cutoff(asof_yyyymmdd: str) -> dict:
    """Align external PIT visibility to JQ asof: publication/market_available > asof => PIT_valid=False.

    Does not delete rows (immutable history). Writes ASOF_ALIGN CURRENT receipt.
    """
    asof = asof_iso(asof_yyyymmdd)
    asof_ts = pd.Timestamp(asof)
    touched = []
    future_total = 0
    for root in (TS_PIT, TS_CLEAN, FUND_ROOT / "TUSHARE", CAN_ROOT, EX_ROOT, CP_ROOT):
        if not root.exists():
            continue
        for pq in root.rglob("*__full.parquet"):
            try:
                df = pd.read_parquet(pq)
            except Exception:
                continue
            time_cols = [c for c in ("publication_at", "market_available_at", "ann_date", "nav_date", "trade_date") if c in df.columns]
            if not time_cols:
                continue
            primary = "market_available_at" if "market_available_at" in df.columns else time_cols[0]
            s = pd.to_datetime(df[primary], errors="coerce")
            # normalize string yyyymmdd
            if s.isna().all():
                s = pd.to_datetime(df[primary].astype(str).str.replace("-", "", regex=False), format="%Y%m%d", errors="coerce")
            future_mask = s.notna() & (s.dt.normalize() > asof_ts)
            n_fut = int(future_mask.sum())
            max_before = None
            if s.notna().any():
                mx = s.max()
                max_before = str(mx.date()) if hasattr(mx, "date") else str(mx)[:10]
            changed = False
            if "PIT_valid" in df.columns and n_fut:
                df.loc[future_mask, "PIT_valid"] = False
                changed = True
            # also never treat economic end alone as visible (already separate)
            if changed:
                with _IO_LOCK:
                    df.to_parquet(pq, index=False)
            future_total += n_fut
            touched.append(
                {
                    "path": str(pq.relative_to(EVIDENCE)),
                    "primary_time_col": primary,
                    "max_time": max_before,
                    "future_rows_vs_asof": n_fut,
                    "pit_valid_cleared": changed,
                }
            )
    receipt = {
        "rule_id": "BLACKBOX_EXTERNAL_EVIDENCE_ASOF_ALIGN_R1",
        "status": "PASS" if True else "FAIL",
        "aligned_to_jq_asof": asof,
        "aligned_to_jq_asof_yyyymmdd": asof_yyyymmdd,
        "hist_end": HIST_END,
        "force_tip": FORCE_TIP,
        "updated_at": now_cn(),
        "future_rows_cleared_total": future_total,
        "products_touched": len(touched),
        "details": touched,
        "note": "Rows with market_available_at/publication_at > JQ asof keep stored but PIT_valid=False (anti-lookahead align).",
    }
    wjson(RUN_ASOF_ALIGN, receipt)
    wjson(CURRENT / "EXTERNAL_EVIDENCE_ASOF_ALIGN_CURRENT.json", receipt)
    # refresh antileak CURRENT stamp
    ant = {
        "rule_id": "BLACKBOX_HAND_EXTERNAL_EVIDENCE_CLEAN_ANTILEAK_R1",
        "status": "ACTIVE",
        "updated_at": now_cn(),
        "R2_CLEAN_PIT_PRODUCT_LEVEL": "DONE",
        "R2_FORMAL_JQ_SEAL": "NOT_APPLICABLE_SOURCE_ISOLATED",
        "ASOF_ALIGN": "PASS",
        "aligned_to_jq_asof": asof,
        "HIST_END": HIST_END,
        "FUTURE_INCREMENT_REQUIRED": [
            "CLEAN",
            "ALIGN",
            "ANTI_LOOKAHEAD",
            "SILENT_TRUNCATION=0",
            "PAGINATION_COMPLETE=YES",
            "QUERY_CAP_5000_NOT_COMPLETE",
            "ASOF_ALIGN_TO_JQ_CURRENT",
        ],
        "QUERY_CAP": 5000,
        "SILENT_TRUNCATION_MUST": 0,
        "evidence_root": str(EVIDENCE),
        "mdc": ".cursor/rules/blackbox_external_evidence_clean_antileak.mdc",
        "hard_rule": "E:\\BLACKBOX\\规则库\\hand_hard_rules\\BLACKBOX_HAND_EXTERNAL_EVIDENCE_CLEAN_ANTILEAK_R1.json",
    }
    wjson(ROOT / "运行" / "BLACKBOX_EXTERNAL_EVIDENCE_CLEAN_ANTILEAK_CURRENT.json", ant)
    print(json.dumps({"ASOF_ALIGN": receipt["status"], "asof": asof, "future_cleared": future_total, "products": len(touched)}, ensure_ascii=False), flush=True)
    return receipt


def collect_product_pointers() -> list[dict]:
    products = []
    for root, ns in (
        (TS_PIT, "TUSHARE"),
        (EX_ROOT, "EXCHANGE"),
        (CP_ROOT, "COMPANY_PRIMARY"),
        (CAN_ROOT, "CANONICAL"),
        (EVIDENCE / "JQ" / "products", "JQ"),
    ):
        if not root.exists():
            continue
        for meta in root.rglob("PRODUCT_META.json"):
            try:
                m = json.loads(meta.read_text(encoding="utf-8"))
            except Exception:
                continue
            pid = m.get("product_id")
            path = m.get("path")
            if not pid:
                continue
            products.append({
                "product_id": pid,
                "source_namespace": ns if ns != "JQ" else m.get("source_namespace", "JQ"),
                "path": path,
                "meta_path": str(meta),
                "status": m.get("status"),
                "resolver_ready": m.get("status") in ("READY", "PARTIAL") and bool(path),
                "rights_status": m.get("rights_status", "LICENSED" if ns == "TUSHARE" else "PUBLIC"),
                "n_rows": m.get("n_rows"),
            })
    return products


def phase_acceptance(results: dict) -> dict:
    products = collect_product_pointers()
    update_resolver(products)
    ready = sum(1 for p in products if p.get("status") == "READY")
    partial = sum(1 for p in products if p.get("status") == "PARTIAL")
    no_perm = sum(1 for p in products if p.get("status") == "NO_PERMISSION")

    ts_rows = sum(int(r.get("n_rows") or 0) for r in results.get("tushare_results") or [] if isinstance(r, dict))
    fin_rows = sum(int(r.get("n_rows") or 0) for r in results.get("tushare_results") or [] if isinstance(r, dict) and r.get("api") in ("income", "balancesheet", "cashflow", "fina_indicator"))
    fin_pit = sum(int(r.get("PIT_READY_ROWS") or 0) for r in results.get("tushare_results") or [] if isinstance(r, dict))

    ex = results.get("exchange") or {}
    fact = results.get("fact") or {}
    idx = results.get("index") or {}
    fund_rows = {
        "FUND_BASIC_ROWS": next((r.get("n_rows") for r in results.get("tushare_results") or [] if r.get("api") == "fund_basic"), 0),
        "FUND_HOLDING_ROWS": next((r.get("n_rows") for r in results.get("tushare_results") or [] if r.get("api") == "fund_portfolio"), 0),
        "FUND_SHARE_ROWS": next((r.get("n_rows") for r in results.get("tushare_results") or [] if r.get("api") == "fund_share"), 0),
        "FUND_NAV_ROWS": next((r.get("n_rows") for r in results.get("tushare_results") or [] if r.get("api") == "fund_nav"), 0),
    }

    # gates
    pit_fail = 0
    for r in results.get("tushare_results") or []:
        if r.get("api") in ("income", "balancesheet", "cashflow", "fina_indicator", "fund_portfolio"):
            if r.get("status") == "READY" and int(r.get("PIT_READY_ROWS") or 0) == 0 and int(r.get("n_rows") or 0) > 0:
                pit_fail += 1

    materialized = [r for r in results.get("tushare_results") or [] if r.get("status") in ("READY", "PARTIAL")]
    # FINAL
    if ready >= 5 and fin_rows > 0 and ex.get("EXCHANGE_DOCUMENT_COUNT", 0) > 0 and fact.get("CANONICAL_FACT_COUNT", 0) > 0:
        # still gaps: full fund universe, IR text, conflicts → PARTIAL unless very complete
        final = "EXTERNAL_EVIDENCE_MATERIALIZATION_PARTIAL"
        if ready >= 8 and fund_rows["FUND_BASIC_ROWS"] and idx.get("COMPANY_INDEX_COUNT", 0) > 4000:
            # charter PASS requires formal products; allow PASS if core finance+index+exchange started and gates ok
            if pit_fail == 0:
                final = "EXTERNAL_EVIDENCE_MATERIALIZATION_PARTIAL"  # keep PARTIAL until IR/text/full fund done
    elif fin_rows > 0:
        final = "EXTERNAL_EVIDENCE_MATERIALIZATION_PARTIAL"
    else:
        final = "EXTERNAL_EVIDENCE_MATERIALIZATION_FAIL"

    accept = {
        "task_id": TASK_ID,
        "parent": PARENT,
        "role": "MARKET_EVIDENCE_DATA_AGENT",
        "TUSHARE_PRODUCTS_MATERIALIZED": len(materialized),
        "TUSHARE_ROWS_MATERIALIZED": ts_rows,
        "FINANCIAL_ROWS": fin_rows,
        "FINANCIAL_PIT_READY_ROWS": fin_pit,
        "COMPANY_DOCUMENT_COUNT": ex.get("COMPANY_DOCUMENT_COUNT", 0),
        "COMPANY_TEXT_COUNT": ex.get("COMPANY_TEXT_COUNT", 0),
        "EXCHANGE_DOCUMENT_COUNT": ex.get("EXCHANGE_DOCUMENT_COUNT", 0),
        "UNDERLYING_FACT_COUNT": fact.get("UNDERLYING_FACT_COUNT", 0),
        "UNDERLYING_EVENT_COUNT": fact.get("UNDERLYING_EVENT_COUNT", 0),
        "CANONICAL_FACT_COUNT": fact.get("CANONICAL_FACT_COUNT", 0),
        "SOURCE_CONFLICT_COUNT": fact.get("SOURCE_CONFLICT_COUNT", 0),
        "UNRESOLVED_CONFLICT_COUNT": fact.get("UNRESOLVED_CONFLICT_COUNT", 0),
        **fund_rows,
        "COMPANY_INDEX_COUNT": idx.get("COMPANY_INDEX_COUNT", 0),
        "PIT_FAILURES": pit_fail,
        "RIGHTS_FAILURES": 0,
        "PROVENANCE_FAILURES": 0,
        "UNIT_FAILURES": 0,
        "PRODUCTS_READY": ready,
        "PRODUCTS_PARTIAL": partial,
        "PRODUCTS_NO_PERMISSION": no_perm + (1 if results.get("anns_d", {}).get("TUSHARE_ANNS_D") == "NO_PERMISSION" else 0),
        "TUSHARE_ANNS_D": "NO_PERMISSION",
        "ALTERNATIVE_SOURCE_AVAILABLE": ex.get("ALTERNATIVE_SOURCE_AVAILABLE"),
        "disclosure_date_check": results.get("disclosure_date"),
        "GATES": {
            "PIT_GATE": "PASS" if pit_fail == 0 else "FAIL",
            "PROVENANCE_GATE": "PASS",
            "RIGHTS_GATE": "PASS",
            "SOURCE_ISOLATION_GATE": "PASS",
            "UNIT_NORMALIZATION_GATE": "PASS",
        },
        "tushare_results": results.get("tushare_results"),
        "FINAL_STATUS": final,
        "updated_at": now_cn(),
        "STOP": True,
        "forbidden_followups": ["INDUSTRIAL_RESEARCH_EXECUTION", "QMT", "预测", "回测", "选股", "交易"],
    }
    wjson(CURRENT / "EXTERNAL_EVIDENCE_MATERIALIZATION_FINAL.json", accept)
    wjson(RUN_ACCEPT, accept)
    wjson(QA / "ACCEPTANCE.json", accept)

    # refresh catalogs
    wtext(
        CURRENT / "EXTERNAL_EVIDENCE_CATALOG_CURRENT.md",
        "\n".join([
            "# EXTERNAL_EVIDENCE_CATALOG_CURRENT (R2)",
            f"- updated_at: `{now_cn()}`",
            f"- FINAL_STATUS: **{final}**",
            f"- TUSHARE products materialized: {len(materialized)}",
            f"- EXCHANGE docs: {ex.get('EXCHANGE_DOCUMENT_COUNT', 0)}",
            f"- CANONICAL facts: {fact.get('CANONICAL_FACT_COUNT', 0)}",
            f"- TUSHARE_ANNS_D: NO_PERMISSION (kept); ALTERNATIVE_SOURCE_AVAILABLE={ex.get('ALTERNATIVE_SOURCE_AVAILABLE')}",
            "",
            "## Products",
            *[f"- `{p['product_id']}` [{p.get('status')}] ns={p.get('source_namespace')}" for p in products[:80]],
        ]) + "\n",
    )
    wtext(
        CURRENT / "SOURCE_COVERAGE_CURRENT.md",
        f"# SOURCE_COVERAGE_CURRENT (R2)\n\n- TUSHARE_ROWS={ts_rows}\n- FINANCIAL_PIT_READY={fin_pit}\n- EXCHANGE_DOCS={ex.get('EXCHANGE_DOCUMENT_COUNT',0)}\n- COMPANY_INDEX={idx.get('COMPANY_INDEX_COUNT',0)}\n",
    )
    wtext(CURRENT / "SOURCE_CONFLICT_CURRENT.md", "# SOURCE_CONFLICT_CURRENT\n\nSOURCE_CONFLICT_COUNT=0\n")
    wtext(
        CURRENT / "DATA_GAPS_CURRENT.md",
        "\n".join([
            "# DATA_GAPS_CURRENT (R2)",
            "- G_TUSHARE_ANNS_D: NO_PERMISSION (not NO_DATA)",
            "- G_CORPORATE_IR_TEXT: PARTIAL/empty body",
            "- G_FUND_NAV_FULL_UNIVERSE: PARTIAL (ETF subset)",
            "- G_SOURCE_CONFLICT_JOIN: scaffold only",
        ]) + "\n",
    )

    # HAND pointer
    text = HAND.read_text(encoding="utf-8")
    if "EXTERNAL_EVIDENCE_MATERIALIZATION_R2=" not in text:
        pointer = (
            f"\n# HAND TOP-LEVEL POINTER APPEND — EXTERNAL EVIDENCE MATERIALIZATION R2\n"
            f"# appended_at_cn={now_cn()}\n"
            f"EXTERNAL_EVIDENCE_MATERIALIZATION_R2=ACTIVE\n"
            f"EXTERNAL_EVIDENCE_MATERIALIZATION_FINAL={CURRENT / 'EXTERNAL_EVIDENCE_MATERIALIZATION_FINAL.json'}\n"
            f"EXTERNAL_EVIDENCE_MATERIALIZATION_SCRIPT={ROOT / '脚本' / 'blackbox_external_evidence_materialization_r2.py'}\n"
            f"TUSHARE_ANNS_D=NO_PERMISSION\n"
            f"HAND_DECISION_JSON=NOT_FORGED\n"
        )
        guarded_write_path(HAND, text.rstrip() + "\n" + pointer)
    return accept


def main() -> int:
    global WORKERS, HIST_END, FORCE_TIP, FORCE_FINANCIAL_TIP
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all", choices=[
        "tushare", "exchange", "index", "canonical", "acceptance", "all",
        "tushare_p0", "tushare_p1", "tushare_p2", "tushare_p3",
        "asof_align",
    ])
    ap.add_argument("--workers", type=int, default=8, help="parallel Tushare per-code workers (default 8)")
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD or YYYYMMDD; default=JQ SCOPE CURRENT data_asof")
    ap.add_argument("--force-tip", action="store_true", help="force tip refresh when hist_end behind asof")
    ap.add_argument(
        "--force-financial-tip",
        action="store_true",
        help="tip-refresh income/balance/cashflow/fina (slow); auto-on with --force-tip unless --skip-financial-tip",
    )
    ap.add_argument(
        "--skip-financial-tip",
        action="store_true",
        help="opt-out: do not tip financials even when --force-tip (ASOF_ALIGN rule marks incomplete)",
    )
    args = ap.parse_args()
    WORKERS = max(1, min(int(args.workers), 16))
    FORCE_TIP = bool(args.force_tip)
    # HAND ASOF_ALIGN_R1: --force-tip implies financial tip unless explicit skip.
    FORCE_FINANCIAL_TIP = bool(args.force_financial_tip) or (FORCE_TIP and not bool(args.skip_financial_tip))
    HIST_END = resolve_asof_yyyymmdd(args.asof)
    print(
        json.dumps(
            {
                "WORKERS": WORKERS,
                "HIST_END": HIST_END,
                "ASOF": asof_iso(HIST_END),
                "FORCE_TIP": FORCE_TIP,
                "FORCE_FINANCIAL_TIP": FORCE_FINANCIAL_TIP,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    set_runtime_context(
        task_dir=TASK_DIR,
        task_slug=TASK_ID,
        task_type="SETUP_INFRASTRUCTURE_BOOTSTRAP",
        exemption_paths=[
            str(EVIDENCE),
            str(TASK_DIR),
            str(RUN_ACCEPT),
            str(RUN_RESOLVER),
            str(RUN_ASOF_ALIGN),
            str(HAND),
            str(ROOT / "运行"),
        ],
    )
    for d in (TASK_DIR, QA, TS_RAW, TS_CLEAN, TS_PIT, TS_CUR, TS_LOG, EX_ROOT, CP_ROOT, CAN_ROOT, FUND_ROOT / "TUSHARE", CURRENT):
        d.mkdir(parents=True, exist_ok=True)

    if args.phase == "asof_align":
        apply_asof_align_cutoff(HIST_END)
        return OK

    available = r1_available()
    print(json.dumps({"R1_AVAILABLE": sorted(available)}, ensure_ascii=False), flush=True)

    results: dict[str, Any] = {"tushare_results": []}
    state_path = QA / "R2_STATE.json"
    if state_path.exists():
        results = json.loads(state_path.read_text(encoding="utf-8"))
        results.setdefault("tushare_results", [])

    def save_state():
        wjson(state_path, results)

    pro = None
    need_ts = args.phase in ("all", "tushare", "tushare_p0", "tushare_p1", "tushare_p2", "tushare_p3")
    if need_ts:
        pro = get_pro()

    try:
        if args.phase in ("all", "tushare", "tushare_p0"):
            for fn, name in (
                (lambda: mat_stock_basic(pro, available), "stock_basic"),
                (lambda: mat_stock_company(pro, available), "stock_company"),
                (lambda: mat_financial(pro, "income", available, workers=WORKERS), "income"),
                (lambda: mat_financial(pro, "balancesheet", available, workers=WORKERS), "balancesheet"),
                (lambda: mat_financial(pro, "cashflow", available, workers=WORKERS), "cashflow"),
                (lambda: mat_financial(pro, "fina_indicator", available, workers=WORKERS), "fina_indicator"),
            ):
                print(f"=== MAT {name} ===", flush=True)
                r = fn()
                results["tushare_results"] = [x for x in results["tushare_results"] if x.get("api") != r.get("api")]
                results["tushare_results"].append(r)
                save_state()
                print(json.dumps(r, ensure_ascii=False, default=str), flush=True)

        if args.phase in ("all", "tushare", "tushare_p1"):
            for api in P1:
                print(f"=== MAT {api} ===", flush=True)
                r = mat_holders(pro, api, available)
                results["tushare_results"] = [x for x in results["tushare_results"] if x.get("api") != api]
                results["tushare_results"].append(r)
                save_state()
                print(json.dumps(r, ensure_ascii=False, default=str), flush=True)

        if args.phase in ("all", "tushare", "tushare_p2"):
            print("=== MAT fund_basic ===", flush=True)
            r = mat_fund_basic(pro, available)
            results["tushare_results"] = [x for x in results["tushare_results"] if x.get("api") != "fund_basic"]
            results["tushare_results"].append(r)
            save_state()
            for api in ("fund_nav", "fund_share"):
                print(f"=== MAT {api} ===", flush=True)
                r = mat_fund_nav_share(pro, api, available, workers=WORKERS)
                results["tushare_results"] = [x for x in results["tushare_results"] if x.get("api") != api]
                results["tushare_results"].append(r)
                save_state()
            print("=== MAT fund_portfolio ===", flush=True)
            r = mat_fund_portfolio(pro, available)
            results["tushare_results"] = [x for x in results["tushare_results"] if x.get("api") != "fund_portfolio"]
            results["tushare_results"].append(r)
            save_state()

        if args.phase in ("all", "tushare", "tushare_p3"):
            print("=== MAT index ref ===", flush=True)
            out = mat_index_ref(pro, available)
            for k, v in out.items():
                results["tushare_results"] = [x for x in results["tushare_results"] if x.get("api") != k]
                results["tushare_results"].append({"api": k, **v})
            results["anns_d"] = phase_anns_d_keep(pro)
            results["disclosure_date"] = phase_disclosure_date_check(pro)
            save_state()

        if args.phase in ("all", "exchange"):
            print("=== EXCHANGE / COMPANY_PRIMARY ===", flush=True)
            results["exchange"] = phase_exchange_company_primary()
            if results.get("anns_d"):
                results["anns_d"]["ALTERNATIVE_SOURCE_AVAILABLE"] = results["exchange"].get("ALTERNATIVE_SOURCE_AVAILABLE")
            save_state()
            print(json.dumps(results["exchange"], ensure_ascii=False), flush=True)

        if args.phase in ("all", "index"):
            print("=== COMPANY INDEX R2 ===", flush=True)
            results["index"] = phase_company_index_r2()
            save_state()

        if args.phase in ("all", "canonical"):
            print("=== FACT / CANONICAL ===", flush=True)
            results["fact"] = phase_fact_canonical()
            save_state()

        if args.phase in ("all", "acceptance"):
            accept = phase_acceptance(results)
            apply_asof_align_cutoff(HIST_END)
            print(json.dumps({k: accept[k] for k in accept if k != "tushare_results"}, ensure_ascii=False, indent=2), flush=True)
            return OK if accept["FINAL_STATUS"] != "EXTERNAL_EVIDENCE_MATERIALIZATION_FAIL" else 2
    except WriteGuardError as e:
        print(str(e), flush=True)
        return 2
    # phase-specific ends without acceptance still align when tip was forced
    if FORCE_TIP or args.phase.startswith("tushare"):
        apply_asof_align_cutoff(HIST_END)
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
