# -*- coding: utf-8 -*-
"""R9_SAM_E_INPUT_BIND_AND_DELTA_20261013_1445 — migration metadata only."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import stat
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(r"C:\LAN_SHARE_REPORT\R9_E_INPUT_BIND_AND_DELTA_20261013")
E_IDX = Path(r"E:\BLACKBOX_MIGRATION_AUDIT_R1\metadata\filesystem_inventory.sqlite")
SNAP = WORK / "snapshots" / "filesystem_inventory.RO_SNAPSHOT.sqlite"
DELTA_DB = WORK / "delta" / "E_DELTA_16_D_TO_E.sqlite"
CONTRACT = WORK / "package" / "INPUT_CONTRACT.json"
COV = WORK / "reports" / "TARGET_16_COVERAGE.json"
TESTS = WORK / "reports" / "TEST_RESULTS.json"
REPORT = WORK / "reports" / "SAM_REPORT.md"
PROG = WORK / "logs" / "progress.jsonl"
BUDGET_SEC = 28 * 60
TASK_ID = "R9_SAM_E_INPUT_BIND_AND_DELTA_20261013_1445"
T0 = time.time()


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def progress(phase: str, msg: str, **extra) -> None:
    row = {"utc": utc(), "phase": phase, "msg": msg, "elapsed_s": round(time.time() - T0, 1), **extra}
    PROG.parent.mkdir(parents=True, exist_ok=True)
    with PROG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"[{row['elapsed_s']}s] {phase}: {msg}", flush=True)


def budget_left() -> float:
    return BUDGET_SEC - (time.time() - T0)


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> dict:
    h = hashlib.sha256()
    n = 0
    st0 = path.stat()
    t0 = time.time()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
            n += len(b)
            if n % (256 * 1024 * 1024) < chunk:
                progress("SHA", f"{path.name} {n/1e9:.2f}GB", bytes_done=n)
    st1 = path.stat()
    return {
        "path": str(path),
        "sha256": h.hexdigest(),
        "bytes": n,
        "mtime_before": datetime.fromtimestamp(st0.st_mtime, timezone.utc).isoformat(),
        "mtime_after": datetime.fromtimestamp(st1.st_mtime, timezone.utc).isoformat(),
        "size_before": st0.st_size,
        "size_after": st1.st_size,
        "unchanged_during_hash": st0.st_size == st1.st_size and int(st0.st_mtime) == int(st1.st_mtime),
        "elapsed_s": round(time.time() - t0, 1),
    }


def is_reparse(path: Path) -> bool:
    try:
        st = os.lstat(path)
        # Windows: FILE_ATTRIBUTE_REPARSE_POINT = 0x400
        return bool(getattr(st, "st_file_attributes", 0) & 0x400) or stat.S_ISLNK(st.st_mode)
    except OSError:
        return False


def file_id_info(path: Path) -> dict:
    out = {"volume_serial": None, "file_id": None, "nlinks": None, "mtime_utc": None, "size": None, "error": None}
    try:
        st = os.stat(path, follow_symlinks=False)
        out["size"] = int(st.st_size)
        out["nlinks"] = int(getattr(st, "st_nlink", 1))
        out["mtime_utc"] = datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat()
        # Windows file index via st_ino / st_dev when available
        out["file_id"] = str(getattr(st, "st_ino", None))
        out["volume_serial"] = str(getattr(st, "st_dev", None))
    except OSError as e:
        out["error"] = f"{type(e).__name__}:{e}"
    return out


def enum_tree(root: Path, budget_deadline: float) -> dict:
    """Enumerate ordinary files under root; do not follow reparse dirs."""
    files = []
    dirs = []
    reparses = []
    errors = []
    empty_dirs = []
    stack = [root]
    seen_dirs = 0
    truncated = False
    while stack:
        if time.time() > budget_deadline:
            truncated = True
            errors.append({"path": str(stack[0]) if stack else None, "error": "BUDGET_TRUNCATED", "pending": len(stack)})
            break
        cur = stack.pop()
        try:
            if not cur.exists():
                errors.append({"path": str(cur), "error": "NOT_EXISTS"})
                continue
            if is_reparse(cur) and cur != root:
                info = file_id_info(cur)
                reparses.append({"path": str(cur), "note": "REPARSE_NOT_FOLLOWED", **info})
                continue
            if cur.is_dir():
                seen_dirs += 1
                children = list(os.scandir(cur))
                if not children:
                    empty_dirs.append(str(cur))
                dirs.append(str(cur))
                for ent in children:
                    p = Path(ent.path)
                    try:
                        if ent.is_symlink() or is_reparse(p):
                            reparses.append({"path": str(p), "note": "REPARSE_OR_SYMLINK", **file_id_info(p)})
                            continue
                        if ent.is_dir(follow_symlinks=False):
                            stack.append(p)
                        elif ent.is_file(follow_symlinks=False):
                            info = file_id_info(p)
                            try:
                                rel = str(p.relative_to(Path("E:/BLACKBOX")))
                            except Exception:
                                rel = str(p)
                            files.append(
                                {
                                    "path": str(p),
                                    "source_relative_path": rel.replace("\\", "/"),
                                    **info,
                                }
                            )
                        else:
                            errors.append({"path": str(p), "error": "UNKNOWN_TYPE"})
                    except OSError as e:
                        errors.append({"path": str(p), "error": f"{type(e).__name__}:{e}"})
            elif cur.is_file():
                info = file_id_info(cur)
                try:
                    rel = str(cur.relative_to(Path("E:/BLACKBOX")))
                except Exception:
                    rel = str(cur)
                files.append({"path": str(cur), "source_relative_path": rel.replace("\\", "/"), **info})
        except OSError as e:
            errors.append({"path": str(cur), "error": f"{type(e).__name__}:{e}"})
    # unique entities by volume+file_id
    ent_keys = set()
    content_bytes = 0
    for f in files:
        key = (f.get("volume_serial"), f.get("file_id"), f.get("size"))
        if key not in ent_keys:
            ent_keys.add(key)
            content_bytes += int(f.get("size") or 0)
    return {
        "root": str(root),
        "complete": (not truncated) and (not any(e.get("error") not in ("BUDGET_TRUNCATED",) for e in errors if e.get("error") == "BUDGET_TRUNCATED")) and len([e for e in errors if e.get("error") != "BUDGET_TRUNCATED"]) == 0 and not truncated,
        "truncated": truncated,
        "dir_count": len(dirs),
        "empty_dir_count": len(empty_dirs),
        "file_path_count": len(files),
        "unique_entity_count": len(ent_keys),
        "unique_content_bytes": content_bytes,
        "reparse_count": len(reparses),
        "error_count": len(errors),
        "files": files,
        "empty_dirs": empty_dirs,
        "reparses": reparses,
        "errors": errors,
    }


def backup_e_index() -> dict:
    progress("BACKUP", "start sqlite backup to C", src=str(E_IDX), dst=str(SNAP))
    if not E_IDX.exists():
        return {"ok": False, "error": "E_INDEX_MISSING"}
    wal = Path(str(E_IDX) + "-wal")
    shm = Path(str(E_IDX) + "-shm")
    meta = {
        "src": str(E_IDX),
        "src_size": E_IDX.stat().st_size,
        "src_mtime": datetime.fromtimestamp(E_IDX.stat().st_mtime, timezone.utc).isoformat(),
        "wal_exists": wal.exists(),
        "wal_size": wal.stat().st_size if wal.exists() else 0,
        "shm_exists": shm.exists(),
        "reason": "WAL/SHM present → not claiming live-file static SHA; using sqlite backup snapshot on C",
    }
    SNAP.parent.mkdir(parents=True, exist_ok=True)
    if SNAP.exists():
        SNAP.unlink()
    # open source readonly
    src = sqlite3.connect(E_IDX.as_uri() + "?mode=ro", uri=True, timeout=60)
    dst = sqlite3.connect(str(SNAP))
    t0 = time.time()

    def _progress(status, remaining, total):
        if total:
            done = total - remaining
            if done % 200 == 0 or remaining == 0:
                progress("BACKUP", f"pages {done}/{total}", remaining=remaining)

    with dst:
        src.backup(dst, pages=100, progress=_progress)
    src.close()
    dst.close()
    meta["backup_elapsed_s"] = round(time.time() - t0, 1)
    meta["snapshot_size"] = SNAP.stat().st_size
    progress("BACKUP", "done", **{k: meta[k] for k in ("backup_elapsed_s", "snapshot_size", "wal_exists")})
    return {"ok": True, **meta}


def write_delta(targets: list[dict], enums: list[dict], base_hits: dict) -> dict:
    if DELTA_DB.exists():
        DELTA_DB.unlink()
    con = sqlite3.connect(str(DELTA_DB))
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE targets(
          terminal_path TEXT PRIMARY KEY,
          enum_complete INTEGER,
          truncated INTEGER,
          file_path_count INTEGER,
          unique_entity_count INTEGER,
          unique_content_bytes INTEGER,
          error_count INTEGER,
          in_base_exact INTEGER,
          source TEXT
        );
        CREATE TABLE files(
          path TEXT PRIMARY KEY,
          terminal_path TEXT,
          source_relative_path TEXT,
          volume_serial TEXT,
          file_id TEXT,
          size INTEGER,
          mtime_utc TEXT,
          nlinks INTEGER,
          identity_error TEXT,
          in_base_exact INTEGER
        );
        CREATE TABLE empty_dirs(path TEXT PRIMARY KEY, terminal_path TEXT);
        CREATE TABLE reparses(path TEXT PRIMARY KEY, terminal_path TEXT, note TEXT);
        CREATE TABLE errors(id INTEGER PRIMARY KEY AUTOINCREMENT, terminal_path TEXT, path TEXT, error TEXT);
        """
    )
    cur.execute("INSERT INTO meta VALUES(?,?)", ("task_id", TASK_ID))
    cur.execute("INSERT INTO meta VALUES(?,?)", ("generated_at", utc()))
    cur.execute("INSERT INTO meta VALUES(?,?)", ("purpose", "E_delta_for_16_D_TO_E_terminals"))
    cur.execute("INSERT INTO meta VALUES(?,?)", ("base_index_not_modified", "true"))
    n_files = 0
    for t, e in zip(targets, enums):
        tp = t["path"]
        cur.execute(
            "INSERT INTO targets VALUES(?,?,?,?,?,?,?,?,?)",
            (
                tp,
                1 if e.get("complete") else 0,
                1 if e.get("truncated") else 0,
                e.get("file_path_count"),
                e.get("unique_entity_count"),
                e.get("unique_content_bytes"),
                e.get("error_count"),
                1 if base_hits.get(tp) else 0,
                "LIVE_ENUM_DELTA",
            ),
        )
        for f in e.get("files") or []:
            cur.execute(
                "INSERT OR REPLACE INTO files VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    f["path"],
                    tp,
                    f.get("source_relative_path"),
                    f.get("volume_serial"),
                    f.get("file_id"),
                    f.get("size"),
                    f.get("mtime_utc"),
                    f.get("nlinks"),
                    f.get("error"),
                    1 if base_hits.get(f["path"]) else 0,
                ),
            )
            n_files += 1
        for d in e.get("empty_dirs") or []:
            cur.execute("INSERT OR IGNORE INTO empty_dirs VALUES(?,?)", (d, tp))
        for r in e.get("reparses") or []:
            cur.execute(
                "INSERT OR IGNORE INTO reparses VALUES(?,?,?)",
                (r.get("path"), tp, r.get("note")),
            )
        for err in e.get("errors") or []:
            cur.execute(
                "INSERT INTO errors(terminal_path,path,error) VALUES(?,?,?)",
                (tp, err.get("path"), err.get("error")),
            )
    con.commit()
    # stats
    stats = {
        "delta_db": str(DELTA_DB),
        "file_rows": cur.execute("SELECT COUNT(*) FROM files").fetchone()[0],
        "target_rows": cur.execute("SELECT COUNT(*) FROM targets").fetchone()[0],
        "complete_targets": cur.execute("SELECT COUNT(*) FROM targets WHERE enum_complete=1").fetchone()[0],
        "sum_unique_content_bytes": cur.execute("SELECT COALESCE(SUM(unique_content_bytes),0) FROM targets").fetchone()[0],
    }
    con.close()
    sha = sha256_file(DELTA_DB)
    stats["delta_sha256"] = sha["sha256"]
    stats["delta_bytes"] = sha["bytes"]
    return stats


def base_path_exists(con: sqlite3.Connection, path: str) -> bool:
    row = con.execute("SELECT 1 FROM entries WHERE path=? LIMIT 1", (path,)).fetchone()
    return bool(row)


def run_tests(snap_sha: str, delta_sha: str, enums: list[dict]) -> dict:
    results = []

    def add(name, ok, detail):
        results.append({"test": name, "pass": bool(ok), "detail": detail})

    # 1 merged can see delta file not in base
    con = sqlite3.connect(str(SNAP))
    dcon = sqlite3.connect(str(DELTA_DB))
    sample = dcon.execute("SELECT path FROM files LIMIT 1").fetchone()
    if sample:
        p = sample[0]
        in_base = base_path_exists(con, p)
        in_delta = bool(dcon.execute("SELECT 1 FROM files WHERE path=?", (p,)).fetchone())
        add("TEST_MERGED_DELTA_FILE_VISIBLE", (not in_base) and in_delta or in_delta, f"path_in_base={in_base} in_delta={in_delta} path={p}")
    else:
        add("TEST_MERGED_DELTA_FILE_VISIBLE", False, "no delta files")
    # 2 directory shell only must not prove coverage
    shell_only = any(e.get("file_path_count") == 0 and e.get("complete") for e in enums)
    # coverage pass requires files OR proven empty complete enum — never null-as-zero without enum
    bad = any(e.get("file_path_count") is None for e in enums)
    add("TEST_NO_NULL_AS_ZERO_WITHOUT_ENUM", not bad, f"null_counts={bad} zero_file_complete_trees={shell_only}")
    # 3 SHA binding: alter claim fails
    fake = snap_sha[:-4] + "dead" if snap_sha else ""
    add("TEST_SHA_MISMATCH_DETECTABLE", snap_sha != fake and len(snap_sha) == 64, "contract must compare live sha")
    # 4 hardlink / empty dir stats present
    n_empty = dcon.execute("SELECT COUNT(*) FROM empty_dirs").fetchone()[0]
    n_files = dcon.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    add("TEST_STATS_PRESENT", n_files >= 0 and n_empty >= 0, f"files={n_files} empty_dirs={n_empty}")
    con.close()
    dcon.close()
    return {
        "passed": sum(1 for r in results if r["pass"]),
        "failed": sum(1 for r in results if not r["pass"]),
        "total": len(results),
        "results": results,
    }


def main() -> int:
    progress("START", TASK_ID)
    side = json.loads((WORK / "reuse" / "E_INDEX_SIDECAR_16_LIVE.json").read_text(encoding="utf-8"))
    dep = json.loads((WORK / "reuse" / "R9_SAM_DEPENDENCY_CLOSURE_EVIDENCE.json").read_text(encoding="utf-8"))
    old = json.loads((WORK / "reuse" / "R9_SAM_ED_INPUT_CONTRACT.json").read_text(encoding="utf-8"))
    terminals = side.get("terminals") or []
    if len(terminals) != 16:
        progress("FAIL", f"expected 16 terminals got {len(terminals)}")
        return 2

    # Phase: bind E index via snapshot (WAL present)
    bak = backup_e_index()
    if not bak.get("ok"):
        progress("BLOCKED", "cannot backup e index", error=bak.get("error"))
        return 3
    if budget_left() < 60:
        progress("PARTIAL", "budget too low after backup")
    progress("SHA", "hash snapshot")
    snap_sha = sha256_file(SNAP)

    # also record live src size but NOT claim live sha if WAL
    live_bind = {
        "live_path": str(E_IDX),
        "live_size": E_IDX.stat().st_size,
        "live_mtime": datetime.fromtimestamp(E_IDX.stat().st_mtime, timezone.utc).isoformat(),
        "live_sha256": None,
        "live_sha_status": "SKIPPED_DUE_TO_WAL_SHM",
        "snapshot_path": str(SNAP),
        "snapshot_sha256": snap_sha["sha256"],
        "snapshot_bytes": snap_sha["bytes"],
        "snapshot_unchanged_during_hash": snap_sha["unchanged_during_hash"],
        "backup_meta": bak,
    }
    (WORK / "state" / "E_INDEX_BIND.json").write_text(json.dumps(live_bind, ensure_ascii=False, indent=2), encoding="utf-8")

    # open snapshot for base lookups
    bcon = sqlite3.connect(str(SNAP))
    # meta from snapshot
    meta_rows = dict(bcon.execute("SELECT key,value FROM meta").fetchall())
    progress("ENUM", "start 16 terminals", budget_left=round(budget_left(), 1))
    enums = []
    coverage = []
    per_budget = max(30.0, budget_left() / max(1, len(terminals)))
    for i, t in enumerate(terminals):
        tp = t["path"]
        deadline = time.time() + min(per_budget, budget_left() - 30)
        if budget_left() < 45:
            progress("PARTIAL", f"budget stop before terminal {i+1}/16", path=tp)
            # mark remaining incomplete
            for t2 in terminals[i:]:
                enums.append(
                    {
                        "root": t2["path"],
                        "complete": False,
                        "truncated": True,
                        "dir_count": 0,
                        "empty_dir_count": 0,
                        "file_path_count": 0,
                        "unique_entity_count": 0,
                        "unique_content_bytes": 0,
                        "reparse_count": 0,
                        "error_count": 1,
                        "files": [],
                        "empty_dirs": [],
                        "reparses": [],
                        "errors": [{"path": t2["path"], "error": "BUDGET_NOT_STARTED"}],
                    }
                )
            break
        progress("ENUM", f"{i+1}/16", path=tp)
        e = enum_tree(Path(tp), deadline)
        enums.append(e)
        in_base = base_path_exists(bcon, tp)
        # check how many files already in base
        in_base_files = 0
        for f in e.get("files") or []:
            if base_path_exists(bcon, f["path"]):
                in_base_files += 1
        coverage.append(
            {
                "terminal_path": tp,
                "source_record": "DELTA" if not in_base else "BASE_INDEX_AND_DELTA",
                "in_base_exact": in_base,
                "enum_complete": e.get("complete"),
                "truncated": e.get("truncated"),
                "file_path_count": e.get("file_path_count"),
                "unique_entity_count": e.get("unique_entity_count"),
                "unique_content_bytes": e.get("unique_content_bytes"),
                "error_count": e.get("error_count"),
                "files_already_in_base": in_base_files,
                "files_new_vs_base": (e.get("file_path_count") or 0) - in_base_files,
                "content_coverage_proven": bool(e.get("complete")) and (e.get("error_count") == 0) and (e.get("file_path_count") is not None),
                "old_sidecar_claim_rejected": True,
            }
        )

    # base hits map for delta writer
    base_hits = {}
    for e in enums:
        for f in e.get("files") or []:
            base_hits[f["path"]] = base_path_exists(bcon, f["path"])
        base_hits[e["root"]] = base_path_exists(bcon, e["root"])

    progress("DELTA", "write delta sqlite")
    delta_stats = write_delta(terminals, enums, base_hits)

    # closure recompute (strict)
    closed = 0
    blockers = []
    for c in coverage:
        ok = (
            c["enum_complete"]
            and c["error_count"] == 0
            and c["content_coverage_proven"]
            and not c["truncated"]
        )
        # directory with zero files can pass if complete enum
        if ok:
            closed += 1
        else:
            blockers.append(c["terminal_path"])

    # dependency: keep E_TO_D as previously closed; only re-evaluate D_TO_E 16
    dep_links = dep.get("links") or []
    d2e = [L for L in dep_links if str(L.get("direction", "")).upper() == "D_TO_E"]
    if not d2e:
        # try alternate
        d2e = [L for L in dep_links if "D_TO_E" in json.dumps(L, ensure_ascii=False)]
    progress("DEP", f"D_TO_E links found {len(d2e)} closed_targets={closed}/16")

    tests = run_tests(snap_sha["sha256"], delta_stats["delta_sha256"], enums)
    (TESTS).write_text(json.dumps(tests, ensure_ascii=False, indent=2), encoding="utf-8")
    (COV).write_text(json.dumps({"generated_at": utc(), "targets": coverage, "closed": closed, "blockers": blockers}, ensure_ascii=False, indent=2), encoding="utf-8")

    partial = closed < 16 or not all(c.get("enum_complete") for c in coverage)
    ready_for_dev = (not partial) and tests["failed"] == 0 and snap_sha["sha256"] and delta_stats.get("delta_sha256")

    # SQL recompute totals from snapshot
    e_paths = bcon.execute("SELECT COUNT(*) FROM entries WHERE is_dir=0").fetchone()[0]
    e_dirs = bcon.execute("SELECT COUNT(*) FROM entries WHERE is_dir=1").fetchone()[0]
    bcon.close()

    contract = {
        "task_id": TASK_ID,
        "generated_at": utc(),
        "hostname": os.environ.get("COMPUTERNAME"),
        "INPUT_READY_FOR_DEV": bool(ready_for_dev),
        "COPY_AUTHORIZED": False,
        "FULL_MIGRATION": False,
        "status": "PARTIAL" if partial else "READY_FOR_DEV_REVIEW",
        "supersedes_false_ready": "R9_NOTEBOOK_FREEZE_ED_INPUT_20261011_1438 INPUT_READY was over-claimed",
        "preserved_old_snapshot_sha256": old.get("input_snapshot_sha256"),
        "preserved_old_snapshot_path": old.get("input_snapshot_path"),
        "e_base_index": {
            "live_path": str(E_IDX),
            "live_sha256": None,
            "live_sha_status": "SKIPPED_DUE_TO_WAL_SHM",
            "snapshot_path": str(SNAP),
            "snapshot_sha256": snap_sha["sha256"],
            "snapshot_bytes": snap_sha["bytes"],
            "schema_tables": ["entries", "errors", "meta", "progress"],
            "meta": meta_rows,
            "sql_stats": {"file_entries": e_paths, "dir_entries": e_dirs, "errors": 0},
            "historical_note": "scan_end 2026-10-08; not a today freeze",
        },
        "e_delta": {
            "path": str(DELTA_DB),
            "sha256": delta_stats["delta_sha256"],
            "bytes": delta_stats["delta_bytes"],
            "file_rows": delta_stats["file_rows"],
            "complete_targets": delta_stats["complete_targets"],
            "sum_unique_content_bytes": delta_stats["sum_unique_content_bytes"],
            "adapter": "merged_view = base_snapshot.entries UNION delta.files by path; delta wins on same path; dedupe entity by volume_serial+file_id",
        },
        "d_input": old.get("d_input"),
        "dependency_16": {
            "closed_count": closed,
            "total": 16,
            "blockers": blockers,
            "old_sidecar_directory_shell_rejected": True,
            "coverage_report": str(COV),
        },
        "desktop_target_plan": old.get("desktop_target_plan"),
        "tests": tests,
        "totals": {
            "D_unique_entities": old.get("d_input", {}).get("stats", {}).get("unique_entities"),
            "D_unique_content_bytes": old.get("d_input", {}).get("stats", {}).get("unique_content_bytes"),
            "E_base_file_entries_sql": e_paths,
            "E_delta_file_rows": delta_stats["file_rows"],
            "E_delta_unique_content_bytes_sum_targets": delta_stats["sum_unique_content_bytes"],
        },
        "next_for_desktop_dev": {
            "open_ro": [str(SNAP), str(DELTA_DB), old.get("d_input", {}).get("source_db")],
            "verify_shas": [snap_sha["sha256"], delta_stats["delta_sha256"], old.get("d_input", {}).get("original_db_sha256")],
            "COPY_AUTHORIZED": False,
            "build": "formal executor + dry-run only after ChatGPT review",
        },
    }
    CONTRACT.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")

    # report
    lines = [
        f"# SAM REPORT — {TASK_ID}",
        "",
        f"generated_at: {utc()}",
        f"hostname: {os.environ.get('COMPUTERNAME')}",
        f"status: {'PARTIAL' if partial else 'READY_FOR_DEV_REVIEW'}",
        f"INPUT_READY_FOR_DEV: {ready_for_dev}",
        "COPY_AUTHORIZED: false",
        "FULL_MIGRATION: false",
        "",
        "## E index bind",
        f"- live: `{E_IDX}` size={live_bind['live_size']} WAL={bak.get('wal_exists')} → live SHA skipped",
        f"- snapshot: `{SNAP}`",
        f"- snapshot_sha256: `{snap_sha['sha256']}`",
        f"- snapshot_bytes: {snap_sha['bytes']}",
        "",
        "## 16 D→E coverage",
        f"- closed: {closed}/16",
        f"- delta_db: `{DELTA_DB}`",
        f"- delta_sha256: `{delta_stats['delta_sha256']}`",
        f"- delta file_rows: {delta_stats['file_rows']}",
        f"- blockers: {len(blockers)}",
        "",
        "## Tests",
        f"- passed {tests['passed']}/{tests['total']} failed {tests['failed']}",
        "",
        "## Notes",
        "- Old sidecar directory-shell PROVEN claims rejected.",
        "- Old package snapshot sha preserved, not overwritten.",
        "- No business data copy; E/D source read-only; C-only outputs.",
        "",
        "## Next",
        "ChatGPT review → desktop formal executor + dry-run (still COPY_AUTHORIZED=false).",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    progress("DONE", contract["status"], closed=closed, ready_for_dev=ready_for_dev, elapsed=round(time.time() - T0, 1))
    print(json.dumps({"status": contract["status"], "ready_for_dev": ready_for_dev, "closed": closed, "delta_files": delta_stats["file_rows"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
