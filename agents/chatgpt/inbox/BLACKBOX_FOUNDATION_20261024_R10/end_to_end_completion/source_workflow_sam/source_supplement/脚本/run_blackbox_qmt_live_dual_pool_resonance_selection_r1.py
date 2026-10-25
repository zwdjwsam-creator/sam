#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QMT LIVE DUAL POOL RESONANCE SELECTION R1.

ROUTE A = RESEARCH_POOL_VALIDATION (canonical ENERGY L4; subtheme first)
ROUTE B = FULL_MARKET_ANOMALY_DISCOVERY (SW L3 fallback; independent of prior)
ROUTE C = LAOTAO EXTERNAL_HUMAN_PRIOR validation (pool-level; HOLDING_STATUS_WEIGHT=0)

User-facing lists remain LIST A/B only. ROUTE C annotates / validates / logs resonance.
THREE_ROUTES_ENABLED=True (internal); no third user selection list.

ORDER_ALLOWED=FALSE · QMT_MODE=READ_ONLY · NO fake live from web/yesterday.
THRESHOLD_CALIBRATION=UNCALIBRATED · hierarchical gates only.

Usage:
  python -u E:\\BLACKBOX\\脚本\\run_blackbox_qmt_live_dual_pool_resonance_selection_r1.py --mode preflight|arm|status|watch|emit-0926|emit-0931
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

sys.path.insert(0, str(Path(r"E:\BLACKBOX") / "脚本"))
import blackbox_qmt_readonly_marketdata_r1 as qmd
import blackbox_laotao_premarket_route_c_r1 as laotao
import run_blackbox_open_three_line_watch_r1 as ow

ROOT = Path(r"E:\BLACKBOX")
TASK_ID = "QMT_LIVE_DUAL_POOL_RESONANCE_SELECTION_R1"
TASK = ROOT / "任务" / TASK_ID
LIVE_DIR = ROOT / "研究系统" / "CURRENT" / "LIVE"
FG = ROOT / "研究系统" / "FINE_GRAINED_INDUSTRY_TAXONOMY" / "CURRENT"
CN_CANON = FG / "CN_ENERGY_L4_POOLS" / "CN_ENERGY_L4_CANONICAL_POOLS.json"
BASELINE_DIR = FG / "L4_INTRADAY_AMOUNT_BASELINE_20D"
US_RANK_PURE = (
    ROOT / "任务" / "L4_IDENTITY_PURITY_AND_FULL_POOL_LIVE_OBSERVATION_R1" / "out" / "US_ENERGY_L4_RANK_PURE.json"
)
US_RANK_ALT = FG / "US_ENERGY_L4_SEALED" / "US_ENERGY_L4_RANK_PURE.json"
PURITY_CURRENT = ROOT / "运行" / "BLACKBOX_L4_IDENTITY_PURITY_CURRENT.json"
RUN_PTR = ROOT / "运行" / "BLACKBOX_QMT_LIVE_DUAL_POOL_RESONANCE_CURRENT.json"
CALIB = ROOT / "DAILY_RESEARCH" / "EVALUATION" / "LIVE_SELECTION_CALIBRATION_LEDGER" / "LEDGER.jsonl"
MASTER_SUMMARY = ROOT / "研究系统" / "CURRENT" / "MASTER_RESEARCH" / "MASTER_RESEARCH_SUMMARY.txt"

# Display/priority observe — does NOT redefine L4 breadth universe.
FORCE_FOCUS_OBSERVE = [
    {"code": "000968.SZ", "name": "蓝焰控股", "L4": "EN_UP_CRUDE_EP", "why": "USER_FORCE_FOCUS_TODAY"},
    {"code": "300195.SZ", "name": "长荣股份", "L3": "印刷包装机械III", "why": "USER_RESEARCH_ROUTE_WATCH_CONTINUATION"},
]

TOP_RULES = {
    # User-facing remains two lists (A/B); internal routes = A/B/C
    "LIVE_SELECTION_MUST_HAVE_TWO_PARALLEL_ROUTES": True,
    "THREE_ROUTES_ENABLED": True,
    "USER_FACING_SELECTION_LISTS": ["LIST_A_RESEARCH", "LIST_B_FULL_MARKET"],
    "ROUTE_A": "RESEARCH_POOL_VALIDATION",
    "ROUTE_B": "FULL_MARKET_DISCOVERY",
    "ROUTE_C": "LAOTAO_EXTERNAL_HUMAN_PRIOR_VALIDATION",
    "EXTERNAL_HUMAN_OBSERVATION_ROUTE": "LAOTAO_ROUTE_C",
    "RESEARCH_POOL_CANNOT_BE_BYPASSED_IN_ROUTE_A": True,
    "FULL_MARKET_ROUTE_MUST_NOT_BE_CONSTRAINED_BY_RESEARCH_PRIOR": True,
    "FULL_MARKET_SCAN_MUST_BE_BLIND_TO_RESEARCH_PRIOR": True,
    "FULL_MARKET_SCAN_MUST_BE_BLIND_TO_LAOTAO_PRIOR": True,
    "SUBTHEME_FIRST_STOCK_SECOND": True,
    "DUAL_DISCOVERY_RESONANCE_MUST_BE_RECORDED": True,
    "TRIPLE_SOURCE_RESONANCE_MUST_BE_LOGGED": True,
    "LAOTAO_OBSERVATION": "EXTERNAL_HUMAN_PRIOR",
    "LAOTAO_PRIOR": "VALIDATION_INPUT_NOT_TRUTH",
    "LAOTAO_STOCK_MENTION_NE_BUY_SIGNAL": True,
    "LAOTAO_HOLDING_NE_MARKET_LEADERSHIP": True,
    "LAOTAO_THEME_NE_CONFIRMED_THEME": True,
    "LAOTAO_HOLDINGS_HAVE_ZERO_SELECTION_WEIGHT": True,
    "HOLDING_STATUS_WEIGHT": 0,
    "SOURCE_MENTION_THEME_MUST_BE_RECONCILED_WITH_CANONICAL_IDENTITY": True,
    "HUMAN_PRIOR_SINGLE_STOCK_SUCCESS_CANNOT_CONFIRM_THEME": True,
    "HUMAN_PRIOR_MUST_BE_VALIDATED_AT_POOL_LEVEL": True,
    "0926_USES_FINAL_AUCTION": True,
    "0931_USES_FIRST_SEALED_CONTINUOUS_1M_BAR": True,
    "ONE_MINUTE_CONFIRMATION_IS_EARLY_ACCEPTANCE_NOT_FULL_CONFIRMATION": True,
    "MINUTE_ACCEPTANCE_QUALITY_REQUIRED": True,
    "LEADER_WITHOUT_FOLLOWERS_CANNOT_DEFINE_SUBTHEME": True,
    "OPEN_WATCH_CANNOT_DEFINE_L4_UNIVERSE": True,
    "CANONICAL_POOL_DEFINES_BREADTH_UNIVERSE": True,
    "ORDER_ALLOWED": False,
    "THRESHOLD_CALIBRATION": "UNCALIBRATED",
}

# Existing BLACKBOX liquidity heuristic (do not invent new thresholds): reuse open-watch style floor.
# Prefer larger amount; block near-zero amount "spikes".
MIN_AUCTION_AMOUNT_CNY = 5_000_000.0  # documented reuse from patrol absorb filters (~5e6)


def now_cn() -> datetime:
    return datetime.now().astimezone()


def now_iso() -> str:
    return now_cn().strftime("%Y-%m-%dT%H:%M:%S%z")


def write_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def load_json(p: Path) -> dict[str, Any]:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def trade_date_yyyymmdd() -> str:
    return now_cn().strftime("%Y%m%d")


def hhmmss() -> str:
    return now_cn().strftime("%H%M%S")


def load_canonical_pools() -> dict[str, dict[str, Any]]:
    doc = load_json(CN_CANON)
    return doc.get("POOLS") or {}


def research_universe_codes(pools: dict[str, dict[str, Any]]) -> list[str]:
    codes: list[str] = []
    for p in pools.values():
        for c in p.get("CANONICAL_MEMBERS") or []:
            codes.append(c)
    return sorted(set(codes))


def load_research_prior() -> dict[str, Any]:
    """Bind live research line to MASTER summary + mapping CURRENT (not hardcoded ENERGY)."""
    prior = {
        "GLOBAL_PRIMARY_THEME": "UNRESOLVED",
        "GLOBAL_SECONDARY_THEME": "NONE",
        "RESEARCH_ASOF": None,
        "US_L4_RANK_PURE": None,
        "SOURCE": [],
        "LATEST_SESSION_PRICE_LEADER": None,
        "FORMAL_FOCUS": [],
    }
    # Prefer machine mapping CURRENT when present (session-bound)
    map_cur = ROOT / "运行" / "BLACKBOX_GLOBAL_LEADERSHIP_FIRST_MAPPING_R3_CURRENT.json"
    mc = load_json(map_cur)
    if mc.get("PRIMARY_THEME"):
        prior["GLOBAL_PRIMARY_THEME"] = mc.get("PRIMARY_THEME")
        prior["GLOBAL_SECONDARY_THEME"] = mc.get("SECONDARY_THEME") or "NONE"
        prior["US_SESSION_REF"] = mc.get("US_SESSION_REF")
        prior["SOURCE"].append(str(map_cur))
        prior["LATEST_SESSION_PRICE_LEADER"] = mc.get("PRIMARY_THEME")
    if MASTER_SUMMARY.exists():
        txt = MASTER_SUMMARY.read_text(encoding="utf-8", errors="replace")
        prior["SOURCE"].append(str(MASTER_SUMMARY))
        head = "\n".join(txt.splitlines()[:50])
        prior["SUMMARY_HEAD"] = [ln.strip()[:160] for ln in txt.splitlines()[:12] if ln.strip()]
        # Explicit PRIMARY_THEME= line wins over keyword sniff
        for line in txt.splitlines()[:80]:
            s = line.strip()
            if s.startswith("PRIMARY_THEME="):
                prior["GLOBAL_PRIMARY_THEME"] = s.split("=", 1)[1].strip() or prior["GLOBAL_PRIMARY_THEME"]
            if s.startswith("SECONDARY_THEME="):
                prior["GLOBAL_SECONDARY_THEME"] = s.split("=", 1)[1].strip() or prior["GLOBAL_SECONDARY_THEME"]
            if s.startswith("US_SESSION_REF="):
                prior["US_SESSION_REF"] = s.split("=", 1)[1].strip()
            if s.startswith("ASOF_CN="):
                prior["RESEARCH_ASOF"] = s.split("=", 1)[1].strip()[:10]
            if "LATEST_US_SESSION_LEADER" in s or "最新会话" in s and "半导" in s:
                prior["LATEST_SESSION_PRICE_LEADER"] = prior.get("LATEST_SESSION_PRICE_LEADER") or "SEMICONDUCTOR"
        if "REOPEN_R3" in head or "ENERGY_STATUS=HISTORICAL" in txt or "能源=历史候选" in txt:
            # Do not keep ENERGY as live primary from sealed 0831 L4 print alone
            if prior.get("GLOBAL_PRIMARY_THEME") == "ENERGY" and "SEMICONDUCTOR" in txt[:3000]:
                if "PRIMARY_THEME=SEMICONDUCTOR" in txt or "价格领先方向" in txt:
                    prior["GLOBAL_PRIMARY_THEME"] = "SEMICONDUCTOR"
                    prior["ENERGY_STATUS"] = "HISTORICAL_CANDIDATE_NOT_RECONFIRMED"
        if "TOP_FOCUS=[]" in txt or "TOP_FOCUS = []" in txt:
            prior["FORMAL_FOCUS"] = []
    us = load_json(US_RANK_PURE) or load_json(US_RANK_ALT)
    if us:
        prior["US_L4_RANK_PURE"] = us
        prior["SOURCE"].append("US_ENERGY_L4_RANK_PURE")
        formal = us.get("FORMAL_BASKET_RANK") or us.get("FORMAL_RANK") or us.get("US_FORMAL_BASKET_RANK")
        prior["GLOBAL_L4_RANK"] = formal
        prior["US_L4_PRINT_NOTE"] = "HISTORICAL_SEALED_PRINT_NOT_AUTO_LIVE_PRIMARY"
    purity = load_json(PURITY_CURRENT)
    if purity:
        prior["IDENTITY_PURITY_STATUS"] = purity.get("FINAL_STATUS")
        prior["US_FORMAL_BASKET_RANK"] = purity.get("US_FORMAL_BASKET_RANK")
    return prior


def baseline_status() -> dict[str, Any]:
    readme = load_json(BASELINE_DIR / "README.json")
    index = load_json(BASELINE_DIR / "INDEX.json")
    return {
        "STATUS": readme.get("STATUS") or "MISSING",
        "TIP": readme.get("TIP") or readme.get("TIP_DATE"),
        "N_READY": index.get("N_READY") or readme.get("N_READY"),
        "N_MISSING": index.get("N_MISSING") or readme.get("N_MISSING"),
        "PATH": str(BASELINE_DIR),
        "NOTE": readme.get("NOTE"),
    }


def amount_ratio_vs_20d(code: str, snapshot: str, today_cum: float | None) -> float | None:
    if today_cum is None:
        return None
    p = BASELINE_DIR / "BY_CODE" / f"{code}.json"
    if not p.exists():
        # also try underscore name variants
        p2 = BASELINE_DIR / "BY_CODE" / f"{code.replace('.', '_')}.json"
        p = p2 if p2.exists() else p
    if not p.exists():
        return None
    doc = load_json(p)
    snaps = doc.get("SNAPSHOTS") or doc.get("snaps") or doc
    node = snaps.get(snapshot) if isinstance(snaps, dict) else None
    if not isinstance(node, dict):
        return None
    med = node.get("MEDIAN_20D") or node.get("median_20d")
    try:
        med = float(med)
    except Exception:
        return None
    if med <= 0:
        return None
    return today_cum / med


def load_full_market_l3() -> dict[str, Any]:
    """SW L3 tip membership — RESOLUTION=L3_FALLBACK for non-ENERGY L4."""
    uni = ow.load_universes()
    l3 = uni["l3"]
    by_ind: dict[str, list[str]] = {}
    for ind, g in l3.groupby("industry_name"):
        codes = [c for c in g["qmt_code"].tolist() if isinstance(c, str)]
        by_ind[str(ind)] = sorted(set(codes))
    all_codes = sorted({c for cs in by_ind.values() for c in cs})
    return {
        "by_l3": by_ind,
        "all_codes": all_codes,
        "n_l3": len(by_ind),
        "n_codes": len(all_codes),
        "release_root": uni.get("release_root"),
        "RESOLUTION_DEFAULT": "L3_FALLBACK",
    }


def pool_metrics_from_ticks(codes: list[str], ticks: dict[str, Any], trade_day: str) -> dict[str, Any]:
    rows = []
    observed = []
    suspended = []
    invalid = []
    for c in codes:
        raw = ticks.get(c)
        f = qmd.tick_fields(raw if isinstance(raw, dict) else None)
        if not f or f.get("last") is None:
            invalid.append(c)
            continue
        # tradability: zero volume+amount with flat may still be auction; keep if last present
        if f.get("amount") is not None and f["amount"] == 0 and f.get("volume") == 0:
            # could be suspended — mark but still observe price
            suspended.append(c)
        qd = f.get("quote_day")
        stale = qd is not None and qd != trade_day
        rows.append({**f, "code": c, "stale_quote": stale})
        observed.append(c)
    rets = [r["auction_return"] if r.get("auction_return") is not None else r.get("ret") for r in rows]
    rets = [x for x in rets if x is not None]
    amts = [r["amount"] for r in rows if r.get("amount") is not None]
    n_exp = len(codes)
    n_obs = len(observed)
    up = sum(1 for x in rets if x > 0)
    cov = "FULL_COVERAGE" if n_obs >= n_exp and n_exp else ("PARTIAL_COVERAGE" if n_obs else "NO_OBSERVATION")
    leaders = sorted(rows, key=lambda r: (r.get("auction_return") if r.get("auction_return") is not None else r.get("ret") or -9), reverse=True)
    leader = leaders[0] if leaders else None
    followers = leaders[1:4] if len(leaders) > 1 else []
    follower_pos = sum(1 for r in followers if (r.get("auction_return") or r.get("ret") or 0) > 0)
    return {
        "CANONICAL_COUNT": n_exp,
        "EXPECTED_TRADABLE_COUNT": n_exp - len([c for c in suspended if c in codes]),
        "OBSERVED_COUNT": n_obs,
        "MISSING_COUNT": max(0, n_exp - n_obs),
        "MISSING_CODES": [c for c in codes if c not in observed],
        "SUSPENDED_COUNT": len(suspended),
        "INVALID_COUNT": len(invalid),
        "LIVE_COVERAGE_STATUS": cov,
        "POOL_AUCTION_MEDIAN": median(rets) if rets else None,
        "POSITIVE_RATIO": (up / len(rets)) if rets else None,
        "POOL_AUCTION_AMOUNT_MEDIAN": median(amts) if amts else None,
        "LEADER": leader,
        "FOLLOWERS": followers,
        "FOLLOWER_POSITIVE_COUNT": follower_pos,
        "ROWS": rows,
        "STALE_QUOTE_COUNT": sum(1 for r in rows if r.get("stale_quote")),
    }


def hierarchical_select_research(pool_stats: dict[str, dict[str, Any]], prior: dict[str, Any], max_n: int = 5) -> list[dict[str, Any]]:
    """Subtheme first → stock. No forced fill. No numeric score weights."""
    # Rank pools by breadth then median (raw variables kept)
    pool_rank = []
    for lid, st in pool_stats.items():
        if st.get("OBSERVED_COUNT", 0) < 2:
            st = {**st, "FORMAL_L4_RANK_ALLOWED": False, "STATE": "SINGLE_STOCK_OR_THIN"}
        else:
            st = {**st, "FORMAL_L4_RANK_ALLOWED": True}
        if st.get("POSITIVE_RATIO") is None:
            continue
        pool_rank.append((lid, st))
    pool_rank.sort(key=lambda x: (x[1].get("POSITIVE_RATIO") or 0, x[1].get("POOL_AUCTION_MEDIAN") or -9), reverse=True)

    global_primary_l4 = None
    us = prior.get("US_FORMAL_BASKET_RANK") or prior.get("GLOBAL_L4_RANK") or []
    if isinstance(us, list) and us:
        global_primary_l4 = (us[0].get("pool_id") or us[0].get("POOL") or us[0].get("L4")) if isinstance(us[0], dict) else None

    picks: list[dict[str, Any]] = []
    for lid, st in pool_rank:
        if not st.get("FORMAL_L4_RANK_ALLOWED"):
            continue
        if (st.get("POSITIVE_RATIO") or 0) < 0.4:
            continue
        leader = st.get("LEADER") or {}
        code = leader.get("code")
        if not code:
            continue
        amt = leader.get("amount") or 0
        if amt < MIN_AUCTION_AMOUNT_CNY:
            continue
        followers_ok = (st.get("FOLLOWER_POSITIVE_COUNT") or 0) >= 1
        resonance = []
        if followers_ok:
            resonance.append("LEADER_FOLLOWER_RESONANCE")
        if global_primary_l4 and ("OILSERV" in str(global_primary_l4).upper() and "OFS" in lid or "REFIN" in str(global_primary_l4).upper() and "REFIN" in lid):
            resonance.append("GLOBAL_CN_L4_RESONANCE")
        if not followers_ok:
            resonance = ["SINGLE_STOCK_ONLY"]
            # cannot define subtheme alone — skip formal research pick
            continue
        picks.append({
            "CODE": code,
            "NAME": None,
            "L4": lid,
            "GLOBAL_PRIOR": prior.get("GLOBAL_PRIMARY_THEME"),
            "GLOBAL_PRIMARY_L4_US": global_primary_l4,
            "AUCTION_RETURN": leader.get("auction_return") if leader.get("auction_return") is not None else leader.get("ret"),
            "AUCTION_AMOUNT": amt,
            "AUCTION_AMOUNT_QUALITY": "OK" if amt >= MIN_AUCTION_AMOUNT_CNY else "WEAK",
            "POOL_BREADTH": st.get("POSITIVE_RATIO"),
            "POOL_MEDIAN": st.get("POOL_AUCTION_MEDIAN"),
            "LEADER_FOLLOWER": "LEADER" if followers_ok else "LEADER_NO_FOLLOWER",
            "RESONANCE": resonance,
            "SELECTION_REASON": f"pool={lid} breadth={st.get('POSITIVE_RATIO')} leader_from_full_pool",
            "RISK": "UNCALIBRATED_THRESHOLD; early auction only",
            "COVERAGE": st.get("LIVE_COVERAGE_STATUS"),
        })
        if len(picks) >= max_n:
            break
    return picks


def hierarchical_select_full_market(l3_stats: list[dict[str, Any]], research_codes: set[str], max_n: int = 5) -> list[dict[str, Any]]:
    picks = []
    for st in l3_stats:
        if st.get("n_obs", 0) < 5:
            continue
        if (st.get("positive_ratio") or 0) < 0.55:
            continue
        if (st.get("median_ret") or 0) <= 0:
            continue
        leader = st.get("leader") or {}
        code = leader.get("code")
        if not code:
            continue
        amt = leader.get("amount") or 0
        if amt < MIN_AUCTION_AMOUNT_CNY:
            continue
        followers_ok = (st.get("follower_pos") or 0) >= 2
        if not followers_ok:
            # SINGLE_STOCK_ANOMALY — not market leadership
            continue
        in_res = code in research_codes
        picks.append({
            "CODE": code,
            "NAME": None,
            "L3": st.get("l3"),
            "L4": None,
            "RESOLUTION": "L3_FALLBACK",
            "FINE_GRAINED_RESEARCH_REQUIRED": True,
            "POOL_ANOMALY": {
                "median_ret": st.get("median_ret"),
                "breadth": st.get("positive_ratio"),
                "n_obs": st.get("n_obs"),
            },
            "AUCTION_RETURN": leader.get("ret"),
            "AUCTION_AMOUNT": amt,
            "BREADTH": st.get("positive_ratio"),
            "LEADER_FOLLOWER": "LEADER",
            "IN_RESEARCH_POOL": in_res,
            "CROSS_UNIVERSE_RESONANCE": in_res,
            "SELECTION_REASON": f"L3 anomaly {st.get('l3')} breadth={st.get('positive_ratio')}",
            "RESONANCE": (["DUAL_DISCOVERY_RESONANCE"] if in_res else []) + ["LEADER_FOLLOWER_RESONANCE"],
        })
        if len(picks) >= max_n:
            break
    return picks


def scan_l3_anomalies(by_l3: dict[str, list[str]], ticks: dict[str, Any], top_k: int = 30) -> list[dict[str, Any]]:
    out = []
    for ind, codes in by_l3.items():
        rets = []
        rows = []
        for c in codes:
            f = qmd.tick_fields(ticks.get(c) if isinstance(ticks.get(c), dict) else None)
            r = f.get("auction_return") if f.get("auction_return") is not None else f.get("ret")
            if r is None:
                continue
            rows.append({"code": c, "ret": r, "amount": f.get("amount") or 0})
            rets.append(r)
        if len(rets) < 5:
            continue
        rows.sort(key=lambda x: x["ret"], reverse=True)
        pos = sum(1 for x in rets if x > 0)
        leader = rows[0]
        followers = rows[1:4]
        follower_pos = sum(1 for x in followers if x["ret"] > 0)
        out.append({
            "l3": ind,
            "n_obs": len(rets),
            "median_ret": median(rets),
            "positive_ratio": pos / len(rets),
            "leader": leader,
            "follower_pos": follower_pos,
            "RESOLUTION": "L3_FALLBACK",
        })
    out.sort(key=lambda x: (x["positive_ratio"], x["median_ret"]), reverse=True)
    return out[:top_k]


def market_state(research_primary: str | None, fm_primary: str | None, dual_n: int) -> str:
    if dual_n > 0 and research_primary:
        return "RESEARCH_CONFIRMED" if research_primary and fm_primary and research_primary.split("_")[0] in str(fm_primary) else "RESEARCH_PARTIALLY_CONFIRMED"
    if research_primary and not fm_primary:
        return "LOCAL_ROTATION_WITHIN_RESEARCH"
    if fm_primary and not research_primary:
        return "NEW_MARKET_DIRECTION_EMERGING"
    if not research_primary and not fm_primary:
        return "NO_CLEAR_LEADERSHIP"
    return "RESEARCH_PARTIALLY_CONFIRMED"


def format_list_txt(title: str, rows: list[dict[str, Any]], phase: str) -> str:
    lines = [title, f"PHASE={phase}", f"ORDER_ALLOWED=FALSE", f"GENERATED={now_iso()}", ""]
    if not rows:
        lines.append("(empty — NO_FORCE_FILL)")
        return "\n".join(lines) + "\n"
    for i, r in enumerate(rows, 1):
        lines.append(f"RANK={i}")
        for k, v in r.items():
            lines.append(f"  {k}={v}")
        lines.append("")
    return "\n".join(lines) + "\n"


def append_calib(event: dict[str, Any]) -> None:
    CALIB.parent.mkdir(parents=True, exist_ok=True)
    with CALIB.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")


def preflight(asof: str) -> dict[str, Any]:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    TASK.mkdir(parents=True, exist_ok=True)
    gaps = []
    pools = load_canonical_pools()
    research_codes = research_universe_codes(pools)
    prior = load_research_prior()
    base = baseline_status()
    purity = load_json(PURITY_CURRENT)

    qmt_ok = False
    qmt_detail: dict[str, Any] = {}
    try:
        probe = qmd.fetch_ticks(["601857.SH", "000001.SZ"], LIVE_DIR / "_preflight_tick.json")
        qmt_ok = bool(probe.get("ok"))
        sample = {}
        for c, t in (probe.get("ticks") or {}).items():
            sample[c] = qmd.tick_fields(t if isinstance(t, dict) else None)
        qmt_detail = {"port": probe.get("port"), "n": len(probe.get("ticks") or {}), "sample": sample}
        # freshness: quote day vs asof
        days = {v.get("quote_day") for v in sample.values() if v.get("quote_day")}
        qmt_detail["quote_days"] = sorted(days)
        qmt_detail["SESSION_LIVE"] = asof in days
    except Exception as e:
        gaps.append(f"QMT_LIVE_READ={e}")
        qmt_ok = False

    sw_ok = CN_CANON.exists()
    prior_ok = bool(prior.get("GLOBAL_PRIMARY_THEME"))
    baseline_ok = base.get("STATUS") in ("READY", "PARTIAL_READY", "PARTIAL")
    purity_ok = (purity.get("FINAL_STATUS") or "").startswith("PASS")

    try:
        fm = load_full_market_l3()
        fm_ok = fm["n_codes"] > 1000
    except Exception as e:
        fm = {"error": str(e)}
        fm_ok = False
        gaps.append(f"FULL_MARKET_UNIVERSE={e}")

    # Full pool metrics engine ready if canonical + tick path OK (VWAP needs 1m at 0931)
    full_pool_ready = sw_ok and qmt_ok and purity_ok

    # ROUTE C: ensure Laotao prior exists (EXTERNAL_HUMAN_PRIOR validation)
    laotao_prior_doc: dict[str, Any] = {}
    try:
        if not laotao.PRIOR_PATH.exists():
            laotao_prior_doc = laotao.build_laotao_0901_prior()
        else:
            laotao_prior_doc = laotao.load_json(laotao.PRIOR_PATH) or {}
            if not (laotao_prior_doc.get("THEMES") or []):
                laotao_prior_doc = laotao.build_laotao_0901_prior()
        laotao_ok = bool(laotao_prior_doc.get("THEMES"))
    except Exception as e:
        laotao_ok = False
        gaps.append(f"LAOTAO_PRIOR={e}")
        laotao_prior_doc = {}

    armed_0926 = qmt_ok and sw_ok and prior_ok and baseline_ok and fm_ok
    armed_0931 = armed_0926  # same gates; emit will require sealed 1m

    if not qmt_ok:
        gaps.append("QMT_LIVE_GATE=FAIL")
    if not baseline_ok:
        gaps.append("20D_SAME_TIME_BASELINE_NOT_READY")
    if not purity_ok:
        gaps.append("IDENTITY_PURITY_BASELINE_NOT_PASS")
    if not laotao_ok:
        gaps.append("LAOTAO_PRIOR_NOT_READY")

    live_start = "ARMED" if armed_0926 else "NOT_ARMED"
    formal_allowed = bool(qmt_ok and qmt_detail.get("SESSION_LIVE"))
    # Pre-open: connection OK but not session live yet — ARMED for schedule, formal selection blocked until session quotes

    state = {
        "TASK_ID": TASK_ID,
        "ASOF": asof,
        "SYSTEM_TIME": now_iso(),
        "ORDER_ALLOWED": False,
        "QMT_MODE": "READ_ONLY",
        "TOP_RULES": TOP_RULES,
        "QMT_LIVE_READ": "PASS" if qmt_ok else "FAIL",
        "QMT_DETAIL": qmt_detail,
        "QMT_CONNECTED": qmt_ok,
        "QMT_READ_ONLY": True,
        "SW0824_CURRENT_LOADED": sw_ok,
        "RESEARCH_PRIOR_LOADED": prior_ok,
        "ACTIVE_RESEARCH_L4_LOADED": bool(pools),
        "RESEARCH_CANONICAL_N": len(research_codes),
        "FULL_MARKET_UNIVERSE_LOADED": fm_ok,
        "FULL_MARKET_N_CODES": fm.get("n_codes") if isinstance(fm, dict) else None,
        "FULL_MARKET_N_L3": fm.get("n_l3") if isinstance(fm, dict) else None,
        "20D_SAME_TIME_BASELINE": base,
        "20D_SAME_TIME_BASELINE_READY": baseline_ok,
        "FULL_POOL_LIVE_GATE_READY": full_pool_ready,
        "IDENTITY_PURITY": purity.get("FINAL_STATUS"),
        "OUTPUT_0926_ARMED": armed_0926,
        "OUTPUT_0931_ARMED": armed_0931,
        "LIVE_START_0915": live_start,
        "FORMAL_LIVE_SELECTION_ALLOWED": formal_allowed,
        "FORMAL_LIVE_SELECTION_NOTE": "Requires quote_day==ASOF; pre-open ARMED≠formal emit",
        "ROUTE_A_RESEARCH_POOL": "READY" if (sw_ok and prior_ok and pools) else "NOT_READY",
        "ROUTE_B_FULL_MARKET": "READY" if fm_ok else "NOT_READY",
        "ROUTE_C_VALIDATION": "READY" if laotao_ok else "NOT_READY",
        "LAOTAO_PRIOR_LOADED": laotao_ok,
        "LAOTAO_OBSERVATION": "EXTERNAL_HUMAN_PRIOR",
        "LAOTAO_PRIOR": "VALIDATION_INPUT_NOT_TRUTH",
        "LAOTAO_STOCK_MENTION_NE_BUY_SIGNAL": True,
        "LAOTAO_HOLDING_NE_MARKET_LEADERSHIP": True,
        "LAOTAO_THEME_NE_CONFIRMED_THEME": True,
        "LAOTAO_HOLDINGS_HAVE_ZERO_SELECTION_WEIGHT": True,
        "HOLDING_STATUS_WEIGHT": 0,
        "THREE_ROUTES_ENABLED": True,
        "FULL_POOL_METRICS": "READY" if full_pool_ready else "NOT_READY",
        "DUAL_DISCOVERY_RESONANCE": "ENABLED",
        "TRIPLE_SOURCE_RESONANCE": "ENABLED",
        "MINUTE_ACCEPTANCE_QUALITY": "ENABLED",
        "GAPS": gaps,
        "RESEARCH_PRIOR": {k: prior[k] for k in prior if k != "US_L4_RANK_PURE"},
        "LIVE_DIR": str(LIVE_DIR),
        "ENTRY": str(Path(__file__).resolve()),
        "LAOTAO_PRIOR_PATH": str(laotao.PRIOR_PATH),
        "LAOTAO_THEME_N": len(laotao_prior_doc.get("THEMES") or []),
    }
    if gaps and not qmt_ok:
        state["FINAL_STATUS"] = "BLOCKED_BY_LIVE_DATA"
        state["LIVE_START_STATUS"] = "NOT_READY"
    elif armed_0926:
        state["FINAL_STATUS"] = "ARMED_WAIT_SESSION" if not formal_allowed else "READY"
        state["LIVE_START_STATUS"] = "READY"
    else:
        state["FINAL_STATUS"] = "NOT_READY"
        state["LIVE_START_STATUS"] = "NOT_READY"

    write_json(LIVE_DIR / "QMT_LIVE_STATE.json", state)
    write_json(RUN_PTR, {
        "TASK_ID": TASK_ID,
        "CURRENT": str(LIVE_DIR / "QMT_LIVE_STATE.json"),
        "LIVE_DIR": str(LIVE_DIR),
        "ENTRY": str(Path(__file__).resolve()),
        "MARKETDATA": str(Path(qmd.__file__).resolve()),
        "BASELINE_BUILDER": str(ROOT / "脚本" / "blackbox_build_l4_intraday_amount_baseline_20d_r1.py"),
        "UPDATED": now_iso(),
        "ORDER_ALLOWED": False,
        "FINAL_STATUS": state["FINAL_STATUS"],
    })
    return state


def emit_selection(phase: str, asof: str, ticks_cache: Path | str | None = None) -> dict[str, Any]:
    """phase in {0926, 0931}. Fail-closed on stale quotes / missing sealed bar.
    ticks_cache: optional path to existing fetch_ticks payload (_ticks_*.json); skips QMT refetch.
    """
    cache_path = Path(ticks_cache) if ticks_cache else None
    use_cache = bool(cache_path and cache_path.exists())

    if use_cache:
        # Avoid QMT contention with watch; validate session from cached ticks later.
        state = {
            "QMT_LIVE_READ": "PASS",
            "FORMAL_LIVE_SELECTION_ALLOWED": True,
            "TICKS_CACHE": str(cache_path),
            "TICKS_CACHE_MODE": True,
        }
    else:
        state = preflight(asof)
        if state.get("QMT_LIVE_READ") != "PASS":
            out = {"ok": False, "error": "QMT_LIVE_GATE=FAIL", "FORMAL_LIVE_SELECTION_ALLOWED": False}
            write_json(LIVE_DIR / f"EMIT_{phase}_BLOCKED.json", out)
            return out

    pools = load_canonical_pools()
    research_codes = research_universe_codes(pools)
    prior = load_research_prior()
    fm = load_full_market_l3()

    # Fetch research pool ticks always; full market may be large — batch all L3 codes
    all_codes = sorted(set(research_codes) | set(fm["all_codes"]))
    if use_cache:
        tick_payload = load_json(cache_path)
        if not isinstance(tick_payload, dict):
            tick_payload = {}
        ticks = tick_payload.get("ticks") or {}
        if not ticks and tick_payload and all(isinstance(v, dict) for v in list(tick_payload.values())[:3]):
            # bare code->tick map
            ticks = tick_payload
    else:
        tick_payload = qmd.fetch_ticks(all_codes, LIVE_DIR / f"_ticks_{phase}.json")
        ticks = tick_payload.get("ticks") or {}

    # Stale gate
    sample_days = set()
    for c in list(research_codes)[:20]:
        d, _ = qmd.parse_tick_timetag(ticks.get(c) if isinstance(ticks.get(c), dict) else None)
        if d:
            sample_days.add(d)
    session_live = asof in sample_days
    if not session_live:
        out = {
            "ok": False,
            "error": "STALE_OR_PREOPEN_QUOTES",
            "quote_days": sorted(sample_days),
            "asof": asof,
            "FORMAL_LIVE_SELECTION_ALLOWED": False,
            "NOTE": "禁止用昨日缓存伪装实时选股",
        }
        write_json(LIVE_DIR / f"EMIT_{phase}_BLOCKED.json", out)
        write_json(LIVE_DIR / "LIVE_MARKET_STATE.json", {**out, "MARKET_STATE": "NO_CLEAR_LEADERSHIP", "SYSTEM_TIME": now_iso()})
        return out

    # Time gates
    hm = hhmmss()
    if phase == "0926" and hm < "092500":
        return {"ok": False, "error": "TOO_EARLY_FOR_0926_NEED_FINAL_AUCTION", "hm": hm}
    if phase == "0931" and hm < "093100":
        return {"ok": False, "error": "TOO_EARLY_FOR_0931_NEED_SEALED_0930", "hm": hm}

    pool_stats = {}
    for lid, p in pools.items():
        members = list(p.get("CANONICAL_MEMBERS") or [])
        if not members:
            continue
        pool_stats[lid] = pool_metrics_from_ticks(members, ticks, asof)

    list_a = hierarchical_select_research(pool_stats, prior, max_n=5)
    l3_stats = scan_l3_anomalies(fm["by_l3"], ticks, top_k=40)
    list_b = hierarchical_select_full_market(l3_stats, set(research_codes), max_n=5)

    # Enrich names via instrument detail not required; leave None

    bars = {}
    if phase == "0931":
        try:
            need = sorted({r["CODE"] for r in list_a + list_b} | set(research_codes))
            bar_payload = qmd.fetch_1m_bars(need, asof, end_hhmmss="093059", out_json=LIVE_DIR / "_bars_0930.json")
            bars = bar_payload.get("bars") or {}
        except Exception as e:
            write_json(LIVE_DIR / "EMIT_0931_BAR_GAP.json", {"error": str(e), "SYSTEM_TIME": now_iso()})
            bars = {}

        # recompute list with minute acceptance — drop OPEN_REJECTION
        def enrich(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            out_rows = []
            for r in rows:
                code = r["CODE"]
                b = bars.get(code) or []
                # first sealed minute only
                first = None
                for row in b:
                    # keep bars with time <= 09:30:59
                    first = row
                    break
                last = qmd.tick_fields(ticks.get(code) if isinstance(ticks.get(code), dict) else None)
                price = last.get("last")
                vw = qmd.vwap_from_1m(b[:1] if b else [], ref_price=price)
                vwap = vw.get("vwap")
                above = (price > vwap) if (price is not None and vwap is not None) else None
                dist = ((price / vwap) - 1.0) if (price and vwap) else None
                quality = "EVIDENCE_GAP"
                if first and price is not None:
                    o = first.get("open")
                    h = first.get("high")
                    l = first.get("low")
                    c = first.get("close")
                    try:
                        o, h, l, c = float(o), float(h), float(l), float(c)
                        loc = (c - l) / (h - l) if h > l else None
                        if above is False and (last.get("ret") or 0) > 0:
                            quality = "OPEN_REJECTION_OR_HIGH_VOLUME_WEAK_ACCEPTANCE"
                        elif above and loc is not None and loc >= 0.6:
                            quality = "EARLY_ACCEPTANCE_GOOD"
                        else:
                            quality = "EARLY_MINUTE_ACCEPTANCE_MIXED"
                    except Exception:
                        quality = "EVIDENCE_GAP"
                r2 = {
                    **r,
                    "OPEN_RETURN": last.get("auction_return"),
                    "FIRST_MIN_BAR": first,
                    "VWAP_0930": vwap,
                    "VWAP_VOLUME_UNIT": vw.get("VOLUME_UNIT"),
                    "ABOVE_VWAP": above,
                    "VWAP_DISTANCE": dist,
                    "MINUTE_ACCEPTANCE_QUALITY": quality,
                    "FINAL_0931_STATE": "EARLY_MINUTE_ACCEPTANCE",
                    "NOT": "FULL_INTRADAY_CONFIRMATION",
                }
                # Annotate weak acceptance; do NOT hard-drop (unit bugs previously emptied lists)
                out_rows.append(r2)
            return out_rows[:5]

        # Compare to 0926
        prev_a = load_json(LIVE_DIR / "RESEARCH_POOL_0926.json").get("SELECTION") or []
        prev_b = load_json(LIVE_DIR / "FULL_MARKET_0926.json").get("SELECTION") or []
        list_a = enrich(list_a)
        list_b = enrich(list_b)
        for i, r in enumerate(list_a, 1):
            r["0931_RANK"] = i
            old = next((j for j, x in enumerate(prev_a, 1) if x.get("CODE") == r["CODE"]), None)
            r["0926_RANK"] = old
            r["RANK_CHANGE"] = (old - i) if old else None
        for i, r in enumerate(list_b, 1):
            r["0931_RANK"] = i
            old = next((j for j, x in enumerate(prev_b, 1) if x.get("CODE") == r["CODE"]), None)
            r["0926_RANK"] = old
            r["NEW_SINCE_0926"] = old is None
            r["RANK_CHANGE"] = (old - i) if old else None
        dropped_a = [x.get("CODE") for x in prev_a if x.get("CODE") not in {r["CODE"] for r in list_a}]
        new_a = [r["CODE"] for r in list_a if r.get("NEW_SINCE_0926") or r.get("0926_RANK") is None]
    else:
        dropped_a, new_a = [], []

    dual_codes = {r["CODE"] for r in list_a} & {r["CODE"] for r in list_b}
    for r in list_a + list_b:
        if r["CODE"] in dual_codes:
            res = list(r.get("RESONANCE") or [])
            if "DUAL_DISCOVERY_RESONANCE" not in res:
                res.append("DUAL_DISCOVERY_RESONANCE")
            r["RESONANCE"] = res
            r["CROSS_UNIVERSE_RESONANCE"] = True

    # --- ROUTE C: Laotao validation + triple-source annotations (user lists stay A/B only) ---
    laotao_prior = laotao.load_json(laotao.PRIOR_PATH) or laotao.build_laotao_0901_prior()
    laotao_anchor_set = set(laotao.laotao_anchor_codes(laotao_prior))
    codes_a = {r["CODE"] for r in list_a}
    codes_b = {r["CODE"] for r in list_b}
    laotao_val = laotao.validate_theme_pools(
        prior=laotao_prior,
        ticks=ticks,
        tick_fields_fn=qmd.tick_fields,
        pool_metrics_fn=pool_metrics_from_ticks,
        trade_day=asof,
        phase=phase,
        bars=bars if phase == "0931" else None,
        vwap_fn=qmd.vwap_from_1m if phase == "0931" else None,
    )
    write_json(LIVE_DIR / f"LAOTAO_VALIDATION_{phase}.json", laotao_val)

    for r in list_a + list_b:
        code = r["CODE"]
        fields = laotao.stock_laotao_fields(code, laotao_prior, laotao_val)
        r.update(fields)
        a_sel = code in codes_a
        b_sel = code in codes_b
        c_sel = code in laotao_anchor_set or bool(fields.get("LAOTAO_PRIOR_MATCH"))
        r["BLACKBOX_RESEARCH_SELECTED"] = a_sel
        r["FULL_MARKET_SELECTED"] = b_sel
        r["LAOTAO_PRIOR_SELECTED"] = c_sel
        r["RESONANCE_COUNT"] = int(a_sel) + int(b_sel) + int(c_sel)
        r["RESONANCE_TYPE"] = laotao.resonance_type(a_sel, b_sel, c_sel)

    research_primary = list_a[0]["L4"] if list_a else None
    fm_primary = list_b[0].get("L3") if list_b else None
    mstate = market_state(research_primary, fm_primary, len(dual_codes))
    energy_cross = laotao.energy_vs_laotao_cross(
        research_primary,
        laotao_val.get("LAOTAO_DAILY_VALIDATION") or {},
    )

    triple = {
        "PHASE": phase,
        "ASOF": asof,
        "SYSTEM_TIME": now_iso(),
        "ORDER_ALLOWED": False,
        "LIST_A": [r.get("CODE") for r in list_a],
        "LIST_B": [r.get("CODE") for r in list_b],
        "LAOTAO_ANCHORS": sorted(laotao_anchor_set),
        "DUAL_CODES": sorted(dual_codes),
        "TRIPLE_CODES": sorted(codes_a & codes_b & laotao_anchor_set),
        "LAOTAO_DAILY_VALIDATION": laotao_val.get("LAOTAO_DAILY_VALIDATION"),
        "ENERGY_VS_LAOTAO_CROSS": energy_cross,
        "HOLDING_STATUS_WEIGHT": 0,
        "USER_FACING_LISTS": ["A", "B"],
        "NOTE": "ROUTE_C validates/annotates only; no third user selection list",
    }
    write_json(LIVE_DIR / f"THREE_ROUTE_RESONANCE_{phase}.json", triple)
    laotao.append_human_calib({
        "event": f"LAOTAO_ROUTE_C_{phase}",
        "asof": asof,
        "system_time": now_iso(),
        "list_a": [r.get("CODE") for r in list_a],
        "list_b": [r.get("CODE") for r in list_b],
        "laotao_daily": laotao_val.get("LAOTAO_DAILY_VALIDATION"),
        "energy_vs_laotao_cross": energy_cross,
        "triple_codes": triple["TRIPLE_CODES"],
        "HOLDING_STATUS_WEIGHT": 0,
        "ORDER_ALLOWED": False,
    })

    # If research weak and FM strong
    research_weak = not list_a
    note = None
    if research_weak and list_b:
        note = {
            "RESEARCH_PRIOR_NOT_CONFIRMED": True,
            "FULL_MARKET_NEW_LEADERSHIP_CANDIDATE": fm_primary,
        }

    cross = {
        "RESEARCH_POOL_PRIMARY_L4": research_primary,
        "FULL_MARKET_PRIMARY_L4": fm_primary,
        "CROSS_POOL_RESONANCE": sorted(dual_codes),
        "DUAL_DISCOVERY_COUNT": len(dual_codes),
        "ENERGY_VS_LAOTAO_CROSS": energy_cross,
        "TRIPLE_SOURCE_RESONANCE_COUNT": len(triple["TRIPLE_CODES"]),
        "MARKET_STATE": mstate,
        "NOTE": note,
        "SYSTEM_TIME": now_iso(),
        "MARKET_TIME": hm,
        "LATEST_QUOTE_TIME": sorted(sample_days),
        "LATEST_SEALED_BAR_TIME": "093059" if phase == "0931" else None,
        "RESEARCH_ASOF": asof,
        "THRESHOLD_CALIBRATION": "UNCALIBRATED",
        "ORDER_ALLOWED": False,
    }

    meta = {
        "TASK_ID": TASK_ID,
        "PHASE": phase,
        "ASOF": asof,
        "SYSTEM_TIME": now_iso(),
        "MARKET_TIME": hm,
        "ORDER_ALLOWED": False,
        "SELECTION": list_a if phase else [],
        "TOP_RULES": TOP_RULES,
    }

    if phase == "0926":
        write_json(LIVE_DIR / "RESEARCH_POOL_0926.json", {**meta, "SELECTION": list_a})
        write_json(LIVE_DIR / "FULL_MARKET_0926.json", {**meta, "SELECTION": list_b, "ROUTE": "B"})
        write_json(LIVE_DIR / "CROSS_RESONANCE_0926.json", cross)
        (LIVE_DIR / "QMT_LIVE_SELECTION_0926.txt").write_text(
            format_list_txt("## A. RESEARCH POOL SELECTION — 09:26", list_a, "0926")
            + format_list_txt("## B. FULL MARKET SELECTION — 09:26", list_b, "0926")
            + f"\nMARKET_STATE={mstate}\nRESEARCH_POOL_PRIMARY_L4={research_primary}\nFULL_MARKET_PRIMARY_L3={fm_primary}\n",
            encoding="utf-8",
        )
    else:
        write_json(LIVE_DIR / "RESEARCH_POOL_0931.json", {**meta, "SELECTION": list_a, "DROPPED_FROM_0926": dropped_a, "NEW_AT_0931": new_a})
        write_json(LIVE_DIR / "FULL_MARKET_0931.json", {**meta, "SELECTION": list_b, "ROUTE": "B"})
        write_json(LIVE_DIR / "CROSS_RESONANCE_0931.json", cross)
        (LIVE_DIR / "QMT_LIVE_SELECTION_0931.txt").write_text(
            format_list_txt("## A. RESEARCH POOL SELECTION — 09:31", list_a, "0931")
            + format_list_txt("## B. FULL MARKET SELECTION — 09:31", list_b, "0931")
            + f"\nMARKET_STATE={mstate}\nEARLY_MINUTE_ACCEPTANCE=TRUE\nFULL_INTRADAY_CONFIRMATION=FALSE\n",
            encoding="utf-8",
        )

    write_json(LIVE_DIR / "LIVE_MARKET_STATE.json", {
        **cross,
        "POOL_STATS_SUMMARY": {k: {kk: vv for kk, vv in v.items() if kk != "ROWS"} for k, v in pool_stats.items()},
        "L3_TOP": l3_stats[:10],
        "PHASE": phase,
    })

    append_calib({
        "event": f"SELECTION_{phase}",
        "asof": asof,
        "system_time": now_iso(),
        "list_a": [r.get("CODE") for r in list_a],
        "list_b": [r.get("CODE") for r in list_b],
        "market_state": mstate,
        "placeholders": {"1000_STATE": None, "1030_STATE": None, "CLOSE_STATE": None, "NEXT_DAY_OPEN": None, "NEXT_DAY_CLOSE": None},
    })

    # refresh state (skip QMT probe when ticks_cache to avoid watch contention)
    if use_cache:
        state2 = load_json(LIVE_DIR / "QMT_LIVE_STATE.json") or {}
        state2.update({
            "SYSTEM_TIME": now_iso(),
            "ORDER_ALLOWED": False,
            "LAST_EMIT": phase,
            "LAST_EMIT_OK": True,
            "TICKS_CACHE": str(cache_path),
            "TICKS_CACHE_MODE": True,
            "FORMAL_LIVE_SELECTION_ALLOWED": True,
            "QMT_LIVE_READ": state2.get("QMT_LIVE_READ") or "PASS",
            "FINAL_STATUS": "READY",
        })
    else:
        state2 = preflight(asof)
        state2["LAST_EMIT"] = phase
        state2["LAST_EMIT_OK"] = True
    write_json(LIVE_DIR / "QMT_LIVE_STATE.json", state2)
    return {
        "ok": True,
        "phase": phase,
        "list_a_n": len(list_a),
        "list_b_n": len(list_b),
        "market_state": mstate,
        "dual": sorted(dual_codes),
        "ticks_cache_mode": use_cache,
        "laotao_daily": (laotao_val.get("LAOTAO_DAILY_VALIDATION") if isinstance(laotao_val, dict) else None),
    }


def watch_loop(asof: str, interval: int = 15) -> None:
    """09:15+ accumulate into session tick cache; formal emit at 09:26/09:31 from cache when possible."""
    state = preflight(asof)
    write_json(
        LIVE_DIR / "WATCH_ARMED.json",
        {
            "armed_at": now_iso(),
            "state": state["FINAL_STATUS"],
            "ORDER_ALLOWED": False,
            "CACHE_FIRST": True,
            "SESSION_TICK_CACHE": str(LIVE_DIR / "_ticks_session_cache.json"),
        },
    )
    emitted_0926 = False
    emitted_0931 = False
    last_full_cache_hm = ""
    session_cache = LIVE_DIR / "_ticks_session_cache.json"
    fm = load_full_market_l3()
    full_codes = list(fm.get("all_codes") or [])

    while True:
        hm = hhmmss()
        # 09:15–09:26: light research ticks + periodic full-market session cache refresh
        if "091500" <= hm < "092600":
            pools = load_canonical_pools()
            codes = research_universe_codes(pools)
            focus = [x["code"] for x in FORCE_FOCUS_OBSERVE if x.get("code")]
            try:
                laotao_prior = laotao.load_json(laotao.PRIOR_PATH) or {}
                laotao_anchors = laotao.laotao_anchor_codes(laotao_prior) if laotao_prior else []
            except Exception:
                laotao_anchors = []
            light_codes = sorted(set(codes) | set(focus) | set(laotao_anchors))
            try:
                payload = qmd.fetch_ticks(light_codes, LIVE_DIR / "_watch_ticks.json")
                ticks = payload.get("ticks") or {}
                focus_snap = {
                    c: qmd.tick_fields(ticks.get(c) if isinstance(ticks.get(c), dict) else None) for c in focus
                }
                write_json(
                    LIVE_DIR / "FORCE_FOCUS_TICK_SNAP.json",
                    {"SYSTEM_TIME": now_iso(), "MARKET_TIME": hm, "FOCUS": focus_snap, "ORDER_ALLOWED": False},
                )
                write_json(
                    LIVE_DIR / "PROVISIONAL_0915_0925.json",
                    {
                        "SYSTEM_TIME": now_iso(),
                        "MARKET_TIME": hm,
                        "n_ticks": len(ticks),
                        "FORCE_FOCUS": focus,
                        "LAOTAO_ANCHORS_TICKED": laotao_anchors,
                        "HOLDING_STATUS_WEIGHT": 0,
                        "NOTE": "provisional only — NOT formal user selection; cache-first session",
                        "ORDER_ALLOWED": False,
                        "SESSION_CACHE": str(session_cache),
                    },
                )
                # Full-market cache: once at/after 09:15, refresh again near 09:24 for auction finality
                need_full = (not session_cache.exists()) or (
                    hm >= "092400" and last_full_cache_hm < "092400"
                ) or (hm >= "091500" and last_full_cache_hm < "091500")
                if need_full and full_codes:
                    full_payload = qmd.fetch_ticks(full_codes, session_cache)
                    # also mirror phase path for emit-0926 --ticks-cache default
                    write_json(LIVE_DIR / "_ticks_0926.json", full_payload)
                    last_full_cache_hm = hm
                    write_json(
                        LIVE_DIR / "SESSION_CACHE_META.json",
                        {
                            "SYSTEM_TIME": now_iso(),
                            "MARKET_TIME": hm,
                            "n_ticks": len(full_payload.get("ticks") or {}),
                            "path": str(session_cache),
                            "ORDER_ALLOWED": False,
                        },
                    )
            except Exception as e:
                write_json(LIVE_DIR / "WATCH_ERROR.json", {"t": now_iso(), "e": str(e)})

        if hm >= "092600" and not emitted_0926:
            cache_for_0926 = session_cache if session_cache.exists() else (LIVE_DIR / "_ticks_0926.json")
            if not cache_for_0926.exists() and full_codes:
                # one-shot fill cache then emit from cache (no second ad-hoc path)
                qmd.fetch_ticks(full_codes, cache_for_0926)
            emit_selection("0926", asof, ticks_cache=cache_for_0926 if cache_for_0926.exists() else None)
            emitted_0926 = True

        if hm >= "093100" and not emitted_0931:
            cache_0931 = LIVE_DIR / "_ticks_0931.json"
            # Refresh session cache once into 0931 file, then emit exclusively from that cache
            src = session_cache if session_cache.exists() else None
            if full_codes:
                qmd.fetch_ticks(full_codes, cache_0931)
            elif src and src.exists():
                write_json(cache_0931, load_json(src))
            emit_selection("0931", asof, ticks_cache=cache_0931 if cache_0931.exists() else None)
            emitted_0931 = True
            break

        if hm >= "093500" and emitted_0926 and emitted_0931:
            break
        time.sleep(interval)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["preflight", "arm", "status", "watch", "emit-0926", "emit-0931"])
    ap.add_argument("--asof", default=None, help="YYYYMMDD default today")
    ap.add_argument("--interval-sec", type=int, default=15)
    ap.add_argument("--ticks-cache", default=None, help="Reuse existing _ticks_*.json; skip fetch_ticks")
    args = ap.parse_args()
    asof = args.asof or trade_date_yyyymmdd()

    if args.mode in ("preflight", "arm", "status"):
        st = preflight(asof)
        print(json.dumps({
            "QMT_LIVE_READ": st["QMT_LIVE_READ"],
            "LIVE_START_0915": st["LIVE_START_0915"],
            "ROUTE_A_RESEARCH_POOL": st["ROUTE_A_RESEARCH_POOL"],
            "ROUTE_B_FULL_MARKET": st["ROUTE_B_FULL_MARKET"],
            "ROUTE_C_VALIDATION": st.get("ROUTE_C_VALIDATION"),
            "LAOTAO_PRIOR_LOADED": st.get("LAOTAO_PRIOR_LOADED"),
            "LAOTAO_OBSERVATION": st.get("LAOTAO_OBSERVATION"),
            "LAOTAO_HOLDINGS_HAVE_ZERO_SELECTION_WEIGHT": st.get("LAOTAO_HOLDINGS_HAVE_ZERO_SELECTION_WEIGHT"),
            "HOLDING_STATUS_WEIGHT": st.get("HOLDING_STATUS_WEIGHT"),
            "THREE_ROUTES_ENABLED": st.get("THREE_ROUTES_ENABLED"),
            "TRIPLE_SOURCE_RESONANCE": st.get("TRIPLE_SOURCE_RESONANCE"),
            "FULL_POOL_METRICS": st["FULL_POOL_METRICS"],
            "20D_SAME_TIME_BASELINE": "READY" if st["20D_SAME_TIME_BASELINE_READY"] else "NOT_READY",
            "0926_SELECTION": "ARMED" if st["OUTPUT_0926_ARMED"] else "NOT_ARMED",
            "0931_SELECTION": "ARMED" if st["OUTPUT_0931_ARMED"] else "NOT_ARMED",
            "DUAL_DISCOVERY_RESONANCE": st["DUAL_DISCOVERY_RESONANCE"],
            "MINUTE_ACCEPTANCE_QUALITY": st["MINUTE_ACCEPTANCE_QUALITY"],
            "ORDER_ALLOWED": False,
            "FORMAL_LIVE_SELECTION_ALLOWED": st["FORMAL_LIVE_SELECTION_ALLOWED"],
            "FINAL_STATUS": st["FINAL_STATUS"],
            "GAPS": st.get("GAPS"),
            "LIVE_DIR": st["LIVE_DIR"],
            "ENTRY": st["ENTRY"],
            "LAOTAO_PRIOR_PATH": st.get("LAOTAO_PRIOR_PATH"),
            "LAOTAO_THEME_N": st.get("LAOTAO_THEME_N"),
        }, ensure_ascii=False, indent=2))
        return 0 if st["LIVE_START_STATUS"] == "READY" else 2

    if args.mode == "watch":
        watch_loop(asof, args.interval_sec)
        return 0
    if args.mode == "emit-0926":
        print(json.dumps(emit_selection("0926", asof, ticks_cache=args.ticks_cache), ensure_ascii=False, indent=2))
        return 0
    if args.mode == "emit-0931":
        print(json.dumps(emit_selection("0931", asof, ticks_cache=args.ticks_cache), ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
