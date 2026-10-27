# -*- coding: utf-8 -*-
"""Ingest val/adjust into R43 cleaning; tip-extend adjust+val+SW on cache candidate; atomic publish."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"E:\BLACKBOX")
sys.path.insert(0, str(ROOT / "脚本"))
sys.path.insert(0, str(ROOT / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1"))
sys.path.insert(0, r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924")

ASOF = "2026-09-24"
PY = ROOT / ".venv" / "Scripts" / "python.exe"
CLEAN_PTR = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
CACHE_CAND = ROOT / "数据" / "回测缓存" / "releases" / "BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20260925_034907"
VAL_ACC = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\VAL_ADJUST_ACCEPTANCE.json")
OUT = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\qa")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(msg: str) -> None:
    print(f"[{now_iso()}] {msg}", flush=True)


def place(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main() -> int:
    from blackbox_daily_increment_common_r1 import rebuild_capability_facts_candidate, wjson
    from blackbox_daily_increment_publish_gate_r1 import publish_atomic
    from cache_compiler_tip_rebase_from_current_r1 import SW_REWRITE, build_valuation, inject_sw

    OUT.mkdir(parents=True, exist_ok=True)
    clean = json.loads(CLEAN_PTR.read_text(encoding="utf-8"))
    std = Path(clean["standard_root"])
    acc = json.loads(VAL_ACC.read_text(encoding="utf-8"))

    # 1) place tip files into cleaning
    place(Path(acc["adjust_factor"]["raw_path"]), std / acc["adjust_factor"]["clean_rel_ref"].replace("\\", "/"))
    place(Path(acc["adjust_factor"]["path_p6"]), std / acc["adjust_factor"]["clean_rel_factor"].replace("\\", "/"))
    place(Path(acc["valuation"]["raw_path"]), std / acc["valuation"]["clean_rel_factor"].replace("\\", "/"))
    place(Path(acc["valuation"]["raw_path"]), std / acc["valuation"]["clean_rel_ref"].replace("\\", "/"))
    log("val/adjust placed into cleaning R45")

    # 2) tip-extend adjust factor in candidate
    tip_adj = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\tip_extend_adjust_r1.py")
    rc = subprocess.call([str(PY), "-u", str(tip_adj), str(CACHE_CAND)])
    log(f"tip_extend_adjust rc={rc}")
    if rc != 0:
        return rc

    # 3) rebuild valuation from cleaning
    val = build_valuation(std, CACHE_CAND / "VALUATION_PIT_R1", ASOF)
    log(f"valuation {val}")

    # 4) reinject SW from CURRENT_*_RELEASE.json (already tip-sealed)
    sw_out = {}
    for lv, cfg in SW_REWRITE.items():
        sw_out[lv] = inject_sw(CACHE_CAND, lv, cfg)
        log(f"SW_{lv} {sw_out[lv]}")

    # 5) refresh RELEASE.json fields
    rel_ptr = json.loads((CACHE_CAND / "RELEASE.json").read_text(encoding="utf-8"))
    rel_ptr.update(
        {
            "asof": ASOF,
            "valuation_status": val.get("status"),
            "sw_l1_status": "READY_INTEGRATED" if sw_out.get("L1", {}).get("status") == "READY" else sw_out.get("L1"),
            "sw_l2_status": "READY_INTEGRATED" if sw_out.get("L2", {}).get("status") == "READY" else sw_out.get("L2"),
            "sw_l3_status": "READY_INTEGRATED" if sw_out.get("L3", {}).get("status") == "READY" else sw_out.get("L3"),
            "patched_val_sw_at": now_iso(),
            "source_cleaning_release": clean.get("release_id"),
        }
    )
    wjson(CACHE_CAND / "RELEASE.json", rel_ptr)

    # 6) rebuild capability facts for candidate generation
    facts = rebuild_capability_facts_candidate(
        cache_id=rel_ptr["cache_release_id"],
        cache_root=CACHE_CAND,
        target=ASOF,
    )
    facts_path = CACHE_CAND / "PRODUCT_CAPABILITY_FACTS_CANDIDATE.json"
    wjson(facts_path, facts)
    log(f"facts VAL max={facts['products']['VALUATION_PIT_R1'].get('FORMAL_COVERAGE_MAX')}")
    log(f"facts ADJ max={facts['products']['ADJUST_FACTOR_PIT_R1'].get('FORMAL_COVERAGE_MAX')}")
    log(f"facts SW_L3 max={facts['products']['SW_L3_MEMBERSHIP_PIT_R1'].get('FORMAL_COVERAGE_MAX')}")

    # 7) atomic publish
    out = publish_atomic(
        cache_pointer=rel_ptr,
        cache_root=CACHE_CAND,
        facts=facts,
        target=ASOF,
        cleaning_pointer=clean,
        dry_run=False,
    )
    wjson(OUT / "PUBLISH_RESULT.json", out)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("OPERATIONAL_READINESS") == "PASS" and out.get("published") else 2


if __name__ == "__main__":
    raise SystemExit(main())
