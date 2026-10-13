# -*- coding: utf-8 -*-
"""R9_SAM_METADATA_HANDOFF_20261013_1524 — upload migration metadata via HUB."""
from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT")
import r9_pilot_common_r9fix as r9  # noqa: E402

WORK = Path(r"C:\LAN_SHARE_REPORT\R9_SAM_METADATA_HANDOFF_20261013")
D_SRC = Path(r"C:\LAN_SHARE_REPORT\BLACKBOX_R9_SELECTED_MANIFEST\SELECTED_D_MANIFEST_REPAIRED.sqlite")
DELTA_SRC = Path(r"C:\LAN_SHARE_REPORT\R9_E_INPUT_BIND_AND_DELTA_20261013\delta\E_DELTA_16_D_TO_E.sqlite")
TASK_ID = "R9_SAM_METADATA_HANDOFF_20261013_1524"
BASELINE = {
    "file_paths": 34745,
    "unique_entities": 34744,
    "unique_content_bytes": 8163480337,
    "directories": 10637,
    "reparse": 16,
}
T0 = time.time()


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def progress(msg: str, **kw) -> None:
    row = {"utc": utc(), "elapsed_s": round(time.time() - T0, 1), "msg": msg, **kw}
    (WORK / "logs").mkdir(parents=True, exist_ok=True)
    with (WORK / "logs" / "progress.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False), flush=True)


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def backup_sqlite(src: Path, dst: Path) -> dict:
    if dst.exists():
        dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    s = sqlite3.connect(src.as_uri() + "?mode=ro", uri=True, timeout=60)
    d = sqlite3.connect(str(dst))
    with d:
        s.backup(d)
    s.close()
    d.close()
    return {"path": str(dst), "bytes": dst.stat().st_size, "sha256": sha256_file(dst)}


def d_stats(db: Path) -> dict:
    con = sqlite3.connect(str(db))
    cur = con.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    counts = {}
    for t in tables:
        try:
            counts[t] = cur.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        except Exception as e:
            counts[t] = f"ERR:{e}"
    # try common schemas
    stats = {"tables": tables, "counts": counts, "computed": {}, "diffs_vs_baseline": {}, "integrity_check": None}
    try:
        stats["integrity_check"] = cur.execute("PRAGMA integrity_check").fetchone()[0]
    except Exception as e:
        stats["integrity_check"] = f"ERR:{e}"

    # entities / paths heuristics from repaired manifest
    computed = {}
    if "entities" in tables:
        computed["unique_entities"] = cur.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        try:
            computed["unique_content_bytes"] = cur.execute(
                "SELECT COALESCE(SUM(size),0) FROM entities"
            ).fetchone()[0]
        except Exception:
            try:
                computed["unique_content_bytes"] = cur.execute(
                    "SELECT COALESCE(SUM(logical_size),0) FROM entities"
                ).fetchone()[0]
            except Exception as e:
                computed["unique_content_bytes_error"] = str(e)
    if "paths" in tables:
        computed["file_paths"] = cur.execute(
            "SELECT COUNT(*) FROM paths WHERE COALESCE(is_dir,0)=0"
        ).fetchone()[0]
        computed["directories"] = cur.execute(
            "SELECT COUNT(*) FROM paths WHERE COALESCE(is_dir,0)=1"
        ).fetchone()[0]
    # alternate: nodes
    if "nodes" in tables and "file_paths" not in computed:
        cols = [r[1] for r in cur.execute("PRAGMA table_info(nodes)")]
        if "is_dir" in cols:
            computed["file_paths"] = cur.execute("SELECT COUNT(*) FROM nodes WHERE is_dir=0").fetchone()[0]
            computed["directories"] = cur.execute("SELECT COUNT(*) FROM nodes WHERE is_dir=1").fetchone()[0]
        if "file_id" in cols and "volume_serial" in cols:
            computed["unique_entities"] = cur.execute(
                "SELECT COUNT(DISTINCT volume_serial || '|' || file_id) FROM nodes WHERE COALESCE(is_dir,0)=0"
            ).fetchone()[0]
            size_col = "size" if "size" in cols else ("logical_size" if "logical_size" in cols else None)
            if size_col:
                computed["unique_content_bytes"] = cur.execute(
                    f"""
                    SELECT COALESCE(SUM(sz),0) FROM (
                      SELECT MAX({size_col}) AS sz FROM nodes
                      WHERE COALESCE(is_dir,0)=0 AND volume_serial IS NOT NULL AND file_id IS NOT NULL
                      GROUP BY volume_serial, file_id
                    )
                    """
                ).fetchone()[0]
    if "reparse_links" in tables:
        computed["reparse"] = cur.execute("SELECT COUNT(*) FROM reparse_links").fetchone()[0]
    elif "reparses" in tables:
        computed["reparse"] = cur.execute("SELECT COUNT(*) FROM reparses").fetchone()[0]

    # identity unresolved
    unresolved = None
    for t, q in [
        ("entities", "SELECT COUNT(*) FROM entities WHERE volume_serial IS NULL OR file_id IS NULL OR volume_serial='' OR file_id=''"),
        ("nodes", "SELECT COUNT(*) FROM nodes WHERE COALESCE(is_dir,0)=0 AND (volume_serial IS NULL OR file_id IS NULL OR volume_serial='' OR file_id='')"),
    ]:
        if t in tables:
            try:
                unresolved = cur.execute(q).fetchone()[0]
                break
            except Exception:
                pass
    computed["unresolved_identity_rows"] = unresolved
    stats["computed"] = computed
    for k, v in BASELINE.items():
        cv = computed.get(k)
        if cv is not None and cv != v:
            stats["diffs_vs_baseline"][k] = {"baseline": v, "actual": cv}
    con.close()
    return stats


def win32_identity_twice(path: str) -> dict:
    h = r9.open_source_stable(path)
    try:
        a = r9.handle_identity(h)
        b = r9.handle_identity(h)
    finally:
        r9.CloseHandle(h)
    if (
        a["volume_serial_dword"] != b["volume_serial_dword"]
        or a["file_id"] != b["file_id"]
        or a["size"] != b["size"]
        or a["mtime_ft"] != b["mtime_ft"]
    ):
        raise RuntimeError(f"IDENTITY_UNSTABLE path={path}")
    # roots check
    root = Path(r"E:\BLACKBOX")
    p = Path(path)
    try:
        p.resolve().relative_to(root.resolve())
    except Exception as e:
        raise RuntimeError(f"OUTSIDE_DECLARED_ROOT path={path} err={e}") from e
    a["mtime_utc"] = r9.filetime_to_utc_datetime(int(a["mtime_ft"])).isoformat()
    a["path"] = path
    a["observed_twice_stable"] = True
    return a


def build_canonical_delta(src_delta: Path, dst: Path) -> dict:
    if dst.exists():
        dst.unlink()
    scon = sqlite3.connect(str(src_delta))
    files = scon.execute(
        "SELECT path, terminal_path, source_relative_path, volume_serial, file_id, size, mtime_utc, nlinks, identity_error FROM files ORDER BY path"
    ).fetchall()
    targets = scon.execute("SELECT * FROM targets").fetchall()
    target_cols = [d[0] for d in scon.execute("PRAGMA table_info(targets)")]
    empty_dirs = scon.execute("SELECT path, terminal_path FROM empty_dirs").fetchall()
    scon.close()

    dcon = sqlite3.connect(str(dst))
    cur = dcon.cursor()
    cur.executescript(
        """
        CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE targets(
          terminal_path TEXT PRIMARY KEY,
          enum_complete INTEGER,
          file_path_count INTEGER,
          unique_entity_count INTEGER,
          unique_content_bytes INTEGER,
          error_count INTEGER
        );
        CREATE TABLE files(
          path TEXT PRIMARY KEY,
          terminal_path TEXT,
          source_relative_path TEXT,
          volume_serial_dword INTEGER NOT NULL,
          file_id TEXT NOT NULL,
          size INTEGER NOT NULL,
          mtime_ft TEXT NOT NULL,
          mtime_utc TEXT,
          nlinks INTEGER,
          attrs INTEGER,
          allocation_size INTEGER,
          python_prev_volume_serial TEXT,
          python_prev_file_id TEXT,
          observed_twice_stable INTEGER NOT NULL
        );
        CREATE TABLE empty_dirs(path TEXT PRIMARY KEY, terminal_path TEXT);
        CREATE TABLE errors(id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT, error TEXT);
        CREATE UNIQUE INDEX ux_entity ON files(volume_serial_dword, file_id);
        """
    )
    cur.execute("INSERT INTO meta VALUES(?,?)", ("task_id", TASK_ID))
    cur.execute("INSERT INTO meta VALUES(?,?)", ("generated_at", utc()))
    cur.execute("INSERT INTO meta VALUES(?,?)", ("source_delta", str(src_delta)))
    cur.execute("INSERT INTO meta VALUES(?,?)", ("historical_delta_sha256", "9f1a37f945e80682a93190565e553bdef61bf8451b96216c2686c1d3e8887ad6"))
    cur.execute("INSERT INTO meta VALUES(?,?)", ("identity_api", "r9_pilot_common_r9fix.open_source_stable+handle_identity"))

    # targets
    for row in targets:
        rec = dict(zip(target_cols, row))
        cur.execute(
            "INSERT INTO targets VALUES(?,?,?,?,?,?)",
            (
                rec.get("terminal_path"),
                rec.get("enum_complete"),
                rec.get("file_path_count"),
                rec.get("unique_entity_count"),
                rec.get("unique_content_bytes"),
                rec.get("error_count"),
            ),
        )
    for p, tp in empty_dirs:
        cur.execute("INSERT OR IGNORE INTO empty_dirs VALUES(?,?)", (p, tp))

    errors = []
    ok = 0
    entity_map = {}
    for path, terminal_path, srel, pvol, pfid, psize, pmtime, pnlinks, perr in files:
        try:
            ident = win32_identity_twice(path)
            key = (ident["volume_serial_dword"], ident["file_id"])
            if key in entity_map:
                prev = entity_map[key]
                if prev["size"] != ident["size"] or prev["mtime_ft"] != ident["mtime_ft"]:
                    raise RuntimeError(
                        f"ENTITY_KEY_CONFLICT key={key} prev_size={prev['size']} size={ident['size']}"
                    )
            entity_map[key] = ident
            cur.execute(
                "INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    path,
                    terminal_path,
                    srel,
                    ident["volume_serial_dword"],
                    ident["file_id"],
                    ident["size"],
                    ident["mtime_ft"],
                    ident["mtime_utc"],
                    ident["nlinks"],
                    ident["attrs"],
                    ident["allocation_size"],
                    str(pvol) if pvol is not None else None,
                    str(pfid) if pfid is not None else None,
                    1,
                ),
            )
            ok += 1
        except Exception as e:
            errors.append({"path": path, "error": f"{type(e).__name__}:{e}"})
            cur.execute("INSERT INTO errors(path,error) VALUES(?,?)", (path, f"{type(e).__name__}:{e}"))
            progress("DELTA_ERR", path=path, error=str(e)[:200])

    dcon.commit()
    n_files = cur.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    n_targets = cur.execute("SELECT COUNT(*) FROM targets").fetchone()[0]
    null_ident = cur.execute(
        "SELECT COUNT(*) FROM files WHERE volume_serial_dword IS NULL OR file_id IS NULL OR file_id='' OR file_id='None'"
    ).fetchone()[0]
    # coverage: each target file_path_count vs actual files
    cov = []
    for (tp, want) in cur.execute("SELECT terminal_path, file_path_count FROM targets"):
        got = cur.execute("SELECT COUNT(*) FROM files WHERE terminal_path=?", (tp,)).fetchone()[0]
        cov.append({"terminal_path": tp, "declared": want, "canonical_files": got, "match": want == got})
    dcon.close()
    meta = {
        "path": str(dst),
        "bytes": dst.stat().st_size,
        "sha256": sha256_file(dst),
        "file_rows": n_files,
        "target_rows": n_targets,
        "error_rows": len(errors),
        "null_identity_rows": null_ident,
        "expected_files": 42,
        "expected_targets": 16,
        "coverage": cov,
        "errors": errors,
    }
    return meta


def gzip_one(src: Path, dst: Path) -> dict:
    if dst.exists():
        dst.unlink()
    with src.open("rb") as f_in, gzip.open(dst, "wb", compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out, length=8 * 1024 * 1024)
    return {"path": str(dst), "bytes": dst.stat().st_size, "sha256": sha256_file(dst), "inner_name": src.name}


def local_roundtrip_validate(gz: Path, expect_sha: str, expect_bytes: int, expect_stats: dict) -> dict:
    tmp = WORK / "validate" / "D_REPAIRED_SNAPSHOT.roundtrip.sqlite"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    if tmp.exists():
        tmp.unlink()
    with gzip.open(gz, "rb") as f_in, tmp.open("wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    got_sha = sha256_file(tmp)
    got_bytes = tmp.stat().st_size
    st = d_stats(tmp)
    ok = (
        got_sha == expect_sha
        and got_bytes == expect_bytes
        and st.get("integrity_check") == "ok"
        and not st.get("diffs_vs_baseline")
    )
    return {
        "pass": ok,
        "sha_match": got_sha == expect_sha,
        "bytes_match": got_bytes == expect_bytes,
        "integrity": st.get("integrity_check"),
        "diffs_vs_baseline": st.get("diffs_vs_baseline"),
        "computed": st.get("computed"),
    }


def main() -> int:
    for p in ["logs", "snapshots", "delta", "upload", "validate", "reports", "src"]:
        (WORK / p).mkdir(parents=True, exist_ok=True)
    progress("START", task_id=TASK_ID)
    if not D_SRC.exists():
        progress("FAIL", error="D_SRC_MISSING", path=str(D_SRC))
        return 2
    if not DELTA_SRC.exists():
        progress("FAIL", error="DELTA_SRC_MISSING", path=str(DELTA_SRC))
        return 2

    # D snapshot
    progress("D_BACKUP", path=str(D_SRC))
    d_snap = WORK / "snapshots" / "D_REPAIRED_SNAPSHOT.sqlite"
    d_meta = backup_sqlite(D_SRC, d_snap)
    # freeze: write sidecar AFTER hash already computed on snapshot — do not rewrite snapshot
    d_stat = d_stats(d_snap)
    # re-hash after stats (readonly open should not mutate)
    d_meta["sha256_after_stats"] = sha256_file(d_snap)
    d_meta["unchanged"] = d_meta["sha256"] == d_meta["sha256_after_stats"]
    d_meta["stats"] = d_stat
    (WORK / "reports" / "D_SNAPSHOT_STATS.json").write_text(
        json.dumps(d_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    progress("D_BACKUP_DONE", sha=d_meta["sha256"], bytes=d_meta["bytes"], diffs=d_stat.get("diffs_vs_baseline"))

    # gzip D
    d_gz = WORK / "upload" / "D_REPAIRED_SNAPSHOT.sqlite.gz"
    progress("D_GZIP", path=str(d_gz))
    d_gz_meta = gzip_one(d_snap, d_gz)
    progress("D_GZIP_DONE", sha=d_gz_meta["sha256"], bytes=d_gz_meta["bytes"])

    # canonical delta
    progress("DELTA_CANONICAL", n_expected=42)
    cdelta = WORK / "delta" / "E_DELTA_CANONICAL.sqlite"
    c_meta = build_canonical_delta(DELTA_SRC, cdelta)
    (WORK / "reports" / "E_DELTA_CANONICAL_STATS.json").write_text(
        json.dumps(c_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    progress(
        "DELTA_DONE",
        files=c_meta["file_rows"],
        errors=c_meta["error_rows"],
        sha=c_meta["sha256"],
    )

    # optional gzip delta (small)
    c_gz = WORK / "upload" / "E_DELTA_CANONICAL.sqlite.gz"
    c_gz_meta = gzip_one(cdelta, c_gz)

    # validations
    v_d = local_roundtrip_validate(d_gz, d_meta["sha256"], d_meta["bytes"], d_stat)
    delta_ok = (
        c_meta["file_rows"] == 42
        and c_meta["target_rows"] == 16
        and c_meta["error_rows"] == 0
        and c_meta["null_identity_rows"] == 0
        and all(x["match"] for x in c_meta["coverage"])
    )
    tests = {
        "D_ROUNDTRIP_SHA_INTEGRITY": v_d,
        "DELTA_CANONICAL_COUNTS_AND_IDENTITY": {
            "pass": delta_ok,
            "file_rows": c_meta["file_rows"],
            "target_rows": c_meta["target_rows"],
            "error_rows": c_meta["error_rows"],
            "null_identity_rows": c_meta["null_identity_rows"],
            "coverage_mismatch": [x for x in c_meta["coverage"] if not x["match"]],
        },
        "D_BASELINE_SQL_MATCH": {
            "pass": not bool(d_stat.get("diffs_vs_baseline")) and d_stat.get("integrity_check") == "ok",
            "diffs": d_stat.get("diffs_vs_baseline"),
            "computed": d_stat.get("computed"),
            "integrity": d_stat.get("integrity_check"),
        },
    }
    (WORK / "reports" / "TEST_RESULTS.json").write_text(json.dumps(tests, ensure_ascii=False, indent=2), encoding="utf-8")

    handoff_ready = bool(
        v_d["pass"]
        and tests["DELTA_CANONICAL_COUNTS_AND_IDENTITY"]["pass"]
        and tests["D_BASELINE_SQL_MATCH"]["pass"]
        and d_meta["unchanged"]
    )

    contract = {
        "task_id": TASK_ID,
        "generated_at": utc(),
        "hostname": __import__("os").environ.get("COMPUTERNAME"),
        "HANDOFF_READY": False,  # flipped true only after confirmed HUB upload
        "COPY_AUTHORIZED": False,
        "FULL_MIGRATION": False,
        "artifacts": {
            "D_REPAIRED_SNAPSHOT.sqlite.gz": {
                "local_gz": str(d_gz),
                "gz_sha256": d_gz_meta["sha256"],
                "gz_bytes": d_gz_meta["bytes"],
                "inner_sqlite_sha256": d_meta["sha256"],
                "inner_sqlite_bytes": d_meta["bytes"],
                "hub_path": "agents/chatgpt/inbox/R9_SAM_METADATA_HANDOFF_20261013/D_REPAIRED_SNAPSHOT.sqlite.gz",
                "single_file_in_archive": True,
                "stats": d_stat.get("computed"),
                "schema_tables": d_stat.get("tables"),
                "table_counts": d_stat.get("counts"),
                "integrity_check": d_stat.get("integrity_check"),
                "source_db": str(D_SRC),
                "note": "Do not validate against unrepaired 787b14... SHA",
            },
            "E_DELTA_CANONICAL.sqlite": {
                "local": str(cdelta),
                "sqlite_sha256": c_meta["sha256"],
                "sqlite_bytes": c_meta["bytes"],
                "gz_optional": {
                    "local_gz": str(c_gz),
                    "gz_sha256": c_gz_meta["sha256"],
                    "gz_bytes": c_gz_meta["bytes"],
                },
                "hub_path": "agents/chatgpt/inbox/R9_SAM_METADATA_HANDOFF_20261013/E_DELTA_CANONICAL.sqlite",
                "hub_gz_path": "agents/chatgpt/inbox/R9_SAM_METADATA_HANDOFF_20261013/E_DELTA_CANONICAL.sqlite.gz",
                "file_rows": c_meta["file_rows"],
                "target_rows": c_meta["target_rows"],
                "identity": "Win32 volume_serial_dword + 64-bit file_id",
                "historical_delta_sha256_retained": "9f1a37f945e80682a93190565e553bdef61bf8451b96216c2686c1d3e8887ad6",
            },
        },
        "tests": tests,
        "local_validation_pass_before_upload": handoff_ready,
        "desktop_note": "Existing E 9.38GB snapshot already on desktop; do not re-upload. Next desktop task must implement real validators merging D+E+delta.",
        "share_readonly_note": r"\\192.168.100.2\E_DRIVE previously unreadable from desktop — this handoff bypasses that path",
    }
    (WORK / "reports" / "HANDOFF_CONTRACT.json").write_text(
        json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report = f"""# SAM REPORT — {TASK_ID}

generated_at: {utc()}
hostname: SAM
HANDOFF_READY: pending_upload_confirm
COPY_AUTHORIZED: false
FULL_MIGRATION: false

## D repaired snapshot
- source: `{D_SRC}`
- snapshot: `{d_snap}`
- sqlite_sha256: `{d_meta['sha256']}`
- sqlite_bytes: {d_meta['bytes']}
- gz: `{d_gz}` sha `{d_gz_meta['sha256']}` bytes {d_gz_meta['bytes']}
- integrity: {d_stat.get('integrity_check')}
- computed: {json.dumps(d_stat.get('computed'), ensure_ascii=False)}
- diffs_vs_baseline: {json.dumps(d_stat.get('diffs_vs_baseline'), ensure_ascii=False)}

## E delta canonical (42)
- path: `{cdelta}`
- sha256: `{c_meta['sha256']}`
- files: {c_meta['file_rows']} / targets: {c_meta['target_rows']} / errors: {c_meta['error_rows']}
- null_identity: {c_meta['null_identity_rows']}
- identity: Win32 dword volume serial + 64-bit file index via r9fix handle_identity
- historical delta sha retained: 9f1a37...

## Tests
{json.dumps(tests, ensure_ascii=False, indent=2)}

## Next
Desktop receives HUB artifacts only; implement real D merge + validators. No copy. No format.
"""
    (WORK / "reports" / "SAM_REPORT.md").write_text(report, encoding="utf-8")
    progress("LOCAL_DONE", handoff_ready_local=handoff_ready)
    print("LOCAL_OK", json.dumps({"handoff_ready_local": handoff_ready, "d_gz_bytes": d_gz_meta["bytes"], "delta_files": c_meta["file_rows"]}))
    return 0 if handoff_ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
