# -*- coding: utf-8 -*-
"""One-shot launcher. Does not modify the reviewed executor modules."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_ABC_RESUME_ONLY_20261014")
WORK = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
SAMPLE = r"C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\CAPABILITY_SAMPLE.json"
CONTRACT = r"C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_ABC_RESUME_ONLY_20261014\PILOT_EXECUTION_CONTRACT.json"
TASK = "R9_DESKTOP_REAL_ABC_RESUME_ONLY_20261014_1437"
CST = timezone(timedelta(hours=8))


def main() -> int:
    phase = sys.argv[1]
    scenario = sys.argv[2]
    mode = sys.argv[3]
    fault = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "-" else None
    key = f"{TASK}_{scenario}_{phase}"
    claims = ROOT / "claims"
    logs = ROOT / "logs"
    claims.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    claim = claims / key
    log = logs / f"{key}.log"
    meta = claims / f"{key}.json"
    try:
        claim_handle = claim.open("x", encoding="utf-8")
        log_handle = log.open("x", encoding="utf-8")
    except FileExistsError:
        print(f"CLAIM_EXISTS {key}")
        return 9
    argv = [
        sys.executable, "-m", "r9_capability_pilot", mode,
        "--scenario", scenario, "--sample", SAMPLE, "--contract", CONTRACT,
    ]
    if fault:
        argv.extend(["--fault", fault])
    started = datetime.now(timezone.utc)
    claim_handle.write(json.dumps({
        "task_id": TASK,
        "scenario": scenario,
        "phase": phase,
        "launcher_pid": os.getpid(),
        "argv": argv,
        "start_utc": started.isoformat(),
        "start_cst": started.astimezone(CST).isoformat(),
    }, ensure_ascii=False) + "\n")
    claim_handle.flush()
    child = subprocess.Popen(argv, cwd=WORK, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    claim_handle.write(f"child_pid={child.pid}\n")
    claim_handle.flush()
    out, err = child.communicate()
    ended = datetime.now(timezone.utc)
    log_handle.write(out)
    if err:
        log_handle.write("\n--- stderr ---\n")
        log_handle.write(err)
    log_handle.close()
    import hashlib
    digest = hashlib.sha256(log.read_bytes()).hexdigest()
    record = {
        "task_id": TASK,
        "scenario": scenario,
        "phase": phase,
        "launcher_pid": os.getpid(),
        "child_pid": child.pid,
        "argv": argv,
        "exit": child.returncode,
        "start_utc": started.isoformat(),
        "end_utc": ended.isoformat(),
        "start_cst": started.astimezone(CST).isoformat(),
        "end_cst": ended.astimezone(CST).isoformat(),
        "log": str(log),
        "log_sha256": digest,
        "stdout": out,
    }
    meta.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    claim_handle.write(f"exit={child.returncode}\nend_utc={ended.isoformat()}\n")
    claim_handle.close()
    print(out, end="")
    print(f"child_pid={child.pid} exit={child.returncode} log_sha256={digest}")
    return child.returncode


if __name__ == "__main__":
    sys.exit(main())
