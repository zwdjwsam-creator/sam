# -*- coding: utf-8 -*-
"""
R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014 — SAM local no-follow source reconcile.

- COPY_AUTHORIZED=false; writes only under WORK
- Reuses r9_pilot_common_r9fix + selected_manifest identity pattern
- Stream enum → CURRENT_ENUM.sqlite; compare → DELTA.sqlite
- HISTORICAL_CONTENT_MATCH always UNPROVEN
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORK = Path(r"C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014")
BASELINE_DIR = WORK / "baseline"
BASELINE_DB = BASELINE_DIR / "SOURCE_BASELINE.sqlite"
SCOPE_JSON = BASELINE_DIR / "SOURCE_SCOPE.json"
CONTRACT_JSON = BASELINE_DIR / "SOURCE_BASELINE_CONTRACT.json"
DB_DIR = WORK / "db"
CURRENT_DB = DB_DIR / "CURRENT_ENUM.sqlite"
DELTA_DB = DB_DIR / "DELTA.sqlite"
LOG_DIR = WORK / "logs"
REPORT_DIR = WORK / "reports"
STATE_DIR = WORK / "state"
PID_FILE = STATE_DIR / "reconcile_pid.txt"
PROGRESS_JSON = STATE_DIR / "progress.json"

EXPECT_BASELINE_SHA = "94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba"
EXPECT_BASELINE_BYTES = 6025072640
EXPECT_SCOPE_SHA = "e03948d4a23aa2bd63c4d4b7644e3682e06a22c5fa64b1595892bdbcb284607f"
EXPECT_CONTRACT_SHA = "46655c97069c19ad010faec358cc12f2c9f5b31615dc5280406b59fa7dd20d3d"
EXPECT_E_VOL = 2387166462
EXPECT_D_VOL = 3187598165
E_DIR_REPARSE_STORED_VOL = 11708076955747828990  # low32 == EXPECT_E_VOL
E_DIR_REPARSE_LOW32 = E_DIR_REPARSE_STORED_VOL & 0xFFFFFFFF

TASK_ID = "R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014_2312"
TZ = timezone(timedelta(hours=8))
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_REPARSE_POINT = 0x400

sys.path.insert(0, r"C:\LAN_SHARE_REPORT")
sys.path.insert(0, r"C:\LAN_SHARE_REPORT\BLACKBOX_R9_SELECTED_MANIFEST")
sys.path.insert(0, str(WORK / "src"))
import r9_pilot_common_r9fix as C  # noqa: E402
from reparse_nofollow_r1 import read_reparse_nofollow  # noqa: E402
from pathutil_r2 import normalize_win_path  # noqa: E402


def now() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def log(msg: str, log_fp=None) -> None:
    line = f"{now()} {msg}"
    print(line, flush=True)
    if log_fp:
        log_fp.write(line + "\n")
        log_fp.flush()


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def volume_serial_dword(root: str) -> int:
    serial = ctypes_vol_serial(root)
    return int(serial)


def ctypes_vol_serial(root: str) -> int:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    vol = wintypes.DWORD(0)
    maxc = wintypes.DWORD(0)
    flags = wintypes.DWORD(0)
    fsname = ctypes.create_unicode_buffer(64)
    label = ctypes.create_unicode_buffer(64)
    drive = root[:3] if len(root) >= 3 and root[1] == ":" else root
    ok = kernel32.GetVolumeInformationW(
        drive, label, 64, ctypes.byref(vol), ctypes.byref(maxc), ctypes.byref(flags), fsname, 64
    )
    if not ok:
        raise OSError(ctypes.get_last_error(), f"GetVolumeInformationW fail {drive}")
    return int(vol.value)


def verify_baseline(log_fp=None) -> dict:
    out = {
        "BASELINE_VERIFIED": False,
        "bytes": None,
        "sha256": None,
        "sha_match": False,
        "wal_bytes": 0,
        "journal_bytes": 0,
        "shm_bytes": 0,
        "quick_check": None,
        "scope_sha_match": False,
        "contract_sha_match": False,
        "block": None,
        "path_count": None,
        "link_count": None,
    }
    if not BASELINE_DB.exists():
        out["block"] = "BASELINE_MISSING"
        return out
    sz = BASELINE_DB.stat().st_size
    out["bytes"] = sz
    if sz != EXPECT_BASELINE_BYTES:
        out["block"] = f"BASELINE_SIZE_MISMATCH got={sz} expect={EXPECT_BASELINE_BYTES}"
        return out
    for suffix, key in [("-wal", "wal_bytes"), ("-journal", "journal_bytes"), ("-shm", "shm_bytes")]:
        p = Path(str(BASELINE_DB) + suffix)
        out[key] = p.stat().st_size if p.exists() else 0
    if out["wal_bytes"] or out["journal_bytes"]:
        out["block"] = f"BASELINE_HAS_WAL_OR_JOURNAL wal={out['wal_bytes']} journal={out['journal_bytes']}"
        return out
    log("hashing SOURCE_BASELINE.sqlite (may take several minutes)...", log_fp)
    got = sha256_file(BASELINE_DB)
    out["sha256"] = got
    out["sha_match"] = got == EXPECT_BASELINE_SHA
    if not out["sha_match"]:
        out["block"] = f"BASELINE_SHA_MISMATCH got={got}"
        return out
    scope_sha = sha256_file(SCOPE_JSON)
    contract_sha = sha256_file(CONTRACT_JSON)
    out["scope_sha_match"] = scope_sha == EXPECT_SCOPE_SHA
    out["contract_sha_match"] = contract_sha == EXPECT_CONTRACT_SHA
    if not out["scope_sha_match"]:
        out["block"] = f"SCOPE_SHA_MISMATCH got={scope_sha}"
        return out
    if not out["contract_sha_match"]:
        out["block"] = f"CONTRACT_SHA_MISMATCH got={contract_sha}"
        return out
    con = sqlite3.connect(str(BASELINE_DB))
    try:
        qc = con.execute("PRAGMA quick_check").fetchone()[0]
        out["quick_check"] = qc
        if qc != "ok":
            out["block"] = f"QUICK_CHECK_FAIL {qc}"
            return out
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        out["tables"] = tables
        if "paths" in tables:
            out["path_count"] = con.execute("SELECT COUNT(*) FROM paths").fetchone()[0]
        if "links" in tables:
            out["link_count"] = con.execute("SELECT COUNT(*) FROM links").fetchone()[0]
    finally:
        con.close()
    out["BASELINE_VERIFIED"] = True
    return out


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
        "reparse_tag": None,
        "reparse_target": None,
        "identity_err": None,
        "access_err": None,
        "object_class": None,
        "baseline_identity_status": "PROVEN",
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
            rp = read_reparse_nofollow(path)
            out["reparse_tag"] = rp.get("reparse_tag")
            out["reparse_target"] = rp.get("normalized_target") or rp.get("raw_target")
            out["volume_serial"] = rp.get("volume_serial")
            out["file_id"] = rp.get("file_id")
            out["logical_size"] = rp.get("logical_size")
            out["nlinks"] = rp.get("nlinks")
            out["mtime_ft"] = rp.get("mtime_ft")
            if rp.get("error"):
                out["identity_err"] = rp["error"]
            return out
        h = C.open_source_stable(path)
        try:
            ident = C.handle_identity(h)
            out["logical_size"] = ident["size"]
            out["volume_serial"] = ident["volume_serial"]
            out["file_id"] = ident["file_id"]
            out["nlinks"] = ident["nlinks"]
            out["mtime_ft"] = ident["mtime_ft"]
        finally:
            C.safe_close(h)
    except Exception as e:
        msg = f"{type(e).__name__}:{e}"
        if "GetFileInformation" in msg or "SOURCE_IS_REPARSE" in msg:
            out["identity_err"] = msg
        else:
            out["access_err"] = msg
    return out


def init_current_db(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS nodes(
          path TEXT PRIMARY KEY,
          root_id TEXT,
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
          reparse_tag INTEGER,
          reparse_target TEXT,
          identity_err TEXT,
          access_err TEXT,
          object_class TEXT,
          compared INTEGER DEFAULT 0,
          updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS queue(
          path TEXT PRIMARY KEY,
          root_id TEXT,
          enqueued_at TEXT,
          status TEXT
        );
        CREATE TABLE IF NOT EXISTS dir_enum(
          path TEXT PRIMARY KEY,
          root_id TEXT,
          status TEXT,
          child_count INTEGER,
          started_at TEXT,
          finished_at TEXT,
          error TEXT
        );
        CREATE INDEX IF NOT EXISTS ix_queue_status ON queue(status);
        CREATE INDEX IF NOT EXISTS ix_nodes_root ON nodes(root_id);
        """
    )
    con.commit()


def init_delta_db(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS deltas(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          path TEXT,
          root_id TEXT,
          kind TEXT,
          detail TEXT,
          at TEXT,
          UNIQUE(path, kind, detail)
        );
        CREATE TABLE IF NOT EXISTS root_stats(
          root_id TEXT PRIMARY KEY,
          baseline_paths INTEGER,
          current_paths INTEGER,
          added INTEGER,
          missing INTEGER,
          type_mismatch INTEGER,
          identity_mismatch INTEGER,
          size_mismatch INTEGER,
          reparse_mismatch INTEGER,
          errors INTEGER,
          updated_at TEXT
        );
        CREATE INDEX IF NOT EXISTS ix_deltas_kind ON deltas(kind);
        CREATE INDEX IF NOT EXISTS ix_deltas_root ON deltas(root_id);
        """
    )
    con.commit()


def meta_set(con, k, v):
    con.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (k, str(v)))


def meta_get(con, k, default=None):
    r = con.execute("SELECT value FROM meta WHERE key=?", (k,)).fetchone()
    return r[0] if r else default


def add_delta(dcon, path, root_id, kind, detail):
    dcon.execute(
        "INSERT OR IGNORE INTO deltas(path,root_id,kind,detail,at) VALUES(?,?,?,?,?)",
        (path, root_id, kind, detail[:2000] if detail else None, now()),
    )


def vol_equal(live_vol, baseline_vol, *, is_e_dir_or_reparse: bool) -> bool:
    if live_vol is None and baseline_vol is None:
        return True
    if live_vol is None or baseline_vol is None:
        return False
    try:
        lv = int(live_vol)
        bv = int(baseline_vol)
    except (TypeError, ValueError):
        return str(live_vol) == str(baseline_vol)
    if is_e_dir_or_reparse and bv == E_DIR_REPARSE_STORED_VOL:
        return lv == E_DIR_REPARSE_LOW32 or lv == bv
    return lv == bv


def compare_one(bcon, dcon, root_id: str, path: str, info: dict, is_d16_reparse_root: bool) -> None:
    brow = bcon.execute(
        "SELECT path,is_dir,is_reparse,logical_size,volume_serial,file_id,nlinks,reparse_target,source "
        "FROM paths WHERE path=?",
        (path,),
    ).fetchone()
    if brow is None:
        add_delta(dcon, path, root_id, "ADDED", f"class={info.get('object_class')}")
        return

    b_is_dir, b_is_reparse = int(brow[1] or 0), int(brow[2] or 0)
    c_is_dir = 1 if info.get("is_dir") else 0
    c_is_reparse = 1 if info.get("is_reparse") else 0
    if c_is_dir != b_is_dir or c_is_reparse != b_is_reparse:
        add_delta(
            dcon,
            path,
            root_id,
            "TYPE_MISMATCH",
            f"baseline_dir={b_is_dir} reparse={b_is_reparse} current_dir={c_is_dir} reparse={c_is_reparse}",
        )

    is_e = path.upper().startswith("E:\\")
    is_e_dir_or_reparse = is_e and (c_is_dir or c_is_reparse or b_is_dir or b_is_reparse)

    # D16 reparse: identity UNPROVEN; path/tag/target only
    if is_d16_reparse_root and (c_is_reparse or b_is_reparse):
        link = bcon.execute(
            "SELECT path,target,original_target,reparse_tag FROM links WHERE path=?",
            (path,),
        ).fetchone()
        b_tag = link[3] if link else None
        b_tgt = None
        if link:
            b_tgt = link[2] or link[1]
        b_tgt2 = brow[7]
        expect_tgt = b_tgt or b_tgt2
        c_tag = info.get("reparse_tag")
        c_tgt = info.get("reparse_target")
        if b_tag is not None and c_tag is not None and int(b_tag) != int(c_tag):
            add_delta(dcon, path, root_id, "REPARSE_TAG_MISMATCH", f"b={b_tag} c={c_tag}")
        if expect_tgt and c_tgt:
            bn = normalize_win_path(str(expect_tgt)) or ""
            cn = normalize_win_path(str(c_tgt)) or ""
            if bn.rstrip("\\").lower() != cn.rstrip("\\").lower():
                add_delta(dcon, path, root_id, "REPARSE_TARGET_MISMATCH", f"b={expect_tgt} c={c_tgt}")
        # do not treat NULL baseline identity as mismatch
        return

    if c_is_reparse or b_is_reparse:
        link = bcon.execute(
            "SELECT path,target,original_target,reparse_tag FROM links WHERE path=?",
            (path,),
        ).fetchone()
        b_tag = link[3] if link else None
        b_tgt = (link[2] or link[1]) if link else brow[7]
        c_tag = info.get("reparse_tag")
        c_tgt = info.get("reparse_target") or info.get("reparse_target")
        if b_tag is not None and c_tag is not None and int(b_tag) != int(c_tag):
            add_delta(dcon, path, root_id, "REPARSE_TAG_MISMATCH", f"b={b_tag} c={c_tag}")
        elif b_tag is not None and c_tag is None:
            add_delta(dcon, path, root_id, "REPARSE_TAG_MISSING_CURRENT", f"b={b_tag}")
        if b_tgt and c_tgt:
            bn = (normalize_win_path(str(b_tgt)) or "").rstrip("\\").lower()
            cn = (normalize_win_path(str(c_tgt)) or "").rstrip("\\").lower()
            if bn != cn:
                add_delta(dcon, path, root_id, "REPARSE_TARGET_MISMATCH", f"b={b_tgt} c={c_tgt}")
        # volume/file_id for E reparse: low32 quirk
        if not vol_equal(info.get("volume_serial"), brow[4], is_e_dir_or_reparse=is_e_dir_or_reparse):
            add_delta(
                dcon,
                path,
                root_id,
                "VOLUME_MISMATCH",
                f"b={brow[4]} c={info.get('volume_serial')} e_quirk={is_e_dir_or_reparse}",
            )
        if brow[5] and info.get("file_id") and str(brow[5]) != str(info.get("file_id")):
            add_delta(dcon, path, root_id, "FILE_ID_MISMATCH", f"b={brow[5]} c={info.get('file_id')}")
        return

    # ordinary file/dir
    if not vol_equal(info.get("volume_serial"), brow[4], is_e_dir_or_reparse=is_e_dir_or_reparse):
        add_delta(
            dcon,
            path,
            root_id,
            "VOLUME_MISMATCH",
            f"b={brow[4]} c={info.get('volume_serial')} e_quirk={is_e_dir_or_reparse}",
        )
    if brow[5] and info.get("file_id") and str(brow[5]) != str(info.get("file_id")):
        add_delta(dcon, path, root_id, "FILE_ID_MISMATCH", f"b={brow[5]} c={info.get('file_id')}")
    if not c_is_dir and not c_is_reparse:
        bsz = brow[3]
        csz = info.get("logical_size")
        if bsz is not None and csz is not None and int(bsz) != int(csz):
            add_delta(dcon, path, root_id, "SIZE_MISMATCH", f"b={bsz} c={csz}")
    if info.get("access_err") or info.get("identity_err"):
        add_delta(
            dcon,
            path,
            root_id,
            "CURRENT_READ_ERROR",
            info.get("access_err") or info.get("identity_err"),
        )


def upsert_node(con, path, root_id, parent, name, info):
    con.execute(
        """
        INSERT INTO nodes(path,root_id,parent,name,is_dir,is_reparse,attrs,logical_size,volume_serial,file_id,nlinks,
          mtime_ft,reparse_tag,reparse_target,identity_err,access_err,object_class,compared,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?)
        ON CONFLICT(path) DO UPDATE SET
          root_id=excluded.root_id, parent=excluded.parent, name=excluded.name,
          is_dir=excluded.is_dir, is_reparse=excluded.is_reparse, attrs=excluded.attrs,
          logical_size=excluded.logical_size, volume_serial=excluded.volume_serial, file_id=excluded.file_id,
          nlinks=excluded.nlinks, mtime_ft=excluded.mtime_ft, reparse_tag=excluded.reparse_tag,
          reparse_target=excluded.reparse_target, identity_err=excluded.identity_err,
          access_err=excluded.access_err, object_class=excluded.object_class, updated_at=excluded.updated_at
        """,
        (
            path,
            root_id,
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
            info.get("reparse_tag"),
            info.get("reparse_target"),
            info.get("identity_err"),
            info.get("access_err"),
            info.get("object_class"),
            now(),
        ),
    )


def enqueue(con, path, root_id):
    con.execute(
        "INSERT INTO queue(path,root_id,enqueued_at,status) VALUES(?,?,?,?) "
        "ON CONFLICT(path) DO UPDATE SET status=CASE WHEN queue.status='done' THEN queue.status ELSE 'pending' END",
        (path, root_id, now(), "pending"),
    )


def write_progress(payload: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PROGRESS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_running_reports(payload: dict) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary = dict(payload)
    summary["HISTORICAL_CONTENT_MATCH"] = "UNPROVEN"
    (REPORT_DIR / "SOURCE_RECONCILE_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md = []
    md.append(f"# SAM_REPORT — {TASK_ID}")
    md.append("")
    md.append(f"- status: {payload.get('status')}")
    md.append(f"- host: {payload.get('hostname')}")
    md.append(f"- pid: {payload.get('pid')}")
    md.append(f"- updated_at: {payload.get('updated_at')}")
    md.append(f"- BASELINE_VERIFIED: {payload.get('BASELINE_VERIFIED')}")
    md.append(f"- SOURCE_ENUMERATION_COMPLETE: {payload.get('SOURCE_ENUMERATION_COMPLETE')}")
    md.append(f"- SOURCE_METADATA_MATCH: {payload.get('SOURCE_METADATA_MATCH')}")
    md.append(f"- SOURCE_CURRENT_MATCH: {payload.get('SOURCE_CURRENT_MATCH')}")
    md.append(f"- HISTORICAL_CONTENT_MATCH: UNPROVEN")
    md.append(f"- SOURCE_SCAN_STABILITY: {payload.get('SOURCE_SCAN_STABILITY')}")
    md.append(f"- dirs_done: {payload.get('dirs_done')}")
    md.append(f"- queue_pending: {payload.get('queue_pending')}")
    md.append(f"- paths_enumerated: {payload.get('paths_enumerated')}")
    md.append(f"- deltas: {payload.get('delta_counts')}")
    md.append(f"- resume: python -u {WORK / 'src' / 'source_reconcile_r1.py'} --mode run")
    md.append("")
    md.append("## Notes")
    for n in payload.get("notes") or []:
        md.append(f"- {n}")
    if payload.get("block"):
        md.append("")
        md.append(f"## BLOCK\n{payload['block']}")
    (REPORT_DIR / "SAM_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def try_usn_snapshot(roots: list[str]) -> dict:
    """Best-effort read-only USN journal query; never create/reset journal."""
    out = {"SOURCE_SCAN_STABILITY": "UNPROVEN", "usn": {}, "error": None}
    try:
        import ctypes
        from ctypes import wintypes

        # FSCTL_QUERY_USN_JOURNAL = CTL_CODE(FILE_DEVICE_FILE_SYSTEM, 61, METHOD_BUFFERED, FILE_ANY_ACCESS)
        FSCTL_QUERY_USN_JOURNAL = 0x000900F4

        class USN_JOURNAL_DATA_V0(ctypes.Structure):
            _fields_ = [
                ("UsnJournalID", ctypes.c_ulonglong),
                ("FirstUsn", ctypes.c_longlong),
                ("NextUsn", ctypes.c_longlong),
                ("LowestValidUsn", ctypes.c_longlong),
                ("MaxUsn", ctypes.c_longlong),
                ("MaximumSize", ctypes.c_ulonglong),
                ("AllocationDelta", ctypes.c_ulonglong),
            ]

        GENERIC_READ = 0x80000000
        FILE_SHARE_READ = 1
        FILE_SHARE_WRITE = 2
        OPEN_EXISTING = 3
        FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
        for root in roots:
            drive = root[:2] + "\\"
            if drive in out["usn"]:
                continue
            h = C.CreateFileW(
                drive,
                GENERIC_READ,
                FILE_SHARE_READ | FILE_SHARE_WRITE,
                None,
                OPEN_EXISTING,
                FILE_FLAG_BACKUP_SEMANTICS,
                None,
            )
            if h == C.INVALID_HANDLE_VALUE or h is None:
                out["usn"][drive] = {"ok": False, "winerror": ctypes.get_last_error()}
                continue
            try:
                data = USN_JOURNAL_DATA_V0()
                ret = wintypes.DWORD(0)
                ok = ctypes.windll.kernel32.DeviceIoControl(
                    h,
                    FSCTL_QUERY_USN_JOURNAL,
                    None,
                    0,
                    ctypes.byref(data),
                    ctypes.sizeof(data),
                    ctypes.byref(ret),
                    None,
                )
                if ok:
                    out["usn"][drive] = {
                        "ok": True,
                        "UsnJournalID": int(data.UsnJournalID),
                        "NextUsn": int(data.NextUsn),
                        "FirstUsn": int(data.FirstUsn),
                    }
                else:
                    out["usn"][drive] = {"ok": False, "winerror": ctypes.get_last_error()}
            finally:
                C.safe_close(h)
        if any(v.get("ok") for v in out["usn"].values()):
            # Still UNPROVEN unless we also capture end + no changes; record start only for now
            out["SOURCE_SCAN_STABILITY"] = "UNPROVEN"
            out["usn_note"] = "start snapshot recorded; end compare may update later; default UNPROVEN"
    except Exception as e:
        out["error"] = f"{type(e).__name__}:{e}"
        out["SOURCE_SCAN_STABILITY"] = "UNPROVEN"
    return out


def load_roots() -> list[dict]:
    scope = json.loads(SCOPE_JSON.read_text(encoding="utf-8"))
    roots = []
    roots.append(
        {
            "root_id": "E_BLACKBOX",
            "path": scope["e_source_root"],
            "kind": "E_ENTIRE",
            "is_d16_reparse_root": False,
        }
    )
    for r in scope["d_regular_roots"]:
        roots.append(
            {
                "root_id": "D_" + Path(r["root"]).name,
                "path": r["root"],
                "kind": "D_ENTIRE",
                "is_d16_reparse_root": False,
            }
        )
    partial = scope["d_partial_root"]["included_subtree"]
    roots.append(
        {
            "root_id": "D_PIT_PRODUCTS",
            "path": partial,
            "kind": "D_PARTIAL",
            "is_d16_reparse_root": True,
        }
    )
    return roots


def enum_one_dir(ccon, bcon, dcon, path: str, root_id: str, is_d16: bool) -> str:
    started = now()
    info = identity_for_path(path)
    parent = str(Path(path).parent) if Path(path).parent != Path(path) else None
    upsert_node(ccon, path, root_id, parent, Path(path).name, info)
    compare_one(bcon, dcon, root_id, path, info, is_d16)
    ccon.execute("UPDATE nodes SET compared=1 WHERE path=?", (path,))

    if info.get("access_err") and info.get("is_dir") is None:
        ccon.execute(
            "INSERT OR REPLACE INTO dir_enum(path,root_id,status,child_count,started_at,finished_at,error) VALUES(?,?,?,?,?,?,?)",
            (path, root_id, "ERROR", 0, started, now(), info.get("access_err")),
        )
        add_delta(dcon, path, root_id, "ENUM_ERROR", info.get("access_err"))
        return "ERROR"

    if info.get("is_reparse"):
        ccon.execute(
            "INSERT OR REPLACE INTO dir_enum(path,root_id,status,child_count,started_at,finished_at,error) VALUES(?,?,?,?,?,?,?)",
            (path, root_id, "ENUM_DONE", 0, started, now(), "REPARSE_NOT_FOLLOWED"),
        )
        return "ENUM_DONE"

    children: list[tuple[str, str]] = []
    try:
        with os.scandir(C.to_win_long_path(path)) as it:
            for ent in it:
                children.append((path.rstrip("\\") + "\\" + ent.name, ent.name))
    except OSError as e:
        err = f"SCANDIR:{e}"
        ccon.execute(
            "INSERT OR REPLACE INTO dir_enum(path,root_id,status,child_count,started_at,finished_at,error) VALUES(?,?,?,?,?,?,?)",
            (path, root_id, "ERROR", 0, started, now(), err),
        )
        add_delta(dcon, path, root_id, "ENUM_ERROR", err)
        return "ERROR"

    for child_path, name in children:
        cinfo = identity_for_path(child_path)
        upsert_node(ccon, child_path, root_id, path, name, cinfo)
        compare_one(bcon, dcon, root_id, child_path, cinfo, is_d16)
        ccon.execute("UPDATE nodes SET compared=1 WHERE path=?", (child_path,))
        if cinfo.get("is_dir") and not cinfo.get("is_reparse"):
            enqueue(ccon, child_path, root_id)

    ccon.execute(
        "INSERT OR REPLACE INTO dir_enum(path,root_id,status,child_count,started_at,finished_at,error) VALUES(?,?,?,?,?,?,?)",
        (path, root_id, "ENUM_DONE", len(children), started, now(), None),
    )
    return "ENUM_DONE"


def finalize_missing(bcon, ccon, dcon, roots: list[dict]) -> None:
    """Mark baseline paths under completed roots that were never seen as MISSING."""
    for r in roots:
        root = r["path"].rstrip("\\")
        root_id = r["root_id"]
        # stream baseline paths under root
        cur = bcon.execute(
            "SELECT path FROM paths WHERE path=? OR path LIKE ?",
            (root, root + "\\%"),
        )
        while True:
            rows = cur.fetchmany(5000)
            if not rows:
                break
            for (p,) in rows:
                exists = ccon.execute("SELECT 1 FROM nodes WHERE path=?", (p,)).fetchone()
                if not exists:
                    add_delta(dcon, p, root_id, "MISSING", "in_baseline_not_in_current")


def delta_counts(dcon) -> dict:
    rows = dcon.execute("SELECT kind, COUNT(*) FROM deltas GROUP BY kind").fetchall()
    return {k: int(v) for k, v in rows}


def build_status(
    *,
    status,
    baseline_info,
    ccon,
    dcon,
    usn_info,
    block=None,
    notes=None,
    enumeration_complete=False,
) -> dict:
    q_pending = ccon.execute("SELECT COUNT(*) FROM queue WHERE status='pending'").fetchone()[0]
    q_done = ccon.execute("SELECT COUNT(*) FROM queue WHERE status='done'").fetchone()[0]
    dirs_done = ccon.execute("SELECT COUNT(*) FROM dir_enum WHERE status='ENUM_DONE'").fetchone()[0]
    dirs_err = ccon.execute("SELECT COUNT(*) FROM dir_enum WHERE status='ERROR'").fetchone()[0]
    paths_n = ccon.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    dcounts = delta_counts(dcon)
    # metadata match only if complete and no compare deltas of mismatch kinds
    mismatch_kinds = {
        "ADDED",
        "MISSING",
        "TYPE_MISMATCH",
        "VOLUME_MISMATCH",
        "FILE_ID_MISMATCH",
        "SIZE_MISMATCH",
        "REPARSE_TAG_MISMATCH",
        "REPARSE_TARGET_MISMATCH",
        "REPARSE_TAG_MISSING_CURRENT",
        "ENUM_ERROR",
        "CURRENT_READ_ERROR",
    }
    mismatch_n = sum(dcounts.get(k, 0) for k in mismatch_kinds)
    metadata_match = bool(enumeration_complete and mismatch_n == 0 and dirs_err == 0 and not block)
    current_match = False  # never claim full current match without content proof; metadata-only may be true
    if metadata_match:
        current_match = False  # HISTORICAL_CONTENT_MATCH UNPROVEN ⇒ SOURCE_CURRENT_MATCH false
    return {
        "task_id": TASK_ID,
        "status": status,
        "hostname": __import__("socket").gethostname(),
        "pid": os.getpid(),
        "updated_at": now(),
        "BASELINE_VERIFIED": bool(baseline_info.get("BASELINE_VERIFIED")),
        "baseline": baseline_info,
        "SOURCE_ENUMERATION_COMPLETE": enumeration_complete,
        "SOURCE_METADATA_MATCH": metadata_match,
        "SOURCE_CURRENT_MATCH": current_match,
        "HISTORICAL_CONTENT_MATCH": "UNPROVEN",
        "SOURCE_SCAN_STABILITY": usn_info.get("SOURCE_SCAN_STABILITY", "UNPROVEN"),
        "usn": usn_info.get("usn"),
        "dirs_done": dirs_done,
        "dirs_error": dirs_err,
        "queue_pending": q_pending,
        "queue_done": q_done,
        "paths_enumerated": paths_n,
        "delta_counts": dcounts,
        "delta_mismatch_total": mismatch_n,
        "block": block,
        "notes": notes or [],
        "COPY_AUTHORIZED": False,
        "FULL_MIGRATION": False,
        "work_dir": str(WORK),
        "current_db": str(CURRENT_DB),
        "delta_db": str(DELTA_DB),
    }


def run(mode: str = "run", report_every_sec: int = 120, commit_every: int = 200) -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DB_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"reconcile_{datetime.now(TZ).strftime('%Y%m%d_%H%M%S')}.log"
    # append to stable log too
    stable_log = LOG_DIR / "reconcile_main.log"
    log_fp = open(stable_log, "a", encoding="utf-8")
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    log(f"START pid={os.getpid()} mode={mode} log={stable_log}", log_fp)

    # volume gate
    try:
        e_vol = ctypes_vol_serial("E:\\")
        d_vol = ctypes_vol_serial("D:\\")
    except Exception as e:
        payload = {
            "status": "HARD_BLOCK",
            "block": f"VOLUME_QUERY_FAIL:{e}",
            "BASELINE_VERIFIED": False,
            "SOURCE_ENUMERATION_COMPLETE": False,
            "SOURCE_METADATA_MATCH": False,
            "SOURCE_CURRENT_MATCH": False,
            "HISTORICAL_CONTENT_MATCH": "UNPROVEN",
            "SOURCE_SCAN_STABILITY": "UNPROVEN",
            "pid": os.getpid(),
            "hostname": __import__("socket").gethostname(),
            "updated_at": now(),
            "notes": [],
            "delta_counts": {},
            "dirs_done": 0,
            "queue_pending": 0,
            "paths_enumerated": 0,
        }
        write_running_reports(payload)
        log(f"HARD_BLOCK {payload['block']}", log_fp)
        log_fp.close()
        return 2
    if e_vol != EXPECT_E_VOL or d_vol != EXPECT_D_VOL:
        payload = {
            "status": "HARD_BLOCK",
            "block": f"VOLUME_MISMATCH E={e_vol} expect={EXPECT_E_VOL} D={d_vol} expect={EXPECT_D_VOL}",
            "BASELINE_VERIFIED": False,
            "SOURCE_ENUMERATION_COMPLETE": False,
            "SOURCE_METADATA_MATCH": False,
            "SOURCE_CURRENT_MATCH": False,
            "HISTORICAL_CONTENT_MATCH": "UNPROVEN",
            "SOURCE_SCAN_STABILITY": "UNPROVEN",
            "pid": os.getpid(),
            "hostname": __import__("socket").gethostname(),
            "updated_at": now(),
            "notes": [],
            "delta_counts": {},
            "dirs_done": 0,
            "queue_pending": 0,
            "paths_enumerated": 0,
        }
        write_running_reports(payload)
        log(f"HARD_BLOCK {payload['block']}", log_fp)
        log_fp.close()
        return 2
    log(f"volumes OK E={e_vol} D={d_vol}", log_fp)

    baseline_info = verify_baseline(log_fp)
    if not baseline_info.get("BASELINE_VERIFIED"):
        payload = {
            "status": "HARD_BLOCK",
            "block": baseline_info.get("block") or "BASELINE_VERIFY_FAIL",
            "BASELINE_VERIFIED": False,
            "baseline": baseline_info,
            "SOURCE_ENUMERATION_COMPLETE": False,
            "SOURCE_METADATA_MATCH": False,
            "SOURCE_CURRENT_MATCH": False,
            "HISTORICAL_CONTENT_MATCH": "UNPROVEN",
            "SOURCE_SCAN_STABILITY": "UNPROVEN",
            "pid": os.getpid(),
            "hostname": __import__("socket").gethostname(),
            "updated_at": now(),
            "notes": ["Stopped before enumeration; no alternate baseline forged."],
            "delta_counts": {},
            "dirs_done": 0,
            "queue_pending": 0,
            "paths_enumerated": 0,
        }
        write_running_reports(payload)
        log(f"HARD_BLOCK {payload['block']}", log_fp)
        log_fp.close()
        return 2
    log(
        f"BASELINE_VERIFIED paths={baseline_info.get('path_count')} links={baseline_info.get('link_count')}",
        log_fp,
    )

    roots = load_roots()
    for r in roots:
        if not Path(r["path"]).exists() and not _path_exists_nofollow(r["path"]):
            # GetFileAttributes may still see reparse/dirs
            attrs_ok = False
            try:
                C.get_attrs(r["path"])
                attrs_ok = True
            except Exception:
                attrs_ok = False
            if not attrs_ok:
                payload = {
                    "status": "HARD_BLOCK",
                    "block": f"ROOT_MISSING:{r['path']}",
                    "BASELINE_VERIFIED": True,
                    "baseline": baseline_info,
                    "SOURCE_ENUMERATION_COMPLETE": False,
                    "SOURCE_METADATA_MATCH": False,
                    "SOURCE_CURRENT_MATCH": False,
                    "HISTORICAL_CONTENT_MATCH": "UNPROVEN",
                    "SOURCE_SCAN_STABILITY": "UNPROVEN",
                    "pid": os.getpid(),
                    "hostname": __import__("socket").gethostname(),
                    "updated_at": now(),
                    "notes": [],
                    "delta_counts": {},
                    "dirs_done": 0,
                    "queue_pending": 0,
                    "paths_enumerated": 0,
                }
                write_running_reports(payload)
                log(f"HARD_BLOCK {payload['block']}", log_fp)
                log_fp.close()
                return 2

    usn_start = try_usn_snapshot([r["path"] for r in roots])
    log(f"USN start: {json.dumps(usn_start, ensure_ascii=False)}", log_fp)

    ccon = sqlite3.connect(str(CURRENT_DB))
    ccon.execute("PRAGMA journal_mode=WAL")
    ccon.execute("PRAGMA synchronous=NORMAL")
    init_current_db(ccon)
    dcon = sqlite3.connect(str(DELTA_DB))
    dcon.execute("PRAGMA journal_mode=WAL")
    init_delta_db(dcon)
    bcon = sqlite3.connect(f"file:{BASELINE_DB.as_posix()}?mode=ro", uri=True)

    meta_set(ccon, "task_id", TASK_ID)
    meta_set(ccon, "started_at", meta_get(ccon, "started_at") or now())
    meta_set(dcon, "HISTORICAL_CONTENT_MATCH", "UNPROVEN")
    ccon.execute("UPDATE queue SET status='pending' WHERE status='in_progress'")
    ccon.commit()
    dcon.commit()

    # seed roots if not done
    for r in roots:
        st = ccon.execute("SELECT status FROM dir_enum WHERE path=?", (r["path"],)).fetchone()
        if not st or st[0] != "ENUM_DONE":
            enqueue(ccon, r["path"], r["root_id"])
    ccon.commit()

    root_d16 = {r["path"]: r["is_d16_reparse_root"] for r in roots}
    root_id_of = {}
    # map any path to root_id via queue row or prefix
    for r in roots:
        root_id_of[r["path"]] = r["root_id"]

    def resolve_root_id(path: str, fallback: str | None) -> tuple[str, bool]:
        if fallback:
            for r in roots:
                if r["root_id"] == fallback:
                    return fallback, r["is_d16_reparse_root"]
        for r in roots:
            rp = r["path"].rstrip("\\").upper()
            pu = path.rstrip("\\").upper()
            if pu == rp or pu.startswith(rp + "\\"):
                return r["root_id"], r["is_d16_reparse_root"]
        return fallback or "UNKNOWN", False

    last_report = 0.0
    processed = 0
    try:
        while True:
            row = ccon.execute(
                "SELECT path, root_id FROM queue WHERE status='pending' LIMIT 1"
            ).fetchone()
            if not row:
                break
            path, root_id = row[0], row[1]
            root_id, is_d16 = resolve_root_id(path, root_id)
            ccon.execute(
                "UPDATE queue SET status='in_progress' WHERE path=?",
                (path,),
            )
            ccon.commit()
            try:
                enum_one_dir(ccon, bcon, dcon, path, root_id, is_d16)
                ccon.execute("UPDATE queue SET status='done' WHERE path=?", (path,))
            except Exception as e:
                err = f"{type(e).__name__}:{e}"
                log(f"ENUM_EXCEPTION {path} {err}", log_fp)
                add_delta(dcon, path, root_id, "ENUM_ERROR", err)
                ccon.execute(
                    "INSERT OR REPLACE INTO dir_enum(path,root_id,status,child_count,started_at,finished_at,error) VALUES(?,?,?,?,?,?,?)",
                    (path, root_id, "ERROR", 0, now(), now(), err),
                )
                ccon.execute("UPDATE queue SET status='done' WHERE path=?", (path,))
            processed += 1
            if processed % commit_every == 0:
                ccon.commit()
                dcon.commit()
            now_t = time.time()
            if now_t - last_report >= report_every_sec:
                ccon.commit()
                dcon.commit()
                payload = build_status(
                    status="RUNNING",
                    baseline_info=baseline_info,
                    ccon=ccon,
                    dcon=dcon,
                    usn_info=usn_start,
                    notes=[f"processed_batch_dirs={processed}", f"log={stable_log}"],
                )
                write_progress(payload)
                write_running_reports(payload)
                log(
                    f"PROGRESS dirs_done={payload['dirs_done']} queue={payload['queue_pending']} "
                    f"paths={payload['paths_enumerated']} deltas={payload['delta_mismatch_total']}",
                    log_fp,
                )
                last_report = now_t

        ccon.commit()
        dcon.commit()
        log("queue empty — scanning baseline for MISSING...", log_fp)
        finalize_missing(bcon, ccon, dcon, roots)
        dcon.commit()

        usn_end = try_usn_snapshot([r["path"] for r in roots])
        # If start/end NextUsn differ on any volume, still UNPROVEN (changes may have occurred)
        stability = "UNPROVEN"
        usn_info = {
            "SOURCE_SCAN_STABILITY": stability,
            "usn_start": usn_start.get("usn"),
            "usn_end": usn_end.get("usn"),
        }

        # completeness: all roots ENUM_DONE and queue empty
        roots_ok = True
        for r in roots:
            st = ccon.execute("SELECT status FROM dir_enum WHERE path=?", (r["path"],)).fetchone()
            if not st or st[0] != "ENUM_DONE":
                roots_ok = False
        q_left = ccon.execute(
            "SELECT COUNT(*) FROM queue WHERE status IN ('pending','in_progress')"
        ).fetchone()[0]
        enumeration_complete = roots_ok and q_left == 0
        payload = build_status(
            status="COMPLETE" if enumeration_complete else "HARD_BLOCK",
            baseline_info=baseline_info,
            ccon=ccon,
            dcon=dcon,
            usn_info=usn_info,
            block=None if enumeration_complete else "ENUMERATION_INCOMPLETE",
            notes=[
                "Queue empty + roots done required for COMPLETE",
                "HISTORICAL_CONTENT_MATCH=UNPROVEN (baseline has no mtime/hash)",
                f"current_db={CURRENT_DB}",
                f"delta_db={DELTA_DB}",
            ],
            enumeration_complete=enumeration_complete,
        )
        # FILE_SHA256 for small artifacts
        sha_map = {}
        for p in [
            REPORT_DIR / "SAM_REPORT.md",
            REPORT_DIR / "SOURCE_RECONCILE_SUMMARY.json",
            SCOPE_JSON,
            CONTRACT_JSON,
        ]:
            if p.exists():
                sha_map[str(p)] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
        write_running_reports(payload)
        # rewrite summary after SAM_REPORT exists
        write_running_reports(payload)
        for p in [REPORT_DIR / "SAM_REPORT.md", REPORT_DIR / "SOURCE_RECONCILE_SUMMARY.json"]:
            if p.exists():
                sha_map[str(p)] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
        sha_map[str(BASELINE_DB)] = {
            "sha256": baseline_info.get("sha256"),
            "bytes": baseline_info.get("bytes"),
        }
        sha_map[str(CURRENT_DB)] = {
            "sha256": None,
            "bytes": CURRENT_DB.stat().st_size if CURRENT_DB.exists() else 0,
            "note": "large; hash optional",
        }
        sha_map[str(DELTA_DB)] = {
            "sha256": sha256_file(DELTA_DB) if DELTA_DB.exists() else None,
            "bytes": DELTA_DB.stat().st_size if DELTA_DB.exists() else 0,
        }
        (REPORT_DIR / "FILE_SHA256.json").write_text(
            json.dumps(sha_map, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # script refs
        refs = {
            "source_reconcile_r1.py": str(WORK / "src" / "source_reconcile_r1.py"),
            "reparse_nofollow_r1.py": str(WORK / "src" / "reparse_nofollow_r1.py"),
            "r9_pilot_common_r9fix.py": r"C:\LAN_SHARE_REPORT\r9_pilot_common_r9fix.py",
            "selected_manifest_enumerator_r2.py": r"C:\LAN_SHARE_REPORT\BLACKBOX_R9_SELECTED_MANIFEST\selected_manifest_enumerator_r2.py",
            "query_d_reparse_and_share_facts_r1.py": r"C:\LAN_SHARE_REPORT\R9_NOTEBOOK_SOURCE_LINK_AND_SHARE_FACTS_20261013\src\query_d_reparse_and_share_facts_r1.py",
        }
        (REPORT_DIR / "SCRIPT_REFS.json").write_text(
            json.dumps(refs, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        write_progress(payload)
        log(f"DONE status={payload['status']} metadata_match={payload['SOURCE_METADATA_MATCH']}", log_fp)
        log_fp.close()
        bcon.close()
        ccon.close()
        dcon.close()
        return 0 if enumeration_complete else 3
    except Exception as e:
        log(f"FATAL {type(e).__name__}:{e}\n{traceback.format_exc()}", log_fp)
        try:
            payload = build_status(
                status="HARD_BLOCK",
                baseline_info=baseline_info,
                ccon=ccon,
                dcon=dcon,
                usn_info=usn_start,
                block=f"FATAL:{type(e).__name__}:{e}",
            )
            write_running_reports(payload)
        except Exception:
            pass
        log_fp.close()
        return 1


def _path_exists_nofollow(path: str) -> bool:
    try:
        C.get_attrs(path)
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["run", "status", "verify-baseline"], default="run")
    ap.add_argument("--report-every-sec", type=int, default=120)
    ap.add_argument("--commit-every", type=int, default=200)
    args = ap.parse_args()
    if args.mode == "verify-baseline":
        info = verify_baseline()
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0 if info.get("BASELINE_VERIFIED") else 2
    if args.mode == "status":
        if PROGRESS_JSON.exists():
            print(PROGRESS_JSON.read_text(encoding="utf-8"))
            return 0
        print("{}")
        return 0
    return run(mode=args.mode, report_every_sec=args.report_every_sec, commit_every=args.commit_every)


if __name__ == "__main__":
    sys.exit(main() or 0)
