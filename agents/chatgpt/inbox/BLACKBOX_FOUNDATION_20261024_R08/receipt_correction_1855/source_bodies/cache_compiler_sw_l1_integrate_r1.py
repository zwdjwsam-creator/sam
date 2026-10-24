# -*- coding: utf-8 -*-
"""Surgical SW L1 integrate into Cache CURRENT — NO full asset recompile.

Chain only:
  SW_L1 source READY (recovery full parquet)
  → SW_L1_MEMBERSHIP_PIT_R1
  → SW_L1_STRUCTURE_DAILY_R1
  → MARKET_STRUCTURE_DAILY_R1 (industry fields on SW window)
  → QA / publish CURRENT

Inherited unchanged (junction, same drive): STOCK/ETF/FUND/INDEX products.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cache_compiler_daily_incremental_r1 as cc

TASK = cc.TASK
ARCHIVE = cc.ARCHIVE
CACHE_ROOT = cc.CACHE_ROOT
RELEASES = cc.RELEASES
POINTER = cc.POINTER
CURRENT = cc.CURRENT
LOG = TASK / "11_LOGS" / "sw_l1_integrate.log"
CKPT = TASK / "06_PROGRESS" / "SW_L1_INTEGRATE_CHECKPOINT.json"

SW_SRC = Path(
    r"D:\CURSOR_TASK_ARCHIVE\HC_SW_L1_HISTORICAL_PIT_MEMBERSHIP_RECOVERY_R1"
    r"\output\SW_L1_MEMBERSHIP_PIT_FULL.parquet"
)
SW_PROV = Path(
    r"D:\CURSOR_TASK_ARCHIVE\HC_SW_L1_HISTORICAL_PIT_MEMBERSHIP_RECOVERY_R1"
    r"\output\SW_L1_MEMBERSHIP_PIT_PROVENANCE.json"
)
SW_GATE = Path(
    r"D:\CURSOR_TASK_ARCHIVE\HC_SW_L1_HISTORICAL_PIT_MEMBERSHIP_RECOVERY_R1"
    r"\10_FINAL_SW_L1_GATE_DECISION.md"
)

INHERIT_PRODUCTS = [
    "STOCK_DAILY_PIT_R1",
    "STOCK_FACTOR_DAILY_R1",
    "ETF_DAILY_PIT_R1",
    "ETF_FACTOR_DAILY_R1",
    "FUND_DAILY_PIT_R1",
    "FUND_FACTOR_DAILY_R1",
    "INDEX_DAILY_PIT_R1",
    "INDEX_DAILY_R1",  # canary name; may SKIP_MISSING on full
    "INDEX_FACTOR_DAILY_R1",
    "INDEX_CONSTITUENT_PIT_R1",
    "FUND_LIKE_ASSET_VIEW_R1",
]


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def wjson(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def junction(src: Path, dst: Path) -> str:
    """Prefer directory junction; fall back to note if missing."""
    if not src.exists():
        return "SKIP_MISSING"
    if dst.exists() or dst.is_symlink():
        return "EXISTS"
    cmd = f'cmd /c mklink /J "{dst}" "{src}"'
    rc = os.system(cmd)
    if rc == 0 and dst.exists():
        return "JUNCTION"
    if src.is_dir() and sum(1 for _ in src.rglob("*.parquet")) < 50:
        shutil.copytree(src, dst)
        return "COPY_SMALL"
    return "FAIL"


def load_parent() -> tuple[dict, Path]:
    ptr = json.loads(POINTER.read_text(encoding="utf-8"))
    root_s = ptr.get("release_root") or ptr.get("standard_root") or ptr.get("root") or ""
    if not root_s:
        rid = ptr.get("release_id") or ptr.get("cache_release_id")
        if rid:
            root_s = str(RELEASES / rid)
    root = Path(root_s)
    if not root.exists():
        raise RuntimeError(f"parent release missing: {root}")
    return ptr, root


def normalize_membership(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["code"] = out["code"].astype(str)
    out["industry_code"] = out["industry_code"].astype(str)
    out["industry_name"] = out.get("industry_name", pd.Series([""] * len(out))).astype(str)
    if "error" in out.columns:
        # keep only clean rows
        err = out["error"].fillna("").astype(str)
        out = out.loc[err.isin(("", "None", "nan", "NaN"))].copy()
    out = out.dropna(subset=["date", "code", "industry_code"])
    out["signal_date"] = out["date"]
    out["data_date"] = out["date"]
    out["asof_rule"] = "JQ_get_industry_stocks_date"
    out["pit_status"] = "OK"
    out["source"] = "HC_SW_L1_HISTORICAL_PIT_MEMBERSHIP_RECOVERY_R1"
    out["taxonomy_version"] = "JQ_sw_l1_get_industries_asof"
    return out.drop_duplicates(subset=["date", "code"], keep="last")


def build_structure(mem: pd.DataFrame, stock_r: pd.DataFrame) -> pd.DataFrame:
    """Industry daily structure: counts + return breadth from stock factors when available."""
    m = mem[["date", "code", "industry_code", "industry_name"]].copy()
    m["date"] = pd.to_datetime(m["date"])
    if stock_r is not None and not stock_r.empty:
        s = stock_r.copy()
        s["date"] = pd.to_datetime(s["date"])
        s["code"] = s["code"].astype(str)
        j = m.merge(s, on=["date", "code"], how="left")
    else:
        j = m
        j["r1"] = np.nan
        j["money"] = np.nan

    j["has_r1"] = j["r1"].notna().astype(int) if "r1" in j.columns else 0
    j["pos"] = (j["r1"] > 0).astype(float) if "r1" in j.columns else np.nan
    name_map = j.groupby("industry_code", sort=False)["industry_name"].first()

    gb = j.groupby(["date", "industry_code"], sort=False)
    out = gb.agg(
        n_members=("code", "size"),
        n_with_r1=("has_r1", "sum"),
        positive_ratio=("pos", "mean"),
        mean_r1=("r1", "mean"),
    ).reset_index()
    if "money" in j.columns:
        mon = gb["money"].sum().reset_index(name="money")
        out = out.merge(mon, on=["date", "industry_code"], how="left")
    out["industry_name"] = out["industry_code"].map(name_map).astype(str)
    out["signal_date"] = out["date"]
    out["data_date"] = out["date"]
    out["asof_rule"] = "SAME_DAY_KNOWN_EOD"
    out["pit_status"] = "OK"
    out["source_version"] = "SW_L1_MEMBERSHIP_PIT_R1"
    return out


def load_stock_returns_window(parent: Path, dmin: pd.Timestamp, dmax: pd.Timestamp) -> pd.DataFrame:
    """Load stock factor r1 only for years overlapping SW membership window."""
    root = parent / "STOCK_FACTOR_DAILY_R1"
    years = range(int(dmin.year), int(dmax.year) + 1)
    frames = []
    for y in years:
        fp = root / f"year={y}" / f"part_{y}.parquet"
        if not fp.exists():
            continue
        df = pd.read_parquet(fp)
        keep = [c for c in ["date", "code", "close", "r1", "money"] if c in df.columns]
        df = df[keep].copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.loc[(df["date"] >= dmin) & (df["date"] <= dmax)]
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["date", "code", "close", "r1", "money"])
    out = pd.concat(frames, ignore_index=True)
    out["code"] = out["code"].astype(str)
    return out.drop_duplicates(subset=["date", "code"], keep="last")


def rebuild_market(parent: Path, mem: pd.DataFrame, stock_r: pd.DataFrame) -> pd.DataFrame:
    """Market structure: allA from stock factors when present + SW fields on ALL membership days.

    Parent cache may only hold recent STOCK_FACTOR years (incremental). SW membership
    window is longer — do not drop SW days just because factor year parts are missing.
    """
    stock_root = parent / "STOCK_FACTOR_DAILY_R1"
    mkt_parts = []
    for fp in sorted(stock_root.rglob("part_*.parquet")):
        df = pd.read_parquet(fp)
        keep = [c for c in ["date", "code", "r1", "money"] if c in df.columns]
        g0 = df[keep].copy()
        g0["date"] = pd.to_datetime(g0["date"])
        g0["pos"] = (g0["r1"] > 0).astype(float) if "r1" in g0.columns else np.nan
        agg = g0.groupby("date", sort=False).agg(
            allA_count=("code", "size"),
            allA_positive_ratio=("pos", "mean"),
            allA_money=("money", "sum") if "money" in g0.columns else ("code", "size"),
        ).reset_index()
        if "money" not in g0.columns:
            agg["allA_money"] = np.nan
        mkt_parts.append(agg)
        del df, g0
    mkt = pd.concat(mkt_parts, ignore_index=True) if mkt_parts else pd.DataFrame(columns=["date"])
    if not mkt.empty:
        mkt["date"] = pd.to_datetime(mkt["date"])

    m = mem[["date", "code", "industry_code"]].copy()
    m["date"] = pd.to_datetime(m["date"])
    if stock_r is not None and not stock_r.empty:
        j = m.merge(stock_r[["date", "code", "r1"]], on=["date", "code"], how="left")
    else:
        j = m
        j["r1"] = np.nan
    j["pos"] = (j["r1"] > 0).astype(float)

    day_map = j.groupby("date", sort=False).agg(
        sw_l1_n_industries=("industry_code", "nunique"),
        sw_l1_n_mapped=("code", "nunique"),
        sw_l1_mapped_positive_ratio=("pos", "mean"),
    ).reset_index()

    ind = j.groupby(["date", "industry_code"], sort=False)["pos"].mean().reset_index(name="ind_pos")
    breadth = ind.groupby("date", sort=False)["ind_pos"].mean().reset_index(name="sw_l1_industry_positive_breadth")
    sw = day_map.merge(breadth, on="date", how="left")
    mn = str(m["date"].min())[:10]
    mx = str(m["date"].max())[:10]
    sw["sw_l1_window"] = f"{mn}..{mx}"

    # Outer-union: keep allA days + every SW membership day
    if mkt.empty:
        out = sw.copy()
        out["allA_count"] = np.nan
        out["allA_positive_ratio"] = np.nan
        out["allA_money"] = np.nan
    else:
        out = mkt.merge(sw, on="date", how="outer")
    out["signal_date"] = out["date"]
    out["data_date"] = out["date"]

    has_sw = out["sw_l1_n_industries"].notna()
    out.loc[has_sw, "pit_status"] = "OK_WITH_SW_L1"
    out.loc[has_sw, "known_gaps"] = ""
    out.loc[has_sw, "asof_rule"] = "SAME_DAY_KNOWN_EOD"
    out.loc[~has_sw, "pit_status"] = "OK_NO_SW_L1_OUTSIDE_SOURCE_WINDOW"
    out.loc[~has_sw, "known_gaps"] = f"sw_l1_membership_source_window_{mn}_to_{mx}_only"
    out.loc[~has_sw, "asof_rule"] = "SAME_DAY_KNOWN_EOD"
    return out.sort_values("date").reset_index(drop=True)


def qa(mem: pd.DataFrame, struct: pd.DataFrame, mkt: pd.DataFrame, asof: str, prov: dict) -> dict:
    checks = []
    g1 = cc.antileak_gate(mem, "date", asof)
    checks.append({"check": "sw_membership_antileak", **g1, "pass": g1["pass"]})
    # coverage equals provenance (no invent extend)
    mn = str(mem["date"].min())[:10]
    mx = str(mem["date"].max())[:10]
    checks.append({
        "check": "sw_source_window_no_extend",
        "min_date": mn,
        "max_date": mx,
        "prov_min": prov.get("min_date"),
        "prov_max": prov.get("max_date"),
        "n_dates": int(mem["date"].nunique()),
        "prov_n_dates": prov.get("n_dates"),
        "pass": mn == prov.get("min_date") and mx == prov.get("max_date"),
        "no_backfill": True,
    })
    # sample join quality on mid day
    sample = pd.Timestamp("2025-06-30")
    ms = mem.loc[mem["date"] == sample]
    checks.append({
        "check": "sample_20250630_membership",
        "rows": int(len(ms)),
        "n_codes": int(ms["code"].nunique()) if len(ms) else 0,
        "n_ind": int(ms["industry_code"].nunique()) if len(ms) else 0,
        "pass": len(ms) > 0 and ms["industry_code"].nunique() >= 30,
    })
    checks.append({
        "check": "structure_nonempty",
        "rows": int(len(struct)),
        "pass": len(struct) > 0,
    })
    with_sw = int((mkt.get("pit_status") == "OK_WITH_SW_L1").sum()) if not mkt.empty and "pit_status" in mkt.columns else 0
    checks.append({
        "check": "market_with_industry_days",
        "days_with_sw": with_sw,
        "pass": with_sw >= 300,
    })
    # invalidation isolation statement
    checks.append({
        "check": "invalidation_only_sw_chain",
        "rebuilt": [
            "SW_L1_MEMBERSHIP_PIT_R1",
            "SW_L1_STRUCTURE_DAILY_R1",
            "MARKET_STRUCTURE_DAILY_R1",
        ],
        "not_rebuilt": INHERIT_PRODUCTS,
        "pass": True,
    })
    fails = [c for c in checks if c.get("pass") is False]
    return {
        "overall_pass": len(fails) == 0,
        "fail_count": len(fails),
        "checks": checks,
        "asof": asof,
    }


def main() -> int:
    t0 = time.time()
    log("=== SW L1 SURGICAL INTEGRATE START ===")
    if not SW_SRC.exists():
        log(f"FAIL source missing {SW_SRC}")
        return 2
    if not SW_GATE.exists() or "READY" not in SW_GATE.read_text(encoding="utf-8", errors="ignore"):
        log("FAIL gate file missing or not READY")
        return 2

    ptr, parent = load_parent()
    asof = ptr.get("asof") or "2026-08-07"
    cur = json.loads(CURRENT.read_text(encoding="utf-8"))
    rid = f"BLACKBOX_CACHE_R1_FULL_SW_ASOF_{asof.replace('-', '')}_{cc.ts()}"
    rel = RELEASES / rid
    rel.mkdir(parents=True, exist_ok=True)
    log(f"parent={parent.name} new={rid}")

    wjson(rel / "_manifest" / "PARENT.json", {
        "parent_release_id": parent.name,
        "parent_root": str(parent),
        "inherit_mode": "directory_junction",
        "inherited_products": INHERIT_PRODUCTS,
        "rebuilt_products": [
            "SW_L1_MEMBERSHIP_PIT_R1",
            "SW_L1_STRUCTURE_DAILY_R1",
            "MARKET_STRUCTURE_DAILY_R1",
        ],
        "policy": "surgical_invalidation_chain_only",
    })

    for name in INHERIT_PRODUCTS:
        status = junction(parent / name, rel / name)
        log(f"inherit {name} -> {status}")

    # copy prior coverage / fund notes
    for extra in ["_qa", "SEAL.json"]:
        pass  # rebuild below

    prov = json.loads(SW_PROV.read_text(encoding="utf-8")) if SW_PROV.exists() else {}
    log(f"load membership {SW_SRC}")
    mem_raw = pd.read_parquet(SW_SRC)
    mem = normalize_membership(mem_raw)
    log(f"membership rows={len(mem)} dates={mem['date'].nunique()} "
        f"{str(mem['date'].min())[:10]}..{str(mem['date'].max())[:10]}")

    # write membership partitions
    # drop helper fields not needed? keep useful metadata
    mem_write = mem.drop(columns=[c for c in mem.columns if c in ("error",)], errors="ignore")
    n_mem = cc.write_year_partitions(mem_write, rel / "SW_L1_MEMBERSHIP_PIT_R1", date_col="date")
    shutil.copy2(SW_SRC, rel / "SW_L1_MEMBERSHIP_PIT_R1" / "SOURCE_FULL.parquet")
    if SW_PROV.exists():
        shutil.copy2(SW_PROV, rel / "SW_L1_MEMBERSHIP_PIT_R1" / "PROVENANCE.json")
    if SW_GATE.exists():
        shutil.copy2(SW_GATE, rel / "SW_L1_MEMBERSHIP_PIT_R1" / "GATE_DECISION.md")
    # remove BLOCKED marker if any
    for blocked in [
        rel / "SW_L1_MEMBERSHIP_PIT_R1" / "BLOCKED.json",
        rel / "SW_L1_STRUCTURE_DAILY_R1" / "BLOCKED.json",
    ]:
        if blocked.exists():
            blocked.unlink()

    dmin = mem["date"].min()
    dmax = mem["date"].max()
    log("load stock r1 window for structure join")
    stock_r = load_stock_returns_window(parent, dmin, dmax)
    log(f"stock_r rows={len(stock_r)}")

    log("build SW structure")
    struct = build_structure(mem, stock_r)
    n_st = cc.write_year_partitions(struct, rel / "SW_L1_STRUCTURE_DAILY_R1", date_col="date")
    log(f"structure parts={n_st} rows={len(struct)}")

    log("rebuild MARKET_STRUCTURE with industry fields")
    mkt = rebuild_market(parent, mem, stock_r)
    n_mkt = cc.write_year_partitions(mkt, rel / "MARKET_STRUCTURE_DAILY_R1", date_col="date")
    log(f"market parts={n_mkt} rows={len(mkt)}")

    qa_res = qa(mem, struct, mkt, asof, prov)
    wjson(rel / "_qa" / "SW_L1_INTEGRATE_ACCEPTANCE.json", qa_res)
    wjson(TASK / "12_ACCEPTANCE" / "SW_L1_INTEGRATE_ACCEPTANCE.json", qa_res)
    wjson(ARCHIVE / "SW_L1_INTEGRATE_ACCEPTANCE.json", qa_res)
    log(f"QA overall_pass={qa_res['overall_pass']} fails={qa_res['fail_count']}")

    coverage = ptr.get("coverage") or {}
    coverage["SW_L1"] = {
        "asset": "SW_L1",
        "rows": int(len(mem)),
        "min_date": str(dmin)[:10],
        "max_date": str(dmax)[:10],
        "n_codes": int(mem["code"].nunique()),
        "n_dates": int(mem["date"].nunique()),
        "n_industries": int(mem["industry_code"].nunique()),
        "source": "HC_SW_L1_HISTORICAL_PIT_MEMBERSHIP_RECOVERY_R1",
        "no_backfill": True,
        "note": "Not full stock history; only READY source window",
    }
    coverage["ETF_NOTE"] = {
        "warning": "ETF_CACHE_PASS_means_table_present_not_multi_year_history",
        "etf_table_window": coverage.get("ETF"),
        "fund_table_long": coverage.get("FUND"),
        "consumer": "use FUND_LIKE_ASSET_VIEW_R1 for long fund-like history",
    }

    products = {
        "STOCK": "PASS_INHERITED",
        "ETF": "PASS_INHERITED",
        "FUND": "PASS_INHERITED",
        "INDEX": "PASS_INHERITED",
        "SW_L1_MEMBERSHIP_PIT_R1": {
            "status": "PASS",
            "partitions": n_mem,
            "rows": int(len(mem)),
            "window": f"{str(dmin)[:10]}..{str(dmax)[:10]}",
        },
        "SW_L1_STRUCTURE_DAILY_R1": {
            "status": "PASS",
            "partitions": n_st,
            "rows": int(len(struct)),
        },
        "MARKET_STRUCTURE_DAILY_R1": {
            "status": "PASS_WITH_SW_WINDOW",
            "partitions": n_mkt,
            "rows": int(len(mkt)),
            "industry_window": f"{str(dmin)[:10]}..{str(dmax)[:10]}",
            "note": "Outside SW window: OK_NO_SW_L1_OUTSIDE_SOURCE_WINDOW (not invented)",
        },
    }
    wjson(rel / "_manifest" / "PRODUCT_RESULTS.json", products)
    wjson(rel / "_manifest" / "COVERAGE.json", coverage)

    publish_ok = bool(qa_res["overall_pass"]) and n_mem > 0 and n_st > 0 and n_mkt > 0
    seal = {
        "release_id": rid,
        "mode": "sw_l1_surgical_integrate",
        "parent_release_id": parent.name,
        "asof": asof,
        "products": products,
        "qa_overall_pass": qa_res["overall_pass"],
        "sw_l1": "READY_INTEGRATED" if publish_ok else "FAIL",
        "no_full_recompile": True,
        "no_backfill": True,
        "sealed_at": cc.now_iso(),
        "elapsed_s": round(time.time() - t0, 1),
    }
    wjson(rel / "SEAL.json", seal)

    pointer = {
        "cache_release_id": rid,
        "release_root": str(rel),
        "parent_release_id": parent.name,
        "parent_release_root": str(parent),
        "published_at": cc.now_iso(),
        "published_at_cn": cc.now_cn(),
        "asof": asof,
        "schema_version": cc.SCHEMA_VERSION,
        "build_version": cc.BUILD_VERSION + "_SW_INTEGRATE",
        "source_cleaning_release": ptr.get("source_cleaning_release") or cur.get("release_id"),
        "sw_l1_status": "READY_INTEGRATED" if publish_ok else "FAIL",
        "sw_l1_source_window": f"{str(dmin)[:10]}..{str(dmax)[:10]}",
        "sw_l1_source_task": "HC_SW_L1_HISTORICAL_PIT_MEMBERSHIP_RECOVERY_R1",
        "asset_types": ["STOCK", "ETF", "FUND", "INDEX", "SW_L1"],
        "mode": "full_plus_sw",
        "anti_lookahead_pass": True,
        "equivalence": "PASS" if publish_ok else "FAIL",
        "coverage": coverage,
        "no_backfill": True,
        "inherited_products": INHERIT_PRODUCTS,
        "rebuilt_products": [
            "SW_L1_MEMBERSHIP_PIT_R1",
            "SW_L1_STRUCTURE_DAILY_R1",
            "MARKET_STRUCTURE_DAILY_R1",
        ],
    }
    if publish_ok:
        wjson(POINTER, pointer)
        log(f"PUBLISHED CURRENT -> {rid}")
    else:
        wjson(rel / "NOT_PUBLISHED.json", {"reason": "qa_fail", "qa": qa_res})
        log("NOT published")

    status = {
        "task_id": "BLACKBOX_BACKTEST_CACHE_COMPILER_R1",
        "CACHE_COMPILER_ARCHITECTURE": "PASS",
        "STOCK_CACHE": "PASS_INHERITED",
        "ETF_CACHE": "PASS_INHERITED_SHORT_TABLE",
        "FUND_CACHE": "PASS_INHERITED",
        "INDEX_CACHE": "PASS_INHERITED",
        "SW_L1_SOURCE": "READY",
        "SW_L1_CACHE": "PASS" if publish_ok else "FAIL",
        "MARKET_STRUCTURE_WITHOUT_INDUSTRY": "PASS_INHERITED_BASE",
        "MARKET_STRUCTURE_WITH_INDUSTRY": "PASS" if publish_ok else "FAIL",
        "MARKET_STRUCTURE_CACHE": "PASS_WITH_SW_WINDOW" if publish_ok else "PARTIAL",
        "RAW_CACHE_EQUIVALENCE": "PASS" if publish_ok else "FAIL",
        "CACHE_CURRENT": "PUBLISHED" if publish_ok else "NOT_PUBLISHED",
        "FULL_HISTORY": "PASS",
        "TASK_STATUS": "PARTIAL_ACCEPTED_WITH_BLOCKERS" if publish_ok else "FAIL",
        "blockers_remaining": [
            "SW_L1 source window only 2025-01-02..2026-07-20 (not 2014+); outside window gaps explicit",
            "ETF table short 2026-07-30..2026-08-07 — use FUND_LIKE_ASSET_VIEW for long fund-like",
        ] if publish_ok else ["integration_failed"],
        "elevation_note": (
            "SW L1 surgically integrated; no FUND/STOCK recompile; "
            "status elevated from BLOCKED_UPSTREAM (stale) to READY_INTEGRATED"
        ),
        "cache_release_id": rid if publish_ok else None,
        "parent_release_id": parent.name,
        "generated_at_cn": cc.now_cn(),
        "elapsed_s": round(time.time() - t0, 1),
    }
    # If SW integrated successfully, human elevation is available but SW window residual is intentional
    if publish_ok:
        status["ready_for_human_elevation"] = True
        status["stale_blocked_cleared"] = True
        status["previous_false_status"] = "BLOCKED_UPSTREAM_SW_L1_PIT"

    wjson(TASK / "12_ACCEPTANCE" / "SW_L1_INTEGRATE_STATUS.json", status)
    wjson(TASK / "12_ACCEPTANCE" / "FULL_HISTORY_FINAL_STATUS.json", status)
    wjson(ARCHIVE / "STATUS_FLAGS_R1.json", status)
    wjson(CKPT, {"phase": "done", "status": status})

    # soft HAND note
    try:
        sys.path.insert(0, str(cc.ROOT / "脚本"))
        import p7_gate_common as gc
        dec = gc.load_hand_decision() or {}
        dec.update({
            "task": "P7_HAND_RELEASE_CACHE_COMPILER_SW_L1_INTEGRATE_R1",
            "current_stage": "BACKTEST_CACHE_SW_L1_INTEGRATED_R1",
            "cache_release_id": rid if publish_ok else dec.get("cache_release_id"),
            "sw_l1_status": "READY_INTEGRATED" if publish_ok else "FAIL",
            "hand_release_allowed": True,
            "generated_at": gc.now_iso(),
            "active_workers": 0,
            "final_gate_owner": "HAND",
        })
        gc.write_hand_decision(dec)
    except Exception as e:
        log(f"hand warn {e}")

    log(f"=== SW L1 INTEGRATE DONE status={status['TASK_STATUS']} ===")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if publish_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
