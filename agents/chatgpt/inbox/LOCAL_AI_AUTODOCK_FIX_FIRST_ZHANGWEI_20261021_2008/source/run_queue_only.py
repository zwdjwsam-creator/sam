# -*- coding: utf-8 -*-
"""QUEUE_ONLY watcher. Reads HUB staging, persists events, never types or presses Enter."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
HERE = Path(__file__).resolve().parent
STATE = HERE / "state"
LOGS = HERE / "logs"
QUEUE = STATE / "delivery_queue.json"
SEEN = STATE / "seen_events.json"
MUTEX = STATE / "notifier.lock"
MAIL = Path(r"E:\BLACKBOX\运行\外部大脑信箱")

# Direction-specific. Outbox/reviews repair tips must not be dropped for a LOCAL_AI prefix.
IGNORE_BOTH = ("PILOT_", "CURSOR_CLAIMED", "ACK_", "HEARTBEAT", "STATUS_PROGRESS")
IGNORE_INBOX = IGNORE_BOTH + (
    "LOCAL_AI_AUTODOCK",
    "LOCAL_AI_GEMMA_DIRECT_OPERATOR",
    "LOCAL_AI_TWO_WINDOW_HUB_NOTIFIER",
    "LOCAL_AI_HUB_TWO_SIGNAL_ONLY",
    "LOCAL_AI_INSTALL_GEMMA",
    "_hub_",
    "INBOX_FOR_CHATGPT",
)


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def log(msg: str) -> None:
    line = f"{now()} QUEUE_ONLY {msg}"
    print(line, flush=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    with (LOGS / "queue_only.out.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    r = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = r.stdout or ""
    return str(pid) in out and "No tasks" not in out


def acquire() -> bool:
    STATE.mkdir(parents=True, exist_ok=True)
    if MUTEX.exists():
        try:
            old = json.loads(MUTEX.read_text(encoding="utf-8"))
            if pid_alive(int(old.get("pid") or 0)):
                return False
        except Exception:
            pass
    MUTEX.write_text(
        json.dumps({"pid": os.getpid(), "at": now(), "mode": "QUEUE_ONLY"}, ensure_ascii=False),
        encoding="utf-8",
    )
    return True


def release() -> None:
    try:
        if MUTEX.exists():
            cur = json.loads(MUTEX.read_text(encoding="utf-8"))
            if int(cur.get("pid") or 0) == os.getpid():
                MUTEX.unlink()
    except Exception:
        pass


def sha1_file(p: Path) -> str:
    h = hashlib.sha1()
    h.update(p.read_bytes())
    return h.hexdigest()


def ignored(rel: str, direction: str) -> bool:
    u = rel.upper()
    parts = IGNORE_INBOX if direction == "CURSOR_TO_GPT" else IGNORE_BOTH
    return any(part.upper() in u for part in parts)


def scan(root_rel: str, direction: str) -> list[dict]:
    root = MAIL / root_rel.replace("/", "\\")
    out = []
    if not root.exists():
        return out
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".md", ".json"}:
            continue
        rel = str(p.relative_to(MAIL)).replace("\\", "/")
        if ignored(rel, direction):
            continue
        try:
            st = p.stat()
            out.append(
                {
                    "path": rel,
                    "sha1": sha1_file(p),
                    "size": st.st_size,
                    "mtime": int(st.st_mtime),
                }
            )
        except OSError:
            continue
    return out


def main() -> int:
    once = "--once" in sys.argv
    if not acquire():
        log("MUTEX_HELD")
        return 2
    try:
        baseline = STATE / "seen_events.baseline.json"
        if SEEN.exists() and not baseline.exists():
            baseline.write_bytes(SEEN.read_bytes())
        seen = {}
        if SEEN.exists():
            seen = json.loads(SEEN.read_text(encoding="utf-8"))
        objects = seen.setdefault("objects", {})
        queue = []
        if QUEUE.exists():
            queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        queued_keys = {(q.get("path"), q.get("sha1"), q.get("direction")) for q in queue}
        new_n = 0
        for direction, rel in (
            ("GPT_TO_CURSOR", "agents/chatgpt/outbox"),
            ("GPT_TO_CURSOR", "agents/chatgpt/reviews"),
            ("CURSOR_TO_GPT", "agents/chatgpt/inbox"),
        ):
            for item in scan(rel, direction):
                prev = objects.get(item["path"])
                if prev == item["sha1"]:
                    continue
                qk = (item["path"], item["sha1"], direction)
                if qk in queued_keys:
                    objects[item["path"]] = item["sha1"]
                    continue
                queue.append(
                    {
                        "at": now(),
                        "direction": direction,
                        "path": item["path"],
                        "sha1": item["sha1"],
                        "status": "QUEUED_NO_SEND",
                        "body": "HUB",
                    }
                )
                queued_keys.add(qk)
                objects[item["path"]] = item["sha1"]
                new_n += 1
        # Queue file first so a crash cannot mark seen without the event.
        tmp_q = QUEUE.with_suffix(".json.tmp")
        tmp_q.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_q.replace(QUEUE)
        tmp_s = SEEN.with_suffix(".json.tmp")
        tmp_s.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_s.replace(SEEN)
        (STATE / "STATUS_LIVE.json").write_text(
            json.dumps(
                {
                    "mode": "QUEUE_ONLY",
                    "at": now(),
                    "send_armed": False,
                    "new_this_cycle": new_n,
                    "queue_len": len(queue),
                    "once": once,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        log(f"new={new_n} queue={len(queue)} send=OFF")
        return 0
    finally:
        release()


if __name__ == "__main__":
    raise SystemExit(main())
