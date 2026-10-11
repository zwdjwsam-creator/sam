# -*- coding: utf-8 -*-
"""R2 resumable selected-root enumerator — repairs resume/stats/completion/config SHA."""
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
sys.path.insert(0, str(OUT))
import r9_pilot_common_r9fix as C  # noqa: E402
from pathutil_r2 import normalize_win_path, path_under  # noqa: E402

TZ = timezone(timedelta(hours=8))
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def now() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def canonical_config_sha(cfg: dict) -> str:
    obj = {k: v for k, v in cfg.items() if k != "config_sha256"}
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_config(cfg: dict) -> str:
    expect = canonical_config_sha(cfg)
    got = cfg.get("config_sha256")
    if got != expect:
        raise RuntimeError(f"CONFIG_SHA_MISMATCH got={got} expect={expect}")
    return expect


def connect(db: Path, rw: bool = True) -> sqlite3.Connection:
    con = sqlite3.connect(str(db)) if rw else sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    if rw:
        con.execute("pragma journal_mode=WAL")
        con.execute("pragma synchronous=FULL")
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
          enum_generation INTEGER,
          current_child INTEGER DEFAULT 1,
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
          enum_generation INTEGER,
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
          at TEXT,
          UNIQUE(path, kind, detail)
        );
        CREATE TABLE IF NOT EXISTS checkpoints(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          at TEXT,
          processed_dirs INTEGER,
          queue_pending INTEGER,
          queue_in_progress INTEGER,
          nodes INTEGER,
          note TEXT
        );
        """
    )
    # migrate columns if old schema
    cols = {r[1] for r in con.execute("pragma table_info(nodes)")}
    if "enum_generation" not in cols:
        con.execute("alter table nodes add column enum_generation INTEGER")
    if "current_child" not in cols:
        con.execute("alter table nodes add column current_child INTEGER DEFAULT 1")
    dcols = {r[1] for r in con.execute("pragma table_info(dir_enum)")}
    if "enum_generation" not in dcols:
        con.execute("alter table dir_enum add column enum_generation INTEGER")
    con.commit()


def meta_set(con, k, v):
    con.execute("insert or replace into meta(key,value) values(?,?)", (k, str(v)))


def meta_get(con, k, default=None):
    r = con.execute("select value from meta where key=?", (k,)).fetchone()
    return r[0] if r else default


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
        out["object_class"] = (
            "Reparse" if out["is_reparse"] else ("Directory" if out["is_dir"] else "File")
        )
        if out["is_reparse"]:
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
        if "GetFileInformation" in msg or "SOURCE_IS_REPARSE" in msg:
            out["identity_err"] = msg
        else:
            out["access_err"] = msg
    return out


def upsert_node(con, path, parent, name, info, generation: int, current_child: int = 1):
    con.execute(
        """
        insert into nodes(path,parent,name,is_dir,is_reparse,attrs,logical_size,volume_serial,file_id,nlinks,
          mtime_ft,mtime_iso,identity_err,access_err,object_class,enum_generation,current_child,updated_at)
        values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        on conflict(path) do update set
          parent=excluded.parent, name=excluded.name, is_dir=excluded.is_dir, is_reparse=excluded.is_reparse,
          attrs=excluded.attrs, logical_size=excluded.logical_size, volume_serial=excluded.volume_serial,
          file_id=excluded.file_id, nlinks=excluded.nlinks, mtime_ft=excluded.mtime_ft, mtime_iso=excluded.mtime_iso,
          identity_err=excluded.identity_err, access_err=excluded.access_err, object_class=excluded.object_class,
          enum_generation=excluded.enum_generation, current_child=excluded.current_child, updated_at=excluded.updated_at
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
            generation,
            current_child,
            now(),
        ),
    )


def enqueue(con, path: str):
    con.execute(
        "insert into queue(path,enqueued_at,status) values(?,?,?) "
        "on conflict(path) do update set status=CASE WHEN queue.status='done' THEN 'pending' ELSE queue.status END, "
        "enqueued_at=CASE WHEN queue.status='done' THEN excluded.enqueued_at ELSE queue.enqueued_at END",
        (path, now(), "pending"),
    )


def add_diff(con, path, kind, detail):
    con.execute(
        "insert or ignore into diffs(path,kind,detail,at) values(?,?,?,?)",
        (path, kind, detail, now()),
    )


def bind_volume_for_roots(roots: list[str], *, allow_unknown: bool) -> str:
    vols = set()
    for r in roots:
        info = identity_for_path(r)
        if info.get("volume_serial"):
            vols.add(str(info["volume_serial"]))
        elif info.get("is_reparse"):
            continue
        else:
            if not allow_unknown:
                raise RuntimeError(f"ROOT_VOLUME_UNKNOWN:{r}:{info.get('access_err') or info.get('identity_err')}")
    if not vols:
        if allow_unknown:
            return "SYNTH_OR_UNKNOWN"
        raise RuntimeError("SOURCE_VOLUME_UNKNOWN")
    if len(vols) > 1:
        raise RuntimeError(f"MULTI_VOLUME_ROOTS:{sorted(vols)}")
    return next(iter(vols))


def enum_one_dir(con, path: str, generation: int) -> str:
    started = now()
    before = identity_for_path(path)
    if before.get("access_err") and before.get("is_dir") is None:
        con.execute(
            "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,enum_generation,error) values(?,?,?,?,?,?,?,?,?)",
            (path, "ERROR", 0, started, now(), None, None, generation, before.get("access_err")),
        )
        return "ERROR"
    if before.get("identity_err") and not before.get("is_reparse"):
        con.execute(
            "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,enum_generation,error) values(?,?,?,?,?,?,?,?,?)",
            (path, "ERROR", 0, started, now(), None, None, generation, before.get("identity_err")),
        )
        return "ERROR"

    parent = str(Path(path).parent) if Path(path).parent != Path(path) else None
    upsert_node(con, path, parent, Path(path).name, before, generation, 1)

    if before.get("is_reparse"):
        con.execute(
            "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,enum_generation,error) values(?,?,?,?,?,?,?,?,?)",
            (path, "ENUM_DONE", 0, started, now(), before.get("mtime_ft"), before.get("mtime_ft"), generation, "REPARSE_NOT_FOLLOWED"),
        )
        return "ENUM_DONE"

    # mark previous children of this parent as not current until refreshed
    con.execute(
        "update nodes set current_child=0 where parent=? and path!=?",
        (path, path),
    )

    children: list[tuple[str, str]] = []
    try:
        with os.scandir(C.to_win_long_path(path)) as it:
            for ent in it:
                children.append((path.rstrip("\\") + "\\" + ent.name, ent.name))
    except OSError as e:
        con.execute(
            "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,enum_generation,error) values(?,?,?,?,?,?,?,?,?)",
            (path, "ERROR", 0, started, now(), before.get("mtime_ft"), None, generation, f"SCANDIR:{e}"),
        )
        return "ERROR"

    for child_path, name in children:
        info = identity_for_path(child_path)
        upsert_node(con, child_path, path, name, info, generation, 1)
        if info.get("is_dir") and not info.get("is_reparse"):
            enqueue(con, child_path)
        if (not info.get("is_dir")) and (not info.get("is_reparse")):
            if not info.get("file_id") or info.get("identity_err") or info.get("access_err"):
                add_diff(
                    con,
                    child_path,
                    "FILE_IDENTITY_UNRESOLVED",
                    info.get("identity_err") or info.get("access_err") or "missing_file_id",
                )

    # soft-delete: previous children not seen this generation
    for r in con.execute(
        "select path from nodes where parent=? and current_child=0",
        (path,),
    ):
        add_diff(con, r["path"], "DELETED_FROM_LIVE", f"missing after enum_generation={generation}")
        con.execute("delete from nodes where path=?", (r["path"],))

    after = identity_for_path(path)
    if after.get("access_err") or after.get("identity_err"):
        con.execute(
            "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,enum_generation,error) values(?,?,?,?,?,?,?,?,?)",
            (
                path,
                "ERROR",
                len(children),
                started,
                now(),
                before.get("mtime_ft"),
                after.get("mtime_ft"),
                generation,
                after.get("access_err") or after.get("identity_err"),
            ),
        )
        return "ERROR"
    if before.get("mtime_ft") and after.get("mtime_ft") and before["mtime_ft"] != after["mtime_ft"]:
        con.execute(
            "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,enum_generation,error) values(?,?,?,?,?,?,?,?,?)",
            (
                path,
                "PENDING_CHANGED",
                len(children),
                started,
                now(),
                before.get("mtime_ft"),
                after.get("mtime_ft"),
                generation,
                "DIR_MTIME_CHANGED_DURING_ENUM",
            ),
        )
        return "PENDING_CHANGED"

    con.execute(
        "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,enum_generation,error) values(?,?,?,?,?,?,?,?,?)",
        (
            path,
            "ENUM_DONE",
            len(children),
            started,
            now(),
            before.get("mtime_ft"),
            after.get("mtime_ft"),
            generation,
            None,
        ),
    )
    return "ENUM_DONE"


def compute_content_stats(con) -> dict:
    conflicts = con.execute(
        """
        select count(*) from (
          select volume_serial, file_id from nodes
          where is_dir=0 and is_reparse=0 and file_id is not null and volume_serial is not null
          group by volume_serial, file_id
          having count(distinct logical_size)>1 or count(distinct mtime_ft)>1
        )
        """
    ).fetchone()[0]
    entities = con.execute(
        """
        select count(*) from (
          select volume_serial, file_id from nodes
          where is_dir=0 and is_reparse=0 and file_id is not null and volume_serial is not null
            and identity_err is null and access_err is null and logical_size is not null
          group by volume_serial, file_id
          having count(distinct logical_size)=1 and count(distinct mtime_ft)=1
        )
        """
    ).fetchone()[0]
    bytes_ = con.execute(
        """
        select coalesce(sum(logical_size),0) from (
          select volume_serial, file_id, max(logical_size) as logical_size from nodes
          where is_dir=0 and is_reparse=0 and file_id is not null and volume_serial is not null
            and identity_err is null and access_err is null and logical_size is not null
          group by volume_serial, file_id
          having count(distinct logical_size)=1 and count(distinct mtime_ft)=1
        )
        """
    ).fetchone()[0]
    path_bytes = con.execute(
        """
        select coalesce(sum(logical_size),0) from nodes
        where is_dir=0 and is_reparse=0 and logical_size is not null
          and identity_err is null and access_err is null
        """
    ).fetchone()[0]
    return {
        "file_path_count": con.execute(
            "select count(*) from nodes where is_dir=0 and is_reparse=0"
        ).fetchone()[0],
        "dir_count": con.execute(
            "select count(*) from nodes where is_dir=1 and is_reparse=0"
        ).fetchone()[0],
        "reparse_count": con.execute("select count(*) from nodes where is_reparse=1").fetchone()[0],
        "unique_file_entities": entities,
        "unique_content_bytes": int(bytes_ or 0),
        "logical_path_bytes": int(path_bytes or 0),
        "fid_size_or_mtime_conflicts": conflicts,
        "sql_note": "unique_content_bytes = sum distinct (volume_serial,file_id) over normal files only; directories excluded",
    }


def snapshot_db_sha(db_path: Path, snap_path: Path) -> str:
    """Consistent snapshot via sqlite backup, then hash snapshot file."""
    if snap_path.exists():
        snap_path.unlink()
    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(snap_path))
    src.backup(dst)
    src.execute("pragma wal_checkpoint(FULL)")
    dst.close()
    src.close()
    h = hashlib.sha256()
    with open(snap_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_summary(con, cfg, config_sha, db_path, snap_sha, stop_reason, elapsed) -> dict:
    q = {
        s: con.execute("select count(*) from queue where status=?", (s,)).fetchone()[0]
        for s in ("pending", "in_progress", "done", "error")
    }
    dstat = {
        s: con.execute("select count(*) from dir_enum where status=?", (s,)).fetchone()[0]
        for s in ("ENUM_DONE", "ERROR", "PENDING_CHANGED")
    }
    roots_ok = True
    for r in cfg["enum_roots"]:
        st = con.execute("select status from dir_enum where path=?", (r["path"],)).fetchone()
        if not st or st[0] != "ENUM_DONE":
            roots_ok = False
    files_bad = con.execute(
        "select count(*) from nodes where is_dir=0 and is_reparse=0 and (file_id is null or identity_err is not null or access_err is not null)"
    ).fetchone()[0]
    content = compute_content_stats(con)
    enumeration_complete = (
        roots_ok
        and q["pending"] == 0
        and q["in_progress"] == 0
        and q["error"] == 0
        and dstat["ERROR"] == 0
        and dstat["PENDING_CHANGED"] == 0
        and stop_reason == "QUEUE_EMPTY"
    )
    identity_complete = files_bad == 0 and content["fid_size_or_mtime_conflicts"] == 0
    # dependency closure filled by caller/export; default unknown here
    dep_closed = bool(cfg.get("dependency_closure_closed", False))
    runtime_blockers = cfg.get("runtime_dependency_blockers") or []
    selected_proven = bool(
        enumeration_complete and identity_complete and dep_closed and not runtime_blockers
    )
    return {
        "generated_at": now(),
        "task_id": cfg.get("task_id"),
        "config_sha256": config_sha,
        "manifest_db": str(db_path),
        "manifest_snapshot_sha256": snap_sha,
        "stop_reason": stop_reason,
        "elapsed_sec": elapsed,
        "queue": q,
        "dir_enum": dstat,
        "roots_all_enum_done": roots_ok,
        "enumeration_complete": enumeration_complete,
        "identity_complete": identity_complete,
        "dependency_closure_closed": dep_closed,
        "runtime_dependency_blockers": runtime_blockers,
        "SELECTED_SCOPE_COVERAGE_PROVEN": selected_proven,
        "filesystem_coverage_selected_roots": enumeration_complete,
        "application_runtime_independence": "unknown" if runtime_blockers is None else (
            False if runtime_blockers else "unknown"
        ),
        "D_GLOBAL_COVERAGE_PROVEN": False,
        "FULL_MIGRATION": False,
        "content_stats": content,
        "nodes": con.execute("select count(*) from nodes").fetchone()[0],
        "generator": "selected_manifest_enumerator_r2",
    }


def run_batch(config_path: Path, db_path: Path, budget_sec: int | None = None) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    config_sha = verify_config(cfg)
    budget = int(budget_sec if budget_sec is not None else cfg.get("budget_sec", 1800))
    ck_every = int(cfg.get("checkpoint_every_sec", 300))
    synth = bool(cfg.get("synthetic", False))
    expected_host = cfg.get("required_hostname")
    host = __import__("socket").gethostname()
    if expected_host and host.upper() != str(expected_host).upper() and not synth:
        raise RuntimeError(f"HOST_MISMATCH live={host} required={expected_host}")

    roots = [r["path"] for r in cfg["enum_roots"]]
    for r in roots:
        # boundary: must be under declared source_root
        src_root = cfg.get("source_root")
        if src_root and not path_under(r, src_root) and not synth:
            raise RuntimeError(f"ROOT_OUTSIDE_SOURCE:{r}")

    t0 = time.time()
    con = connect(db_path, rw=True)
    init_db(con)

    # resume: in_progress -> pending
    con.execute("update queue set status='pending' where status='in_progress'")
    con.commit()

    vol = bind_volume_for_roots(roots, allow_unknown=synth)
    prev_sha = meta_get(con, "config_sha256")
    prev_vol = meta_get(con, "source_volume_serial")
    if prev_sha and prev_sha != config_sha:
        raise RuntimeError(f"CONFIG_SHA_MISMATCH_RESUME prev={prev_sha} now={config_sha}")
    if prev_vol and prev_vol != vol and prev_vol not in ("SYNTH_OR_UNKNOWN",) and vol not in ("SYNTH_OR_UNKNOWN",):
        raise RuntimeError(f"SOURCE_VOLUME_MISMATCH prev={prev_vol} now={vol}")
    if (not synth) and vol in ("UNKNOWN", "SYNTH_OR_UNKNOWN"):
        raise RuntimeError("PRODUCTION_VOLUME_UNKNOWN")

    meta_set(con, "config_sha256", config_sha)
    meta_set(con, "source_volume_serial", vol)
    meta_set(con, "source_host", host)
    if not meta_get(con, "batch_started_at"):
        meta_set(con, "batch_started_at", now())
    gen = int(meta_get(con, "enum_generation", "0") or 0)

    for r in roots:
        enqueue(con, r)
    con.commit()

    processed = int(meta_get(con, "processed_dirs", "0") or 0)
    stop_reason = "BUDGET_OR_COMPLETE"
    last_ck = t0

    while True:
        if time.time() - t0 >= budget:
            stop_reason = "BUDGET_REACHED"
            break
        row = con.execute(
            "select path from queue where status='pending' order by enqueued_at limit 1"
        ).fetchone()
        if not row:
            # if any in_progress left treat incomplete
            ip = con.execute("select count(*) from queue where status='in_progress'").fetchone()[0]
            stop_reason = "QUEUE_EMPTY" if ip == 0 else "IN_PROGRESS_REMAINING"
            break
        path = row["path"]
        gen += 1
        meta_set(con, "enum_generation", gen)
        con.execute("update queue set status='in_progress' where path=?", (path,))
        con.commit()
        try:
            status = enum_one_dir(con, path, gen)
            if status == "ENUM_DONE":
                con.execute("update queue set status='done' where path=?", (path,))
            elif status == "PENDING_CHANGED":
                con.execute("update queue set status='pending' where path=?", (path,))
            else:
                con.execute("update queue set status='error' where path=?", (path,))
            processed += 1
            meta_set(con, "processed_dirs", processed)
            con.commit()
        except Exception as e:
            con.execute(
                "insert or replace into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,enum_generation,error) values(?,?,?,?,?,?,?,?,?)",
                (path, "ERROR", 0, now(), now(), None, None, gen, f"EXC:{e}"),
            )
            con.execute("update queue set status='error' where path=?", (path,))
            con.commit()

        if time.time() - last_ck >= ck_every:
            qp = con.execute("select count(*) from queue where status='pending'").fetchone()[0]
            qi = con.execute("select count(*) from queue where status='in_progress'").fetchone()[0]
            nn = con.execute("select count(*) from nodes").fetchone()[0]
            con.execute(
                "insert into checkpoints(at,processed_dirs,queue_pending,queue_in_progress,nodes,note) values(?,?,?,?,?,?)",
                (now(), processed, qp, qi, nn, f"elapsed={int(time.time()-t0)}"),
            )
            con.commit()
            last_ck = time.time()
            print(json.dumps({"checkpoint": True, "pending": qp, "in_progress": qi, "nodes": nn}), flush=True)

    elapsed = round(time.time() - t0, 2)
    # checkpoint in-progress back to pending for crash safety before exit
    con.execute("update queue set status='pending' where status='in_progress'")
    con.commit()

    snap = db_path.with_suffix(".snapshot.sqlite")
    con.close()
    snap_sha = snapshot_db_sha(db_path, snap)
    con = connect(db_path, rw=True)
    summary = build_summary(con, cfg, config_sha, db_path, snap_sha, stop_reason, elapsed)
    meta_set(con, "last_summary_json", json.dumps(summary, ensure_ascii=False))
    con.commit()
    con.close()
    (OUT / "R9_SAM_MANIFEST_REPAIR_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--budget-sec", type=int, default=None)
    args = ap.parse_args(argv)
    try:
        summary = run_batch(args.config, args.db, args.budget_sec)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}:{e}"}, ensure_ascii=False), flush=True)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    ok = bool(summary.get("enumeration_complete")) and summary.get("queue", {}).get("error", 1) == 0
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
