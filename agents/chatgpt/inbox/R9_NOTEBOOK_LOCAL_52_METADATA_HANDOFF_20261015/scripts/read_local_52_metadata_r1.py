# -*- coding: utf-8 -*-
"""Local read-only metadata for designated 52 items on SAM notebook.

Hard rules: no UNC, no recursion, no content read, no source mutation,
no inventing zeros for missing fields. Tiny scope only.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import socket
import sys
from ctypes import wintypes
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORK = Path(r"C:\LAN_SHARE_REPORT\R9_NOTEBOOK_LOCAL_52_METADATA_HANDOFF_20261015")
STAGING = WORK / "staging"
OUT = WORK / "out"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, r"C:\LAN_SHARE_REPORT")
sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_NOTEBOOK_RESOLVE_234_DELTA_AND_HANDOFF_20261015\src_upload")
import r9_pilot_common_r9fix as r9  # noqa: E402
from reparse_nofollow_r1 import read_reparse_nofollow  # noqa: E402

TZ8 = timezone(timedelta(hours=8))
EXPECTED_VOL = {"E": "2387166462", "D": "3187598165"}
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
FILE_ATTRIBUTE_DIRECTORY = 0x10
FileStandardInfo = 1
FileAttributeTagInfo = 9
GENERIC_READ = 0x80000000
FILE_SHARE_ALL = 0x00000007
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
GetFileInformationByHandleEx = kernel32.GetFileInformationByHandleEx


class FILE_STANDARD_INFO(ctypes.Structure):
    _fields_ = [
        ("AllocationSize", ctypes.c_int64),
        ("EndOfFile", ctypes.c_int64),
        ("NumberOfLinks", wintypes.DWORD),
        ("DeletePending", wintypes.BOOLEAN),
        ("Directory", wintypes.BOOLEAN),
    ]


class FILE_ATTRIBUTE_TAG_INFO(ctypes.Structure):
    _fields_ = [("FileAttributes", wintypes.DWORD), ("ReparseTag", wintypes.DWORD)]


MAILBOX_ACTIVITY_NAMES = {
    "INBOX_FOR_CHATGPT.md",
    "INBOX_FOR_DESKTOP.md",
    "INBOX_FOR_NOTEBOOK.md",
}


def now_iso() -> str:
    return datetime.now(TZ8).isoformat(timespec="milliseconds")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def load_52_paths() -> list[dict]:
    patch = json.loads((STAGING / "SOURCE_PLAN_PATCH.json").read_text(encoding="utf-8"))
    probe = json.loads((STAGING / "PROBE_52.json").read_text(encoding="utf-8"))
    rows = []
    for r in patch["added_51_metadata_candidates"]:
        rows.append(
            {
                "path": r["path"],
                "source_bucket": "added_51_metadata_candidates",
                "subclass": r.get("subclass"),
                "verdict": r.get("verdict"),
                "detail": r.get("detail"),
            }
        )
    mcp = patch["mcp_and_real_changes"][0]
    rows.append(
        {
            "path": mcp["path"],
            "source_bucket": "mcp_and_real_changes",
            "subclass": "MCP_JSON",
            "verdict": mcp.get("verdict"),
            "detail": mcp.get("detail"),
        }
    )
    paths = [r["path"] for r in rows]
    probe_paths = [r["path"] for r in probe["rows"]]
    if len(paths) != 52 or len(set(paths)) != 52:
        raise SystemExit(f"PATH_SET_BAD count={len(paths)} unique={len(set(paths))}")
    if set(paths) != set(probe_paths):
        raise SystemExit("PATH_SET_MISMATCH_VS_PROBE_52")
    return rows


def ancestor_checks(path: str) -> list[dict]:
    """Necessary ancestor existence only — no tree walk."""
    p = Path(path)
    out = []
    for anc in [p.parent, p.parent.parent if p.parent != p else None]:
        if anc is None:
            continue
        s = str(anc)
        if len(s) <= 3:  # drive root
            out.append({"path": s, "exists": anc.exists(), "is_drive_root": True})
            break
        out.append({"path": s, "exists": anc.exists(), "is_drive_root": False})
        if not anc.exists():
            break
    return out


def read_one(path: str) -> dict:
    observed_at = now_iso()
    observed_at_utc = now_utc()
    rec: dict = {
        "path": path,
        "observed_at": observed_at,
        "observed_at_utc": observed_at_utc,
        "ok": False,
        "error": None,
        "winerror": None,
        "access_mode": "LOCAL_NOFOLLOW_CREATEFILE",
        "unc_used": False,
        "item_class": None,
        "is_directory": None,
        "is_reparse": None,
        "file_attributes": None,
        "volume_serial": None,
        "volume_serial_expected": None,
        "volume_serial_match_expected": None,
        "file_id": None,
        "size": None,
        "allocation_size": None,
        "mtime_ft": None,
        "mtime_iso": None,
        "ctime_ft": None,
        "nlinks": None,
        "delete_pending": None,
        "reparse_tag": None,
        "reparse_tag_hex": None,
        "reparse_raw_target": None,
        "reparse_print_name": None,
        "reparse_normalized_target": None,
        "ancestor_checks": ancestor_checks(path),
        "sharing_or_lock_note": None,
    }
    drive = path[:1].upper() if len(path) >= 2 and path[1] == ":" else None
    if drive in EXPECTED_VOL:
        rec["volume_serial_expected"] = EXPECTED_VOL[drive]

    long_path = r9.to_win_long_path(path)
    # FindEx first for attributes without following? GetFileAttributesW follows some links;
    # use CreateFile with OPEN_REPARSE_POINT for identity.
    h = r9.CreateFileW(
        long_path,
        GENERIC_READ,
        FILE_SHARE_ALL,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if h == INVALID_HANDLE_VALUE or h is None:
        err = ctypes.get_last_error()
        rec["winerror"] = err
        rec["error"] = f"CreateFileW_fail winerror={err}"
        if err in (32, 33):
            rec["sharing_or_lock_note"] = "SHARING_OR_LOCK_VIOLATION_AT_OBSERVED_AT"
        return rec

    try:
        info = r9.BY_HANDLE_FILE_INFORMATION()
        if not r9.GetFileInformationByHandle(h, ctypes.byref(info)):
            err = ctypes.get_last_error()
            rec["winerror"] = err
            rec["error"] = f"GetFileInformationByHandle_fail winerror={err}"
            return rec

        attrs = int(info.dwFileAttributes)
        fid = (info.nFileIndexHigh << 32) | info.nFileIndexLow
        size = (info.nFileSizeHigh << 32) | info.nFileSizeLow
        mtime = (info.ftLastWriteTime.dwHighDateTime << 32) | info.ftLastWriteTime.dwLowDateTime
        ctime = (info.ftCreationTime.dwHighDateTime << 32) | info.ftCreationTime.dwLowDateTime
        vol = str(info.dwVolumeSerialNumber)

        rec["file_attributes"] = attrs
        rec["is_directory"] = bool(attrs & FILE_ATTRIBUTE_DIRECTORY)
        rec["is_reparse"] = bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
        rec["volume_serial"] = vol
        if rec["volume_serial_expected"] is not None:
            rec["volume_serial_match_expected"] = vol == rec["volume_serial_expected"]
        rec["file_id"] = str(fid)
        rec["size"] = int(size)
        rec["nlinks"] = int(info.nNumberOfLinks)
        rec["mtime_ft"] = str(mtime)
        rec["ctime_ft"] = str(ctime)
        try:
            rec["mtime_iso"] = r9.filetime_to_utc_datetime(mtime).astimezone(TZ8).isoformat(
                timespec="milliseconds"
            )
        except Exception as e:
            rec["mtime_iso"] = None
            rec["mtime_iso_error"] = f"{type(e).__name__}:{e}"

        std = FILE_STANDARD_INFO()
        if GetFileInformationByHandleEx(h, FileStandardInfo, ctypes.byref(std), ctypes.sizeof(std)):
            rec["allocation_size"] = int(std.AllocationSize)
            rec["delete_pending"] = bool(std.DeletePending)
            # prefer EndOfFile if differs
            if int(std.EndOfFile) != int(size):
                rec["size_end_of_file"] = int(std.EndOfFile)
            if int(std.NumberOfLinks) != rec["nlinks"]:
                rec["nlinks_standard_info"] = int(std.NumberOfLinks)
        # do not invent allocation_size=0 on failure — leave None

        if rec["is_reparse"]:
            tag_info = FILE_ATTRIBUTE_TAG_INFO()
            if GetFileInformationByHandleEx(
                h, FileAttributeTagInfo, ctypes.byref(tag_info), ctypes.sizeof(tag_info)
            ):
                rec["reparse_tag"] = int(tag_info.ReparseTag)
                rec["reparse_tag_hex"] = hex(int(tag_info.ReparseTag))
            # close and re-read via trusted helper for target
            r9.safe_close(h)
            h = None
            rp = read_reparse_nofollow(path)
            if rp.get("reparse_tag") is not None:
                rec["reparse_tag"] = rp["reparse_tag"]
                rec["reparse_tag_hex"] = hex(int(rp["reparse_tag"]))
            rec["reparse_raw_target"] = rp.get("raw_target")
            rec["reparse_print_name"] = rp.get("print_name")
            rec["reparse_normalized_target"] = rp.get("normalized_target")
            if rp.get("error") and not rec.get("reparse_raw_target"):
                rec["reparse_error"] = rp["error"]
            # fill identity from rp only if primary missing (should not happen)
            for k in ("volume_serial", "file_id", "logical_size", "nlinks", "mtime_ft"):
                if rec.get(k if k != "logical_size" else "size") is None and rp.get(k) is not None:
                    if k == "logical_size":
                        rec["size"] = int(rp[k]) if rp[k] is not None else None
                    else:
                        rec[k] = rp[k]

        if rec["is_reparse"]:
            rec["item_class"] = "REPARSE_DIRECTORY" if rec["is_directory"] else "REPARSE_FILE"
        elif rec["is_directory"]:
            rec["item_class"] = "DIRECTORY"
        else:
            rec["item_class"] = "FILE"

        rec["ok"] = True
        rec["error"] = None
        return rec
    except Exception as e:
        rec["error"] = f"{type(e).__name__}:{e}"
        return rec
    finally:
        if h is not None and h != INVALID_HANDLE_VALUE:
            r9.safe_close(h)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    started = now_iso()
    path_rows = load_52_paths()
    results = []
    mailbox_activity = []
    for i, meta in enumerate(path_rows, 1):
        path = meta["path"]
        print(f"[{i}/52] {path}", flush=True)
        row = read_one(path)
        row["index"] = i
        row["source_bucket"] = meta["source_bucket"]
        row["subclass"] = meta.get("subclass")
        row["plan_verdict"] = meta.get("verdict")
        row["plan_detail"] = meta.get("detail")
        results.append(row)
        name = Path(path).name
        if name in MAILBOX_ACTIVITY_NAMES or path.replace("\\", "/").endswith(
            "/agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md"
        ):
            mailbox_activity.append(
                {
                    "path": path,
                    "observed_at": row["observed_at"],
                    "ok": row["ok"],
                    "size": row.get("size"),
                    "mtime_iso": row.get("mtime_iso"),
                    "mtime_ft": row.get("mtime_ft"),
                    "file_id": row.get("file_id"),
                    "volume_serial": row.get("volume_serial"),
                    "note": "activity_file_value_at_observed_at_not_frozen_across_items",
                }
            )

    finished = now_iso()
    ok_n = sum(1 for r in results if r["ok"])
    fail_n = 52 - ok_n
    vol_mismatch = [
        r["path"]
        for r in results
        if r.get("ok") and r.get("volume_serial_match_expected") is False
    ]
    missing_identity = [
        r["path"]
        for r in results
        if r.get("ok") and (r.get("volume_serial") is None or r.get("file_id") is None)
    ]
    payload = {
        "task_id": "R9_NOTEBOOK_LOCAL_52_METADATA_HANDOFF_20261015_0739",
        "wake_from": "R9_REVIEW_FULL_CHAIN_AND_SESSION_20261015_0800",
        "host": socket.gethostname(),
        "started_at": started,
        "finished_at": finished,
        "COPY_AUTHORIZED": False,
        "FULL_MIGRATION": False,
        "access": "LOCAL_E_AND_D_ONLY_NO_UNC_NO_SMB",
        "path_set": {
            "count": 52,
            "unique": 52,
            "sources": [
                "SOURCE_PLAN_PATCH.json added_51_metadata_candidates + mcp_and_real_changes",
                "PROBE_52.json rows (set equality verified)",
            ],
            "expected_volume_serials": EXPECTED_VOL,
        },
        "summary": {
            "ok": ok_n,
            "fail": fail_n,
            "volume_serial_mismatch_vs_expected": len(vol_mismatch),
            "missing_identity_despite_ok": len(missing_identity),
            "directories": sum(1 for r in results if r.get("item_class") == "DIRECTORY"),
            "files": sum(1 for r in results if r.get("item_class") == "FILE"),
            "reparse": sum(1 for r in results if r.get("is_reparse")),
        },
        "volume_serial_mismatch_paths": vol_mismatch,
        "missing_identity_paths": missing_identity,
        "mailbox_activity_snapshots": mailbox_activity,
        "rows": results,
    }
    out_json = OUT / "LOCAL_52_METADATA.json"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE {out_json} ok={ok_n} fail={fail_n}", flush=True)
    return 0 if fail_n == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
