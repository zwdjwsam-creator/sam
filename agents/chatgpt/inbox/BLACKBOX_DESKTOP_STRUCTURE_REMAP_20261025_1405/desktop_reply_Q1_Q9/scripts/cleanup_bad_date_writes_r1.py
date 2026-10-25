#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理 `--date 2026-09-24`（ISO，被 932 行当作紧凑 YYYYMMDD）造成的写入污染 R1。

根因: run_blackbox_daily_incremental_data_plane_r1.py:932
      cn_date = args.date or today_yyyymmdd()
      cn_iso  = f"{cn_date[:4]}-{cn_date[4:6]}-{cn_date[6:8]}"
      传 "2026-09-24" -> cn_iso = "2026--0-9-"
且 `--mode status` 并非只读：会重写 STATE / DAILY / 两个 DOMESTIC CURRENT / INPUT_PACK。

本脚本只做确定性修复，不重跑 lane、不下载、不下单:
  1. 目录: 把 日增量/2026--0-9-/ 里的产物挪回 日增量/2026-09-24/，再删空壳
  2. STATE / DAILY delta: "2026--0-9-" -> "2026-09-24"
  3. INPUT_PACK: CN_RESEARCH_DATE / DATA_MANIFEST_ID / BUILD_TIME 对齐已回填的 manifest
  4. DOMESTIC CURRENT: 按代码语义重算（sellside=cn_iso；news=obs asof）
  5. DAILY/2026-09-24/08_MANIFEST.json <- 现行 CURRENT manifest
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
TASK = ROOT / "任务" / "BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1"
PLANE = ROOT / "研究系统" / "数据平面"
OUT = TASK / "输出"
BAD = "2026--0-9-"
GOOD = "2026-09-24"
BAD_MID = "DAILY_DATA_MANIFEST_202609"

SELL_DAILY = ROOT / "数据" / "研究报告" / "国内卖方" / "日增量"
NEWS_DAILY = ROOT / "数据" / "研究报告" / "国内新闻" / "日增量"
SELL_CUR = ROOT / "数据" / "研究报告" / "国内卖方" / "CURRENT" / "DOMESTIC_SELLSIDE_CURRENT.json"
NEWS_CUR = ROOT / "数据" / "研究报告" / "国内新闻" / "CURRENT" / "DOMESTIC_NEWS_CURRENT.json"
NEWS_OBS = ROOT / "任务" / "STRATEGY_RESEARCH_PRO_TRADER_TAO_DECISION_POLICY_AND_DATA_SYSTEM_RECONSTRUCTION_R1" / "LIVE" / "INTRADAY_NEWS_OBS_R1"
MANIFEST = PLANE / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json"
PACK = PLANE / "CURRENT" / "DAILY_RESEARCH_INPUT_PACK_CURRENT.json"


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8-sig"))


def atomic(p: Path, o: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    t = p.with_name(p.name + f".tmp_clean_{os.getpid()}")
    t.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(t, p)


def main() -> int:
    acts: list[str] = []
    quarantine = TASK / "备份" / f"bad_date_{datetime.now(CN).strftime('%Y%m%d_%H%M%S')}"
    quarantine.mkdir(parents=True, exist_ok=True)

    # 1. 目录挪回 + 删空壳
    for base, fname in ((SELL_DAILY, "DOMESTIC_SELLSIDE_LEDGER.csv"),
                        (NEWS_DAILY, "DOMESTIC_NEWS_SLICE.json")):
        bad_dir = base / BAD
        if not bad_dir.exists():
            continue
        dst_dir = base / GOOD
        dst_dir.mkdir(parents=True, exist_ok=True)
        src = bad_dir / fname
        if src.exists():
            dst = dst_dir / fname
            if not dst.exists():
                shutil.move(str(src), str(dst))
                acts.append(f"移动 {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
            else:
                shutil.move(str(src), str(quarantine / f"{base.name}_{fname}"))
                acts.append(f"重复件隔离 {src.relative_to(ROOT)}")
        for rest in sorted(bad_dir.rglob("*")):
            if rest.is_file():
                rel = rest.relative_to(ROOT).as_posix().replace("/", "_")
                shutil.move(str(rest), str(quarantine / rel))
                acts.append(f"残留隔离 {rest.relative_to(ROOT)}")
        shutil.rmtree(bad_dir, ignore_errors=True)
        acts.append(f"删除空壳 {bad_dir.relative_to(ROOT)}")

    # 2. STATE + DAILY delta 字符串修正
    targets = [
        PLANE / "STATE" / "DOMESTIC_RESEARCH_INCREMENTAL_STATE.json",
        PLANE / "STATE" / "US_NEWS_INCREMENTAL_STATE.json",
        PLANE / "DAILY" / GOOD / "04_DOMESTIC_RESEARCH_DELTA.json",
        PLANE / "DAILY" / GOOD / "05_US_NEWS_DELTA.json",
    ]
    for p in targets:
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8-sig")
        if BAD not in txt:
            continue
        atomic(p, json.loads(txt.replace(BAD, GOOD)))

    shipped = quarantine / "STATE"
    shipped.mkdir(parents=True, exist_ok=True)
    for p in targets:
        if p.exists():
            shutil.copy2(p, shipped / p.name)
    acts.append(f"STATE/DAILY delta 日期修正 {BAD} -> {GOOD}")

    man = load(MANIFEST)

    # 3. INPUT_PACK 对齐
    if PACK.exists():
        pack = load(PACK)
        pack["BUILD_TIME"] = man["BUILD_TIME"]
        pack["DATA_MANIFEST_ID"] = man["manifest_id"]
        pack["CN_RESEARCH_DATE"] = man["CN_RESEARCH_DATE"]
        atomic(PACK, pack)
        acts.append("INPUT_PACK: BUILD_TIME/DATA_MANIFEST_ID/CN_RESEARCH_DATE 对齐 manifest")

    # 4. DOMESTIC CURRENT 按代码语义重算
    if SELL_CUR.exists():
        c = load(SELL_CUR)
        ledger = SELL_DAILY / GOOD / "DOMESTIC_SELLSIDE_LEDGER.csv"
        n = 0
        if ledger.exists():
            n = max(0, sum(1 for _ in ledger.read_text(encoding="utf-8", errors="replace").splitlines()) - 1)
        c["DISCOVERY_ASOF"] = man["CN_RESEARCH_DATE"]
        c["SOURCE_PATH"] = str(ledger if ledger.exists() else (SELL_DAILY / GOOD))
        c["N_ROWS"] = n
        c["STATUS"] = "PASS" if n > 0 else "DEGRADED"
        c["INGEST_TIME"] = now_cn()
        atomic(SELL_CUR, c)
        acts.append(f"DOMESTIC_SELLSIDE_CURRENT: DISCOVERY_ASOF={c['DISCOVERY_ASOF']} N_ROWS={n} SOURCE_PATH 修正")

    if NEWS_CUR.exists():
        c = load(NEWS_CUR)
        obs_p = Path(str(c.get("source_obs") or ""))
        obs = load(obs_p) if obs_p.exists() else {}
        c["DISCOVERY_ASOF"] = obs.get("asof") or man["CN_RESEARCH_DATE"]  # 代码: obs_news.asof or cn_iso
        c["daily_slice"] = str(NEWS_DAILY / GOOD)
        c["INGEST_TIME"] = now_cn()
        atomic(NEWS_CUR, c)
        acts.append(f"DOMESTIC_NEWS_CURRENT: DISCOVERY_ASOF={c['DISCOVERY_ASOF']}（obs asof）daily_slice 修正")

    # 5. DAILY/08_MANIFEST.json <- CURRENT
    mpath = PLANE / "DAILY" / GOOD / "08_MANIFEST.json"
    atomic(mpath, man)
    acts.append(f"DAILY/{GOOD}/08_MANIFEST.json 用已回填 manifest 覆盖")

    # 6. 全仓残留检查
    residual = []
    for base in (ROOT / "研究系统", ROOT / "数据", ROOT / "运行"):
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".json", ".md", ".csv", ".txt"):
                continue
            try:
                if BAD in p.read_text(encoding="utf-8", errors="ignore"):
                    residual.append(str(p.relative_to(ROOT)))
            except OSError:
                pass
            if len(residual) > 30:
                break

    rep = {
        "schema": "BLACKBOX_BAD_DATE_CLEANUP_LEDGER_R1",
        "cleaned_at_cn": now_cn(),
        "root_cause": {
            "file": "脚本/run_blackbox_daily_incremental_data_plane_r1.py",
            "line": 932,
            "code": "cn_date = args.date or today_yyyymmdd(); cn_iso = f\"{cn_date[:4]}-{cn_date[4:6]}-{cn_date[6:8]}\"",
            "bad_input": "--date 2026-09-24 (ISO)",
            "result": "cn_iso='2026--0-9-'",
            "note": "--mode status 也会写 CURRENT/STATE/DAILY，不是只读",
        },
        "actions": acts,
        "quarantine_dir": str(quarantine),
        "manifest": {
            "manifest_id": man["manifest_id"],
            "CN_RESEARCH_DATE": man["CN_RESEARCH_DATE"],
            "DATA_GENERATION_ID": man["DATA_GENERATION_ID"],
        },
        "residual_bad_string_files": residual,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "BAD_DATE_CLEANUP_LEDGER.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if not residual else 2


if __name__ == "__main__":
    raise SystemExit(main())
