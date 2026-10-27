#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extend SW L1/L2/L3 membership PIT by one trade day 2026-09-24; seal + switch CURRENT.

SW CURRENT formal_data_asof was 09-02; densify 09-03 then tip-rebase inject L123.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

CN = timezone(timedelta(hours=8))
ASOF = date(2026, 9, 24)
TASK = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924")
SW_CODE = Path(r"D:\CURSOR_TASK_ARCHIVE\DYNAMIC_MOTHERLINE_SW_HISTORY_EXTEND_R1\code")
SW_OUT = Path(r"D:\CURSOR_TASK_ARCHIVE\DYNAMIC_MOTHERLINE_SW_HISTORY_EXTEND_R1\output")
CLEAN_ROOT = Path(r"E:\BLACKBOX\数据\清洗成品\releases")
PTR_ROOT = Path(r"E:\BLACKBOX\数据\清洗成品")
CAL = Path(
    r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P0_meta\calendar_cn_exchange"
    r"\calendar_cn_exchange_v2_asof_20260924\CALENDAR_TRADE_DAYS.parquet"
)
CACHE_PTR = Path(r"E:\BLACKBOX\数据\回测缓存\CURRENT_CACHE_RELEASE.json")
sys.path.insert(0, str(SW_CODE))
from multihead_membership_dense_r1 import fetch_day, jq_auth, write_shard, shard_path  # noqa: E402

FLOOR = {
    "sw_l1": {"min_codes": 1000, "min_ind": 20, "product": "SW_L1_PIT_ALIGN", "ptr": "CURRENT_SW_L1_PIT_ALIGN_RELEASE.json", "mem": "SW_L1_MEMBERSHIP_PIT_FULL.parquet", "struct": "SW_L1_STRUCTURE_DAILY_FULL.parquet"},
    "sw_l2": {"min_codes": 1000, "min_ind": 50, "product": "SW_L2_PIT_ALIGN", "ptr": "CURRENT_SW_L2_PIT_ALIGN_RELEASE.json", "mem": "SW_L2_MEMBERSHIP_PIT_FULL.parquet", "struct": "SW_L2_STRUCTURE_DAILY_FULL.parquet"},
    "sw_l3": {"min_codes": 1000, "min_ind": 100, "product": "SW_L3_PIT_ALIGN", "ptr": "CURRENT_SW_L3_PIT_ALIGN_RELEASE.json", "mem": "SW_L3_MEMBERSHIP_PIT_FULL.parquet", "struct": "SW_L3_STRUCTURE_DAILY_FULL.parquet"},
}


def log(msg: str) -> None:
    line = f"[{datetime.now(CN).isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    p = TASK / "logs" / "run.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def wjson(p: Path, o) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def assert_trade_day(d: date) -> None:
    cal = pq.read_table(CAL).to_pandas()
    col = "calendar_date" if "calendar_date" in cal.columns else cal.columns[0]
    days = set(pd.to_datetime(cal[col]).dt.date)
    if d not in days:
        raise RuntimeError(f"{d} not in calendar {CAL}")


def day_ok(df: pd.DataFrame, tax: str) -> dict:
    fl = FLOOR[tax]
    ok = df.copy()
    if "code" in ok.columns:
        ok = ok[ok["code"].astype(str) != "__ERROR__"]
    if "error" in ok.columns:
        err = ok["error"].fillna("").astype(str)
        ok = ok[err.isin(("", "None", "nan", "NaN"))]
    n_c = int(ok["code"].nunique()) if "code" in ok.columns else 0
    n_i = int(ok["industry_code"].nunique()) if "industry_code" in ok.columns else 0
    return {
        "rows": int(len(ok)),
        "n_codes": n_c,
        "n_ind": n_i,
        "pass": n_c >= fl["min_codes"] and n_i >= fl["min_ind"],
    }


def densify_one(jq, tax: str) -> dict:
    df = None
    st = None
    for attempt in range(1, 4):
        df = fetch_day(jq, tax, ASOF)
        write_shard(tax, ASOF, df)
        st = day_ok(df, tax)
        log(f"{tax} fetch attempt={attempt} {st}")
        if st["pass"]:
            break
        time.sleep(0.5)
    if not st or not st["pass"]:
        raise RuntimeError(f"{tax} thin after retries: {st}")
    return {"tax": tax, **st, "shard": str(shard_path(tax, ASOF))}


def load_prior_mem(tax: str) -> pd.DataFrame:
    ptr = json.loads((PTR_ROOT / FLOOR[tax]["ptr"]).read_text(encoding="utf-8"))
    root = Path(ptr["standard_root"])
    fp = root / f"{tax}_membership_pit" / FLOOR[tax]["mem"]
    if not fp.exists():
        # fallback SW output
        fp = SW_OUT / FLOOR[tax]["mem"]
    log(f"{tax} prior mem {fp}")
    return pd.read_parquet(fp)


def clean_stamp(mem: pd.DataFrame, tax: str) -> pd.DataFrame:
    out = mem.copy()
    out["date"] = pd.to_datetime(out["date"])
    out["signal_date"] = out["date"]
    out["data_date"] = out["date"]
    out["asof_rule"] = "JQ_get_industry_stocks_date"
    out["pit_status"] = "OK"
    out["source"] = "JQ_DAILY_TIP_20260924"
    out["taxonomy"] = tax
    out["taxonomy_version"] = f"JQ_{tax}_get_industries_asof"
    out["no_current_backfill"] = True
    out["no_ffill_membership"] = True
    out = out.dropna(subset=["date", "code", "industry_code"])
    return out.drop_duplicates(subset=["date", "code"], keep="last")


def build_structure(mem: pd.DataFrame, stock: pd.DataFrame, tax: str) -> pd.DataFrame:
    m = mem[["date", "code", "industry_code", "industry_name"]].copy()
    m["date"] = pd.to_datetime(m["date"])
    m["code"] = m["code"].astype(str)
    if stock is not None and len(stock):
        s = stock.copy()
        s["date"] = pd.to_datetime(s["date"])
        s["code"] = s["code"].astype(str)
        j = m.merge(s, on=["date", "code"], how="left")
    else:
        j = m
        j["r1"] = np.nan
        j["money"] = np.nan
    j["has_r1"] = j["r1"].notna().astype(int)
    j["pos"] = (j["r1"] > 0).astype(float)
    name_map = j.groupby("industry_code", sort=False)["industry_name"].first()
    gb = j.groupby(["date", "industry_code"], sort=False)
    out = gb.agg(
        n_members=("code", "size"),
        n_with_r1=("has_r1", "sum"),
        positive_ratio=("pos", "mean"),
        mean_r1=("r1", "mean"),
        money=("money", "sum"),
    ).reset_index()
    out["industry_name"] = out["industry_code"].map(name_map).astype(str)
    day_tot = out.groupby("date")["money"].transform("sum")
    out["money_share"] = np.where(day_tot > 0, out["money"] / day_tot, np.nan)
    out["signal_date"] = out["date"]
    out["data_date"] = out["date"]
    out["asof_rule"] = "SAME_DAY_KNOWN_EOD_MEMBERSHIP_PIT"
    out["pit_status"] = "OK"
    out["taxonomy"] = tax
    out["source_version"] = "ASOF_20260924_TIP"
    out["no_lookahead"] = True
    return out


def load_stock_factors() -> pd.DataFrame:
    if not CACHE_PTR.exists():
        return pd.DataFrame()
    ptr = json.loads(CACHE_PTR.read_text(encoding="utf-8"))
    root_s = (
        ptr.get("release_root")
        or ptr.get("standard_root")
        or ptr.get("root")
        or ptr.get("path")
        or ""
    )
    if not root_s and (ptr.get("release_id") or ptr.get("cache_release_id")):
        rid = ptr.get("release_id") or ptr.get("cache_release_id")
        root_s = str(Path(r"E:\BLACKBOX\数据\回测缓存\releases") / rid)
    root = Path(root_s)
    # standard_root may already point inside release
    if (root / "STOCK_FACTOR_DAILY_R1").exists():
        root = root / "STOCK_FACTOR_DAILY_R1"
    elif root.name != "STOCK_FACTOR_DAILY_R1":
        cand = root / "STOCK_FACTOR_DAILY_R1"
        root = cand
    frames = []
    for y in (2026,):
        fp = root / f"year={y}" / f"part_{y}.parquet"
        if not fp.exists():
            # empty is OK for structure metrics; seal still proceeds
            continue
        df = pd.read_parquet(fp)
        keep = [c for c in ["date", "code", "r1", "money", "close"] if c in df.columns]
        df = df[keep].copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.loc[df["date"] == pd.Timestamp(ASOF)]
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["date", "code", "r1", "money"])
    return pd.concat(frames, ignore_index=True).drop_duplicates(subset=["date", "code"], keep="last")


def write_year_parts(df: pd.DataFrame, root: Path) -> int:
    root.mkdir(parents=True, exist_ok=True)
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    n = 0
    for y, g in d.groupby(d["date"].dt.year):
        yp = root / f"year={y}"
        yp.mkdir(parents=True, exist_ok=True)
        g.to_parquet(yp / f"part_{y}.parquet", index=False)
        n += 1
    return n


def seal_one(tax: str, mem: pd.DataFrame, struct: pd.DataFrame, dens: dict) -> dict:
    cfg = FLOOR[tax]
    fl = FLOOR[tax]
    mem_max = pd.to_datetime(mem["date"]).max().date()
    mem_min = pd.to_datetime(mem["date"]).min().date()
    have = set(pd.to_datetime(mem["date"]).dt.date.unique())
    if ASOF not in have:
        raise RuntimeError(f"{tax} missing ASOF day after merge")
    g = mem.groupby(pd.to_datetime(mem["date"]).dt.date).agg(
        n_codes=("code", "nunique"), n_ind=("industry_code", "nunique")
    )
    thin = g.loc[(g["n_codes"] < fl["min_codes"]) | (g["n_ind"] < fl["min_ind"])]
    gate = {
        "overall_pass": mem_max == ASOF and len(thin) == 0 and dens.get("pass") is True,
        "mem_max": str(mem_max),
        "mem_min": str(mem_min),
        "thin_days": int(len(thin)),
        "asof_day_stats": dens,
        "n_dates": int(len(have)),
    }
    if not gate["overall_pass"]:
        raise RuntimeError(f"{tax} gate fail {gate}")

    ts = datetime.now(CN).strftime("%Y%m%d_%H%M%S")
    rid = f"BLACKBOX_{cfg['product']}_R1_ASOF_20260924_{ts}"
    rel = CLEAN_ROOT / rid
    std = rel / "standard"
    mem_dir = std / f"{tax}_membership_pit"
    st_dir = std / f"{tax}_structure_daily"
    mem_dir.mkdir(parents=True, exist_ok=True)
    st_dir.mkdir(parents=True, exist_ok=True)

    mem_full = TASK / "output" / cfg["mem"]
    st_full = TASK / "output" / cfg["struct"]
    mem_full.parent.mkdir(parents=True, exist_ok=True)
    mem.to_parquet(mem_full, index=False)
    struct.to_parquet(st_full, index=False)
    shutil.copy2(mem_full, SW_OUT / cfg["mem"])
    shutil.copy2(st_full, SW_OUT / cfg["struct"])
    shutil.copy2(mem_full, mem_dir / cfg["mem"])
    shutil.copy2(st_full, st_dir / cfg["struct"])
    n_y = write_year_parts(mem, mem_dir / "partitions")
    write_year_parts(struct, st_dir / "partitions")

    seal_obj = {
        "release_id": rid,
        "task": "JQ_DAILY_TIP_20260924",
        "created_at": datetime.now(CN).isoformat(timespec="seconds"),
        "taxonomy": tax,
        "window": f"{mem_min}..{mem_max}",
        "formal_data_asof": str(mem_max),
        "CLEAN_ALIGN_ANTILEAK": gate,
        "forbidden": ["current_snapshot_backfill", "membership_ffill"],
        "membership_sha256": hashlib.sha256(mem_full.read_bytes()).hexdigest(),
        "structure_sha256": hashlib.sha256(st_full.read_bytes()).hexdigest(),
        "n_membership_rows": int(len(mem)),
        "n_structure_rows": int(len(struct)),
        "year_partitions": n_y,
        "CACHE_PUBLISH": "NOT_APPLICABLE_NO_CACHE_PRODUCT_YET" if tax != "sw_l1" else "EXISTING_CACHE_PRODUCT_SEE_CACHE_CURRENT",
        "gate_pass": True,
        "thin_days": 0,
    }
    wjson(rel / "SEAL.json", seal_obj)
    wjson(TASK / "qa" / f"SEAL_{cfg['product']}.json", seal_obj)
    ptr = {
        "product": cfg["product"],
        "release_id": rid,
        "release_root": str(rel),
        "standard_root": str(std),
        "updated_at": seal_obj["created_at"],
        "window": seal_obj["window"],
        "formal_data_asof": str(mem_max),
        "gate_pass": True,
        "thin_days": 0,
        "n_membership_rows": seal_obj["n_membership_rows"],
        "membership_sha256": seal_obj["membership_sha256"],
    }
    wjson(PTR_ROOT / cfg["ptr"], ptr)
    log(f"{tax} SEALED {rid} window={ptr['window']}")
    return ptr


def main() -> int:
    for d in (TASK / "logs", TASK / "qa", TASK / "output"):
        d.mkdir(parents=True, exist_ok=True)
    assert_trade_day(ASOF)
    log(f"START SW L1/L2/L3 asof={ASOF}")

    jq = jq_auth()
    dens = {}
    for tax in ("sw_l1", "sw_l2", "sw_l3"):
        dens[tax] = densify_one(jq, tax)
    try:
        jq.logout()
    except Exception:
        pass
    wjson(TASK / "qa" / "DENSIFY_20260811.json", dens)

    stock = load_stock_factors()
    log(f"stock_factor rows for asof day={len(stock)}")
    results = {}
    for tax in ("sw_l1", "sw_l2", "sw_l3"):
        prior = load_prior_mem(tax)
        day = pd.read_parquet(shard_path(tax, ASOF))
        day = day.loc[day["code"].astype(str) != "__ERROR__"].copy() if "code" in day.columns else day
        if "error" in day.columns:
            err = day["error"].fillna("").astype(str)
            day = day.loc[err.isin(("", "None", "nan", "NaN"))]
        day["date"] = pd.to_datetime(day["date"]).dt.date
        # force date
        day["date"] = ASOF
        prior["date"] = pd.to_datetime(prior["date"]).dt.date
        prior = prior.loc[prior["date"] != ASOF]
        mem = pd.concat([prior, day], ignore_index=True)
        mem = clean_stamp(mem, tax)
        struct = build_structure(mem, stock, tax)
        results[tax] = seal_one(tax, mem, struct, dens[tax])

    wjson(TASK / "qa" / "RESULT.json", {"final_status": "PASS", "asof": str(ASOF), "releases": results})
    print(json.dumps({"final_status": "PASS", "asof": str(ASOF), "releases": {k: v["release_id"] for k, v in results.items()}}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

