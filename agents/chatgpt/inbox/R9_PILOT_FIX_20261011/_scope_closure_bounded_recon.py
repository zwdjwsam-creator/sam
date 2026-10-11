# -*- coding: utf-8 -*-
"""Bounded read-only D coverage recon for R9_NOTEBOOK_SCOPE_CLOSURE — no full rescan."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ = timezone(timedelta(hours=8))
OUT = Path(r"C:\LAN_SHARE_REPORT\BLACKBOX_R9_FULL_INVENTORY")
DB = OUT / "D_VOLUME_FILESYSTEM_INVENTORY.sqlite"
BUDGET_SEC = 12 * 60  # well under 30m; leave time for reports
MAX_DEPTH_SAMPLE = 2
SAMPLE_CHILDREN_PER_DIR = 40


def now() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def long(p: str) -> str:
    if p.startswith("\\\\?\\"):
        return p
    if p.startswith("\\\\"):
        return "\\\\?\\UNC\\" + p[2:]
    return "\\\\?\\" + p


def main() -> int:
    t0 = time.time()
    report: dict = {
        "generated_at": now(),
        "task_id": "R9_NOTEBOOK_SCOPE_CLOSURE_20261011_1330",
        "hostname": __import__("socket").gethostname(),
        "D_GLOBAL_COVERAGE_PROVEN": False,
        "SELECTED_SCOPE_COVERAGE_PROVEN": False,
        "db_path": str(DB),
        "db_exists": DB.is_file(),
        "budget_sec": BUDGET_SEC,
        "truncation_history": {
            "mechanism": "early save_progress used stack[-5000:] — front of DFS stack could be dropped",
            "code_now": "save_progress persists full stack (see _scan_d_volume.py)",
            "which_checkpoints": "pre-fix checkpoints under D_SCAN_PROGRESS / pending_stack_json history; exact truncated checkpoint blobs not retained as separate archives on disk",
            "recoverable_via_missing_tops_gapfill": "only completely missing tops; RESUME_GAP_FILL.missing_tops=[]",
            "internal_gap_proof": "NOT_PROVEN — no live-scandir↔DB deep diff done; stack_len=0 insufficient",
        },
        "per_directory_completion_evidence": {
            "has_per_dir_success_ledger": False,
            "has_parent_child_edge_table": "UNKNOWN_UNTIL_SCHEMA",
            "what_exists": "entries rows + progress JSON stack_len=0 COMPLETED_STACK_EMPTY",
            "cannot_treat_as": "per-directory enumeration completion certificate",
        },
        "roots": [],
        "errors_disposition": [],
        "bounded_recon": {"sampled_dirs": 0, "mismatches": [], "access_skips": [], "queue": []},
        "schema": {},
        "stop_reason": None,
    }

    if not DB.is_file():
        report["stop_reason"] = "DB_MISSING"
        (OUT / "R9_SAM_D_COVERAGE_RECONCILIATION.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return 2

    report["db_sha256"] = sha256_file(DB)
    report["db_bytes"] = DB.stat().st_size
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    tables = [r[0] for r in con.execute("select name from sqlite_master where type='table' order by 1")]
    report["schema"]["tables"] = tables
    cols = {}
    for t in tables:
        cols[t] = [r[1] for r in con.execute(f"pragma table_info({t})")]
    report["schema"]["columns"] = cols
    # rough counts
    for t in tables:
        try:
            report["schema"][f"count_{t}"] = con.execute(f"select count(*) from {t}").fetchone()[0]
        except Exception as e:
            report["schema"][f"count_{t}"] = f"ERR:{e}"

    # load prior root coverage if present
    root_cov_path = OUT / "D_ROOT_COVERAGE.json"
    root_cov = json.loads(root_cov_path.read_text(encoding="utf-8")) if root_cov_path.exists() else {}

    # classify buckets from snapshot
    class_path = OUT / "D_CLASSIFICATION_SNAPSHOT.json"
    classification = json.loads(class_path.read_text(encoding="utf-8")) if class_path.exists() else {}

    # live tops
    live_tops = []
    try:
        with os.scandir("D:\\") as it:
            for ent in it:
                live_tops.append(
                    {
                        "name": ent.name,
                        "is_dir": ent.is_dir(follow_symlinks=False),
                        "is_symlink": ent.is_symlink(),
                    }
                )
    except OSError as e:
        report["live_root_scan_error"] = str(e)

    # map prior roots
    prior_by_name = {r["name"]: r for r in root_cov.get("live_roots", [])}

    def bucket_for(name: str) -> str:
        for b, items in (classification.get("classification") or {}).items():
            for it in items:
                root = it.get("root") or ""
                if root.rstrip("\\").lower().endswith("\\" + name.lower()) or root.lower() == f"d:\\{name.lower()}":
                    return b
        return "UNCLASSIFIED"

    for top in live_tops:
        name = top["name"]
        prior = prior_by_name.get(name, {})
        bucket = bucket_for(name)
        entry = {
            "name": name,
            "bucket": bucket,
            "live_is_dir": top["is_dir"],
            "live_symlink": top["is_symlink"],
            "prior_in_db": prior.get("in_db"),
            "prior_files": prior.get("files_entries"),
            "prior_dirs": prior.get("dirs_entries"),
            "prior_unique_bytes": prior.get("unique_bytes"),
            "prior_junctions": prior.get("junctions"),
            "completion_evidence": "ROOT_IN_DB_AND_PROGRESS_COMPLETE_ONLY"
            if prior.get("in_db")
            else "MISSING_FROM_PRIOR_ROOT_COVERAGE",
            "status": None,
        }
        if name in ("System Volume Information",):
            entry["status"] = "EXCLUDED_SYSTEM_PROTECTED"
        elif name.startswith("$RECYCLE"):
            entry["status"] = "EXCLUDED_RECYCLE_PARTIAL"
        elif prior.get("in_db"):
            entry["status"] = "HAS_ROOT_ENUM_EVIDENCE_INTERNAL_UNPROVEN"
        else:
            entry["status"] = "NEEDS_REVIEW_NOT_IN_PRIOR"
        report["roots"].append(entry)

    # errors disposition
    for err in root_cov.get("errors", []):
        p = err.get("path", "")
        disp = "KEEP_AS_RECORDED"
        if "System Volume Information" in p or "$RECYCLE.BIN" in p:
            disp = "EXCLUDE_SYSTEM"
        elif "test_value_counts.py" in p:
            disp = "POINT_RETRY_CANDIDATE"
        report["errors_disposition"].append({**err, "disposition": disp})

    # point retry identity fail file
    retry_path = (
        r"D:\CURSOR_TASK_ARCHIVE\XUEQIU_PUBLIC_PORTFOLIO_LOGIC_INFERENCE_R1\scripts\.venv\Lib\site-packages\pandas\tests\series\methods\test_value_counts.py"
    )
    retry = {"path": retry_path, "attempted": False}
    try:
        if os.path.exists(long(retry_path)):
            retry["attempted"] = True
            st = os.stat(long(retry_path))
            retry["exists"] = True
            retry["size"] = int(st.st_size)
            # open via CreateFile would need ctypes; size alone is bounded proof of existence
            retry["result"] = "EXISTS_STAT_OK_IDENTITY_API_NOT_REPEATED"
        else:
            retry["exists"] = False
            retry["result"] = "PATH_MISSING_NOW"
    except OSError as e:
        retry["result"] = f"STAT_FAIL:{e}"
    report["identity_point_retry"] = retry

    # bounded sample: REQUIRED tops, depth<=2, compare child names subset vs DB path prefix
    required_roots = [
        it["root"] for it in (classification.get("classification") or {}).get("REQUIRED", [])
    ]
    queue = []
    mismatches = []
    access_skips = []
    sampled = 0

    # detect entries table shape
    entry_table = None
    path_col = None
    for t, c in cols.items():
        cl = [x.lower() for x in c]
        if "path" in cl and t.lower() in ("entries", "files", "paths", "nodes"):
            entry_table = t
            path_col = c[cl.index("path")]
            break
    if entry_table is None:
        for t, c in cols.items():
            cl = [x.lower() for x in c]
            if "path" in cl:
                entry_table = t
                path_col = c[cl.index("path")]
                break
    report["schema"]["entries_table"] = entry_table
    report["schema"]["path_col"] = path_col

    def db_has_child(prefix: str, child: str) -> bool | None:
        if not entry_table or not path_col:
            return None
        exact = prefix.rstrip("\\") + "\\" + child
        like = exact + "\\%"
        n = con.execute(
            f"select 1 from {entry_table} where {path_col}=? or {path_col} like ? limit 1",
            (exact, like),
        ).fetchone()
        return n is not None

    for root in required_roots:
        if time.time() - t0 > BUDGET_SEC:
            report["stop_reason"] = "BUDGET"
            break
        if not os.path.isdir(long(root)):
            access_skips.append({"path": root, "reason": "NOT_DIR_OR_MISSING"})
            continue
        # BFS limited
        qdirs = [(root, 0)]
        while qdirs and time.time() - t0 <= BUDGET_SEC:
            cur, depth = qdirs.pop(0)
            sampled += 1
            try:
                live_names = []
                with os.scandir(long(cur)) as it:
                    for i, ent in enumerate(it):
                        if i >= SAMPLE_CHILDREN_PER_DIR:
                            break
                        if ent.is_symlink():
                            continue
                        live_names.append(ent.name)
                        if ent.is_dir(follow_symlinks=False) and depth + 1 <= MAX_DEPTH_SAMPLE:
                            qdirs.append((str(Path(cur) / ent.name), depth + 1))
            except OSError as e:
                access_skips.append({"path": cur, "reason": str(e)})
                queue.append({"path": cur, "reason": "ACCESS_DENIED_OR_ENUM_FAIL", "action": "SKIP_NO_ELEVATION"})
                continue
            missing_in_db = []
            for name in live_names:
                has = db_has_child(cur, name)
                if has is None:
                    continue
                if not has:
                    missing_in_db.append(name)
            if missing_in_db:
                mismatches.append(
                    {
                        "dir": cur,
                        "sampled_live_children": len(live_names),
                        "missing_in_db_exact": missing_in_db[:20],
                        "note": "exact/prefix exists check; still not full-tree proof",
                    }
                )
                for m in missing_in_db[:10]:
                    queue.append(
                        {
                            "path": str(Path(cur) / m),
                            "reason": "LIVE_CHILD_NOT_IN_DB",
                            "action": "CANDIDATE_BOUNDED_RESUMABLE_ENUM",
                        }
                    )

    report["bounded_recon"]["sampled_dirs"] = sampled
    report["bounded_recon"]["mismatches"] = mismatches
    report["bounded_recon"]["access_skips"] = access_skips
    report["bounded_recon"]["queue"] = queue
    report["bounded_recon"]["elapsed_sec"] = round(time.time() - t0, 2)

    # SELECTED_SCOPE: REQUIRED roots have root-level evidence; still not internal-proven
    req_ok = all(
        r["status"] in ("HAS_ROOT_ENUM_EVIDENCE_INTERNAL_UNPROVEN", "EXCLUDED_SYSTEM_PROTECTED", "EXCLUDED_RECYCLE_PARTIAL")
        for r in report["roots"]
        if r["bucket"] == "REQUIRED"
    )
    report["SELECTED_SCOPE_COVERAGE_PROVEN"] = False  # internal unproven → must stay false
    report["SELECTED_SCOPE_ROOT_PRESENCE"] = bool(req_ok)
    report["D_GLOBAL_COVERAGE_PROVEN"] = False
    if report["stop_reason"] is None:
        report["stop_reason"] = "BOUNDED_RECON_DONE_NO_FULL_RESCAN"

    # persist full queue (no truncate)
    qpath = OUT / "R9_SAM_COVERAGE_RESUME_QUEUE.json"
    qpath.write_text(
        json.dumps(
            {
                "generated_at": now(),
                "queue_len": len(queue),
                "queue": queue,
                "note": "full queue persisted; do not truncate",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    report["resume_queue_path"] = str(qpath)
    report["resume_queue_len"] = len(queue)

    con.close()
    outp = OUT / "R9_SAM_D_COVERAGE_RECONCILIATION.json"
    outp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"wrote": str(outp), "queue": len(queue), "mismatches": len(mismatches), "sampled": sampled, "elapsed": report["bounded_recon"]["elapsed_sec"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
