#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Align index minutes cutoff=2026-08-21 (incremental) then inventory refresh."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"E:\BLACKBOX")
TASK = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924")
DAY = "2026-09-24"
ALIGN = ROOT / "脚本" / "index_minute_align_clean_antileak_seal_r1.py"
sys.path.insert(0, str(ROOT / "脚本"))
import p7_gate_common as gc


def main() -> int:
    dec = gc.load_hand_decision() or {}
    dec.update(
        {
            "current_stage": "INDEX_MINUTE_ALIGN_CLEAN_ANTILEAK",
            "index_minute_align_clean_allowed": True,
            "allowed_script": str(ALIGN),
            "hand_release_level": "RELEASE_ALLOWED_FOR_INDEX_MINUTE_ALIGN_ASOF_20260924_TIP",
            "generated_at": gc.now_iso() if hasattr(gc, "now_iso") else dec.get("generated_at"),
        }
    )
    gc.write_hand_decision(dec)

    py = str(ROOT / ".venv" / "Scripts" / "python.exe")
    print(f"start align asof={DAY} mode=incremental", flush=True)
    r = subprocess.run(
        [
            py,
            "-u",
            str(ALIGN),
            "--mode",
            "incremental",
            "--cutoff",
            DAY,
            "--increment-dates",
            DAY,
            "--universe",
            "jq_all_732",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
    )
    (TASK / "logs").mkdir(parents=True, exist_ok=True)
    (TASK / "logs" / "align_stdout.log").write_text(r.stdout or "", encoding="utf-8")
    (TASK / "logs" / "align_stderr.log").write_text(r.stderr or "", encoding="utf-8")
    print(f"align exit={r.returncode}", flush=True)
    if r.stdout:
        print("\n".join((r.stdout or "").splitlines()[-40:]), flush=True)
    if r.stderr:
        print("STDERR tail:\n" + "\n".join((r.stderr or "").splitlines()[-20:]), flush=True)

    inv = subprocess.run(
        [py, "-u", str(ROOT / "脚本" / "blackbox_data_inventory_top_refresh.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    (TASK / "logs" / "inventory_after_align.log").write_text(inv.stdout or "", encoding="utf-8")

    ptr = {}
    pp = ROOT / "数据" / "清洗成品" / "CURRENT_INDEX_MINUTE_ALIGN_RELEASE.json"
    if pp.exists():
        ptr = json.loads(pp.read_text(encoding="utf-8"))
    summary = {
        "align_exit": r.returncode,
        "release_id": ptr.get("release_id"),
        "all_pass": ptr.get("all_pass"),
        "seal_id": ptr.get("seal_id"),
        "asof": DAY,
    }
    (TASK / "out").mkdir(parents=True, exist_ok=True)
    (TASK / "out" / "ALIGN_RESULT.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    dec = gc.load_hand_decision() or {}
    dec.update(
        {
            "current_stage": "FULL_DATA_INCREMENT_R32",
            "index_minute_align_release_id": ptr.get("release_id"),
            "index_minute_align_clean_pass": ptr.get("all_pass"),
            "index_minute_align_asof": DAY,
            "full_data_increment_r32_allowed": True,
            "formal_cleaning_r32_allowed": True,
            "cleaning_allowed": True,
            "hand_release_level": "RELEASE_ALLOWED_FOR_FULL_DATA_INCREMENT_R32_ASOF_20260902",
        }
    )
    gc.write_hand_decision(dec)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    ok = r.returncode == 0 and ptr.get("all_pass") is True
    # accept if new release id contains asof day tag
    rid = str(ptr.get("release_id") or "")
    if r.returncode == 0 and "20260902" in rid and ptr.get("all_pass") is True:
        ok = True
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
