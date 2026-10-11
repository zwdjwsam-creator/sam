# -*- coding: utf-8 -*-
"""
Resumable full metadata enum for selected D roots.
- No 40-child / depth-2 caps
- Long-path + REPARSE_POINT detection; record links, do not follow
- SQLite checkpoint; 30m budget; 5m checkpoints
- Read-only on E/D; writes only under C:\\LAN_SHARE_REPORT\\BLACKBOX_R9_SELECTED_MANIFEST
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"C:\LAN_SHARE_REPORT")
OUT = ROOT / "BLACKBOX_R9_SELECTED_MANIFEST"
INV = ROOT / "BLACKBOX_R9_FULL_INVENTORY"
sys.path.insert(0, str(ROOT))
import r9_pilot_common_r9fix as C  # noqa: E402

TZ = timezone(timedelta(hours=8))
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def now() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def connect(db: Path, rw: bool = True) -> sqlite3.Connection:
    if rw:
        con = sqlite3.connect(str(db))
    else:
        con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    con.execute("pragma journal_mode=WAL")
    con.execute("pragma synchronous=NORMAL")
    return con


def init_db(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS nodes(
          path TEXT PRIMARY KEY,
          parent TEXT,
          name TEXT,
          is_dir INTEGER,
          is_reparse INTEGER,
          attrs INTEGER,
          logical_size INTEGER,
          volume_serial TEXT,
          file_id TEXT,
          nlinks INTEGER,
          mtime_ft TEXT,
          mtime_iso TEXT,
          identity_err TEXT,
          access_err TEXT,
          object_class TEXT,
          updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS dir_enum(
          path TEXT PRIMARY KEY,
          status TEXT,
          child_count INTEGER,
          started_at TEXT,
          finished_at TEXT,
          before_mtime_ft TEXT,
          after_mtime_ft TEXT,
          error TEXT
        );
        CREATE TABLE IF NOT EXISTS queue(
          path TEXT PRIMARY KEY,
          enqueued_at TEXT,
          status TEXT
        );
        CREATE TABLE IF NOT EXISTS diffs(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          path TEXT,
          kind TEXT,
          detail TEXT,
          at TEXT
        );
        CREATE TABLE IF NOT EXISTS checkpoints(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          at TEXT,
          processed_dirs INTEGER,
          queue_len INTEGER,
          nodes INTEGER,
          note TEXT
        );
        """
    )
    con.commit()


def meta_set(con, k, v):
    con.execute("insert or replace into meta(key,value) values(?,?)", (k, str(v)))


def meta_get(con, k, default=None):
    r = con.execute("select value from meta where key=?", (k,)).fetchone()
    return r[0] if r else default


def get_vol_serial_d() -> str:
    # from known inventory / live
    try:
        # open D:\ root
        h = C.open_source_stable("D:\\")
        try:
            ident = C.handle_identity(h)
            return str(ident["volume_serial"])
        finally:
            C.safe_close(h)
    except Exception:
        return "UNKNOWN"


def classify_attrs(attrs: int) -> str:
    if attrs & FILE_ATTRIBUTE_REPARSE_POINT:
        return "Reparse"
    if attrs & FILE_ATTRIBUTE_DIRECTORY:
        return "Directory"
    return "File"


def identity_for_path(path: str) -> dict:
    out = {
        "attrs": None,
        "is_dir": None,
        "is_reparse": None,
        "logical_size": None,
        "volume_serial": None,
        "file_id": None,
        "nlinks": None,
        "mtime_ft": None,
        "mtime_iso": None,
        "identity_err": None,
        "access_err": None,
        "object_class": None,
    }
    try:
        attrs = C.get_attrs(path)
        out["attrs"] = attrs
        out["is_reparse"] = bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
        out["is_dir"] = bool(attrs & FILE_ATTRIBUTE_DIRECTORY)
        out["object_class"] = classify_attrs(attrs)
        if out["is_reparse"]:
            # record only; do not open-follow
            return out
        h = C.open_source_stable(path)
        try:
            ident = C.handle_identity(h)
            out["logical_size"] = ident["size"]
            out["volume_serial"] = ident["volume_serial"]
            out["file_id"] = ident["file_id"]
            out["nlinks"] = ident["nlinks"]
            out["mtime_ft"] = ident["mtime_ft"]
            try:
                out["mtime_iso"] = C.filetime_to_utc_datetime(ident["mtime_ft"]).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            except Exception:
                out["mtime_iso"] = None
        finally:
            C.safe_close(h)
    except Exception as e:
        msg = f"{type(e).__name__}:{e}"
        if "identity" in msg.lower() or "GetFileInformation" in msg:
            out["identity_err"] = msg
        else:
            out["access_err"] = msg
    return out


def upsert_node(con, path: str, parent: str | None, name: str, info: dict):
    con.execute(
        """
        insert into nodes(path,parent,name,is_dir,is_reparse,attrs,logical_size,volume_serial,file_id,nlinks,mtime_ft,mtime_iso,identity_err,access_err,object_class,updated_at)
        values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        on conflict(path) do update set
          parent=excluded.parent, name=excluded.name, is_dir=excluded.is_dir, is_reparse=excluded.is_reparse,
          attrs=excluded.attrs, logical_size=excluded.logical_size, volume_serial=excluded.volume_serial,
          file_id=excluded.file_id, nlinks=excluded.nlinks, mtime_ft=excluded.mtime_ft, mtime_iso=excluded.mtime_iso,
          identity_err=excluded.identity_err, access_err=excluded.access_err, object_class=excluded.object_class,
          updated_at=excluded.updated_at
        """,
        (
            path,
            parent,
            name,
            1 if info.get("is_dir") else 0,
            1 if info.get("is_reparse") else 0,
            info.get("attrs"),
            info.get("logical_size"),
            info.get("volume_serial"),
            info.get("file_id"),
            info.get("nlinks"),
            info.get("mtime_ft"),
            info.get("mtime_iso"),
            info.get("identity_err"),
            info.get("access_err"),
            info.get("object_class"),
            now(),
        ),
    )


def enqueue(con, path: str):
    con.execute(
        "insert or ignore into queue(path,enqueued_at,status) values(?,?,?)",
        (path, now(), "pending"),
    )


def load_old_index(selected_prefixes: list[str]) -> dict[str, dict]:
    """Exact path map from legacy inventory for selected prefixes only."""
    db = INV / "D_VOLUME_FILESYSTEM_INVENTORY.sqlite"
    if not db.is_file():
        return {}
    con = connect(db, rw=False)
    idx = {}
    for pref in selected_prefixes:
        p = pref.rstrip("\\")
        rows = con.execute(
            "select path,parent,name,is_dir,attrs,logical_size,volume_serial,file_id,mtime_utc,identity_err,reparse_tag from entries where path=? or path like ?",
            (p, p + "\\%"),
        )
        for r in rows:
            idx[r["path"]] = dict(r)
    con.close()
    return idx


def compare_with_old(con, old_idx: dict):
    # live nodes vs old
    for r in con.execute("select * from nodes"):
        p = r["path"]
        old = old_idx.get(p)
        if old is None:
            con.execute(
                "insert into diffs(path,kind,detail,at) values(?,?,?,?)",
                (p, "LIVE_NOT_IN_OLD_DB", "new or previously missed", now()),
            )
            continue
        # type
        old_dir = int(old["is_dir"] or 0)
        if int(r["is_dir"] or 0) != old_dir:
            con.execute(
                "insert into diffs(path,kind,detail,at) values(?,?,?,?)",
                (p, "TYPE_MISMATCH", f"live_dir={r['is_dir']} old_dir={old_dir}", now()),
            )
        if r["file_id"] and old.get("file_id") and str(r["file_id"]) != str(old["file_id"]):
            con.execute(
                "insert into diffs(path,kind,detail,at) values(?,?,?,?)",
                (p, "FILE_ID_DRIFT", f"live={r['file_id']} old={old['file_id']}", now()),
            )
        if r["logical_size"] is not None and old.get("logical_size") is not None:
            if int(r["logical_size"]) != int(old["logical_size"]):
                con.execute(
                    "insert into diffs(path,kind,detail,at) values(?,?,?,?)",
                    (p, "SIZE_DRIFT", f"live={r['logical_size']} old={old['logical_size']}", now()),
                )
    # old exact paths missing live — only for paths under completed ENUM_DONE parents ideally;
    # here: if parent ENUM_DONE and old child missing from nodes
    done_parents = {
        r["path"] for r in con.execute("select path from dir_enum where status='ENUM_DONE'")
    }
    for p, old in old_idx.items():
        parent = old.get("parent")
        if parent in done_parents:
            exists = con.execute("select 1 from nodes where path=?", (p,)).fetchone()
            if not exists:
                con.execute(
                    "insert into diffs(path,kind,detail,at) values(?,?,?,?)",
                    (p, "OLD_DB_NOT_IN_LIVE", "missing under ENUM_DONE parent", now()),
                )


def enum_one_dir(con, path: str) -> str:
    """Returns ENUM_DONE / ERROR / PENDING_CHANGED."""
    started = now()
    before = identity_for_path(path)
    upsert_node(con, path, str(Path(path).parent) if Path(path).parent != Path(path) else None, Path(path).name, before)
    if before.get("is_reparse"):
        con.execute(
            "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,error) values(?,?,?,?,?,?,?,?)",
            (path, "ENUM_DONE", 0, started, now(), before.get("mtime_ft"), before.get("mtime_ft"), "REPARSE_NOT_FOLLOWED"),
        )
        return "ENUM_DONE"
    if before.get("access_err") and before.get("is_dir") is None:
        con.execute(
            "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,error) values(?,?,?,?,?,?,?,?)",
            (path, "ERROR", 0, started, now(), None, None, before.get("access_err")),
        )
        return "ERROR"

    children = []
    try:
        with os.scandir(C.to_win_long_path(path)) as it:
            for ent in it:
                # use name; rebuild path without relying on ent.path short forms
                child_path = path.rstrip("\\") + "\\" + ent.name
                children.append((child_path, ent.name))
    except OSError as e:
        con.execute(
            "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,error) values(?,?,?,?,?,?,?,?)",
            (path, "ERROR", 0, started, now(), before.get("mtime_ft"), None, f"SCANDIR:{e}"),
        )
        return "ERROR"

    for child_path, name in children:
        info = identity_for_path(child_path)
        upsert_node(con, child_path, path, name, info)
        if info.get("is_dir") and not info.get("is_reparse"):
            enqueue(con, child_path)
        elif info.get("is_reparse"):
            # recorded as node; not enqueued
            pass
        else:
            # file: must have identity for normal files
            if not info.get("is_reparse") and not info.get("is_dir"):
                if not info.get("file_id") or info.get("identity_err"):
                    con.execute(
                        "insert into diffs(path,kind,detail,at) values(?,?,?,?)",
                        (child_path, "FILE_IDENTITY_UNRESOLVED", info.get("identity_err") or info.get("access_err") or "missing_file_id", now()),
                    )

    after = identity_for_path(path)
    status = "ENUM_DONE"
    err = None
    if before.get("mtime_ft") and after.get("mtime_ft") and before["mtime_ft"] != after["mtime_ft"]:
        status = "PENDING_CHANGED"
        err = "DIR_MTIME_CHANGED_DURING_ENUM"
    con.execute(
        "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,error) values(?,?,?,?,?,?,?,?)",
        (path, status, len(children), started, now(), before.get("mtime_ft"), after.get("mtime_ft"), err),
    )
    return status


def run_batch(config_path: Path, db_path: Path, budget_sec: int | None = None) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    config_sha = cfg.get("config_sha256") or hashlib.sha256(
        config_path.read_bytes()
    ).hexdigest()
    budget = int(budget_sec if budget_sec is not None else cfg.get("budget_sec", 1800))
    ck_every = int(cfg.get("checkpoint_every_sec", 300))

    con = connect(db_path, rw=True)
    init_db(con)

    # resume guards
    prev_sha = meta_get(con, "config_sha256")
    prev_vol = meta_get(con, "source_volume_serial")
    vol = get_vol_serial_d()
    if prev_sha and prev_sha != config_sha:
        raise RuntimeError(f"CONFIG_SHA_MISMATCH prev={prev_sha} now={config_sha}")
    if prev_vol and prev_vol != vol and prev_vol != "UNKNOWN" and vol != "UNKNOWN":
        raise RuntimeError(f"SOURCE_VOLUME_MISMATCH prev={prev_vol} now={vol}")

    meta_set(con, "config_sha256", config_sha)
    meta_set(con, "source_volume_serial", vol)
    meta_set(con, "source_host", __import__("socket").gethostname())
    if not meta_get(con, "batch_started_at"):
        meta_set(con, "batch_started_at", now())
    con.commit()

    # seed roots
    for root in cfg["enum_roots"]:
        p = root["path"]
        enqueue(con, p)
        # ensure root node
        info = identity_for_path(p)
        upsert_node(con, p, str(Path(p).parent), Path(p).name, info)
    con.commit()

    # load old index for prefixes
    prefixes = [r["path"] for r in cfg["enum_roots"]]
    old_idx = load_old_index(prefixes)

    t0 = time.time()
    last_ck = t0
    processed = int(meta_get(con, "processed_dirs", "0") or 0)
    stop_reason = "BUDGET_OR_COMPLETE"

    while True:
        elapsed = time.time() - t0
        if elapsed >= budget:
            stop_reason = "BUDGET_REACHED"
            break
        row = con.execute(
            "select path from queue where status='pending' order by enqueued_at limit 1"
        ).fetchone()
        if not row:
            stop_reason = "QUEUE_EMPTY"
            break
        path = row["path"]
        con.execute("update queue set status='in_progress' where path=?", (path,))
        con.commit()
        try:
            enum_one_dir(con, path)
            con.execute("update queue set status='done' where path=?", (path,))
            processed += 1
            meta_set(con, "processed_dirs", processed)
            con.commit()
        except Exception as e:
            con.execute(
                "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,error) values(?,?,?,?,?,?,?,?)",
                (path, "ERROR", 0, now(), now(), None, None, f"EXC:{e}"),
            )
            con.execute("update queue set status='error' where path=?", (path,))
            con.commit()

        if time.time() - last_ck >= ck_every:
            qlen = con.execute("select count(*) from queue where status='pending'").fetchone()[0]
            nnodes = con.execute("select count(*) from nodes").fetchone()[0]
            con.execute(
                "insert into checkpoints(at,processed_dirs,queue_len,nodes,note) values(?,?,?,?,?)",
                (now(), processed, qlen, nnodes, f"elapsed={int(time.time()-t0)}"),
            )
            meta_set(con, "last_checkpoint_at", now())
            con.commit()
            last_ck = time.time()
            print(
                json.dumps(
                    {"checkpoint": True, "processed_dirs": processed, "queue_pending": qlen, "nodes": nnodes},
                    ensure_ascii=False,
                ),
                flush=True,
            )

    # final compare
    compare_with_old(con, old_idx)
    con.commit()

    q_pending = con.execute("select count(*) from queue where status='pending'").fetchone()[0]
    q_error = con.execute("select count(*) from queue where status='error'").fetchone()[0]
    enum_done = con.execute("select count(*) from dir_enum where status='ENUM_DONE'").fetchone()[0]
    enum_err = con.execute("select count(*) from dir_enum where status='ERROR'").fetchone()[0]
    enum_chg = con.execute("select count(*) from dir_enum where status='PENDING_CHANGED'").fetchone()[0]
    nodes = con.execute("select count(*) from nodes").fetchone()[0]
    files_ok = con.execute(
        "select count(*) from nodes where is_dir=0 and is_reparse=0 and file_id is not null and identity_err is null"
    ).fetchone()[0]
    files_bad = con.execute(
        "select count(*) from nodes where is_dir=0 and is_reparse=0 and (file_id is null or identity_err is not null)"
    ).fetchone()[0]
    diffs = con.execute("select count(*) from diffs").fetchone()[0]
    unique_entities = con.execute(
        "select count(*) from (select distinct volume_serial, file_id from nodes where file_id is not null)"
    ).fetchone()[0]
    unique_bytes = con.execute(
        "select coalesce(sum(sz),0) from (select max(logical_size) sz from nodes where file_id is not null group by volume_serial, file_id)"
    ).fetchone()[0]

    # SELECTED_SCOPE_COVERAGE_PROVEN criteria
    roots_ok = True
    for r in cfg["enum_roots"]:
        st = con.execute("select status from dir_enum where path=?", (r["path"],)).fetchone()
        if not st or st[0] != "ENUM_DONE":
            # root might still be pending if budget
            roots_ok = False
    selected_proven = bool(
        roots_ok
        and q_pending == 0
        and enum_err == 0
        and enum_chg == 0
        and files_bad == 0
        and q_error == 0
    )
    # unknown deps boundary → overall false even if enum complete
    enumeration_complete = q_pending == 0 and stop_reason == "QUEUE_EMPTY"

    summary = {
        "generated_at": now(),
        "task_id": cfg.get("task_id"),
        "config_sha256": config_sha,
        "manifest_db": str(db_path),
        "manifest_db_sha256": sha_file(db_path) if db_path.exists() else None,
        "source_volume_serial": vol,
        "stop_reason": stop_reason,
        "elapsed_sec": round(time.time() - t0, 2),
        "processed_dirs": processed,
        "queue_pending": q_pending,
        "queue_error": q_error,
        "dir_enum_done": enum_done,
        "dir_enum_error": enum_err,
        "dir_enum_changed": enum_chg,
        "nodes": nodes,
        "files_identity_ok": files_ok,
        "files_identity_unresolved": files_bad,
        "diffs": diffs,
        "unique_entities": unique_entities,
        "unique_bytes": int(unique_bytes or 0),
        "enumeration_complete": enumeration_complete,
        "SELECTED_SCOPE_COVERAGE_PROVEN": selected_proven and enumeration_complete,
        "D_GLOBAL_COVERAGE_PROVEN": False,
        "FULL_MIGRATION": False,
        "schema": {
            "tables": ["meta", "nodes", "dir_enum", "queue", "diffs", "checkpoints"],
            "nodes_columns": [
                "path",
                "parent",
                "name",
                "is_dir",
                "is_reparse",
                "attrs",
                "logical_size",
                "volume_serial",
                "file_id",
                "nlinks",
                "mtime_ft",
                "mtime_iso",
                "identity_err",
                "access_err",
                "object_class",
            ],
        },
    }
    meta_set(con, "last_summary_json", json.dumps(summary, ensure_ascii=False))
    meta_set(con, "stop_reason", stop_reason)
    con.commit()
    con.close()
    # refresh sha after close
    summary["manifest_db_sha256"] = sha_file(db_path)
    (OUT / "R9_SAM_SELECTED_MANIFEST_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # resume state dump (full queue, no truncate)
    con = connect(db_path, rw=False)
    queue_rows = [dict(r) for r in con.execute("select * from queue order by enqueued_at")]
    con.close()
    (OUT / "R9_SAM_SELECTED_RESUME_STATE.json").write_text(
        json.dumps(
            {
                "generated_at": now(),
                "config_sha256": config_sha,
                "source_volume_serial": vol,
                "queue_len": len(queue_rows),
                "queue_truncated": False,
                "queue": queue_rows,
                "manifest_db": str(db_path),
                "manifest_db_sha256": summary["manifest_db_sha256"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=OUT / "R9_SAM_SELECTED_SCOPE_CONFIG.json")
    ap.add_argument("--db", type=Path, default=OUT / "SELECTED_D_MANIFEST.sqlite")
    ap.add_argument("--budget-sec", type=int, default=None)
    args = ap.parse_args(argv)
    summary = run_batch(args.config, args.db, args.budget_sec)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
