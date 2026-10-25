# -*- coding: utf-8 -*-
"""Intraday news observer R1 — titles+dates into strategy LIVE folder; market link.

Does NOT: order, touch Blind/Policy, write JQ products.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CN = ZoneInfo("Asia/Shanghai")
ROOT = Path(
    r"E:\BLACKBOX\任务\STRATEGY_RESEARCH_PRO_TRADER_TAO_DECISION_POLICY_AND_DATA_SYSTEM_RECONSTRUCTION_R1"
    r"\LIVE\INTRADAY_NEWS_OBS_R1"
)
CORE_SNAP = Path(
    r"E:\BLACKBOX\任务\STRATEGY_RESEARCH_PRO_TRADER_TAO_DECISION_POLICY_AND_DATA_SYSTEM_RECONSTRUCTION_R1"
    r"\LIVE\20260827_QMT_CORE_THEME_OBS_R1\CURRENT_SNAP.json"
)
SELLSIDE_DIR = Path(r"E:\BLACKBOX\数据\研究报告\日增量")


def theme_from_title(title: str) -> str:
    t = title.lower()
    rules = [
        (("光模块", "cpo", "optical", "中际", "新易盛", "天孚", "磷化铟", "inp"), "CPO_OPTICAL"),
        (("hbm", "dram", "内存", "存储", "澜起"), "MEMORY_HBM"),
        (("半导体", "芯片", "中芯", "华创", "设备", "smic"), "SEMI"),
        (("电力", "电网", "数据中心", "power", "ups", "电力缺口", "gw"), "AI_POWER"),
        (("pcb", "沪电", "生益", "深南"), "PCB"),
        (("铜", "有色", "黄金", "紫金"), "METALS"),
        (("nvidia", "英伟达", "h200"), "NVDA_AI_GLOBAL"),
        (("券商", "金融科技", "东财"), "FINTECH"),
    ]
    for keys, theme in rules:
        if any(k in t for k in keys):
            return theme
    return "OTHER"


def prior_guess(theme: str, source_layer: str) -> str:
    """Initial continuity prior BEFORE market confirmation — not final class."""
    if source_layer == "SELLSIDE_PRIOR" and theme in ("CPO_OPTICAL", "SEMI", "AI_POWER", "MEMORY_HBM", "PCB"):
        return "STRUCTURAL_PRIOR_CANDIDATE"
    if theme in ("METALS",) and "有色" in theme:
        return "MECHANISM_ONLY_CANDIDATE"
    if source_layer == "CN_REALTIME" and theme in ("CPO_OPTICAL", "SEMI"):
        return "MIXED_PENDING_MARKET"
    return "UNCLASSIFIED_PENDING"


def load_sellside(asof: str) -> list[dict]:
    p = SELLSIDE_DIR / asof / "NEW_CANDIDATES.csv"
    if not p.is_file():
        # try previous day
        for d in sorted(SELLSIDE_DIR.glob("2026-*"), reverse=True):
            cand = d / "NEW_CANDIDATES.csv"
            if cand.is_file():
                p = cand
                break
        else:
            return []
    rows = []
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        title = (r.get("title") or "").strip()
        if not title:
            continue
        rd = (r.get("possible_report_date") or asof)[:10]
        inst = r.get("institution") or ""
        rows.append(
            {
                "asof": asof,
                "headline_date": rd,
                "title": title[:200],
                "source_region": "GLOBAL_SELLSIDE",
                "source_layer": "SELLSIDE_PRIOR",
                "source_url": (r.get("source_url") or "")[:240],
                "institution": inst,
                "theme_guess": theme_from_title(title + " " + (r.get("possible_theme") or "")),
            }
        )
    return rows


def seed_manual_headlines(asof: str) -> list[dict]:
    """Seed from today's collected public titles (web search / known wires). Not Tao text."""
    seeds = [
        {
            "headline_date": "2026-08-25",
            "title": "光模块三巨头中报：AI算力业绩兑现，高景气向2027年延伸（中际/新易盛/天孚）",
            "source_region": "CN",
            "source_layer": "CN_REALTIME",
            "source_url": "https://finance.sina.com.cn/money/fund/etf/2026-08-25/doc-inipprns2318329.shtml",
        },
        {
            "headline_date": "2026-08-22",
            "title": "HK: Nvidia H200 chips stuck in Hong Kong warehouses — data center power capacity bottleneck",
            "source_region": "HK",
            "source_layer": "HK_FACT",
            "source_url": "https://wangreport.com/ai-focus-column/2026-08-22-aya-nakamura.html",
        },
        {
            "headline_date": "2026-08-26",
            "title": "MS: DRAM supply shortage may persist to 2028; hyperscaler+NVDA/AVGO infra commitments",
            "source_region": "GLOBAL_SELLSIDE",
            "source_layer": "SELLSIDE_PRIOR",
            "source_url": "https://news.10jqka.com.cn/20260826/c679300942.shtml",
        },
        {
            "headline_date": "2026-08-25",
            "title": "GS: China advanced chip supply +46% CAGR through 2035; SMIC yield fragile (Caixin cite)",
            "source_region": "GLOBAL_SELLSIDE",
            "source_layer": "SELLSIDE_PRIOR",
            "source_url": "https://www.caixinglobal.com/2026-08-25/chinas-advanced-chip-supply-to-surge-46-annually-through-2035-goldman-says-102477668.html",
        },
        {
            "headline_date": "2026-08-19",
            "title": "GS SUSTAIN: AI Data Centers Power Demand Cyclical Progression",
            "source_region": "GLOBAL_SELLSIDE",
            "source_layer": "SELLSIDE_PRIOR",
            "source_url": "https://www.goldmansachs.com/insights/goldman-sachs-research/gs-sustain-ai-data-centers-power-demand-cyclical-progresison-and-sustainability-implications",
        },
        {
            "headline_date": "2026-08-16",
            "title": "Goldman moves China AI trade onshore to A-share hardware (power/PCB/optical)",
            "source_region": "GLOBAL_SELLSIDE",
            "source_layer": "SELLSIDE_PRIOR",
            "source_url": "https://theclarity.today/story/goldman-sachs-identifies-china-stocks-set-to-benefit-from-ai-hardware-exports-509f284d",
        },
        {
            "headline_date": asof,
            "title": "【盘中观察占位】上海半导体/医药政策盘面确认待核 — 仅作假设标签",
            "source_region": "CN",
            "source_layer": "CN_REALTIME",
            "source_url": "",
        },
        {
            "headline_date": asof,
            "title": "【盘中观察占位】英伟达财报相关情绪与A股CPO映射待盘面确认",
            "source_region": "HK",
            "source_layer": "HK_FACT",
            "source_url": "",
        },
    ]
    out = []
    for s in seeds:
        theme = theme_from_title(s["title"])
        out.append(
            {
                "asof": asof,
                "headline_date": s["headline_date"],
                "title": s["title"][:200],
                "source_region": s["source_region"],
                "source_layer": s["source_layer"],
                "source_url": s.get("source_url", ""),
                "institution": "",
                "theme_guess": theme,
            }
        )
    return out


def load_core_snap() -> dict:
    if not CORE_SNAP.is_file():
        return {}
    return json.loads(CORE_SNAP.read_text(encoding="utf-8"))


THEME_TO_CORE = {
    "CPO_OPTICAL": "CPO_CORE",
    "PCB": "CPO_POSITION_PROBE",
    "SEMI": "SEMI_CORE",
    "AI_POWER": "AI_POWER_GRID",
    "MEMORY_HBM": "MEMORY_HBM",
    "METALS": "METALS_CU_OBS",
    "NVDA_AI_GLOBAL": "CPO_CORE",
}


def market_class(theme: str, snap: dict) -> tuple[str, str]:
    """Map theme → core sync → STRUCTURAL vs EMOTIONAL vs PENDING."""
    key = THEME_TO_CORE.get(theme)
    if not snap or not key or key not in snap.get("themes", {}):
        return "UNCLASSIFIED_PENDING", "no_core_snap"
    th = snap["themes"][key]
    sync = th.get("core_sync", "n/a")
    dump = th.get("gap_fade_dump") or []
    strong = th.get("strengthening_or_hold") or []
    # parse sync like 3/3
    try:
        a, b = sync.split("/")
        a, b = int(a), int(b)
        ratio = a / b if b else 0
    except Exception:
        ratio = 0
    note = f"core={key};sync={sync};strong_n={len(strong)};dump_n={len(dump)}"
    if ratio >= 0.67 and len(strong) >= 2:
        return "STRUCTURAL_CONTINUITY_INTRADAY", note
    if dump and ratio < 0.34:
        return "EMOTIONAL_ARBITRAGE_OR_FADE", note
    if ratio == 0 and not strong:
        return "HYPOTHESIS_NOT_CONFIRMED_YET", note
    return "MIXED_PENDING", note


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=datetime.now(CN).strftime("%Y-%m-%d"))
    args = ap.parse_args()
    asof = args.asof
    day = ROOT / "日增量" / asof
    day.mkdir(parents=True, exist_ok=True)

    # dedupe headlines by title
    seen = set()
    headlines = []
    for r in seed_manual_headlines(asof) + load_sellside(asof):
        key = r["title"][:80]
        if key in seen:
            continue
        seen.add(key)
        r["continuity_prior"] = prior_guess(r["theme_guess"], r["source_layer"])
        headlines.append(r)

    snap = load_core_snap()
    links = []
    for i, h in enumerate(headlines, 1):
        cls, note = market_class(h["theme_guess"], snap)
        # metals hard boundary
        if h["theme_guess"] == "METALS":
            cls = "MECHANISM_ONLY_OBS"
        links.append(
            {
                "id": f"{asof}_{i:03d}",
                "headline_date": h["headline_date"],
                "title": h["title"],
                "theme_guess": h["theme_guess"],
                "source_layer": h["source_layer"],
                "source_region": h["source_region"],
                "continuity_prior": h["continuity_prior"],
                "market_class_now": cls,
                "market_note": note,
                "source_url": h.get("source_url", ""),
            }
        )

    # write HEADLINES
    hcols = ["asof", "headline_date", "title", "source_region", "source_layer", "theme_guess", "continuity_prior", "source_url", "institution"]
    with open(day / "HEADLINES.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hcols, extrasaction="ignore")
        w.writeheader()
        for h in headlines:
            w.writerow(h)

    lcols = list(links[0].keys()) if links else []
    with open(day / "MARKET_LINK.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=lcols)
        w.writeheader()
        w.writerows(links)

    # board
    by_cls = {}
    for L in links:
        by_cls.setdefault(L["market_class_now"], []).append(L)

    md = [
        f"# 盘中新闻观察 {asof}",
        "",
        f"- built_at_cn: {datetime.now(CN).isoformat()}",
        f"- headlines: {len(headlines)}",
        f"- core_snap_linked: {bool(snap)}",
        "- Blind/Policy: untouched | ORDER: NO",
        "",
        "## 分类计数（对照盘面 Core Sync）",
        "",
    ]
    for k, v in sorted(by_cls.items(), key=lambda x: -len(x[1])):
        md.append(f"- **{k}**: {len(v)}")
    md.append("")
    md.append("## 明细（标题 | 日期 | 主题 | 盘面类）")
    md.append("")
    for L in links:
        md.append(f"- [{L['headline_date']}] {L['title'][:100]}")
        md.append(f"  - theme={L['theme_guess']} | prior={L['continuity_prior']} | **now={L['market_class_now']}**")
        md.append(f"  - {L['market_note']}")
    md.append("")
    md.append("## 用法")
    md.append("")
    md.append("- `STRUCTURAL_CONTINUITY_INTRADAY`：Prior + 核心共振 → 大方向延续候选")
    md.append("- `EMOTIONAL_ARBITRAGE_OR_FADE`：冲高回落/核心不同步 → 情绪套利嫌疑")
    md.append("- `HYPOTHESIS_NOT_CONFIRMED_YET`：新闻在，盘面核心未确认（如 Semi/电力早盘）")
    md.append("- 收盘后再跑一次本脚本，可刷新 `market_class_now`")
    (day / "DAILY_BOARD.md").write_text("\n".join(md), encoding="utf-8")

    status = {
        "asof": asof,
        "n_headlines": len(headlines),
        "n_linked": len(links),
        "class_counts": {k: len(v) for k, v in by_cls.items()},
        "core_snap": str(CORE_SNAP) if snap else None,
        "ORDER_ALLOWED": False,
        "TOUCH_BLIND": False,
        "built_at_cn": datetime.now(CN).isoformat(),
    }
    (day / "STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "CURRENT.json").write_text(json.dumps({"asof": asof, "day_dir": str(day), **status}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    main()
