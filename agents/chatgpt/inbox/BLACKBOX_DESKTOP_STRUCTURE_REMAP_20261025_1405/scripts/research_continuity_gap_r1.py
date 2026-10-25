#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究连续性缺口盘点 R1 —— 只读.

交易日口径: 优先 CACHE STOCK_DAILY_PIT_R1/year=2026 的实际 date 去重
（RAW P0_meta 的 calendar_cn_exchange 只到 2026-08-10，不能用作 09 月口径）

对每个交易日检查 7 个落点是否存在, 输出缺口矩阵 + 补齐顺序（不执行）。
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
TASK = ROOT / "任务" / "BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1"
OUT = TASK / "输出"
CACHE_CURRENT = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def load(p: Path) -> Any:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def trade_days(start: str, end: str) -> list[str]:
    import pandas as pd

    cur = load(CACHE_CURRENT) or {}
    root = Path(str(cur.get("release_root") or ""))
    part = root / "STOCK_DAILY_PIT_R1" / "year=2026" / "part_2026.parquet"
    if not part.exists():
        return []
    df = pd.read_parquet(part, columns=["date"])
    ds = sorted({str(x)[:10] for x in df["date"].unique()})
    return [d for d in ds if start <= d <= end]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-08-31")
    ap.add_argument("--end", default="2026-09-24")
    args = ap.parse_args()

    days = trade_days(args.start, args.end)
    slices = {
        "DAILY_BRIEF": ROOT / "DAILY_RESEARCH" / "DAILY_BRIEF",
        "RESEARCH_TRACE": ROOT / "DAILY_RESEARCH" / "RESEARCH_TRACE",
        "DOMESTIC_SELLSIDE": ROOT / "数据" / "研究报告" / "国内卖方" / "日增量",
        "DOMESTIC_NEWS": ROOT / "数据" / "研究报告" / "国内新闻" / "日增量",
        "GLOBAL_SELLSIDE": ROOT / "数据" / "研究报告" / "日增量",
        "US_NEWS": ROOT / "数据" / "美国市场" / "新闻" / "日增量",
        "US_MARKET": ROOT / "数据" / "美国市场" / "市场状态" / "日增量",
        "PLANE_DAILY": ROOT / "研究系统" / "数据平面" / "DAILY",
    }

    def hit(key: str, day: str) -> bool:
        base = slices[key]
        if key in ("DAILY_BRIEF",):
            return (base / f"{day}.md").exists()
        if key == "PLANE_DAILY":
            return (base / day.replace("-", "")).exists() or (base / day).exists()
        return (base / day).exists()

    matrix = []
    for d in days:
        row = {"date": d, **{k: hit(k, d) for k in slices}}
        row["missing"] = [k for k in slices if not row[k]]
        matrix.append(row)

    gap = [r for r in matrix if r["missing"]]
    only_data_ok = [r for r in matrix if not r["missing"]]

    # 数据域 vs 研究域分开统计
    data_keys = ["DOMESTIC_SELLSIDE", "DOMESTIC_NEWS", "US_NEWS", "US_MARKET"]
    run_date_keys = ["GLOBAL_SELLSIDE"]  # 三大行按运行日归档, 无市场日切片属正常
    research_keys = ["DAILY_BRIEF", "RESEARCH_TRACE"]
    data_gap = [r["date"] for r in matrix if any(not r[k] for k in data_keys)]
    run_date_note = [r["date"] for r in matrix if any(not r[k] for k in run_date_keys)]
    research_gap = [r["date"] for r in matrix if any(not r[k] for k in research_keys)]

    result = {
        "schema": "BLACKBOX_RESEARCH_CONTINUITY_GAP_R1",
        "generated_at_cn": now_cn(),
        "window": [args.start, args.end],
        "trading_day_source": "CACHE STOCK_DAILY_PIT_R1/year=2026 (RAW calendar_cn_exchange 仅到 2026-08-10)",
        "n_trading_days": len(days),
        "n_fully_present": len(only_data_ok),
        "market_date_gap_days": data_gap,
        "run_date_domain_days_without_slice": run_date_note,
        "research_memory_gap_days": research_gap,
        "matrix": matrix,
        "plan_readonly": [
            "1. 先补市场日数据切片(若缺): 仅在授权下跑对应 Lane D/E/F; 本脚本不执行",
            "2. 再逐日补研究记忆: 脚本/run_blackbox_daily_incremental_research_memory_r1.py --mode run-day",
            "3. 每补一日: 校验 DAILY_BRIEF/<date>.md + RESEARCH_TRACE/<date>/ 同时存在(双轨)",
            "4. 全部补齐后: --mode seal 封存, 再跑研究 OS --mode premarket",
            "5. Manifest 已对齐 2026-09-24; 研究补齐不得回改数据平面 CURRENT",
            "6. 三大行(GLOBAL_SELLSIDE)按运行日归档, 市场日无切片不视为缺口",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "RESEARCH_CONTINUITY_GAP_R1.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 研究连续性缺口（只读盘点）",
        "",
        f"- 窗口: {args.start} → {args.end}　交易日: {len(days)}　完全齐备: {len(only_data_ok)}",
        f"- 市场日数据缺口: {data_gap or '无'}",
        f"- 研究记忆缺口: {len(research_gap)} 天 {research_gap}",
        f"- 三大行无市场日切片(正常, 按运行日归档): {run_date_note or '无'}",
        "",
        "| 交易日 | " + " | ".join(slices) + " |",
        "|---" * (len(slices) + 1) + "|",
    ]
    for r in matrix:
        cells = ["✅" if r[k] else "—" for k in slices]
        lines.append(f"| {r['date']} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## 补齐顺序（未执行）",
        *[f"- {x}" for x in result["plan_readonly"]],
    ]
    (OUT / "RESEARCH_CONTINUITY_GAP_R1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"trading_days={len(days)} fully_present={len(only_data_ok)}")
    print(f"data_gap={data_gap}")
    print(f"research_gap={research_gap}")
    print(f"out={OUT / 'RESEARCH_CONTINUITY_GAP_R1.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
