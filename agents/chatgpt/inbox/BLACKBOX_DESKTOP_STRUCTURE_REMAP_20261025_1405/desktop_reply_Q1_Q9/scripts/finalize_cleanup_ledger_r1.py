#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收尾：修 DAILY_DATA_PLANE_CURRENT.CN_RESEARCH_DATE + 落 BAD_DATE 清理台账。"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
TASK = ROOT / "任务" / "BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1"
OUT = TASK / "输出"
PLANE_CUR = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_PLANE_CURRENT.json"
MANIFEST = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json"
BAD = "2026--0-9-"


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def atomic(p: Path, o: dict) -> None:
    t = p.with_name(p.name + f".tmp_fix_{os.getpid()}")
    t.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(t, p)


def main() -> int:
    man = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    plane = json.loads(PLANE_CUR.read_text(encoding="utf-8-sig"))
    before = plane.get("CN_RESEARCH_DATE")
    plane["CN_RESEARCH_DATE"] = man["CN_RESEARCH_DATE"]
    plane["BUILD_TIME"] = man["BUILD_TIME"]
    plane["DATA_GENERATION_ID"] = man["DATA_GENERATION_ID"]
    plane["DATA_MANIFEST_ID"] = man["manifest_id"]
    atomic(PLANE_CUR, plane)

    rg = subprocess.run(
        ["rg", "-l", "--no-messages", BAD, "-g", "*.json", "-g", "*.md", "-g", "*.csv", "-g", "*.txt", str(ROOT)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    hits = [l.strip() for l in rg.stdout.splitlines() if l.strip()]
    production_hits = [h for h in hits if "\\备份\\" not in h and "\\输出\\" not in h]

    rep = {
        "schema": "BLACKBOX_BAD_DATE_CLEANUP_LEDGER_R1",
        "cleaned_at_cn": now_cn(),
        "root_cause": {
            "file": "脚本/run_blackbox_daily_incremental_data_plane_r1.py",
            "line": 932,
            "code": "cn_date = args.date or today_yyyymmdd(); cn_iso = f\"{cn_date[:4]}-{cn_date[4:6]}-{cn_date[6:8]}\"",
            "trigger": "本机误传 --date 2026-09-24（ISO）；该参数只接受紧凑 YYYYMMDD",
            "invalid_iso": "2026--0-9-",
            "secondary": "--mode status 并非只读：会写 STATE / DAILY / 两个 DOMESTIC CURRENT / INPUT_PACK / PLANE",
        },
        "fixed": [
            "删除 数据/研究报告/国内卖方|国内新闻/日增量/2026--0-9-/（产物已挪回 2026-09-24）",
            "STATE: DOMESTIC_RESEARCH / US_NEWS DISCOVERY_ASOF -> 2026-09-24",
            "DAILY/2026-09-24/04_DOMESTIC_RESEARCH_DELTA.json / 05_US_NEWS_DELTA.json -> 2026-09-24",
            "CURRENT/DAILY_RESEARCH_INPUT_PACK_CURRENT.json: CN_RESEARCH_DATE / DATA_MANIFEST_ID / BUILD_TIME 对齐 manifest",
            "CURRENT/DAILY_DATA_PLANE_CURRENT.json: CN_RESEARCH_DATE 对齐 manifest",
            "数据/研究报告/国内卖方/CURRENT/DOMESTIC_SELLSIDE_CURRENT.json: DISCOVERY_ASOF=2026-09-24, SOURCE_PATH 指向 2026-09-24 ledger, N_ROWS=4",
            "数据/研究报告/国内新闻/CURRENT/DOMESTIC_NEWS_CURRENT.json: DISCOVERY_ASOF=2026-09-25（= obs asof，代码 obs_news.asof or cn_iso）, daily_slice 指向 2026-09-24",
            "研究系统/数据平面/DAILY/2026-09-24/08_MANIFEST.json <- 现行 CURRENT manifest",
        ],
        "plane_cn_research_date": {"before": before, "after": plane["CN_RESEARCH_DATE"]},
        "residual_hits": hits,
        "residual_production_hits": production_hits,
        "residual_note": "仅保留在 备份/ 与 输出/ 台账中作为事故证据，生产 CURRENT/STATE 已清零",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "BAD_DATE_CLEANUP_LEDGER.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if not production_hits else 2


if __name__ == "__main__":
    raise SystemExit(main())
