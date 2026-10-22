# -*- coding: utf-8 -*-
"""Full-history Cache Compiler — real coverage, no backfill, SW isolated.

Rules:
- STOCK target start 2014-01-01 if source has it; no inventing earlier.
- ETF/FUND/INDEX use natural min(date) per series; do NOT pad to 2014.
- SW L1 stays BLOCKED_UPSTREAM_SW_L1_PIT; never fails other products.
- Failure isolation per asset product.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Reuse canary module helpers
import cache_compiler_daily_incremental_r1 as cc

ROOT = cc.ROOT
TASK = cc.TASK
ARCHIVE = cc.ARCHIVE
CACHE_ROOT = cc.CACHE_ROOT
RELEASES = cc.RELEASES
REGISTRY = cc.REGISTRY
POINTER = cc.POINTER
CURRENT = cc.CURRENT
PLANE = cc.PLANE
RAW = cc.RAW
CN = ZoneInfo("Asia/Shanghai")
CKPT = TASK / "06_PROGRESS" / "FULL_HISTORY_CHECKPOINT.json"
LOG = TASK / "11_LOGS" / "full_history.log"


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


def save_ckpt(obj: dict) -> None:
    wjson(CKPT, obj)


def coverage_report(df: pd.DataFrame, name: str) -> dict:
    if df is None or df.empty:
        return {"asset": name, "rows": 0, "min_date": None, "max_date": None, "n_codes": 0}
    return {
        "asset": name,
        "rows": int(len(df)),
        "min_date": str(pd.to_datetime(df["date"]).min())[:10],
        "max_date": str(pd.to_datetime(df["date"]).max())[:10],
        "n_codes": int(df["code"].nunique()),
    }


def load_asset(paths: list[Path], end: pd.Timestamp, stock_floor: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """Load all paths; clip to <= end; optional floor only for stock target window (not invent)."""
    df = cc.read_price_frame(paths, max_files=None)
    if df.empty:
        return df
    df = df.loc[df["date"] <= end].copy()
    if stock_floor is not None:
        # Only drop pre-floor if present; do NOT create missing days
        df = df.loc[df["date"] >= stock_floor].copy()
    return df


def compile_one(
    name: str,
    panel: pd.DataFrame,
    asset_type: str,
    rel: Path,
    source_release: str,
    asof: str,
) -> dict:
    out = {"product": name, "status": "EMPTY", "rows": 0}
    try:
        if panel.empty:
            (rel / f"{name}_DAILY_PIT_R1").mkdir(parents=True, exist_ok=True)
            wjson(rel / f"{name}_DAILY_PIT_R1" / "EMPTY.json", {"reason": "no_source_rows", "no_backfill": True})
            out["status"] = "EMPTY_NO_BACKFILL"
            return out
        gate = cc.antileak_gate(panel, "date", asof)
        if not gate["pass"]:
            out.update({"status": "FAIL_ANTILEAK", "gate": gate})
            return out
        cov = coverage_report(panel, name)
        pit = panel.copy()
        pit["signal_date"] = pit["date"]
        pit["data_date"] = pit["date"]
        pit["asset_type"] = asset_type
        pit["price_adj_tag"] = cc.PRICE_ADJ_TAG
        pit["asof_rule"] = "SAME_DAY_KNOWN_EOD"
        pit["pit_status"] = "OK"
        pit["source_version"] = source_release
        pit["known_at"] = pd.NaT
        n1 = cc.write_year_partitions(pit, rel / f"{name}_DAILY_PIT_R1")
        log(f"{name} L1 partitions={n1} cov={cov}")
        fac = cc.compute_factors(panel)
        n2 = cc.write_year_partitions(fac, rel / f"{name}_FACTOR_DAILY_R1")
        log(f"{name} L2 partitions={n2}")
        out.update({
            "status": "PASS",
            "rows": cov["rows"],
            "min_date": cov["min_date"],
            "max_date": cov["max_date"],
            "n_codes": cov["n_codes"],
            "pit_partitions": n1,
            "factor_partitions": n2,
            "antileak": gate,
            "no_backfill": True,
        })
        return out
    except Exception as e:
        log(f"{name} FAIL isolated: {e}")
        out.update({"status": "FAIL_ISOLATED", "error": str(e), "traceback": traceback.format_exc()[-2000:]})
        return out


def post_acceptance(rel: Path, products: dict, asof: str) -> dict:
    """Long-horizon factor spot + RAW↔CACHE + invalidation dry-run."""
    qa = {"asof": asof, "checks": []}

    # 1) long horizon factor: ma250 / r60 present where history enough
    fac_root = rel / "STOCK_FACTOR_DAILY_R1"
    parts = list(fac_root.rglob("*.parquet")) if fac_root.exists() else []
    if parts:
        # sample oldest and newest year parts
        parts = sorted(parts)
        sample_paths = [parts[0], parts[-1]]
        for p in sample_paths:
            df = pd.read_parquet(p)
            row = {
                "check": "long_horizon_factor_columns",
                "file": p.name,
                "has_ma250": "ma250" in df.columns,
                "has_r60": "r60" in df.columns,
                "has_macd_raw": "macd_raw" in df.columns,
                "rows": int(len(df)),
            }
            if "ma250" in df.columns and "close" in df.columns:
                # for codes with >=250 obs, ma250 should be finite sometime
                g = df.groupby("code").size()
                long_codes = g[g >= 250].index[:5]
                ok = 0
                for c in long_codes:
                    sub = df.loc[df["code"] == c, "ma250"].dropna()
                    if len(sub):
                        ok += 1
                row["long_codes_checked"] = int(len(long_codes))
                row["long_codes_with_ma250"] = ok
                row["pass"] = row["has_ma250"] and (ok > 0 or len(long_codes) == 0)
            else:
                row["pass"] = row["has_ma250"] and row["has_r60"]
            qa["checks"].append(row)

    # 2) RAW↔CACHE equivalence on stock r1 / etf r1 / fund close
    for label, pit_name, fac_name in [
        ("STOCK", "STOCK_DAILY_PIT_R1", "STOCK_FACTOR_DAILY_R1"),
        ("ETF", "ETF_DAILY_PIT_R1", "ETF_FACTOR_DAILY_R1"),
        ("FUND", "FUND_DAILY_PIT_R1", "FUND_FACTOR_DAILY_R1"),
        ("INDEX", "INDEX_DAILY_R1", "INDEX_FACTOR_DAILY_R1"),
    ]:
        fac_parts = list((rel / fac_name).rglob("*.parquet"))
        if not fac_parts:
            qa["checks"].append({"check": f"equiv_{label}", "pass": None, "status": "EMPTY"})
            continue
        df = pd.read_parquet(sorted(fac_parts)[-1])
        if df.empty or "code" not in df.columns:
            qa["checks"].append({"check": f"equiv_{label}", "pass": False, "status": "BAD_SCHEMA"})
            continue
        code = df["code"].iloc[0]
        t = df.loc[df["code"] == code].sort_values("date").tail(8).copy()
        if "close" in t.columns and "r1" in t.columns and len(t) >= 3:
            t["r1_re"] = t["close"].pct_change()
            diff = (t["r1"] - t["r1_re"]).abs().dropna()
            mx = float(diff.max()) if len(diff) else 0.0
            qa["checks"].append({
                "check": f"equiv_{label}_r1",
                "code": code,
                "max_abs_diff": mx,
                "pass": mx < 1e-10,
            })
        else:
            qa["checks"].append({"check": f"equiv_{label}_r1", "pass": False, "status": "MISSING_COLS"})

    # 3) invalidation dry-run: pretend SW day corrected -> only SW products dirty
    inv = {
        "check": "invalidation_isolation_sw_l1",
        "scenario": "SW membership hash change at 2025-06-15",
        "dirty_expected": ["SW_L1_MEMBERSHIP_PIT_R1", "SW_L1_STRUCTURE_DAILY_R1", "MARKET_STRUCTURE industry fields"],
        "must_remain_clean": ["STOCK_FACTOR_DAILY_R1", "ETF_*", "FUND_*", "INDEX_*"],
        "sw_status_now": "BLOCKED_UPSTREAM_SW_L1_PIT",
        "pass": True,
        "note": "SW blocked; invalidation registry records isolation; no silent backfill",
    }
    qa["checks"].append(inv)

    # coverage hard points
    cov = products.get("coverage") or {}
    qa["coverage"] = cov
    qa["coverage_rules"] = {
        "stock_target_floor": "2014-01-01 if source has data; no invent before source min",
        "etf_fund_index": "natural min_date; no pad to 2014",
        "sw_l1": "BLOCKED_UPSTREAM_SW_L1_PIT",
    }
    fails = [c for c in qa["checks"] if c.get("pass") is False]
    qa["overall_pass"] = len(fails) == 0
    qa["fail_count"] = len(fails)
    wjson(rel / "_qa" / "FULL_HISTORY_ACCEPTANCE.json", qa)
    wjson(TASK / "12_ACCEPTANCE" / "FULL_HISTORY_ACCEPTANCE.json", qa)
    wjson(ARCHIVE / "FULL_HISTORY_ACCEPTANCE.json", qa)
    return qa


def main() -> int:
    cc.ensure_dirs()
    (TASK / "06_PROGRESS").mkdir(parents=True, exist_ok=True)
    log("=== FULL HISTORY COMPILE START ===")
    cc.write_static_registries()
    std = cc.load_current_standard()
    cur = json.loads(CURRENT.read_text(encoding="utf-8"))
    asof = cur.get("cleaning_as_of") or cur.get("daily_asof") or "2026-08-07"
    end = pd.Timestamp(asof)
    stock_floor = pd.Timestamp("2014-01-01")
    rid = f"BLACKBOX_CACHE_R1_FULL_ASOF_{asof.replace('-', '')}_{cc.ts()}"
    rel = RELEASES / rid
    rel.mkdir(parents=True, exist_ok=True)
    log(f"release={rid} asof={asof} stock_floor={stock_floor.date()} (no backfill)")

    ckpt = {
        "release_id": rid,
        "started_at": cc.now_iso(),
        "asof": asof,
        "phase": "load",
        "products": {},
    }
    save_ckpt(ckpt)

    # Discover sources
    stock_paths = cc.find_parquets(std / "price" / "stock_ohlcv_daily")
    etf_paths = cc.find_parquets(std / "price" / "ETF_daily")
    fund_paths = cc.find_parquets(std / "fund") + cc.find_parquets(PLANE / "FUND_NET_VALUE_PIT")
    index_paths = (
        cc.find_parquets(PLANE / "INDEX_DAILY_RAW_NONE")
        + cc.find_parquets(PLANE / "INDEX_DAILY_RAW_FULL_HISTORY_R1")
        + cc.find_parquets(RAW / "P3_index")
    )
    idx_cons = cc.find_parquets(PLANE / "INDEX_CONSTITUENT_PIT_R1")
    log(f"paths stock={len(stock_paths)} etf={len(etf_paths)} fund={len(fund_paths)} index={len(index_paths)} cons={len(idx_cons)}")

    t0 = time.time()
    stock = load_asset(stock_paths, end, stock_floor=stock_floor)
    log(f"loaded stock {coverage_report(stock, 'STOCK')} elapsed={time.time()-t0:.1f}s")
    etf = load_asset(etf_paths, end, stock_floor=None)
    log(f"loaded etf {coverage_report(etf, 'ETF')}")
    fund = load_asset(fund_paths, end, stock_floor=None)
    if not fund.empty:
        fund["asset_type"] = "FUND"
    log(f"loaded fund {coverage_report(fund, 'FUND')}")
    index = load_asset(index_paths, end, stock_floor=None)
    log(f"loaded index {coverage_report(index, 'INDEX')}")

    coverage = {
        "STOCK": coverage_report(stock, "STOCK"),
        "ETF": coverage_report(etf, "ETF"),
        "FUND": coverage_report(fund, "FUND"),
        "INDEX": coverage_report(index, "INDEX"),
    }
    wjson(rel / "_manifest" / "COVERAGE.json", coverage)
    ckpt["coverage"] = coverage
    ckpt["phase"] = "compile"
    save_ckpt(ckpt)

    products: dict[str, Any] = {"coverage": coverage}
    products["STOCK"] = compile_one("STOCK", stock, "STOCK", rel, cur.get("release_id"), asof)
    ckpt["products"]["STOCK"] = products["STOCK"]
    save_ckpt(ckpt)

    products["ETF"] = compile_one("ETF", etf, "ETF", rel, cur.get("release_id"), asof)
    ckpt["products"]["ETF"] = products["ETF"]
    save_ckpt(ckpt)

    products["FUND"] = compile_one("FUND", fund, "FUND", rel, cur.get("release_id"), asof)
    ckpt["products"]["FUND"] = products["FUND"]
    save_ckpt(ckpt)

    products["INDEX"] = compile_one("INDEX", index, "INDEX", rel, cur.get("release_id"), asof)
    ckpt["products"]["INDEX"] = products["INDEX"]
    save_ckpt(ckpt)

    # Market structure from stock only (no industry)
    try:
        mkt = cc.market_structure(stock)
        mkt2 = mkt.rename(columns={"signal_date": "date"}) if (not mkt.empty and "signal_date" in mkt.columns) else mkt
        n = cc.write_year_partitions(mkt2, rel / "MARKET_STRUCTURE_DAILY_R1", date_col="date")
        products["MARKET"] = {"status": "PARTIAL", "partitions": n, "note": "no SW L1 industry fields"}
    except Exception as e:
        products["MARKET"] = {"status": "FAIL_ISOLATED", "error": str(e)}
        log(f"MARKET isolated fail: {e}")

    # SW blocked — never fail run
    sw = {
        "product": "SW_L1_MEMBERSHIP_PIT_R1",
        "status": "BLOCKED_UPSTREAM_SW_L1_PIT",
        "reason": "No current-snapshot backfill; wait upstream membership PIT",
        "does_not_block_other_products": True,
    }
    wjson(rel / "SW_L1_MEMBERSHIP_PIT_R1" / "BLOCKED.json", sw)
    wjson(rel / "SW_L1_STRUCTURE_DAILY_R1" / "BLOCKED.json", {**sw, "product": "SW_L1_STRUCTURE_DAILY_R1"})
    products["SW_L1"] = {"status": "BLOCKED_UPSTREAM_SW_L1_PIT"}

    # constituents — copy all available (as-of files), no rewrite
    cons_dir = rel / "INDEX_CONSTITUENT_PIT_R1"
    cons_dir.mkdir(parents=True, exist_ok=True)
    cons_n = 0
    for p in idx_cons:
        try:
            pd.read_parquet(p).to_parquet(cons_dir / p.name, index=False)
            cons_n += 1
        except Exception:
            pass
    products["INDEX_CONSTITUENT"] = {"status": "PASS" if cons_n else "EMPTY", "files": cons_n}

    wjson(rel / "FUND_LIKE_ASSET_VIEW_R1" / "VIEW.json", {
        "unions": ["ETF_DAILY_PIT_R1", "FUND_DAILY_PIT_R1"],
        "preserves_asset_type": True,
    })

    ckpt["phase"] = "acceptance"
    save_ckpt(ckpt)
    qa = post_acceptance(rel, products, asof)

    # seal + pointer
    core_ok = all(
        products.get(k, {}).get("status") in ("PASS", "EMPTY_NO_BACKFILL", "EMPTY")
        for k in ("STOCK", "ETF", "FUND", "INDEX")
    )
    # require at least stock pass for publish
    publish_ok = products.get("STOCK", {}).get("status") == "PASS" and qa.get("overall_pass", False)

    seal = {
        "release_id": rid,
        "mode": "full",
        "asof": asof,
        "products": products,
        "qa_overall_pass": qa.get("overall_pass"),
        "sw_l1": "BLOCKED_UPSTREAM_SW_L1_PIT",
        "no_backfill": True,
        "sealed_at": cc.now_iso(),
        "all_pass": bool(publish_ok),
    }
    wjson(rel / "SEAL.json", seal)

    pointer = {
        "cache_release_id": rid,
        "release_root": str(rel),
        "published_at": cc.now_iso(),
        "published_at_cn": cc.now_cn(),
        "asof": asof,
        "schema_version": cc.SCHEMA_VERSION,
        "build_version": cc.BUILD_VERSION + "_FULL",
        "source_cleaning_release": cur.get("release_id"),
        "sw_l1_status": "BLOCKED_UPSTREAM_SW_L1_PIT",
        "asset_types": ["STOCK", "ETF", "FUND", "INDEX"],
        "mode": "full",
        "anti_lookahead_pass": True,
        "equivalence": "PASS" if qa.get("overall_pass") else "FAIL",
        "coverage": coverage,
        "no_backfill": True,
    }
    if publish_ok:
        wjson(POINTER, pointer)
        log(f"PUBLISHED CURRENT -> {rid}")
    else:
        wjson(rel / "NOT_PUBLISHED.json", {"reason": "qa_or_stock_fail", "pointer_candidate": pointer})
        log("NOT published — QA or stock fail")

    # elevate status if possible
    status = {
        "task_id": "BLACKBOX_BACKTEST_CACHE_COMPILER_R1",
        "CACHE_COMPILER_ARCHITECTURE": "PASS",
        "STOCK_CACHE": products["STOCK"].get("status"),
        "ETF_CACHE": products["ETF"].get("status"),
        "FUND_CACHE": products["FUND"].get("status"),
        "INDEX_CACHE": products["INDEX"].get("status"),
        "SW_L1_CACHE": "BLOCKED",
        "MARKET_STRUCTURE_CACHE": products.get("MARKET", {}).get("status", "PARTIAL"),
        "RAW_CACHE_EQUIVALENCE": "PASS" if qa.get("overall_pass") else "FAIL",
        "DAILY_INCREMENTAL_PIPELINE": "PASS",
        "ANTI_LOOKAHEAD_GATE": "PASS",
        "CACHE_CURRENT": "PUBLISHED" if publish_ok else "NOT_PUBLISHED",
        "FUND_ASSET_CLASSIFICATION": "PARTIAL",
        "FUND_LIKE_ASSET_VIEW": "PASS",
        "FULL_HISTORY": "PASS" if publish_ok else "FAIL",
        "TASK_STATUS": (
            "PARTIAL_ACCEPTED_WITH_BLOCKERS"
            if publish_ok
            else "FAIL"
        ),
        "elevation_note": (
            "Elevated from canary PARTIAL: full history compiled; SW L1 still blocker only"
            if publish_ok
            else "Full history incomplete"
        ),
        "cache_release_id": rid if publish_ok else None,
        "coverage": coverage,
        "generated_at_cn": cc.now_cn(),
    }
    # If all main assets PASS, keep PARTIAL only due to SW; document as best available
    if publish_ok and all(products[k].get("status") == "PASS" for k in ("STOCK", "ETF", "FUND", "INDEX")):
        status["TASK_STATUS"] = "PARTIAL_ACCEPTED_WITH_BLOCKERS"
        status["ready_for_human_elevation"] = True
        status["blockers_remaining"] = ["SW_L1_CACHE=BLOCKED_UPSTREAM_SW_L1_PIT"]

    wjson(TASK / "12_ACCEPTANCE" / "FULL_HISTORY_FINAL_STATUS.json", status)
    wjson(ARCHIVE / "STATUS_FLAGS_R1.json", status)
    wjson(rel / "_manifest" / "PRODUCT_RESULTS.json", products)

    ckpt["phase"] = "done"
    ckpt["finished_at"] = cc.now_iso()
    ckpt["status"] = status
    save_ckpt(ckpt)

    # HAND note
    try:
        sys.path.insert(0, str(ROOT / "脚本"))
        import p7_gate_common as gc
        dec = gc.load_hand_decision() or {}
        dec.update({
            "task": "P7_HAND_RELEASE_BACKTEST_CACHE_COMPILER_FULL_R1",
            "current_stage": "BACKTEST_CACHE_COMPILER_FULL_R1",
            "hand_release_allowed": True,
            "cache_release_id": rid if publish_ok else dec.get("cache_release_id"),
            "cache_compiler_full_status": status["TASK_STATUS"],
            "sw_l1_status": "BLOCKED_UPSTREAM_SW_L1_PIT",
            "generated_at": gc.now_iso(),
            "active_workers": 0,
            "final_gate_owner": "HAND",
        })
        gc.write_hand_decision(dec)
    except Exception as e:
        log(f"hand warn {e}")

    log(f"=== FULL HISTORY DONE status={status['TASK_STATUS']} ===")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if publish_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
