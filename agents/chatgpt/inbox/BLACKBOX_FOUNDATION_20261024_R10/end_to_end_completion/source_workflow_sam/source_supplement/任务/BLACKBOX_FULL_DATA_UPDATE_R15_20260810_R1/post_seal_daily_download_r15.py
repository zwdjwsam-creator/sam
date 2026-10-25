#!/usr/bin/env python3
"""POST_SEAL daily RAW_NONE gap-fill — calendar + A/ETF/index daily, fq=None only."""
from __future__ import annotations

import bisect
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"E:\BLACKBOX\脚本")

TASK = Path(__file__).resolve().parent
RAW = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw")
P0 = RAW / "P0_meta"
P2 = RAW / "P2_stock_daily"
P3 = RAW / "P3_index"
P4_ETF_DAILY = RAW / "P4_fund_etf_raw_none" / "fund_etf_price_daily"
HAND = Path(r"E:\BLACKBOX\运行\HAND_DECISION.json")
LAB_ETF = Path(
    r"D:\backtest_lab\04_data\PHASE2_ETF_DAILY_RAW_NONE_R2"
    r"\etf_daily_raw_none_consolidated.parquet"
)

GAP_START = "2026-08-10"
GAP_END = "2026-08-10"
AS_OF = date(2026, 8, 10)
CAL_START = date(2014, 1, 1)
CAL_VERSION = "calendar_cn_exchange_v2_asof_20260810"

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
    p = TASK / "11_LOGS" / "daily_download.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def wjson(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
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


def hand_allows() -> dict:
    d = json.loads(HAND.read_text(encoding="utf-8"))
    if d.get("final_gate_owner") != "HAND":
        raise RuntimeError("final_gate_owner_not_HAND")
    if d.get("post_seal_daily_raw_none_download_allowed") is not True:
        raise RuntimeError("post_seal_daily_raw_none_download_allowed!=true")
    if d.get("fq_explicit_required") is not True:
        raise RuntimeError("fq_explicit_required!=true")
    if d.get("current_stage") not in ("POST_SEAL_DAILY_RAW_NONE", "POST_SEAL_FRESHNESS_RAW_NONE", "POST_SEAL_FRESHNESS_DAILY_AND_MINUTE", "FULL_DATA_UPDATE_R15", "FULL_DATA_INCREMENT_R15"):
        raise RuntimeError(f"bad_stage:{d.get('current_stage')}")
    return d


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


def download_universe_daily(jq, codes: list[str], batch: int = 200) -> pd.DataFrame:
    frames = []
    for i in range(0, len(codes), batch):
        chunk = codes[i:i + batch]
        df = jq.get_price(
            chunk,
            start_date=GAP_START,
            end_date=GAP_END,
            frequency="daily",
            fields=FIELDS_CORE,
            fq=None,
            panel=False,
        )
        if df is not None and len(df):
            frames.append(normalize_price_df(df))
        if (i // batch) % 5 == 0:
            log(f"  batch {i}/{len(codes)}")
        time.sleep(0.02)
    if not frames:
        return pd.DataFrame(columns=["time", "code"] + FIELDS_CORE + ["fq"])
    return pd.concat(frames, ignore_index=True)


def build_trade_day_table(trade_days: list[date]) -> pd.DataFrame:
    rows = []
    n = len(trade_days)
    for i, d in enumerate(trade_days):
        prev_d = trade_days[i - 1] if i > 0 else pd.NaT
        next_d = trade_days[i + 1] if i + 1 < n else pd.NaT
        month_end = (i + 1 == n) or (trade_days[i + 1].month != d.month)
        year_end = (i + 1 == n) or (trade_days[i + 1].year != d.year)
        q = (d.month - 1) // 3 + 1
        if i + 1 == n:
            quarter_end = True
        else:
            nq = (trade_days[i + 1].month - 1) // 3 + 1
            quarter_end = (trade_days[i + 1].year != d.year) or (nq != q)
        rows.append({
            "trade_date": d,
            "trade_day_sequence": i + 1,
            "previous_trade_date": prev_d,
            "next_trade_date": next_d,
            "year": d.year,
            "month": d.month,
            "quarter": q,
            "month_end_trade_day": bool(month_end),
            "quarter_end_trade_day": bool(quarter_end),
            "year_end_trade_day": bool(year_end),
        })
    return pd.DataFrame(rows)


def build_all_dates(trade_days: list[date]) -> pd.DataFrame:
    trade_set = set(trade_days)
    trade_arr = trade_days
    rows = []
    cur = CAL_START
    while cur <= AS_OF:
        is_td = cur in trade_set
        idx = bisect.bisect_left(trade_arr, cur)
        if is_td:
            prev_td = trade_arr[idx - 1] if idx > 0 else pd.NaT
            next_td = trade_arr[idx + 1] if idx + 1 < len(trade_arr) else pd.NaT
        else:
            prev_td = trade_arr[idx - 1] if idx > 0 else pd.NaT
            next_td = trade_arr[idx] if idx < len(trade_arr) else pd.NaT
        days_since = None if prev_td is pd.NaT or pd.isna(prev_td) else (cur - prev_td).days
        days_to = None if next_td is pd.NaT or pd.isna(next_td) else (next_td - cur).days
        rows.append({
            "calendar_date": cur,
            "is_trade_day": bool(is_td),
            "previous_trade_date": prev_td,
            "next_trade_date": next_td,
            "days_since_previous_trade_day": days_since,
            "days_to_next_trade_day": days_to,
        })
        cur += timedelta(days=1)
    return pd.DataFrame(rows)


def save_unit(
    *,
    domain: str,
    df: pd.DataFrame,
    raw_path: Path,
    clean_rel: str,
    units: list[dict],
    extra: dict | None = None,
) -> dict:
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    staging = TASK / "04_REPAIR_STAGING_DATA" / domain
    staging.mkdir(parents=True, exist_ok=True)
    stage_fp = staging / raw_path.name
    df.to_parquet(str(raw_path), index=False)
    shutil.copy2(raw_path, stage_fp)
    meta = {
        "domain_id": domain,
        "unit_id": f"{domain}__{GAP_START.replace('-', '')}_{GAP_END.replace('-', '')}",
        "fq": None,
        "price_basis": "RAW_NONE",
        "gap_start": GAP_START,
        "gap_end": GAP_END,
        "rows": int(len(df)),
        "codes": int(df["code"].nunique()) if "code" in df.columns else None,
        "min_time": str(pd.to_datetime(df["time"]).min())[:10] if "time" in df.columns and len(df) else None,
        "max_time": str(pd.to_datetime(df["time"]).max())[:10] if "time" in df.columns and len(df) else None,
        "raw_path": str(raw_path),
        "stage_path": str(stage_fp),
        "clean_rel": clean_rel,
        "file_sha256": sha256_file(raw_path),
        "generated_at": now_iso(),
    }
    if extra:
        meta.update(extra)
    wjson(Path(str(raw_path) + ".sidecar.json"), meta)
    wjson(Path(str(stage_fp) + ".sidecar.json"), meta)
    row = {
        "unit_id": meta["unit_id"],
        "domain_id": domain,
        "status": "PASS" if len(df) else "FAIL",
        "rows": meta["rows"],
        "raw_path": str(raw_path),
        "stage_path": str(stage_fp),
        "clean_rel": clean_rel,
        "file_sha256": meta["file_sha256"],
        "min_time": meta.get("min_time"),
        "max_time": meta.get("max_time"),
        "as_of": GAP_END,
    }
    units[:] = [u for u in units if u.get("unit_id") != row["unit_id"]] + [row]
    return row


def refresh_lab_etf(new_df: pd.DataFrame) -> dict:
    if not LAB_ETF.exists():
        return {"status": "SKIP", "reason": "lab_missing"}
    bak = LAB_ETF.with_suffix(f".parquet.bak_before_r6_{ts_stamp()}")
    shutil.copy2(LAB_ETF, bak)
    old = pd.read_parquet(LAB_ETF)
    add = new_df.copy()
    # lab schema: trade_date, code, ohlcv..., paused, high_limit...
    add["trade_date"] = pd.to_datetime(add["time"]).dt.normalize()
    for c in old.columns:
        if c not in add.columns and c != "trade_date":
            add[c] = None
    cols = [c for c in old.columns if c in add.columns]
    add = add[cols]
    # drop overlap dates then concat
    old_dates = set(pd.to_datetime(old["trade_date"]).dt.strftime("%Y-%m-%d"))
    add_mask = ~pd.to_datetime(add["trade_date"]).dt.strftime("%Y-%m-%d").isin(
        {d for d in old_dates if d >= GAP_START}
    )
    # replace gap window from old
    old_keep = old[~pd.to_datetime(old["trade_date"]).dt.strftime("%Y-%m-%d").between(GAP_START, GAP_END)]
    merged = pd.concat([old_keep, add], ignore_index=True)
    merged = merged.sort_values(["trade_date", "code"]).drop_duplicates(["trade_date", "code"], keep="last")
    tmp = LAB_ETF.with_suffix(".parquet.tmp")
    merged.to_parquet(str(tmp), index=False)
    os.replace(tmp, LAB_ETF)
    return {
        "status": "PASS",
        "backup": str(bak),
        "rows_before": int(len(old)),
        "rows_after": int(len(merged)),
        "max_trade_date": str(pd.to_datetime(merged["trade_date"]).max())[:10],
    }


def main() -> int:
    for s in [
        "00_CONTROL", "02_FQ_PREFLIGHT", "04_REPAIR_STAGING_DATA",
        "06_PROGRESS", "08_DAILY_SOURCE_HANDOFF", "10_ACCEPTANCE", "11_LOGS",
    ]:
        (TASK / s).mkdir(parents=True, exist_ok=True)

    try:
        hand = hand_allows()
    except Exception as e:
        log(f"HAND_BLOCKED {e}")
        return 2

    import jq_download_base as jdb
    jdb.auth()
    import jqdatasdk as jq

    q0 = jdb.quota_left(force=True)
    log(f"start gap={GAP_START}..{GAP_END} quota0={q0}")
    units: list[dict] = []
    ts = ts_stamp()

    # FQ preflight: daily None vs pre must both return; None required
    try:
        a = jq.get_price(
            "000001.XSHE", start_date=GAP_START, end_date=GAP_END,
            frequency="daily", fields=["close"], fq=None, panel=False,
        )
        b = jq.get_price(
            "000001.XSHE", start_date=GAP_START, end_date=GAP_END,
            frequency="daily", fields=["close"], fq="pre", panel=False,
        )
        pref = {
            "status": "PASS" if a is not None and len(a) else "FAIL",
            "fq_none_rows": 0 if a is None else int(len(a)),
            "fq_pre_rows": 0 if b is None else int(len(b)),
            "contract": "explicit_fq_None_required",
            "generated_at": now_iso(),
        }
        wjson(TASK / "02_FQ_PREFLIGHT" / "FQ_NONE_PREFLIGHT.json", pref)
        if pref["status"] != "PASS":
            raise RuntimeError("FQ_PREFLIGHT_FAIL")
        log("fq_preflight PASS")
    except Exception as e:
        log(f"fq_preflight FAIL {e}")
        return 2

    # 1) calendar
    try:
        days_raw = jq.get_trade_days(start_date=str(CAL_START), end_date=str(AS_OF))
        trade_days = sorted({
            (d.date() if hasattr(d, "date") else pd.Timestamp(d).date())
            for d in days_raw
            if (d.date() if hasattr(d, "date") else pd.Timestamp(d).date()) <= AS_OF
        })
        td = build_trade_day_table(trade_days)
        ad = build_all_dates(trade_days)
        cal_dir = P0 / "calendar_cn_exchange" / CAL_VERSION
        cal_dir.mkdir(parents=True, exist_ok=True)
        fp_td = cal_dir / "CALENDAR_TRADE_DAYS.parquet"
        fp_ad = cal_dir / "CALENDAR_ALL_DATES.parquet"
        td.to_parquet(str(fp_td), index=False)
        ad.to_parquet(str(fp_ad), index=False)
        # staging copies for cleaning
        st_cal = TASK / "04_REPAIR_STAGING_DATA" / "calendar_cn_exchange"
        st_cal.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fp_td, st_cal / "calendar_cn_exchange__CALENDAR_TRADE_DAYS.parquet")
        shutil.copy2(fp_ad, st_cal / "calendar_cn_exchange__CALENDAR_ALL_DATES.parquet")
        meta = {
            "domain_id": "calendar_cn_exchange",
            "unit_id": f"calendar_cn_exchange__{CAL_VERSION}",
            "calendar_version": CAL_VERSION,
            "as_of": str(AS_OF),
            "trade_day_count": len(td),
            "max_trade_date": str(td["trade_date"].max())[:10],
            "raw_trade_days": str(fp_td),
            "raw_all_dates": str(fp_ad),
            "stage_dir": str(st_cal),
            "clean_rel_trade": "reference/calendar_cn_exchange/calendar_cn_exchange__CALENDAR_TRADE_DAYS.parquet",
            "clean_rel_all": "reference/calendar_cn_exchange/calendar_cn_exchange__CALENDAR_ALL_DATES.parquet",
            "file_sha256_trade": sha256_file(fp_td),
            "file_sha256_all": sha256_file(fp_ad),
            "generated_at": now_iso(),
        }
        wjson(cal_dir / "MANIFEST.json", meta)
        wjson(st_cal / "MANIFEST.json", meta)
        units.append({
            "unit_id": meta["unit_id"],
            "domain_id": "calendar_cn_exchange",
            "status": "PASS",
            "rows": int(len(td)),
            "raw_path": str(fp_td),
            "stage_path": str(st_cal / "calendar_cn_exchange__CALENDAR_TRADE_DAYS.parquet"),
            "clean_rel": meta["clean_rel_trade"],
            "file_sha256": meta["file_sha256_trade"],
            "max_time": meta["max_trade_date"],
            "as_of": str(AS_OF),
            "extra_files": [
                {
                    "raw_path": str(fp_ad),
                    "stage_path": str(st_cal / "calendar_cn_exchange__CALENDAR_ALL_DATES.parquet"),
                    "clean_rel": meta["clean_rel_all"],
                    "file_sha256": meta["file_sha256_all"],
                }
            ],
        })
        log(f"calendar PASS max={meta['max_trade_date']} n={len(td)}")
    except Exception as e:
        log(f"calendar FAIL {e}")
        units.append({"unit_id": "calendar_cn_exchange", "domain_id": "calendar_cn_exchange", "status": "FAIL", "error": str(e)})

    # 2) A-share daily
    try:
        secs = jq.get_all_securities(types=["stock"], date=GAP_END)
        codes = list(secs.index.astype(str))
        log(f"stock universe n={len(codes)}")
        df = download_universe_daily(jq, codes, batch=200)
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
        units.append({"unit_id": "stock_ohlcv_daily", "domain_id": "stock_ohlcv_daily", "status": "FAIL", "error": str(e)})

    # 3) ETF daily
    try:
        secs = jq.get_all_securities(types=["etf"], date=GAP_END)
        codes = list(secs.index.astype(str))
        log(f"etf universe n={len(codes)}")
        df = download_universe_daily(jq, codes, batch=200)
        fp = P4_ETF_DAILY / f"etf_daily__incremental_gap_{GAP_START.replace('-', '')}_{GAP_END.replace('-', '')}__full__{ts}.parquet"
        row = save_unit(
            domain="ETF_daily",
            df=df,
            raw_path=fp,
            clean_rel=f"price/ETF_daily/ETF_daily__{fp.name}",
            units=units,
        )
        lab = refresh_lab_etf(df) if row["status"] == "PASS" else {"status": "SKIP"}
        wjson(TASK / "08_DAILY_SOURCE_HANDOFF" / "LAB_ETF_REFRESH.json", lab)
        log(f"ETF_daily {row['status']} rows={row['rows']} lab={lab.get('status')} max={row.get('max_time')}")
    except Exception as e:
        log(f"ETF_daily FAIL {e}")
        units.append({"unit_id": "ETF_daily", "domain_id": "ETF_daily", "status": "FAIL", "error": str(e)})

    # 4) index daily
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
        units.append({"unit_id": "index_daily", "domain_id": "index_daily", "status": "FAIL", "error": str(e)})

    q1 = jdb.quota_left(force=True)
    done = sum(1 for u in units if u.get("status") == "PASS")
    fail = sum(1 for u in units if u.get("status") == "FAIL")
    status = "PASS" if fail == 0 and done > 0 else ("REVIEW_REQUIRED" if done > 0 else "FAIL")
    handoff = {
        "generated_at": now_iso(),
        "gap_start": GAP_START,
        "gap_end": GAP_END,
        "fq": None,
        "items": units,
        "quota_before": q0,
        "quota_after": q1,
    }
    wjson(TASK / "08_DAILY_SOURCE_HANDOFF" / "STAGING_MANIFEST.json", handoff)
    acc = {
        "generated_at": now_iso(),
        "status": status,
        "unit_total": len(units),
        "unit_done": done,
        "unit_fail": fail,
        "unit_legal_empty": 0,
        "gap_start": GAP_START,
        "gap_end": GAP_END,
        "daily_asof": GAP_END,
        "fq": None,
        "quota_before": q0,
        "quota_after": q1,
        "hand_scope": hand.get("hand_release_scope"),
    }
    wjson(TASK / "10_ACCEPTANCE" / "DOWNLOAD_ACCEPTANCE.json", acc)
    wjson(TASK / "06_PROGRESS" / "PROGRESS.json", {
        "current_stage": "DOWNLOAD_DONE" if status == "PASS" else status,
        "completed_units": [u["unit_id"] for u in units if u.get("status") == "PASS"],
        "updated_at": now_iso(),
    })
    log(f"DONE status={status} done={done} fail={fail} quota={q1}")
    print(json.dumps(acc, ensure_ascii=False))
    return 0 if status in ("PASS", "REVIEW_REQUIRED") else 2


if __name__ == "__main__":
    raise SystemExit(main())
