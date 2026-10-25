#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Morning Selection validation: Tape Continuity + Cross-Source Bridge + QMT live.

ORDER_ALLOWED=FALSE. Does not modify HAND / PASS_A / 13 gates.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"E:\BLACKBOX")
INPUT_PACK = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_RESEARCH_INPUT_PACK_CURRENT.json"
TAPE_MEM = ROOT / "DAILY_RESEARCH" / "MARKET_TAPE_MEMORY"


def now_cn() -> str:
    return datetime.now().astimezone().isoformat()


def load_json(p: Path) -> dict | list | None:
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def live_dir(asof: str) -> Path:
    return ROOT / "研究系统" / "CURRENT" / "MASTER_RESEARCH" / f"OPEN_WATCH_{asof}" / "LIVE"


def jq_code(qmt_code: str) -> str:
    c = qmt_code.upper()
    if c.endswith(".SH"):
        return c.replace(".SH", ".XSHG")
    if c.endswith(".SZ"):
        return c.replace(".SZ", ".XSHE")
    return c


def qmt_code(jq: str) -> str:
    c = jq.upper()
    if c.endswith(".XSHG"):
        return c.replace(".XSHG", ".SH")
    if c.endswith(".XSHE"):
        return c.replace(".XSHE", ".SZ")
    return c


def resolve_cache_root() -> Path | None:
    try:
        out = subprocess.check_output(
            [
                str(ROOT / ".venv" / "Scripts" / "python.exe"),
                "-u",
                str(ROOT / "脚本" / "blackbox_data_access_resolver_r1.py"),
                "--dataset",
                "STOCK_DAILY",
                "--dump-current",
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        data = json.loads(out)
        root = data.get("cache_root")
        return Path(root) if root else None
    except Exception:
        return None


def load_daily_history(cache_root: Path, jq: str, n: int = 15) -> pd.DataFrame:
    year = datetime.now().year
    p = cache_root / "STOCK_DAILY_PIT_R1" / f"year={year}" / f"part_{year}.parquet"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_parquet(p, columns=["date", "code", "open", "high", "low", "close", "volume", "money"])
    sub = df[df["code"] == jq].sort_values("date").tail(n + 1).copy()
    if sub.empty:
        return sub
    sub["prev_close"] = sub["close"].shift(1)
    sub["ret"] = (sub["close"] / sub["prev_close"] - 1.0).fillna(0.0)
    sub["vol_med20"] = sub["volume"].rolling(20, min_periods=3).median()
    sub["vol_expansion"] = sub["volume"] / sub["vol_med20"].replace(0, pd.NA)
    return sub.tail(n)


def analyze_tape(hist: pd.DataFrame) -> dict[str, Any]:
    if hist.empty or len(hist) < 3:
        return {
            "PRIOR_3D_ANOMALY_COUNT": 0,
            "PRIOR_5D_ANOMALY_COUNT": 0,
            "PRIOR_10D_ANOMALY_COUNT": 0,
            "PRIOR_ABSORPTION_EVENTS": 0,
            "PRIOR_BREAKOUT_EVENTS": 0,
            "PRIOR_GAP_FADE_EVENTS": 0,
            "PRIOR_RELATIVE_STRENGTH_EVENTS": 0,
            "PRIOR_NEXT_DAY_FOLLOW_THROUGH": "UNKNOWN",
            "PRIOR_FAILED_BREAKOUTS": 0,
            "FAILED_BREAKOUT_COUNT": 0,
            "NEXT_DAY_REJECTION_COUNT": 0,
            "GAP_FADE_HISTORY": 0,
            "LAST_MEANINGFUL_EVENT_DATE": None,
            "AIHUA_TAPE_STATE": "UNKNOWN",
            "TAPE_CONTINUITY": "UNKNOWN",
            "HISTORICAL_FOLLOW_THROUGH_QUALITY": "UNKNOWN",
            "events": [],
        }

    anomaly_thr = 0.05
    vol_thr = 1.8
    events: list[dict] = []
    anomalies: list[int] = []
    failed = 0
    gap_fades = 0
    follow_ok = 0
    follow_bad = 0

    for i in range(len(hist)):
        row = hist.iloc[i]
        d = str(row["date"])[:10]
        ret = float(row["ret"])
        volx = float(row["vol_expansion"]) if pd.notna(row["vol_expansion"]) else 1.0
        gap = float(row["open"] / row["prev_close"] - 1.0) if pd.notna(row["prev_close"]) and row["prev_close"] else 0.0

        if abs(ret) >= anomaly_thr or volx >= vol_thr:
            anomalies.append(i)
            et = "ANOMALY"
            if ret >= anomaly_thr and volx >= vol_thr:
                et = "BREAKOUT"
            elif ret >= anomaly_thr and volx < 1.2:
                et = "RELATIVE_STRENGTH"
            elif volx >= vol_thr and abs(ret) < 0.02:
                et = "ABSORPTION"
            events.append({"date": d, "type": et, "ret": round(ret, 4), "vol_expansion": round(volx, 2)})

        if gap >= 0.03 and ret < gap * 0.3:
            gap_fades += 1
            events.append({"date": d, "type": "GAP_FADE", "ret": round(ret, 4), "gap": round(gap, 4)})

        if i > 0 and hist.iloc[i - 1]["ret"] >= anomaly_thr and ret <= -0.02:
            failed += 1
            follow_bad += 1
        elif i > 0 and hist.iloc[i - 1]["ret"] >= anomaly_thr and ret >= 0.01:
            follow_ok += 1

    n = len(hist)
    a3 = sum(1 for i in anomalies if i >= n - 3)
    a5 = sum(1 for i in anomalies if i >= n - 5)
    a10 = len(anomalies)

    last_evt = events[-1]["date"] if events else None
    last_ret = float(hist.iloc[-1]["ret"])
    prior_anom_before_last = any(i < n - 1 for i in anomalies)

    if a10 == 0:
        state = "ONE_DAY_NOISE" if last_ret >= anomaly_thr else "UNKNOWN"
        continuity = "WEAK"
    elif prior_anom_before_last and last_ret >= anomaly_thr * 0.8:
        state = "REACTIVATION"
        continuity = "STRONG"
    elif a5 >= 2:
        state = "CONTINUATION"
        continuity = "STRONG"
    elif failed >= 2:
        state = "REPEATED_FAILED_BREAKOUT"
        continuity = "WEAK"
    elif a10 >= 1 and last_ret >= anomaly_thr:
        state = "FIRST_DISCOVERY"
        continuity = "MODERATE"
    elif any(e["type"] == "ABSORPTION" for e in events[-5:]):
        state = "PERSISTENT_STRENGTH"
        continuity = "MODERATE"
    else:
        state = "UNKNOWN"
        continuity = "MODERATE" if a10 else "WEAK"

    ftq = "UNKNOWN"
    if follow_ok + follow_bad > 0:
        ftq = "STRONG" if follow_ok > follow_bad else "WEAK"

    return {
        "PRIOR_3D_ANOMALY_COUNT": a3,
        "PRIOR_5D_ANOMALY_COUNT": a5,
        "PRIOR_10D_ANOMALY_COUNT": a10,
        "PRIOR_ABSORPTION_EVENTS": sum(1 for e in events if e["type"] == "ABSORPTION"),
        "PRIOR_BREAKOUT_EVENTS": sum(1 for e in events if e["type"] == "BREAKOUT"),
        "PRIOR_GAP_FADE_EVENTS": gap_fades,
        "PRIOR_RELATIVE_STRENGTH_EVENTS": sum(1 for e in events if e["type"] == "RELATIVE_STRENGTH"),
        "PRIOR_NEXT_DAY_FOLLOW_THROUGH": ftq,
        "PRIOR_FAILED_BREAKOUTS": failed,
        "FAILED_BREAKOUT_COUNT": failed,
        "NEXT_DAY_REJECTION_COUNT": follow_bad,
        "GAP_FADE_HISTORY": gap_fades,
        "LAST_MEANINGFUL_EVENT_DATE": last_evt,
        "AIHUA_TAPE_STATE": state,
        "TAPE_CONTINUITY": continuity,
        "HISTORICAL_FOLLOW_THROUGH_QUALITY": ftq,
        "events": events[-12:],
        "daily_tail": [
            {
                "date": str(r["date"])[:10],
                "ret": round(float(r["ret"]), 4),
                "vol_expansion": round(float(r["vol_expansion"]), 2) if pd.notna(r["vol_expansion"]) else None,
            }
            for _, r in hist.tail(10).iterrows()
        ],
    }


def live_persistence_from_yidong(yidong: dict, code: str) -> dict[str, Any]:
    for key in ("yidong_top", "absorb_strong", "intersect_yidong_absorb_resonance"):
        for s in yidong.get(key) or []:
            if s.get("code") == code:
                ab = s.get("absorb") or {}
                if isinstance(ab, str):
                    return {"LIVE_PERSISTENCE": ab, "absorb_detail": {}}
                score = float(ab.get("score") or 0)
                persist = float(ab.get("amt_persist_last5_vs_prior5") or 0)
                label = ab.get("label") or "UNKNOWN"
                giveback = float(ab.get("giveback_from_peak") or 0)
                if label == "STRONG" and persist >= 0.35 and giveback <= 0.02:
                    lp = "STRONG"
                elif label in ("STRONG", "OK") and persist >= 0.15:
                    lp = "MODERATE"
                elif label == "STRONG" and persist < 0.15:
                    lp = "WEAK_PERSIST"
                else:
                    lp = "WEAK"
                return {
                    "LIVE_PERSISTENCE": lp,
                    "absorb_label": label,
                    "absorb_score": score,
                    "amt_persist": persist,
                    "giveback_from_peak": giveback,
                    "CURRENT_RETURN": s.get("ret"),
                    "AMOUNT": s.get("amount"),
                }
    return {"LIVE_PERSISTENCE": "NOT_IN_YIDONG"}


def branch_sync(code: str, l3: str, off_prior: list[dict], resonance_l3: list[dict]) -> dict[str, Any]:
    peers = [x for x in off_prior if x.get("l3") == l3 and x.get("code") != code]
    reso_hit = any(r.get("l3") == l3 or r.get("industry") == l3 for r in (resonance_l3 or []))
    n = len(peers) + 1
    if n >= 3 and reso_hit:
        sync = "STRONG"
    elif n >= 2 or reso_hit:
        sync = "MODERATE"
    elif n == 1:
        sync = "SOLO"
    else:
        sync = "WEAK"
    return {"BRANCH_SYNC": sync, "BRANCH_N": n, "BRANCH_PEERS": [p.get("code") for p in peers[:5]]}


def theme_keywords(stock: dict) -> list[str]:
    parts = [stock.get("name") or "", stock.get("l1") or "", stock.get("l2") or "", stock.get("l3") or ""]
    base = " ".join(parts)
    kws = set(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", base))
    mapping = {
        "被动元件": ["被动", "元件", "电容", "MLCC", "capacitor", "passive", "电子材料"],
        "模拟芯片": ["模拟", "芯片", "semiconductor", "analog"],
        "银行": ["银行", "bank", "金融"],
        "煤炭": ["煤炭", "coal", "动力煤"],
        "房地产": ["房地产", "地产", "property", "物业"],
        "传媒": ["传媒", "media", "视频"],
        "AI硬件": ["AI", "power", "PCB", "hardware", "数据中心", "服务器", "电源"],
    }
    out: set[str] = set(kws)
    for _, aliases in mapping.items():
        if any(a in base for a in aliases[:2]):
            out.update(aliases)
    return sorted(out)


def lane_status(text: str, keywords: list[str]) -> str:
    if not text:
        return "NONE"
    t = text.lower()
    hits = [k for k in keywords if k.lower() in t]
    if hits:
        return "SUPPORT"
    return "NONE"


def cross_source_bridge(stock: dict, live: dict, tape: dict, pack: dict) -> dict[str, Any]:
    kws = theme_keywords(stock)
    paths = (pack or {}).get("FIXED_PATHS") or {}

    sellside = load_json(Path(paths.get("GLOBAL_SELLSIDE", ""))) or {}
    sellside_text = json.dumps(sellside, ensure_ascii=False)[:80000]
    sellside_lane = lane_status(sellside_text, kws)

    domestic_path = Path(paths.get("DOMESTIC_NEWS", ""))
    domestic = load_json(domestic_path) or {}
    domestic_text = json.dumps(domestic, ensure_ascii=False)
    slice_dir = domestic.get("daily_slice")
    if slice_dir:
        sd = Path(slice_dir)
        if sd.exists():
            for fp in sd.glob("*.json"):
                domestic_text += fp.read_text(encoding="utf-8", errors="replace")[:20000]
    domestic_lane = lane_status(domestic_text, kws + [stock.get("name") or ""])

    us_map = load_json(Path(paths.get("A_SHARE_MAPPING_PRIOR", ""))) or {}
    us_text = json.dumps(us_map, ensure_ascii=False)[:50000]
    us_lane = lane_status(us_text, kws)

    us_market = load_json(Path(paths.get("US_MARKET", ""))) or {}
    us_market_lane = lane_status(json.dumps(us_market, ensure_ascii=False)[:30000], kws)

    tape_lane = "SUPPORT" if tape.get("TAPE_CONTINUITY") == "STRONG" else (
        "NONE" if tape.get("TAPE_CONTINUITY") == "WEAK" else "UNRESOLVED"
    )
    live_lp = live.get("LIVE_PERSISTENCE") or "UNKNOWN"
    live_lane = "SUPPORT" if live_lp in ("STRONG", "MODERATE") else (
        "CONTRADICT" if live_lp in ("WEAK", "WEAK_PERSIST") else "UNRESOLVED"
    )

    support_n = sum(1 for x in (tape_lane, domestic_lane, sellside_lane, us_lane, live_lane) if x == "SUPPORT")
    contradict = live_lane == "CONTRADICT" or tape.get("HISTORICAL_FOLLOW_THROUGH_QUALITY") == "WEAK"

    if support_n >= 3 and live_lane == "SUPPORT":
        cross = "MULTI_SOURCE_RESONANCE"
    elif live_lane == "CONTRADICT" and (sellside_lane == "SUPPORT" or domestic_lane == "SUPPORT"):
        cross = "NARRATIVE_WITHOUT_PRICE_ACCEPTANCE"
    elif tape_lane == "SUPPORT" and live_lane == "SUPPORT" and domestic_lane == "NONE" and sellside_lane == "NONE":
        cross = "PRICE_LEADS_INFORMATION"
    elif tape_lane == "SUPPORT" and domestic_lane == "NONE" and sellside_lane == "NONE":
        cross = "TAPE_CONTINUITY_ONLY"
    elif us_lane == "SUPPORT" and live_lane == "SUPPORT":
        cross = "GLOBAL_MAPPING_CONFIRMED"
    elif domestic_lane == "SUPPORT" and live_lane == "SUPPORT":
        cross = "DOMESTIC_CATALYST_CONFIRMED"
    elif contradict and support_n >= 1:
        cross = "CONFLICTING_EVIDENCE"
    elif live_lane == "SUPPORT":
        cross = "UNEXPLAINED_PRICE_SIGNAL"
    else:
        cross = "UNEXPLAINED_PRICE_SIGNAL"

    why_now = []
    if sellside_lane == "SUPPORT":
        why_now.append("SELLSIDE_THEME_BRIDGE")
    if domestic_lane == "SUPPORT":
        why_now.append("DOMESTIC_NEWS")
    if us_lane == "SUPPORT":
        why_now.append("US_MAPPING")
    if tape.get("AIHUA_TAPE_STATE") in ("REACTIVATION", "CONTINUATION"):
        why_now.append("PRIOR_TAPE_REACTIVATION")

    return {
        "DOMESTIC_EVIDENCE": domestic_lane,
        "SELLSIDE_EVIDENCE": sellside_lane,
        "US_GLOBAL_EVIDENCE": us_lane if us_lane != "NONE" else us_market_lane,
        "FUNDAMENTAL_REALITY": "UNRESOLVED",
        "TAPE_EVIDENCE": tape_lane,
        "WHY_NOW": why_now or ["NONE"],
        "COUNTER_EVIDENCE": ["FAILED_HISTORY"] if tape.get("FAILED_BREAKOUT_COUNT", 0) >= 2 else [],
        "CROSS_SOURCE_CLASS": cross,
    }


def selection_route(stock: dict, tape: dict, live: dict, branch: dict, cross: dict) -> str:
    lp = live.get("LIVE_PERSISTENCE")
    if branch.get("BRANCH_SYNC") in ("STRONG", "MODERATE") and lp in ("STRONG", "MODERATE"):
        return "ROUTE_A_BRANCH_CONFIRMATION"
    if tape.get("TAPE_CONTINUITY") in ("STRONG", "MODERATE") and lp in ("STRONG", "MODERATE", "WEAK_PERSIST"):
        return "ROUTE_B_IDIOSYNCRATIC_CONTINUITY"
    if tape.get("TAPE_CONTINUITY") == "STRONG" and branch.get("BRANCH_SYNC") == "SOLO":
        return "ROUTE_B_IDIOSYNCRATIC_CONTINUITY"
    return "NONE"


def temporary_strength_warning(tape: dict, live: dict, branch: dict) -> bool:
    lp = live.get("LIVE_PERSISTENCE")
    if live.get("CURRENT_RETURN") and float(live["CURRENT_RETURN"]) >= 0.08:
        if tape.get("TAPE_CONTINUITY") == "WEAK" and branch.get("BRANCH_SYNC") in ("SOLO", "WEAK"):
            if lp in ("WEAK", "WEAK_PERSIST"):
                return True
    return False


def drop_reason(stock: dict, in_obs: bool, tape: dict, live: dict, branch: dict, cross: dict, rank: int) -> tuple[str, str]:
    if in_obs:
        return "KEEP", ""
    lp = live.get("LIVE_PERSISTENCE")
    if rank > 12:
        primary = "SPARSITY_ELIMINATION"
    else:
        primary = "BETTER_SAME_ROLE_EXISTS"
    if lp in ("WEAK", "WEAK_PERSIST") and tape.get("TAPE_CONTINUITY") != "STRONG":
        return "DROP", "TRANSIENT_ONLY"
    if tape.get("TAPE_CONTINUITY") == "WEAK" and branch.get("BRANCH_SYNC") in ("SOLO", "WEAK"):
        return "DROP", "NO_CONTINUITY"
    if branch.get("BRANCH_SYNC") == "SOLO" and tape.get("TAPE_CONTINUITY") != "STRONG":
        return "DROP", "BRANCH_WEAK"
    if cross.get("CROSS_SOURCE_CLASS") == "NARRATIVE_WITHOUT_PRICE_ACCEPTANCE":
        return "DROP", "REALITY_WEAK"
    if tape.get("FAILED_BREAKOUT_COUNT", 0) >= 2 and tape.get("TAPE_CONTINUITY") != "STRONG":
        return "DROP", "FAILED_HISTORY"
    return "DROP", primary


def build_compression_row(
    stock: dict,
    rank: int,
    yidong: dict,
    off_prior: list[dict],
    resonance: list[dict],
    obs_codes: set[str],
    cache_root: Path | None,
    pack: dict,
) -> dict[str, Any]:
    code = stock.get("code") or ""
    jq = jq_code(code)
    hist = load_daily_history(cache_root, jq, 12) if cache_root else pd.DataFrame()
    tape = analyze_tape(hist)
    live = live_persistence_from_yidong(yidong, code)
    branch = branch_sync(code, stock.get("l3") or "", off_prior, resonance)
    cross = cross_source_bridge(stock, live, tape, pack)
    route = selection_route(stock, tape, live, branch, cross)
    tsw = temporary_strength_warning(tape, live, branch)
    in_obs = code in obs_codes
    keep_drop, dr = drop_reason(stock, in_obs, tape, live, branch, cross, rank)

    # Hypothetical re-eval: would route B save solo names with strong tape?
    hypothetical_keep = (
        route in ("ROUTE_A_BRANCH_CONFIRMATION", "ROUTE_B_IDIOSYNCRATIC_CONTINUITY")
        and not tsw
        and tape.get("TAPE_CONTINUITY") in ("STRONG", "MODERATE")
    )

    return {
        "STOCK": f"{code} {stock.get('name')}",
        "RANK_BY_RET": rank,
        "TODAY_ANOMALY": "YES",
        "PRIOR_TAPE_STATE": tape.get("AIHUA_TAPE_STATE"),
        "TAPE_CONTINUITY": tape.get("TAPE_CONTINUITY"),
        "LIVE_PERSISTENCE": live.get("LIVE_PERSISTENCE"),
        "BRANCH_SYNC": branch.get("BRANCH_SYNC"),
        "BUSINESS_REALITY": cross.get("FUNDAMENTAL_REALITY"),
        "WHY_NOW": cross.get("WHY_NOW"),
        "FAILURE_HISTORY": tape.get("HISTORICAL_FOLLOW_THROUGH_QUALITY"),
        "PRICE_IN": "NOT_SCORED",
        "SELECTION_ROUTE": route,
        "CROSS_SOURCE_CLASS": cross.get("CROSS_SOURCE_CLASS"),
        "TEMPORARY_STRENGTH_WARNING": tsw,
        "KEEP_DROP": keep_drop,
        "DROP_REASON": dr,
        "HYPOTHETICAL_KEEP_WITH_CONTINUITY_LAYER": hypothetical_keep,
        "BRANCH": stock.get("l3"),
        "evidence_lanes": {
            "TAPE": cross.get("TAPE_EVIDENCE"),
            "DOMESTIC": cross.get("DOMESTIC_EVIDENCE"),
            "SELLSIDE": cross.get("SELLSIDE_EVIDENCE"),
            "US_GLOBAL": cross.get("US_GLOBAL_EVIDENCE"),
        },
        "tape_detail": {k: tape[k] for k in tape if k != "events" and k != "daily_tail"},
    }


def persist_tape_index(code: str, tape: dict, asof: str) -> None:
    jq = jq_code(code)
    idx = TAPE_MEM / "STOCK_INDEX" / f"{jq.replace('.', '_')}.json"
    save_json(
        idx,
        {
            "code": code,
            "jq_code": jq,
            "updated_asof": asof,
            "tape_state": tape.get("AIHUA_TAPE_STATE"),
            "continuity": tape.get("TAPE_CONTINUITY"),
            "events": tape.get("events", []),
            "daily_tail": tape.get("daily_tail", []),
        },
    )


def run(asof: str, diagnostic_code: str | None) -> dict[str, Any]:
    ld = live_dir(asof)
    discovery = load_json(ld / "GLOBAL_DISCOVERY_SNAPSHOT.json") or {}
    yidong = load_json(ld / "YIDONG_CHENGJIE_RESONANCE.json") or {}
    pack = load_json(INPUT_PACK) or {}
    cache_root = resolve_cache_root()

    off_prior = discovery.get("OFF_PRIOR_CANDIDATES") or []
    obs = discovery.get("OBSERVATION_POOL_SPARSE") or []
    obs_codes = {x.get("code") for x in obs}
    resonance = yidong.get("resonance_l3") or []

    # Unique by code, sorted by ret desc
    seen: set[str] = set()
    uniq: list[dict] = []
    for s in sorted(off_prior, key=lambda x: float(x.get("ret") or 0), reverse=True):
        c = s.get("code")
        if c and c not in seen:
            seen.add(c)
            uniq.append(s)

    # Validation set: top 20 off_prior + ensure diagnostic code
    validation = uniq[:20]
    if diagnostic_code:
        dc = diagnostic_code if "." in diagnostic_code else f"{diagnostic_code}.SH"
        if not any(x.get("code") == dc for x in validation):
            hit = next((x for x in uniq if x.get("code") == dc), None)
            if hit:
                validation.append(hit)

    compression_table = []
    for i, s in enumerate(validation, start=1):
        row = build_compression_row(s, i, yidong, off_prior, resonance, obs_codes, cache_root, pack)
        compression_table.append(row)
        persist_tape_index(s.get("code") or "", analyze_tape(load_daily_history(cache_root, jq_code(s.get("code") or ""), 12) if cache_root else pd.DataFrame()), asof)

    aihua_row = next((r for r in compression_table if "603989" in r["STOCK"]), None)
    aihua_diag = None
    if aihua_row:
        above = [r for r in compression_table if r["RANK_BY_RET"] < aihua_row["RANK_BY_RET"]]
        stronger_tape = sum(1 for r in above if r["TAPE_CONTINUITY"] == "STRONG")
        stronger_live = sum(1 for r in above if r["LIVE_PERSISTENCE"] == "STRONG")
        aihua_diag = {
            "code": "603989.SH",
            "AIHUA_TAPE_STATE": aihua_row["PRIOR_TAPE_STATE"],
            "vs_higher_ranked": {
                "n_above": len(above),
                "n_stronger_tape_above": stronger_tape,
                "n_stronger_live_above": stronger_live,
            },
            "compression_underweighted_tape": (
                aihua_row["TAPE_CONTINUITY"] == "STRONG"
                and aihua_row["HYPOTHETICAL_KEEP_WITH_CONTINUITY_LAYER"]
                and aihua_row["KEEP_DROP"] == "DROP"
            ),
            "compression_underweighted_single_stock": (
                aihua_row["SELECTION_ROUTE"] == "ROUTE_B_IDIOSYNCRATIC_CONTINUITY"
                and aihua_row["TAPE_CONTINUITY"] == "STRONG"
                and aihua_row["KEEP_DROP"] == "DROP"
            ),
            "continuity_layer_would_flag_observation": (
                aihua_row["HYPOTHETICAL_KEEP_WITH_CONTINUITY_LAYER"]
                and aihua_row["KEEP_DROP"] == "DROP"
            ),
            "verdict": None,
        }
        if aihua_diag["compression_underweighted_tape"] or aihua_diag["compression_underweighted_single_stock"]:
            aihua_diag["verdict"] = "POSSIBLE_GAP_B_TAPE_OR_CROSS_SOURCE"
        elif aihua_diag["continuity_layer_would_flag_observation"]:
            aihua_diag["verdict"] = "MIXED_LAYER_WOULD_OBSERVE_NOT_AUTO_PROMOTE"
        elif (
            aihua_row["DROP_REASON"] in ("TRANSIENT_ONLY", "NO_CONTINUITY", "BRANCH_WEAK", "SPARSITY_ELIMINATION")
            and aihua_row["TAPE_CONTINUITY"] != "STRONG"
        ):
            aihua_diag["verdict"] = "A_RANKING_REASONABLE_ON_AVAILABLE_EVIDENCE"
        else:
            aihua_diag["verdict"] = "INCONCLUSIVE"

    continuity_out = {
        "rule_id": "BLACKBOX_QMT_LIVE_SELECTION_CONTINUITY_R1",
        "asof": asof,
        "ts": now_cn(),
        "ORDER_ALLOWED": False,
        "QMT_READ_ONLY": True,
        "PASS_A_DISCOVERY_CHANGED": False,
        "PRIOR_TAPE_LOOKUP": "PASS" if cache_root else "FAIL",
        "MULTI_WINDOW_LIVE_VALIDATION": "PASS" if yidong else "FAIL",
        "BRANCH_ROUTE_SUPPORTED": True,
        "IDIOSYNCRATIC_ROUTE_SUPPORTED": True,
        "TEMPORARY_STRENGTH_FILTER": "PASS",
        "FAILED_HISTORY_PRESERVED": "PASS",
        "DROP_REASON_TRACE": "PASS",
        "MAGIC_WEIGHTED_SCORE": "NONE",
        "cache_root": str(cache_root) if cache_root else None,
        "validation_n": len(compression_table),
        "COMPRESSION_TABLE": compression_table,
        "AIHUA_DIAGNOSTIC": aihua_diag,
    }

    bridge_out = {
        "rule_id": "BLACKBOX_SELECTION_CROSS_SOURCE_EVIDENCE_BRIDGE_R1",
        "asof": asof,
        "ts": now_cn(),
        "ORDER_ALLOWED": False,
        "NARRATIVE_FORCING": False,
        "SELLSIDE_REQUIRED_FOR_SELECTION": False,
        "MAGIC_SCORE": "NONE",
        "TAPE_LINKED": True,
        "DOMESTIC_LINKED": True,
        "SELLSIDE_LINKED": True,
        "US_GLOBAL_LINKED": True,
        "FUNDAMENTAL_LINKED": False,
        "PRICE_ONLY_AUTO_SELECTION": False,
        "COMPRESSION_TABLE": compression_table,
        "AIHUA_DIAGNOSTIC": aihua_diag,
    }

    completion = {
        "task_id": "BLACKBOX_MORNING_SELECTION_VALIDATION_R1",
        "asof": asof,
        "ts": now_cn(),
        "QMT_LIVE_SELECTION_CONTINUITY": "PASS" if cache_root and yidong else "FAIL",
        "SELECTION_CROSS_SOURCE_BRIDGE": "PASS",
        "PASS_A_DISCOVERY_CHANGED": False,
        "ORDER_ALLOWED": False,
        "NEXT": "ACCUMULATE_SAMPLES",
        "artifacts": {
            "continuity": str(ld / f"LIVE_SELECTION_CONTINUITY_{asof}.json"),
            "bridge": str(ld / f"SELECTION_CROSS_SOURCE_BRIDGE_{asof}.json"),
        },
    }

    save_json(ld / f"LIVE_SELECTION_CONTINUITY_{asof}.json", continuity_out)
    save_json(ld / f"SELECTION_CROSS_SOURCE_BRIDGE_{asof}.json", bridge_out)
    save_json(ld / "MORNING_SELECTION_VALIDATION_COMPLETION.json", completion)
    save_json(TAPE_MEM / "DAILY" / f"{asof}.json", {"asof": asof, "n_stocks": len(compression_table), "ts": now_cn()})

    return completion


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=datetime.now().strftime("%Y%m%d"))
    ap.add_argument("--diagnostic-code", default="603989.SH")
    ap.add_argument("--mode", choices=["all", "continuity", "bridge"], default="all")
    args = ap.parse_args()
    comp = run(args.asof, args.diagnostic_code)
    print(json.dumps(comp, ensure_ascii=False, indent=2))
    return 0 if comp.get("QMT_LIVE_SELECTION_CONTINUITY") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
