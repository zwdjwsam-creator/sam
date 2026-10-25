#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Laotao premarket observation = EXTERNAL_HUMAN_PRIOR validation (ROUTE C).

HOLDING_STATUS_WEIGHT=0. Cannot override GLOBAL_RESEARCH / FULL_MARKET / L4 breadth.
ORDER_ALLOWED=FALSE.
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(r"E:\BLACKBOX")
LIVE = ROOT / "研究系统" / "CURRENT" / "LIVE"
PRIOR_PATH = LIVE / "LAOTAO_PRIOR_CURRENT.json"
HUMAN_CALIB = (
    ROOT / "DAILY_RESEARCH" / "EVALUATION" / "EXTERNAL_HUMAN_PRIOR_CALIBRATION_LEDGER" / "LEDGER.jsonl"
)

# Permanent rules (also mirrored into TOP_RULES)
LAOTAO_RULES = {
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
    "FULL_MARKET_SCAN_MUST_BE_BLIND_TO_LAOTAO_PRIOR": True,
    "TRIPLE_SOURCE_RESONANCE_MUST_BE_LOGGED": True,
}


def write_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def load_json(p: Path) -> dict[str, Any]:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _normalize_sw_map(sw_map: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Adapt tip map schema: mapped[] + distinct_l3_pools (or legacy by_code/l3_pools)."""
    sw_map = sw_map or {}
    by_code: dict[str, Any] = {}
    raw_by = sw_map.get("by_code")
    if isinstance(raw_by, dict) and raw_by:
        by_code = dict(raw_by)
    else:
        for row in sw_map.get("mapped") or []:
            if not isinstance(row, dict):
                continue
            code = row.get("code")
            if code:
                by_code[str(code)] = row
    pools = sw_map.get("distinct_l3_pools") or sw_map.get("l3_pools") or {}
    if not isinstance(pools, dict):
        pools = {}
    return by_code, pools


def build_laotao_0901_prior(sw_map: dict[str, Any] | None = None) -> dict[str, Any]:
    """Structured prior for 2026-09-01. Identity from SW tip when available."""
    sw_map = sw_map or load_json(LIVE / "_laotao_sw_l3_map.json")
    by_code, l3_pools = _normalize_sw_map(sw_map if isinstance(sw_map, dict) else {})

    def id_of(code: str, name: str, source_theme: str) -> dict[str, Any]:
        row = by_code.get(code) or {}
        canon_l3 = row.get("l3_name") or row.get("l3")
        return {
            "code": code,
            "name": name,
            "SOURCE_MENTION_THEME": source_theme,
            "CANONICAL_L3": canon_l3,
            "CANONICAL_L3_CODE": row.get("l3_code"),
            "CANONICAL_L4": row.get("l4"),  # usually None until FG exists
            "THEME_MATCH_QUALITY": _match_quality(source_theme, canon_l3),
            "RESOLUTION": "L4" if row.get("l4") else ("L3_FALLBACK" if canon_l3 else "UNMAPPED"),
            "FINE_GRAINED_GAP": not bool(row.get("l4")),
        }

    def pool_members_for_l3(l3_name: str | None, anchors: list[str]) -> list[str]:
        if not l3_name:
            return list(anchors)
        mem = l3_pools.get(l3_name) or {}
        if not isinstance(mem, dict):
            mem = {}
        codes = (
            mem.get("members")
            or mem.get("codes")
            or mem.get("all_codes")
            or mem.get("members_sample_first_15")
        )
        if isinstance(codes, list) and codes:
            return list(codes)
        # fallback: all mapped codes with same l3
        out = []
        for c, r in by_code.items():
            if (r.get("l3_name") or r.get("l3")) == l3_name:
                out.append(c)
        return sorted(set(out)) or list(anchors)

    # --- C1 AI application (must subdivide; 浪潮信息 ≠ AI_APPLICATION) ---
    ai_anchors = [
        id_of("002230.SZ", "科大讯飞", "AI_APPLICATION"),
        id_of("300229.SZ", "拓尔思", "AI_APPLICATION"),
        id_of("300418.SZ", "昆仑万维", "AI_APPLICATION"),
        id_of("300413.SZ", "芒果超媒", "AI_CONTENT_AIGC"),
        id_of("300364.SZ", "中文在线", "AI_CONTENT_AIGC"),
        id_of("000977.SZ", "浪潮信息", "AI_APPLICATION"),  # source said app group; identity may be hardware
    ]
    # Split validation sublines by canonical L3 (not one big AI_APPLICATION basket)
    ai_by_l3: dict[str, list[str]] = {}
    for a in ai_anchors:
        key = a.get("CANONICAL_L3") or "UNMAPPED"
        ai_by_l3.setdefault(key, []).append(a["code"])

    themes = []
    themes.append({
        "LAOTAO_THEME_ID": "C1_AI_APPLICATION_DIFFUSION",
        "POLICY_META": False,
        "SOURCE_PRIOR": "AI应用能否从AI硬件继续向下游扩散；工信部AI应用服务商资源池/大模型/智能体/Token/AIGC",
        "SOURCE_MENTION_THEME": "AI_APPLICATION",
        "SUBDIVISION_REQUIRED": True,
        "FORBIDDEN_BASKET": "AI_APPLICATION_AS_SINGLE_POOL",
        "ANCHORS": ai_anchors,
        "VALIDATION_SUBPOOLS": [
            {
                "SUBTHEME": k,
                "RESOLUTION": "L3_FALLBACK",
                "FINE_GRAINED_GAP": True,
                "SOURCE_ANCHOR_STOCKS": v,
                "CANONICAL_MEMBERS": pool_members_for_l3(k if k != "UNMAPPED" else None, v),
            }
            for k, v in ai_by_l3.items()
        ],
        "EVENT_PRIORS": ["工信部AI应用服务商资源池", "大模型", "智能体", "Token服务采购", "AIGC内容生产"],
    })

    # --- C2 CPO / optical ---
    cpo_core = [
        id_of("300308.SZ", "中际旭创", "OPTICAL_MODULE"),
        id_of("300502.SZ", "新易盛", "OPTICAL_MODULE"),
        id_of("300394.SZ", "天孚通信", "OPTICAL_DEVICE"),
    ]
    cpo_adj = [
        id_of("300570.SZ", "太辰光", "OPTICAL_DEVICE"),
        id_of("688143.SH", "长盈通", "OPTICAL_FIBER_COMPONENT"),
        id_of("600498.SH", "烽火通信", "TELECOM_EQUIPMENT"),
    ]
    # Group optical by L3 for pool acceptance (中际旭创 alone ≠ CPO theme)
    optical_codes = [x["code"] for x in cpo_core + cpo_adj]
    # Prefer members of 中际旭创's L3 as primary optical module pool
    primary_l3 = (cpo_core[0].get("CANONICAL_L3") if cpo_core else None)
    themes.append({
        "LAOTAO_THEME_ID": "C2_CPO_OPTICAL",
        "SOURCE_PRIOR": "中际旭创回购 → CPO/光模块能否带创业板和科技修复",
        "COMPANY_SPECIFIC_CATALYST": {"code": "300308.SZ", "name": "中际旭创", "event": "回购"},
        "ANCHORS": cpo_core + cpo_adj,
        "VALIDATION_SUBPOOLS": [
            {
                "SUBTHEME": "OPTICAL_CORE_POOL",
                "RESOLUTION": "L3_FALLBACK",
                "FINE_GRAINED_GAP": True,
                "NOTE": "Must confirm 旭创+新易盛+天孚 breadth; single 旭创 = BUYBACK_SINGLE_STOCK_EFFECT",
                "SOURCE_ANCHOR_STOCKS": [x["code"] for x in cpo_core],
                "CANONICAL_MEMBERS": pool_members_for_l3(primary_l3, [x["code"] for x in cpo_core]),
                "ACCEPTANCE_RULE": "OPTICAL_POOL_ACCEPTANCE_REQUIRES_MULTI_LEADER_BREADTH",
            },
            {
                "SUBTHEME": "CPO_ADJACENT_NOT_SAME_POOL",
                "RESOLUTION": "L3_FALLBACK",
                "FINE_GRAINED_GAP": True,
                "SOURCE_ANCHOR_STOCKS": [x["code"] for x in cpo_adj],
                "CANONICAL_MEMBERS": [x["code"] for x in cpo_adj],
                "NOTE": "太辰光/长盈通/烽火 — separate profit pools; not auto followers of 光模块",
            },
        ],
    })

    # --- C3 Six networks = POLICY_META_THEME only ---
    six_anchors = [
        id_of("600406.SH", "国电南瑞", "NEW_GRID"),
        id_of("000400.SZ", "许继电气", "NEW_GRID"),
        id_of("603019.SH", "中科曙光", "COMPUTE_NETWORK"),
    ]
    themes.append({
        "LAOTAO_THEME_ID": "C3_SIX_NETWORKS_POLICY_META",
        "POLICY_META_THEME": "SIX_NETWORKS",
        "FORBIDDEN": "SIX_NETWORKS_AS_SINGLE_BREADTH_POOL",
        "SOURCE_PRIOR": "水网/新型电网/算力网/新一代通信网/城市地下管网/物流网",
        "OBSERVATION_ANCHORS_ONLY": six_anchors,
        "VALIDATION_SUBPOOLS": [
            {
                "SUBTHEME": "NEW_GRID",
                "RESOLUTION": "L3_FALLBACK",
                "FINE_GRAINED_GAP": True,
                "SOURCE_ANCHOR_STOCKS": ["600406.SH", "000400.SZ"],
                "CANONICAL_MEMBERS": pool_members_for_l3(
                    six_anchors[0].get("CANONICAL_L3"), ["600406.SH", "000400.SZ"]
                ),
            },
            {
                "SUBTHEME": "COMPUTE_NETWORK",
                "RESOLUTION": "L3_FALLBACK",
                "FINE_GRAINED_GAP": True,
                "SOURCE_ANCHOR_STOCKS": ["603019.SH"],
                "CANONICAL_MEMBERS": pool_members_for_l3(
                    six_anchors[2].get("CANONICAL_L3") if len(six_anchors) > 2 else None,
                    ["603019.SH"],
                ),
            },
        ],
        "NOTE": "Anchors cannot define SIX_NETWORKS_ACCEPTED; validate each real L3/L4 separately",
    })

    # --- Precious metals defensive watch ---
    pm = [
        id_of("600547.SH", "山东黄金", "PRECIOUS_METAL"),
        id_of("601212.SH", "白银有色", "PRECIOUS_METAL"),
    ]
    themes.append({
        "LAOTAO_THEME_ID": "C4_PRECIOUS_METAL_DEFENSIVE_WATCH",
        "PRECIOUS_METAL_PRIOR": "DEFENSIVE_WATCH",
        "SOURCE_PRIOR": "美元/利率可能压制贵金属；非主研究方向",
        "NOT_PRIMARY_RESEARCH": True,
        "CROSS_CHECK_EXTERNAL": ["GOLD_PRICE", "GOLD_MINERS", "SILVER", "REAL_YIELD", "USD"],
        "DIVERGENCE_FLAG_IF": "CN_LOCAL_PRECIOUS_METAL_DIVERGENCE when CN strong & global weak",
        "ANCHORS": pm,
        "VALIDATION_SUBPOOLS": [
            {
                "SUBTHEME": "GOLD_MINERS_CN",
                "RESOLUTION": "L3_FALLBACK",
                "FINE_GRAINED_GAP": True,
                "SOURCE_ANCHOR_STOCKS": ["600547.SH"],
                "CANONICAL_MEMBERS": pool_members_for_l3(pm[0].get("CANONICAL_L3"), ["600547.SH"]),
            },
            {
                "SUBTHEME": "SILVER_RELATED_CN",
                "RESOLUTION": "L3_FALLBACK",
                "FINE_GRAINED_GAP": True,
                "SOURCE_ANCHOR_STOCKS": ["601212.SH"],
                "CANONICAL_MEMBERS": pool_members_for_l3(pm[1].get("CANONICAL_L3"), ["601212.SH"]),
            },
        ],
    })

    holdings = [
        {"code": "600547.SH", "name": "山东黄金"},
        {"code": "300570.SZ", "name": "太辰光"},
        {"code": "688143.SH", "name": "长盈通"},
        {"code": "300607.SZ", "name": "拓斯达"},
        {"code": "601212.SH", "name": "白银有色"},
        {"code": "600206.SH", "name": "有研新材"},
        {"code": "300677.SZ", "name": "英科医疗"},
        {"code": "300456.SZ", "name": "赛微电子"},
        {"code": "603989.SH", "name": "艾华集团"},
        {"code": "600498.SH", "name": "烽火通信"},
    ]
    for h in holdings:
        h.update({k: v for k, v in id_of(h["code"], h["name"], "HOLDING_ONLY").items() if k not in h})

    doc = {
        "TASK_ID": "LAOTAO_PREMARKET_OBSERVATION_VALIDATION_AND_RESONANCE_R1",
        "ASOF": "20260901",
        "LAOTAO_OBSERVATION": "EXTERNAL_HUMAN_PRIOR",
        "RULES": LAOTAO_RULES,
        "ORDER_ALLOWED": False,
        "RAW_SOURCE_NOTE": "2026-09-01 盘前观察结构化；原文另存 SOURCE_TEXT",
        "SOURCE_TEXT": {
            "C1": "AI应用能否从AI硬件继续向下游扩散",
            "C2": "中际旭创回购 → CPO/光模块能否带创业板和科技修复",
            "C3": "六张网：水网/新型电网/算力网/新一代通信网/城市地下管网/物流网",
            "C4": "贵金属防守观察；美元/利率压制可能",
            "HOLDINGS": [h["name"] for h in holdings],
        },
        "THEMES": themes,
        "LAOTAO_DISCLOSED_HOLDINGS": holdings,
        "HOLDING_STATUS_WEIGHT": 0,
        "CROSS_CHECKS_TODAY": [
            "ENERGY_VS_AI_APPLICATION",
            "ENERGY_VS_CPO",
            "ENERGY_VS_GRID/INFRA",
        ],
    }
    write_json(PRIOR_PATH, doc)
    return doc


def _match_quality(source_theme: str, canon_l3: str | None) -> str:
    if not canon_l3:
        return "UNMAPPED"
    s = (source_theme or "").upper()
    c = canon_l3 or ""
    # rough reconcile flags — keep difference if mismatch
    if s == "AI_APPLICATION" and any(k in c for k in ("计算机设备", "服务器", "IT设备", "其他电子")):
        return "MISMATCH_SOURCE_APP_VS_HARDWARE"
    if s in ("AI_CONTENT_AIGC", "AI_MEDIA") and ("文化" in c or "传媒" in c or "广告" in c):
        return "ALIGNED_PARTIAL"
    if "OPTICAL" in s or "CPO" in s:
        if any(k in c for k in ("通信", "光", "器件", "设备")):
            return "ALIGNED_PARTIAL"
    if s == "TELECOM_EQUIPMENT" and "通信" in c:
        return "ALIGNED"
    if s in ("NEW_GRID",) and any(k in c for k in ("电网", "电气", "自动化", "电源")):
        return "ALIGNED_PARTIAL"
    if s == "PRECIOUS_METAL" and any(k in c for k in ("黄金", "贵金属", "白银", "金属")):
        return "ALIGNED_PARTIAL"
    if s == "AI_APPLICATION" and any(k in c for k in ("软件", "IT服务", "计算机应用", "人工智能")):
        return "ALIGNED_PARTIAL"
    return "RECONCILE_REVIEW"


def validate_theme_pools(
    prior: dict[str, Any],
    ticks: dict[str, Any],
    tick_fields_fn,
    pool_metrics_fn,
    trade_day: str,
    phase: str,
    bars: dict[str, Any] | None = None,
    vwap_fn=None,
) -> dict[str, Any]:
    """Pool-level validation. Single named stock strength ≠ theme confirmed."""
    lines = []
    daily = {}
    for th in prior.get("THEMES") or []:
        tid = th.get("LAOTAO_THEME_ID")
        sub_results = []
        for sp in th.get("VALIDATION_SUBPOOLS") or []:
            members = list(sp.get("CANONICAL_MEMBERS") or sp.get("SOURCE_ANCHOR_STOCKS") or [])
            st = pool_metrics_fn(members, ticks, trade_day)
            anchors = sp.get("SOURCE_ANCHOR_STOCKS") or []
            anchor_rets = []
            for a in anchors:
                f = tick_fields_fn(ticks.get(a) if isinstance(ticks.get(a), dict) else None)
                r = f.get("auction_return") if f.get("auction_return") is not None else f.get("ret")
                if r is not None:
                    anchor_rets.append((a, r))
            n_strong_anchors = sum(1 for _, r in anchor_rets if r > 0.02)
            breadth = st.get("POSITIVE_RATIO")
            n_obs = st.get("OBSERVED_COUNT") or 0
            state = "INSUFFICIENT_DATA"
            if n_obs < 2:
                state = "INSUFFICIENT_DATA"
            elif n_obs == 1 or (breadth is not None and breadth < 0.35 and n_strong_anchors <= 1):
                if n_strong_anchors >= 1 and (breadth is None or breadth < 0.4):
                    state = "SINGLE_STOCK_ONLY"
                    if tid == "C2_CPO_OPTICAL" and any(a == "300308.SZ" for a, r in anchor_rets if r > 0.02):
                        state = "BUYBACK_SINGLE_STOCK_EFFECT" if n_strong_anchors == 1 else state
                else:
                    state = "NOT_CONFIRMED"
            elif breadth is not None and breadth >= 0.55 and (st.get("POOL_AUCTION_MEDIAN") or 0) > 0:
                if (st.get("FOLLOWER_POSITIVE_COUNT") or 0) >= 1:
                    state = "CONFIRMED"
                else:
                    state = "PARTIAL"
            elif breadth is not None and breadth >= 0.4:
                state = "PARTIAL"
            elif (st.get("POOL_AUCTION_MEDIAN") or 0) < -0.01:
                state = "REJECTED"
            else:
                state = "NOT_CONFIRMED"

            minute = {}
            if phase == "0931" and bars is not None and vwap_fn is not None:
                above = 0
                checked = 0
                for c in members:
                    b = bars.get(c) or []
                    vw = vwap_fn(b[:1] if b else [])
                    f = tick_fields_fn(ticks.get(c) if isinstance(ticks.get(c), dict) else None)
                    price = f.get("last")
                    vwap = vw.get("vwap")
                    if price is not None and vwap is not None:
                        checked += 1
                        if price > vwap:
                            above += 1
                minute = {
                    "POOL_ABOVE_VWAP_RATIO": (above / checked) if checked else None,
                    "NOTE": "EARLY_MINUTE_ACCEPTANCE_NOT_FULL_CONFIRMATION",
                }
                if state == "CONFIRMED" and minute.get("POOL_ABOVE_VWAP_RATIO") is not None:
                    if minute["POOL_ABOVE_VWAP_RATIO"] < 0.4:
                        state = "PARTIAL"

            sub_results.append({
                "SUBTHEME": sp.get("SUBTHEME"),
                "L3_L4": sp.get("SUBTHEME"),
                "RESOLUTION": sp.get("RESOLUTION"),
                "FINE_GRAINED_GAP": sp.get("FINE_GRAINED_GAP"),
                "SOURCE_PRIOR": th.get("SOURCE_PRIOR"),
                "ANCHOR_STOCKS": anchors,
                "AUCTION_POOL_RETURN": st.get("POOL_AUCTION_MEDIAN"),
                "AUCTION_BREADTH": breadth,
                "AUCTION_AMOUNT": st.get("POOL_AUCTION_AMOUNT_MEDIAN"),
                "LEADER": (st.get("LEADER") or {}).get("code"),
                "FOLLOWERS": [x.get("code") for x in (st.get("FOLLOWERS") or [])],
                "VALIDATION_STATE": state,
                "COVERAGE": {k: st.get(k) for k in (
                    "CANONICAL_COUNT", "OBSERVED_COUNT", "LIVE_COVERAGE_STATUS", "MISSING_CODES"
                )},
                "MINUTE": minute,
            })

        # theme-level aggregate: worst/best without using holdings
        states = [s["VALIDATION_STATE"] for s in sub_results]
        if not states:
            theme_state = "INSUFFICIENT_DATA"
        elif all(s == "CONFIRMED" for s in states):
            theme_state = "CONFIRMED"
        elif any(s in ("CONFIRMED", "PARTIAL") for s in states) and not all(
            s in ("REJECTED", "NOT_CONFIRMED", "INSUFFICIENT_DATA", "SINGLE_STOCK_ONLY", "BUYBACK_SINGLE_STOCK_EFFECT")
            for s in states
        ):
            theme_state = "PARTIAL"
        elif any(s in ("SINGLE_STOCK_ONLY", "BUYBACK_SINGLE_STOCK_EFFECT") for s in states) and not any(
            s in ("CONFIRMED", "PARTIAL") for s in states
        ):
            theme_state = "SINGLE_STOCK_ONLY"
        elif any(s == "REJECTED" for s in states) and not any(s in ("CONFIRMED", "PARTIAL") for s in states):
            theme_state = "REJECTED"
        else:
            theme_state = "NOT_CONFIRMED"

        daily[tid] = theme_state
        lines.append({
            "THEME": tid,
            "SOURCE_PRIOR": th.get("SOURCE_PRIOR"),
            "VALIDATION_STATE": theme_state,
            "SUBPOOLS": sub_results,
            "POLICY_META": th.get("POLICY_META_THEME") or th.get("POLICY_META"),
        })

    return {
        "PHASE": phase,
        "LAOTAO_DAILY_VALIDATION": daily,
        "LINES": lines,
        "HOLDING_STATUS_WEIGHT": 0,
        "ORDER_ALLOWED": False,
    }


def stock_laotao_fields(code: str, prior: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    themes_hit = []
    states = []
    for line in validation.get("LINES") or []:
        for sp in line.get("SUBPOOLS") or []:
            if code in (sp.get("ANCHOR_STOCKS") or []) or code == sp.get("LEADER"):
                themes_hit.append(line.get("THEME"))
                states.append(sp.get("VALIDATION_STATE"))
    holdings = {h["code"] for h in (prior.get("LAOTAO_DISCLOSED_HOLDINGS") or [])}
    return {
        "LAOTAO_PRIOR_MATCH": bool(themes_hit),
        "LAOTAO_THEME": themes_hit[0] if themes_hit else None,
        "LAOTAO_VALIDATION_STATE": states[0] if states else None,
        "LAOTAO_IS_DISCLOSED_HOLDING": code in holdings,
        "HOLDING_STATUS_WEIGHT": 0,
    }


def resonance_type(a: bool, b: bool, c: bool) -> str:
    if a and b and c:
        return "TRIPLE_SOURCE_RESONANCE"
    if a and b and not c:
        return "MODEL_MARKET_RESONANCE"
    if (not a) and b and c:
        return "HUMAN_MARKET_RESONANCE_OUTSIDE_RESEARCH"
    if (not a) and (not b) and c:
        return "HUMAN_PRIOR_ONLY"
    if a and (not b) and c:
        return "RESEARCH_HUMAN_WITHOUT_MARKET"
    if a and (not b) and (not c):
        return "RESEARCH_ONLY"
    if (not a) and b and (not c):
        return "MARKET_ONLY"
    return "NONE"


def energy_vs_laotao_cross(energy_primary: str | None, daily: dict[str, Any]) -> dict[str, Any]:
    ai = daily.get("C1_AI_APPLICATION_DIFFUSION")
    cpo = daily.get("C2_CPO_OPTICAL")
    grid = daily.get("C3_SIX_NETWORKS_POLICY_META")
    energy_ok = bool(energy_primary)
    tech_ok = any(x in ("CONFIRMED", "PARTIAL") for x in (ai, cpo, grid))
    tech_weak = all(x in ("NOT_CONFIRMED", "REJECTED", "SINGLE_STOCK_ONLY", "BUYBACK_SINGLE_STOCK_EFFECT", "INSUFFICIENT_DATA", None) for x in (ai, cpo, grid))
    if energy_ok and tech_weak:
        return {
            "CASE": "A",
            "BLACKBOX_GLOBAL_PRIOR_CONFIRMED": True,
            "LAOTAO_TECH_PRIOR_NOT_CONFIRMED": True,
            "ENERGY_VS_AI_APPLICATION": ai,
            "ENERGY_VS_CPO": cpo,
            "ENERGY_VS_GRID/INFRA": grid,
        }
    if (not energy_ok) and tech_ok:
        return {
            "CASE": "B",
            "CN_MARKET_REJECTS_GLOBAL_ENERGY_MAPPING": True,
            "LAOTAO_TECH_PRIOR_CONFIRMED": True,
            "GLOBAL_US_LEADERSHIP": "ENERGY",
            "CN_LOCAL_LEADERSHIP": "TECHNOLOGY",
            "ENERGY_VS_AI_APPLICATION": ai,
            "ENERGY_VS_CPO": cpo,
            "ENERGY_VS_GRID/INFRA": grid,
        }
    if energy_ok and tech_ok:
        return {
            "CASE": "C",
            "MULTI_THEME_MARKET": True,
            "ENERGY_VS_AI_APPLICATION": ai,
            "ENERGY_VS_CPO": cpo,
            "ENERGY_VS_GRID/INFRA": grid,
        }
    return {
        "CASE": "UNCLEAR",
        "ENERGY_VS_AI_APPLICATION": ai,
        "ENERGY_VS_CPO": cpo,
        "ENERGY_VS_GRID/INFRA": grid,
    }




def laotao_anchor_codes(prior: dict[str, Any] | None = None) -> list[str]:
    """Theme/observation anchors only; holdings have zero selection weight."""
    prior = prior or load_json(PRIOR_PATH) or build_laotao_0901_prior()
    out: set[str] = set()
    for th in prior.get("THEMES") or []:
        for key in ("ANCHORS", "OBSERVATION_ANCHORS_ONLY"):
            for a in th.get(key) or []:
                if isinstance(a, dict) and a.get("code"):
                    out.add(str(a["code"]))
                elif isinstance(a, str):
                    out.add(a)
        for sp in th.get("VALIDATION_SUBPOOLS") or []:
            for a in sp.get("SOURCE_ANCHOR_STOCKS") or []:
                out.add(str(a))
    return sorted(out)


def append_human_calib(row: dict[str, Any]) -> None:
    HUMAN_CALIB.parent.mkdir(parents=True, exist_ok=True)
    with HUMAN_CALIB.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


if __name__ == "__main__":
    doc = build_laotao_0901_prior()
    print(json.dumps({"ok": True, "themes": len(doc["THEMES"]), "path": str(PRIOR_PATH)}, ensure_ascii=False))
