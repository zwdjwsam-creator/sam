# -*- coding: utf-8 -*-
"""Wait for baseline recopy, then run source_reconcile_r1; periodic HUB upload."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORK = Path(r"C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014")
PY = Path(r"E:\BLACKBOX\.venv\Scripts\python.exe")
RECOPY_LOG = WORK / "logs" / "recopy_stdout.log"
RECOPY_PID = WORK / "state" / "recopy_pid.txt"
BASELINE = WORK / "baseline" / "SOURCE_BASELINE.sqlite"
EXPECT_SHA = "94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba"
EXPECT_BYTES = 6025072640
REPORT = WORK / "reports"
TZ = timezone(timedelta(hours=8))
UPLOAD_EVERY = 600  # seconds during reconcile


def now() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def write_running(note: str, **extra):
    REPORT.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": "R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014_2312",
        "status": "RUNNING",
        "hostname": __import__("socket").gethostname(),
        "pid": os.getpid(),
        "updated_at": now(),
        "BASELINE_VERIFIED": False,
        "SOURCE_ENUMERATION_COMPLETE": False,
        "SOURCE_METADATA_MATCH": False,
        "SOURCE_CURRENT_MATCH": False,
        "HISTORICAL_CONTENT_MATCH": "UNPROVEN",
        "SOURCE_SCAN_STABILITY": "UNPROVEN",
        "dirs_done": 0,
        "queue_pending": 0,
        "paths_enumerated": 0,
        "delta_counts": {},
        "notes": [note],
        "COPY_AUTHORIZED": False,
        "phase": extra.get("phase", "baseline_recopy"),
        **{k: v for k, v in extra.items() if k != "phase"},
    }
    (REPORT / "SOURCE_RECONCILE_SUMMARY.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md = f"""# SAM_REPORT — R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014_2312

- status: RUNNING
- phase: {payload.get('phase')}
- host: SAM
- supervisor_pid: {os.getpid()}
- updated_at: {now()}
- note: {note}
- BASELINE_VERIFIED: false (pending clean recopy+verify)
- HISTORICAL_CONTENT_MATCH: UNPROVEN
- COPY_AUTHORIZED: false
- ZHANGWEI: HOLD

Resume: `{PY} -u {WORK / 'src' / 'run_reconcile_supervisor_r1.py'}`
"""
    (REPORT / "SAM_REPORT.md").write_text(md, encoding="utf-8")


def upload():
    try:
        subprocess.check_call(
            [str(PY), "-u", str(WORK / "src" / "hub_upload_running_r1.py")],
            cwd=str(WORK),
        )
    except Exception as e:
        print(f"upload_fail:{type(e).__name__}:{e}", flush=True)


def wait_recopy(timeout_sec: int = 7200) -> bool:
    t0 = time.time()
    last_upload = 0.0
    while time.time() - t0 < timeout_sec:
        # check recopy process
        pid = None
        if RECOPY_PID.exists():
            try:
                pid = int(RECOPY_PID.read_text().strip())
            except Exception:
                pid = None
        alive = False
        if pid:
            try:
                os.kill(pid, 0)
                alive = True
            except OSError:
                alive = False
        # check log for success
        if RECOPY_LOG.exists():
            text = RECOPY_LOG.read_text(encoding="utf-8", errors="replace")
            if "'ok': True" in text or '"ok": True' in text:
                return True
            if "SRC_SIZE_MISMATCH" in text:
                write_running("RECOPY_SRC_SIZE_MISMATCH", phase="hard_block")
                return False
        size = BASELINE.stat().st_size if BASELINE.exists() else 0
        note = f"recopy alive={alive} pid={pid} local_bytes={size}/{EXPECT_BYTES}"
        print(note, flush=True)
        write_running(note, phase="baseline_recopy", recopy_pid=pid, local_bytes=size)
        if time.time() - last_upload > 300:
            upload()
            last_upload = time.time()
        if not alive and size > 0:
            # process ended — check result
            time.sleep(2)
            text = RECOPY_LOG.read_text(encoding="utf-8", errors="replace") if RECOPY_LOG.exists() else ""
            if "'ok': True" in text or '"ok": True' in text:
                return True
            # maybe still hashing finalize
            if size == EXPECT_BYTES and ("'ok': False" in text or '"ok": False' in text):
                write_running(f"RECOPY_SHA_FAIL log_tail={text[-500:]}", phase="hard_block")
                return False
            if size != EXPECT_BYTES and not alive:
                write_running(f"RECOPY_PROCESS_DIED size={size}", phase="hard_block")
                return False
        time.sleep(15)
    write_running("RECOPY_TIMEOUT", phase="hard_block")
    return False


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--start-recopy-if-missing",
        action="store_true",
        help="Only start a new recopy if none is alive AND baseline missing/bad. Default: wait only.",
    )
    args = ap.parse_args()

    WORK.joinpath("state").mkdir(parents=True, exist_ok=True)
    (WORK / "state" / "supervisor_pid.txt").write_text(str(os.getpid()), encoding="utf-8")
    write_running("supervisor started; waiting for baseline recopy", phase="baseline_recopy")
    upload()

    # If baseline already good, skip wait
    need_wait = True
    if BASELINE.exists() and BASELINE.stat().st_size == EXPECT_BYTES:
        # quick check if verify already done via recopy log
        if RECOPY_LOG.exists() and ("'ok': True" in RECOPY_LOG.read_text(encoding="utf-8", errors="replace")):
            need_wait = False

    if need_wait:
        alive = False
        if RECOPY_PID.exists():
            try:
                os.kill(int(RECOPY_PID.read_text().strip()), 0)
                alive = True
            except Exception:
                alive = False
        if not alive and args.start_recopy_if_missing:
            print("starting recopy (explicit flag)...", flush=True)
            p = subprocess.Popen(
                [str(PY), "-u", str(WORK / "src" / "recopy_baseline_sha_r1.py")],
                cwd=str(WORK),
                stdout=open(RECOPY_LOG, "a", encoding="utf-8"),
                stderr=subprocess.STDOUT,
            )
            RECOPY_PID.write_text(str(p.pid), encoding="utf-8")
        elif not alive:
            print("no alive recopy; waiting for external recopy or existing log success", flush=True)
        if not wait_recopy():
            upload()
            return 2

    write_running("baseline recopy OK; starting reconcile", phase="reconcile")
    upload()

    # Run reconcile as child (same process wait)
    log = open(WORK / "logs" / "reconcile_supervisor_child.log", "a", encoding="utf-8")
    proc = subprocess.Popen(
        [str(PY), "-u", str(WORK / "src" / "source_reconcile_r1.py"), "--mode", "run", "--report-every-sec", "120"],
        cwd=str(WORK),
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    (WORK / "state" / "reconcile_pid.txt").write_text(str(proc.pid), encoding="utf-8")
    last_upload = time.time()
    while True:
        rc = proc.poll()
        if rc is not None:
            break
        if time.time() - last_upload >= UPLOAD_EVERY:
            upload()
            last_upload = time.time()
        time.sleep(30)
    log.close()
    upload()  # final
    print(f"reconcile_exit={rc}", flush=True)
    return int(rc or 0)


if __name__ == "__main__":
    sys.exit(main())
