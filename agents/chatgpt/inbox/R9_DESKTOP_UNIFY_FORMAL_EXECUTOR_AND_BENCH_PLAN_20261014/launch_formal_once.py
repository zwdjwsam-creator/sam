# -*- coding: utf-8 -*-
"""One claim, one child, no retry. Does not create the E: bench directory by itself."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014")
WORK = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
TASK = "R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014_1518"
CST = timezone(timedelta(hours=8))


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("dry-run", "execute"):
        print("usage: launch_formal_once.py dry-run|execute CONTRACT")
        return 2
    mode = sys.argv[1]
    contract = str(Path(sys.argv[2]).resolve())
    file_sha = hashlib.sha256(Path(contract).read_bytes()).hexdigest()[:12]
    key = f"{TASK}_{mode}_{file_sha}"
    claims = ROOT / "claims"
    logs = ROOT / "logs"
    claims.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    claim = claims / key
    log = logs / f"{key}.log"
    try:
        claim_handle = claim.open("x", encoding="utf-8")
        log_handle = log.open("x", encoding="utf-8")
    except FileExistsError:
        print(f"CLAIM_EXISTS {key}")
        return 9
    argv = [sys.executable, "-m", "r9_formal_executor", mode, "--contract", contract]
    started = datetime.now(timezone.utc)
    claim_handle.write(json.dumps({
        "task_id": TASK,
        "mode": mode,
        "launcher_pid": os.getpid(),
        "argv": argv,
        "start_utc": started.isoformat(),
    }, ensure_ascii=False) + "\n")
    claim_handle.flush()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    child = subprocess.Popen(
        argv, cwd=WORK, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", env=env,
    )
    claim_handle.write(f"child_pid={child.pid}\n")
    claim_handle.flush()
    out, err = child.communicate()
    log_handle.write(out or "")
    if err:
        log_handle.write("\n--- stderr ---\n")
        log_handle.write(err)
    log_handle.close()
    ended = datetime.now(timezone.utc)
    record = {
        "task_id": TASK,
        "mode": mode,
        "launcher_pid": os.getpid(),
        "child_pid": child.pid,
        "exit": child.returncode,
        "start_utc": started.isoformat(),
        "end_utc": ended.isoformat(),
        "start_cst": started.astimezone(CST).isoformat(),
        "end_cst": ended.astimezone(CST).isoformat(),
        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        "retried": False,
    }
    (claims / f"{key}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    claim_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    claim_handle.close()
    print(json.dumps({"exit": child.returncode, "child_pid": child.pid, "log": str(log)}, ensure_ascii=False))
    return int(child.returncode or 0)


if __name__ == "__main__":
    sys.exit(main())
