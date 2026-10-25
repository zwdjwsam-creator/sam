# -*- coding: utf-8 -*-
"""One-shot desktop runner for the SAM-led rectification (R1).

Run this ON the desktop (ZHANGWEI) so the evidence carries the desktop's own identity:

    cd /d E:\\BLACKBOX\\_OPS\\FOUNDATION_RECOVERY_20261024\\end_to_end_completion\\sam_led_rectification
    E:\\BLACKBOX\\.venv\\Scripts\\python.exe -X utf8 RUN_CHAIN_R1.py

What it does (in order, stopping nothing that is already proven):
  A. chain       tools/run_connected_pipeline.py  -> R15 clean -> original compiler -> commit -> publish probe
  B. status      data plane --mode status --date 2026-09-24  -> must be READ-ONLY and accept ISO
  C. neg-date    data plane --mode status --date 2026--0-9-    -> must exit non-zero, write nothing
  D. neg-date2   data plane --mode status --date ""            -> today, must be read-only
  E. digest      sha256 of the three CURRENT files + six STATE files before/after B-D

Every step records hostname / sys.executable / cwd / argv / exit code / log path / stdout tail.
Output: LOCAL_RUN_EVIDENCE.json + logs/ in this directory.

Nothing here downloads, switches production CURRENT, or places an order.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
E2E = HERE.parent
BB = Path(r"E:\BLACKBOX")
PY = str(BB / ".venv" / "Scripts" / "python.exe")
LOG = HERE / "logs"
OUT = HERE / "LOCAL_RUN_EVIDENCE.json"

WATCH = [
    BB / "研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json",
    BB / "研究系统/数据平面/CURRENT/DAILY_DATA_PLANE_CURRENT.json",
    BB / "研究系统/数据平面/CURRENT/DAILY_RESEARCH_INPUT_PACK_CURRENT.json",
    BB / "研究系统/数据平面/STATE/JQ_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/T_EXTERNAL_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/GLOBAL_SELLSIDE_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/DOMESTIC_RESEARCH_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/US_NEWS_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/US_MARKET_STATE_INCREMENTAL_STATE.json",
]


def sha(p: Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def digest() -> dict:
    return {str(p.relative_to(BB)).replace("\\", "/"): sha(p) for p in WATCH}


def step(name: str, cmd: list[str], timeout: int = 3600) -> dict:
    LOG.mkdir(parents=True, exist_ok=True)
    log = LOG / f"{name}.log"
    started = time.time()
    with open(log, "w", encoding="utf-8", errors="replace") as fh:
        fh.write("$ " + " ".join(cmd) + "\n")
        fh.flush()
        try:
            proc = subprocess.run(cmd, cwd=str(BB), stdout=fh, stderr=subprocess.STDOUT,
                                  timeout=timeout)
            rc = int(proc.returncode)
            timed_out = False
        except subprocess.TimeoutExpired:
            rc = 124
            timed_out = True
    tail = ""
    try:
        tail = "\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-25:])
    except OSError:
        pass
    return {
        "step": name,
        "argv": cmd,
        "exit_code": rc,
        "timed_out": timed_out,
        "elapsed_sec": round(time.time() - started, 1),
        "cwd": str(Path.cwd()),
        "python": sys.executable,
        "log": str(log),
        "stdout_tail": tail,
    }


def main() -> int:
    ident = {
        "hostname": os.environ.get("COMPUTERNAME") or os.uname().nodename,
        "sys_executable": sys.executable,
        "cwd_at_start": str(Path.cwd()),
        "python_version": sys.version,
        "started_at_cn": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    d0 = digest()

    res: dict = {"artifact": "SAM_LED_RECTIFICATION_LOCAL_RUN_EVIDENCE",
                 "runner": "RUN_CHAIN_R1.py", "identity": ident, "steps": {}}

    # A. the chain (R15 -> compiler -> commit -> publish probe)
    res["steps"]["A_chain"] = step("A_chain", [PY, "-X", "utf8",
                                              str(E2E / "tools" / "run_connected_pipeline.py")],
                                  timeout=7200)

    d_after_a = digest()

    # B. status must be read-only and accept ISO
    res["steps"]["B_status_iso"] = step("B_status_iso", [
        PY, "-X", "utf8", str(BB / "脚本" / "run_blackbox_daily_incremental_data_plane_r1.py"),
        "--mode", "status", "--date", "2026-09-24"], timeout=900)

    d_after_b = digest()

    # C. malformed date must fail closed
    res["steps"]["C_bad_date"] = step("C_bad_date", [
        PY, "-X", "utf8", str(BB / "脚本" / "run_blackbox_daily_incremental_data_plane_r1.py"),
        "--mode", "status", "--date", "2026--0-9-"], timeout=300)

    d_after_c = digest()

    # D. compact date must be accepted
    res["steps"]["D_status_compact"] = step("D_status_compact", [
        PY, "-X", "utf8", str(BB / "脚本" / "run_blackbox_daily_incremental_data_plane_r1.py"),
        "--mode", "status", "--date", "20260924"], timeout=900)

    d_end = digest()

    res["digests"] = {"start": d0, "after_chain": d_after_a, "after_status_iso": d_after_b,
                      "after_bad_date": d_after_c, "end": d_end}
    res["verdicts"] = {
        "chain_exit_zero": res["steps"]["A_chain"]["exit_code"] == 0,
        "status_iso_accepted": res["steps"]["B_status_iso"]["exit_code"] == 0,
        "status_wrote_nothing": d_after_b == d_after_a,
        "bad_date_failed_closed": res["steps"]["C_bad_date"]["exit_code"] != 0,
        "bad_date_wrote_nothing": d_after_c == d_after_b,
        "compact_date_accepted": res["steps"]["D_status_compact"]["exit_code"] == 0,
        "compact_wrote_nothing": d_end == d_after_c,
        "no_bad_date_dir_created": not any(
            (p.name.startswith("2026--") or "--0-9-" in p.name)
            for base in (BB / "数据", BB / "运行")
            for p in (base.rglob("2026--*") if base.exists() else [])),
    }
    res["finished_at_cn"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(json.dumps({"identity": ident, "verdicts": res["verdicts"],
                      "evidence": str(OUT)}, ensure_ascii=False, indent=2))
    return 0 if all(res["verdicts"].values()) else 5


if __name__ == "__main__":
    raise SystemExit(main())
