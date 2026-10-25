#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从候选回填 09-24 manifest（修复 --mode status 误写造成的 CURRENT 污染）。

背景：`run_blackbox_daily_incremental_data_plane_r1.py:932` 的 `--date` 只接受紧凑
`YYYYMMDD`；传 `2026-09-24` 会被切成 `2026--0-9-`，且 `--mode status` 会**写**CURRENT，
把刚回退好的 manifest 覆盖掉（并丢掉 F 段细粒度固定路径）。

本脚本只回填 3 个 CURRENT，不重跑任何 lane。
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
TASK = ROOT / "任务" / "BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1"
CAND = TASK / "候选" / "CURRENT" / "DAILY_DATA_MANIFEST_AFTER_Q1_Q9.json"
PROD_MANIFEST = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json"
PROD_PLANE = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_PLANE_CURRENT.json"
OUT = TASK / "输出"
META = ("DATA_GENERATION_ID", "MANIFEST_SEMANTIC_SHA256", "DATA_GENERATION_ID_ISSUER", "BUILD_TIME")


def now() -> datetime:
    return datetime.now(CN)


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8-sig"))


def atomic(p: Path, o: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    t = p.with_name(p.name + f".tmp_restore_{os.getpid()}")
    t.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(t, p)


def dg1(mod: dict) -> str:
    sys.path.insert(0, str(ROOT / "脚本"))
    from blackbox_run_identity_r1 import attach_data_generation_to_manifest

    return attach_data_generation_to_manifest({k: v for k, v in mod.items() if k not in META})["DATA_GENERATION_ID"]


def main() -> int:
    assert CAND.exists(), f"候选缺失: {CAND}"
    old = load(PROD_MANIFEST)
    cand = load(CAND)
    cand["BUILD_TIME"] = now().strftime("%Y-%m-%dT%H:%M:%S%z")
    d = dg1(cand)
    cand["DATA_GENERATION_ID"] = d
    cand["MANIFEST_SEMANTIC_SHA256"] = d.split("-", 1)[1]
    cand["DATA_GENERATION_ID_ISSUER"] = "DATA_PLANE"

    bak = TASK / "备份" / f"restore_{now().strftime('%Y%m%d_%H%M%S')}"
    b = bak / PROD_MANIFEST.relative_to(ROOT)
    b.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROD_MANIFEST, b)
    shutil.copy2(PROD_PLANE, bak / PROD_PLANE.relative_to(ROOT))

    atomic(PROD_MANIFEST, cand)
    plane = load(PROD_PLANE)
    plane["BUILD_TIME"] = cand["BUILD_TIME"]
    plane["DATA_GENERATION_ID"] = d
    plane["DATA_MANIFEST_ID"] = cand["manifest_id"]
    atomic(PROD_PLANE, plane)

    back = load(PROD_MANIFEST)
    rep = {
        "restored_at_cn": cand["BUILD_TIME"],
        "corrupted_before": {
            "CN_RESEARCH_DATE": old.get("CN_RESEARCH_DATE"),
            "DG1": old.get("DATA_GENERATION_ID"),
            "US_MARKET_FIXED_PATHS": sorted((old.get("US_MARKET", {}).get("FIXED_PATHS") or {})),
        },
        "after": {
            "manifest_id": back.get("manifest_id"),
            "CN_RESEARCH_DATE": back.get("CN_RESEARCH_DATE"),
            "DG1": back.get("DATA_GENERATION_ID"),
            "US_MARKET_FIXED_PATHS": sorted(back["US_MARKET"]["FIXED_PATHS"]),
            "alignment_csv_present": "alignment_csv" in back["US_MARKET"]["FIXED_PATHS"],
            "modes": {k: back[k].get("MODE") for k in ("JQ", "T_EXTERNAL", "GLOBAL_SELLSIDE")},
            "fine_grained": (back["US_MARKET"].get("US_FINE_GRAINED_STATUS"),
                             back["US_MARKET"].get("A_SHARE_MAPPING_PRIOR_STATUS")),
        },
        "backup_dir": str(bak),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "CURRENT_RESTORE_LEDGER.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
