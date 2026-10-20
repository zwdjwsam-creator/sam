# -*- coding: utf-8 -*-
"""Read-only EXPLAIN of acceptance MISSING_ENTITY SQL. Never runs the COUNT on production."""
from __future__ import annotations

import ctypes
import json
import sqlite3
import sys
from ctypes import wintypes
from datetime import datetime, timezone, timedelta
from pathlib import Path

STATE = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019\state\full_1938.sqlite")
OUT = Path(r"C:\LAN_SHARE_REPORT\R9_FULL_ACCEPTANCE_QUERY_PLAN_CHECK_20261020_0826")
PID = 17904

ORIGINAL_SQL = """
SELECT COUNT(*) FROM plan_entity p
WHERE NOT EXISTS (
    SELECT 1 FROM st.stage s WHERE s.kind='entity' AND s.phase='DONE' AND s.parent_key=p.entity_key
)
"""

CANDIDATE_SQL = """
SELECT COUNT(*) FROM plan_entity p
WHERE NOT EXISTS (
    SELECT 1 FROM st.stage s
    WHERE s.item_key = 'entity:' || p.entity_key
      AND s.kind='entity' AND s.phase='DONE' AND s.parent_key=p.entity_key
)
"""


class IO(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


def process_io(pid: int) -> dict:
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.restype = wintypes.HANDLE
    k.GetProcessIoCounters.argtypes = [wintypes.HANDLE, ctypes.POINTER(IO)]
    k.GetProcessIoCounters.restype = wintypes.BOOL
    h = k.OpenProcess(0x1000, False, pid)
    if not h:
        return {"status": "NOT_OBSERVED", "winerror": int(ctypes.get_last_error())}
    c = IO()
    ok = k.GetProcessIoCounters(h, ctypes.byref(c))
    k.CloseHandle(h)
    if not ok:
        return {"status": "NOT_OBSERVED", "winerror": int(ctypes.get_last_error())}
    return {
        "status": "OBSERVED",
        "read_transfer_bytes": int(c.ReadTransferCount),
        "write_transfer_bytes": int(c.WriteTransferCount),
        "read_operations": int(c.ReadOperationCount),
        "write_operations": int(c.WriteOperationCount),
    }


def explain(conn: sqlite3.Connection, sql: str) -> list[dict]:
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    # detail, parent, id, notused columns vary; dump as strings
    return [{"row": [str(x) for x in row]} for row in rows]


def main() -> None:
    now = datetime.now(timezone(timedelta(hours=8))).isoformat()
    report: dict = {
        "task_id": "R9_FULL_ACCEPTANCE_QUERY_PLAN_CHECK_20261020_0826",
        "observed_at": now,
        "sqlite_version": sqlite3.sqlite_version,
        "python": sys.version,
        "pid": PID,
        "original_sql": ORIGINAL_SQL.strip(),
        "candidate_sql": CANDIDATE_SQL.strip(),
        "count_executed_on_production": False,
    }
    # process
    import subprocess
    proc = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            f"$p=Get-CimInstance Win32_Process -Filter \"ProcessId={PID}\"; if($p){{$p.CreationDate.ToString('o')+'|'+$p.CommandLine}} else {{'GONE'}}",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    text = (proc.stdout or "").strip()
    report["process_line"] = text[:500]
    report["alive"] = text != "GONE" and "r9_formal_executor.py" in text and "20:47:10" in text.replace("/", "-")
    # CreationDate format may be localized; check argv separately
    report["alive"] = "r9_formal_executor.py" in text and "FULL_RESUME_CONTRACT.json" in text
    report["creation_contains_204710"] = "20:47:10" in text or "2026-10-19" in text
    report["io"] = process_io(PID) if report["alive"] else {"status": "NOT_OBSERVED"}
    stdout = OUT.parent / "R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037" / "execute.stdout.log"
    # fix path
    stdout = Path(r"C:\LAN_SHARE_REPORT\R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037\execute.stdout.log")
    stderr = Path(r"C:\LAN_SHARE_REPORT\R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037\execute.stderr.log")
    report["stdout_bytes"] = stdout.stat().st_size if stdout.exists() else None
    report["stderr_bytes"] = stderr.stat().st_size if stderr.exists() else None

    # schema from production readonly
    schema = {"status": "NOT_OBSERVED"}
    try:
        db = sqlite3.connect(f"file:{STATE.as_posix()}?mode=ro", uri=True, timeout=2)
        db.execute("PRAGMA query_only=ON")
        master = list(db.execute("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE tbl_name='stage' ORDER BY type, name"))
        indexes = list(db.execute("PRAGMA index_list(stage)"))
        index_info = {}
        for idx in indexes:
            name = idx[1]
            index_info[name] = list(db.execute(f"PRAGMA index_info({name})"))
        table_info = list(db.execute("PRAGMA table_info(stage)"))
        schema = {
            "status": "OBSERVED",
            "sqlite_master": [{"type": r[0], "name": r[1], "tbl_name": r[2], "sql": r[3]} for r in master],
            "table_info": [{"cid": r[0], "name": r[1], "type": r[2], "notnull": r[3], "pk": r[5]} for r in table_info],
            "index_list": [{"seq": r[0], "name": r[1], "unique": r[2], "origin": r[3], "partial": r[4]} for r in indexes],
            "index_info": {k: [{"seqno": r[0], "cid": r[1], "name": r[2]} for r in v] for k, v in index_info.items()},
        }
        db.close()
    except sqlite3.Error as exc:
        schema = {"status": "NOT_OBSERVED", "error": type(exc).__name__, "message": str(exc)[:200]}
    report["production_schema"] = schema

    # EXPLAIN with empty plan_entity + ATTACH production as ro
    plans = {"status": "NOT_OBSERVED"}
    try:
        mem = sqlite3.connect(":memory:")
        mem.execute(
            "CREATE TABLE plan_entity(entity_key TEXT PRIMARY KEY, dest_path TEXT, path_count INTEGER, logical_size INTEGER)"
        )
        # one dummy row so planner sees a non-empty outer table
        mem.execute("INSERT INTO plan_entity VALUES ('demo|1','C:\\\\x',1,1)")
        mem.execute(f"ATTACH DATABASE 'file:{STATE.as_posix()}?mode=ro' AS st")
        # force read-only on attached if possible
        original_plan = explain(mem, ORIGINAL_SQL)
        candidate_plan = explain(mem, CANDIDATE_SQL)
        mem.execute("DETACH DATABASE st")
        mem.close()
        plans = {
            "status": "OBSERVED",
            "method": "memory plan_entity + ATTACH production state mode=ro; EXPLAIN QUERY PLAN only",
            "original": original_plan,
            "candidate_item_key": candidate_plan,
        }
    except sqlite3.Error as exc:
        plans = {"status": "NOT_OBSERVED", "error": type(exc).__name__, "message": str(exc)[:300]}
        # fallback synthetic
        try:
            syn = sqlite3.connect(":memory:")
            syn.executescript(
                """
                CREATE TABLE plan_entity(entity_key TEXT PRIMARY KEY, dest_path TEXT, path_count INTEGER, logical_size INTEGER);
                CREATE TABLE stage(
                    item_key TEXT PRIMARY KEY, kind TEXT, phase TEXT, dest_path TEXT, sha256 TEXT,
                    file_id TEXT, volume_serial TEXT, object_type TEXT, link_target TEXT,
                    logical_size INTEGER, parent_key TEXT
                );
                INSERT INTO plan_entity VALUES ('a|1','C:\\\\x',1,1);
                """
            )
            # rewrite SQL to use stage not st.stage
            orig = ORIGINAL_SQL.replace("st.stage", "stage")
            cand = CANDIDATE_SQL.replace("st.stage", "stage")
            plans = {
                "status": "OBSERVED_SYNTHETIC_ONLY",
                "attach_error": type(exc).__name__,
                "original": explain(syn, orig),
                "candidate_item_key": explain(syn, cand),
            }
            syn.close()
        except sqlite3.Error as exc2:
            plans = {"status": "NOT_OBSERVED", "error": type(exc2).__name__}

    report["query_plans"] = plans
    text_blob = json.dumps(plans, ensure_ascii=False)
    report["original_shows_scan_s"] = "SCAN s" in text_blob or any(
        "SCAN" in " ".join(row.get("row", [])) and any(part == "s" or part.endswith(" s") or "TABLE s" in part for part in row.get("row", []))
        for row in plans.get("original", [])
        if isinstance(row, dict)
    )
    # simpler detection
    orig_text = " | ".join(" ".join(r.get("row", [])) for r in plans.get("original", []) if isinstance(r, dict))
    cand_text = " | ".join(" ".join(r.get("row", [])) for r in plans.get("candidate_item_key", []) if isinstance(r, dict))
    report["original_plan_text"] = orig_text
    report["candidate_plan_text"] = cand_text
    report["risk_confirmed"] = ("SCAN" in orig_text.upper() and "STAGE" in orig_text.upper()) or ("SCAN s" in orig_text) or ("SCAN TABLE stage" in orig_text.upper()) or ("SCAN s " in orig_text + " ")
    report["candidate_uses_search"] = "SEARCH" in cand_text.upper()

    (OUT / "QUERY_PLAN_RAW.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "alive": report["alive"],
        "sqlite": report["sqlite_version"],
        "schema": schema.get("status"),
        "plans": plans.get("status"),
        "original": orig_text[:300],
        "candidate": cand_text[:300],
        "risk": report["risk_confirmed"],
        "candidate_search": report["candidate_uses_search"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
