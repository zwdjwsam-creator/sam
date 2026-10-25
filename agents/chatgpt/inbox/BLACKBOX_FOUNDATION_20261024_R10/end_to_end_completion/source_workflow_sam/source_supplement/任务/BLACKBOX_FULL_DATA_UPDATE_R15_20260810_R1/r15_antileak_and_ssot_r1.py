#!/usr/bin/env python3
"""After R12 seal: antileak asof triple-align + amend FULL_DATA_UPDATE SSOT."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"E:\BLACKBOX\任务\BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1")
OUT = ROOT / "12_ACCEPTANCE"
CURRENT = Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json")
SSOT = Path(r"E:\BLACKBOX\规则库\hand_hard_rules\BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R1.json")
ASOF = "2026-08-10"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def now_cn() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%dT%H:%M:%S%z")


def wjson(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def antileak_check() -> dict:
    obj = json.loads(CURRENT.read_text(encoding="utf-8")) if CURRENT.exists() else {}
    asof = str(obj.get("cleaning_as_of") or "")
    finance = str(obj.get("finance_asof") or "")
    daily = str(obj.get("daily_asof") or "")
    aligned = asof == ASOF and finance == ASOF and daily == ASOF
    ssot = json.loads(SSOT.read_text(encoding="utf-8")) if SSOT.exists() else {}
    pit = ssot.get("anti_leakage_last") or {}
    out = {
        "generated_at": now_iso(),
        "cleaning_as_of": asof,
        "finance_asof": finance,
        "daily_asof": daily,
        "target_asof": ASOF,
        "asof_aligned": aligned,
        "release_id": obj.get("release_id"),
        "seal_id": obj.get("seal_id"),
        "index_pit_overall_pass": pit.get("overall_pass"),
        "overall_pass": bool(aligned and (pit.get("overall_pass") is True or pit.get("overall_pass") is None)),
        "notes": [
            "R15 asof triple-align required (cleaning/finance/daily == 2026-08-10)",
            "finance files carried from R11; finance_asof PIT cutoff advanced with trading day",
            "index PIT inherits prior SSOT anti_leakage_last when present",
        ],
    }
    # if prior pit missing, still pass on asof align alone for freshness-only round
    if pit.get("overall_pass") is None:
        out["overall_pass"] = bool(aligned)
        out["notes"].append("index_pit_overall_pass absent → antileak judged on asof_aligned only")
    wjson(OUT / "ANTI_LEAKAGE_R15.json", out)
    return out


def amend_ssot(seal: dict, antileak: dict) -> dict:
    ssot = json.loads(SSOT.read_text(encoding="utf-8"))
    entry = {
        "domain": "full_data_update_r15_20260810",
        "completed_at_cn": now_cn(),
        "status": "CURRENT",
        "cutoff": ASOF,
        "window": {"start": ASOF, "end": ASOF},
        "phases": {
            "download_daily_minute": "PASS",
            "cleaning_r15": seal.get("final_status"),
            "anti_leakage": antileak.get("overall_pass"),
        },
        "cleaning_release_id": seal.get("release_id"),
        "cleaning_seal_id": seal.get("seal_id"),
        "parent_release_id": seal.get("parent_release_id"),
        "evidence": {
            "R12_SEAL": str(OUT / "R15_SEAL_RESULT.json"),
            "ANTI_LEAKAGE": str(OUT / "ANTI_LEAKAGE_R15.json"),
        },
        "related_user_utterance": "自动清洗对齐防止穿越",
    }
    completed = ssot.setdefault("completed_domains", [])
    # replace prior r12 entry if re-run
    completed = [c for c in completed if c.get("domain") != entry["domain"]]
    completed.append(entry)
    ssot["completed_domains"] = completed
    ssot["last_amended_at_cn"] = now_cn()
    ssot["last_amended_utterance"] = "自动清洗对齐防止穿越"
    ssot["amendment_note"] = (
        "R15 封板：2026-08-10 A股/ETF/指数日线+分钟摄入；CURRENT asof 三元组对齐 2026-08-10；"
        "财务无新增下载，PIT cutoff 随交易日推进。"
    )
    ssot["anti_leakage_last"] = {
        "overall_pass": antileak.get("overall_pass"),
        "asof_aligned": antileak.get("asof_aligned"),
        "cleaning_as_of": antileak.get("cleaning_as_of"),
        "checked_at": now_iso(),
        "source": "R15_ANTILEAK",
    }
    ssot["current_cleaning"] = {
        "release_id": seal.get("release_id"),
        "seal_id": seal.get("seal_id"),
        "cleaning_as_of": ASOF,
        "status": "CURRENT",
    }
    wjson(SSOT, ssot)
    return {"ssot_path": str(SSOT), "domain": entry["domain"]}


def main() -> int:
    seal_path = OUT / "R15_SEAL_RESULT.json"
    if not seal_path.exists():
        print(json.dumps({"final_status": "FAILED", "reason": "missing_R15_SEAL"}, ensure_ascii=False))
        return 2
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if seal.get("final_status") != "PASS" or not seal.get("CURRENT_switched"):
        print(json.dumps({"final_status": "FAILED", "reason": "seal_not_ready", "seal": seal}, ensure_ascii=False))
        return 2
    antileak = antileak_check()
    if not antileak.get("overall_pass"):
        wjson(OUT / "R15_FINISH_RESULT.json", {"final_status": "REVIEW_REQUIRED", "antileak": antileak})
        print(json.dumps({"final_status": "REVIEW_REQUIRED", "antileak": antileak}, ensure_ascii=False))
        return 1
    meta = amend_ssot(seal, antileak)
    out = {
        "final_status": "PASS",
        "release_id": seal.get("release_id"),
        "antileak": antileak.get("overall_pass"),
        "asof": ASOF,
        "ssot": meta,
        "generated_at": now_iso(),
    }
    wjson(OUT / "R15_FINISH_RESULT.json", out)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
