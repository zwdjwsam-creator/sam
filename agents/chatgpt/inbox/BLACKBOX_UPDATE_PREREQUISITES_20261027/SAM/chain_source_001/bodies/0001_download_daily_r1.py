# -*- coding: utf-8 -*-
"""Download A/ETF/index daily RAW_NONE for 2026-09-24 into JQ RAW incremental_gap files."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, r"E:\BLACKBOX\脚本")

GAP_START = "2026-09-24"
GAP_END = "2026-09-24"
AS_OF = date(2026, 9, 24)
RAW = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw")
P0 = RAW / "P0_meta"
P2 = RAW / "P2_stock_daily"
P3 = RAW / "P3_index"
P4_ETF_DAILY = RAW / "P4_fund_etf_raw_none" / "fund_etf_price_daily"
OUT = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924")
CAL_VERSION = "calendar_cn_exchange_v2_asof_20260924"
FIELDS_CORE = [
    "open", "high", "low", "close", "volume", "money",
    "paused", "high_limit", "low_limit", "avg", "pre_close", "factor",
]
INDEX_CODES = [
    "000001.XSHG", "399001.XSHE", "399006.XSHE",
    "000300.XSHG", "000905.XSHG", "000852.XSHG", "000016.XSHG",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ts_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def log(msg: str) -> None:
    line = f"[{now_iso()}] {msg}"
    print(line, flush=True)
    p = OUT / "download.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def wjson(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def normalize_price_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["time", "code"] + FIELDS_CORE)
    out = df.copy()
    if not isinstance(out, pd.DataFrame):
        out = pd.DataFrame(out)
    if "code" not in out.columns or "time" not in out.columns:
        out = out.reset_index()
        rename = {}
        for c in list(out.columns):
            cl = str(c).lower()
            if cl in ("date", "index", "level_0") and "time" not in out.columns:
                rename[c] = "time"
            if cl in ("level_1",) and "code" not in out.columns:
                rename[c] = "code"
        if rename:
            out = out.rename(columns=rename)
    if "time" not in out.columns and "date" in out.columns:
        out = out.rename(columns={"date": "time"})
    keep = [c for c in ["time", "code"] + FIELDS_CORE if c in out.columns]
    out = out[keep].copy()
    out["time"] = pd.to_datetime(out["time"])
    out["code"] = out["code"].astype(str)
    out["fq"] = None
    return out


def download_universe_daily(jq, codes: list[str], batch: int = 80) -> pd.DataFrame:
    frames = []
    for i in range(0, len(codes), batch):
        chunk = codes[i : i + batch]
        df = None
        last_err = None
        for attempt in range(1, 5):
            try:
                df = jq.get_price(
                    chunk,
                    start_date=GAP_START,
                    end_date=GAP_END,
                    frequency="daily",
                    fields=FIELDS_CORE,
                    fq=None,
                    panel=False,
                )
                last_err = None
                break
            except Exception as e:
                last_err = e
                log(f"  batch {i} retry={attempt} err={type(e).__name__}: {e}")
                time.sleep(min(20, 2 * attempt))
                try:
                    import jq_download_base as jdb
                    jdb.auth()
                except Exception:
                    pass
        if last_err is not None and df is None:
            raise last_err
        n = 0 if df is None else len(df)
        if n >= 5000:
            raise RuntimeError(f"SILENT_TRUNCATION_SUSPECT batch={i} rows={n}")
        if df is not None and n:
            frames.append(normalize_price_df(df))
        if (i // batch) % 5 == 0:
            log(f"  batch {i}/{len(codes)}")
        time.sleep(0.05)
    if not frames:
        return pd.DataFrame(columns=["time", "code"] + FIELDS_CORE + ["fq"])
    return pd.concat(frames, ignore_index=True)


def save_unit(*, domain: str, df: pd.DataFrame, raw_path: Path, clean_rel: str, units: list) -> dict:
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(str(raw_path), index=False)
    meta = {
        "domain_id": domain,
        "unit_id": f"{domain}__{GAP_START.replace('-', '')}_{GAP_END.replace('-', '')}",
        "fq": None,
        "price_basis": "RAW_NONE",
        "gap_start": GAP_START,
        "gap_end": GAP_END,
        "rows": int(len(df)),
        "codes": int(df["code"].nunique()) if "code" in df.columns and len(df) else 0,
        "min_time": str(pd.to_datetime(df["time"]).min())[:10] if "time" in df.columns and len(df) else None,
        "max_time": str(pd.to_datetime(df["time"]).max())[:10] if "time" in df.columns and len(df) else None,
        "raw_path": str(raw_path),
        "clean_rel": clean_rel,
        "file_sha256": sha256_file(raw_path),
        "generated_at": now_iso(),
    }
    wjson(Path(str(raw_path) + ".sidecar.json"), meta)
    row = {
        "unit_id": meta["unit_id"],
        "domain_id": domain,
        "status": "PASS" if len(df) else "FAIL",
        "rows": meta["rows"],
        "raw_path": str(raw_path),
        "clean_rel": clean_rel,
        "file_sha256": meta["file_sha256"],
        "min_time": meta.get("min_time"),
        "max_time": meta.get("max_time"),
        "as_of": GAP_END,
    }
    units.append(row)
    return row


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    import jq_download_base as jdb

    jdb.auth()
    import jqdatasdk as jq

    q0 = jdb.quota_left(force=True)
    log(f"quota_before={q0} gap={GAP_START}..{GAP_END}")
    units: list[dict] = []
    ts = ts_stamp()

    try:
        days = jq.get_trade_days(start_date="2014-01-01", end_date=GAP_END)
        days = [pd.Timestamp(x).date() for x in days]
        if AS_OF not in days:
            raise RuntimeError(f"NOT_TRADE_DAY:{GAP_END}")
        cal_dir = P0 / "calendar_cn_exchange" / CAL_VERSION
        cal_dir.mkdir(parents=True, exist_ok=True)
        td = pd.DataFrame({"trade_date": pd.to_datetime(days)})
        fp_td = cal_dir / "CALENDAR_TRADE_DAYS.parquet"
        td.to_parquet(str(fp_td), index=False)
        units.append(
            {
                "unit_id": f"calendar_cn_exchange__{CAL_VERSION}",
                "domain_id": "calendar_cn_exchange",
                "status": "PASS",
                "rows": int(len(td)),
                "raw_path": str(fp_td),
                "max_time": str(td["trade_date"].max())[:10],
                "as_of": GAP_END,
            }
        )
        log(f"calendar PASS n={len(td)} max={str(td['trade_date'].max())[:10]}")
    except Exception as e:
        log(f"calendar FAIL {e}")
        units.append({"unit_id": "calendar", "status": "FAIL", "error": str(e)})

    try:
        secs = jq.get_all_securities(types=["stock"], date=GAP_END)
        codes = list(secs.index.astype(str))
        log(f"stock universe n={len(codes)}")
        df = download_universe_daily(jq, codes, batch=80)
        fp = P2 / f"stock_daily__incremental_gap_{GAP_START.replace('-', '')}_{GAP_END.replace('-', '')}__full__{ts}.parquet"
        row = save_unit(
            domain="stock_ohlcv_daily",
            df=df,
            raw_path=fp,
            clean_rel=f"price/stock_ohlcv_daily/stock_ohlcv_daily__{fp.name}",
            units=units,
        )
        log(f"stock_ohlcv_daily {row['status']} rows={row['rows']} max={row.get('max_time')}")
    except Exception as e:
        log(f"stock_ohlcv_daily FAIL {e}")
        units.append({"unit_id": "stock_ohlcv_daily", "status": "FAIL", "error": str(e)})

    try:
        secs = jq.get_all_securities(types=["etf"], date=GAP_END)
        codes = list(secs.index.astype(str))
        log(f"etf universe n={len(codes)}")
        df = download_universe_daily(jq, codes, batch=80)
        fp = P4_ETF_DAILY / f"etf_daily__incremental_gap_{GAP_START.replace('-', '')}_{GAP_END.replace('-', '')}__full__{ts}.parquet"
        row = save_unit(
            domain="ETF_daily",
            df=df,
            raw_path=fp,
            clean_rel=f"price/ETF_daily/ETF_daily__{fp.name}",
            units=units,
        )
        log(f"ETF_daily {row['status']} rows={row['rows']} max={row.get('max_time')}")
    except Exception as e:
        log(f"ETF_daily FAIL {e}")
        units.append({"unit_id": "ETF_daily", "status": "FAIL", "error": str(e)})

    try:
        df = download_universe_daily(jq, INDEX_CODES, batch=50)
        fp = P3 / f"index_daily__incremental_gap_{GAP_START.replace('-', '')}_{GAP_END.replace('-', '')}__{ts}.parquet"
        row = save_unit(
            domain="index_daily",
            df=df,
            raw_path=fp,
            clean_rel=f"reference/index_daily/index_daily__{fp.name}",
            units=units,
        )
        log(f"index_daily {row['status']} rows={row['rows']} max={row.get('max_time')}")
    except Exception as e:
        log(f"index_daily FAIL {e}")
        units.append({"unit_id": "index_daily", "status": "FAIL", "error": str(e)})

    q1 = jdb.quota_left(force=True)
    fail = sum(1 for u in units if u.get("status") == "FAIL")
    done = sum(1 for u in units if u.get("status") == "PASS")
    status = "PASS" if fail == 0 and done > 0 else "FAIL"
    acc = {
        "status": status,
        "gap_start": GAP_START,
        "gap_end": GAP_END,
        "unit_done": done,
        "unit_fail": fail,
        "quota_before": q0,
        "quota_after": q1,
        "items": units,
        "generated_at": now_iso(),
    }
    wjson(OUT / "DOWNLOAD_ACCEPTANCE.json", acc)
    log(f"DONE status={status} done={done} fail={fail}")
    print(json.dumps({k: acc[k] for k in ("status", "unit_done", "unit_fail", "gap_end")}, ensure_ascii=False))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
