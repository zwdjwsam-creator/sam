# -*- coding: utf-8 -*-
"""Read two representative files twice, in memory only."""
import ctypes
import hashlib
import json
import sqlite3
from pathlib import Path

import r9_plan_reader as reader

PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite")
PREV = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_REUSE_SESSION_RESOLVE_1219_20261014\probe.json")
OUT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_SOURCE_STABLE_READ_AND_PREP_SUMMARY_20261014\SOURCE_STABLE_READ.json")
EXPECTED_PLAN = "94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba"


class FILETIME(ctypes.Structure):
    _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]


class FILEINFO(ctypes.Structure):
    _fields_ = [
        ("attrs", ctypes.c_uint32), ("creation", FILETIME), ("access", FILETIME),
        ("write", FILETIME), ("volume", ctypes.c_uint32), ("size_high", ctypes.c_uint32),
        ("size_low", ctypes.c_uint32), ("links", ctypes.c_uint32),
        ("id_high", ctypes.c_uint32), ("id_low", ctypes.c_uint32),
    ]


def identity(kernel, handle):
    info = FILEINFO()
    if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
        raise OSError(ctypes.get_last_error(), "identity")
    return {
        "volume_serial": int(info.volume),
        "file_id": str((int(info.id_high) << 32) | int(info.id_low)),
        "logical_size": (int(info.size_high) << 32) | int(info.size_low),
        "mtime_ft": str((int(info.write.high) << 32) | int(info.write.low)),
        "is_dir": bool(int(info.attrs) & 0x10),
    }


def read_once(kernel, path):
    unc = "\\\\?\\UNC\\" + path[2:]
    handle = kernel.CreateFileW(unc, 0x80000000, 1, None, 3, 0x02000000 | 0x00200000, None)
    invalid = ctypes.c_void_p(-1).value
    if handle is None or handle == invalid:
        return {"ok": False, "winerror": ctypes.get_last_error(), "stage": "open"}
    try:
        before = identity(kernel, handle)
        digest = hashlib.sha256()
        total = 0
        while True:
            buf = ctypes.create_string_buffer(1024 * 1024)
            got = ctypes.c_uint32(0)
            ok = kernel.ReadFile(handle, buf, len(buf), ctypes.byref(got), None)
            if not ok:
                return {"ok": False, "winerror": ctypes.get_last_error(), "stage": "read", "before": before}
            if got.value == 0:
                break
            digest.update(bytes(buf[: got.value]))
            total += got.value
        after = identity(kernel, handle)
        return {
            "ok": True,
            "before": before,
            "after": after,
            "sha256": digest.hexdigest(),
            "bytes_read": total,
            "payload_saved": False,
        }
    finally:
        kernel.CloseHandle(handle)


def main():
    from ctypes import wintypes as wt
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wt.LPCWSTR, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, wt.HANDLE]
    kernel.CreateFileW.restype = wt.HANDLE
    kernel.ReadFile.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p]
    kernel.ReadFile.restype = ctypes.c_int
    kernel.GetFileInformationByHandle.argtypes = [wt.HANDLE, ctypes.POINTER(FILEINFO)]
    kernel.GetFileInformationByHandle.restype = ctypes.c_int
    kernel.CloseHandle.argtypes = [wt.HANDLE]
    kernel.CloseHandle.restype = ctypes.c_int

    conn = reader.connect(PLAN)
    try:
        freeze = reader.plan_freeze_status(PLAN)
        digest = reader.plan_digest(conn) if freeze["frozen"] else None
    finally:
        conn.close()
    previous = json.loads(PREV.read_text(encoding="utf-8"))
    plan = sqlite3.connect(f"file:{PLAN.resolve().as_posix()}?mode=ro", uri=True)
    rows = []
    total = 0
    for item in previous["files"]:
        planned = plan.execute(
            "SELECT logical_size, volume_serial, file_id FROM paths WHERE path=?",
            (item["inventory_path"],),
        ).fetchone()
        passes = [read_once(kernel, item["path"]), read_once(kernel, item["path"])]
        for result in passes:
            total += int(result.get("bytes_read") or 0)
        stable = (
            passes[0].get("ok") and passes[1].get("ok")
            and passes[0]["sha256"] == passes[1]["sha256"]
            and passes[0]["bytes_read"] == passes[1]["bytes_read"]
            and passes[0]["before"] == passes[0]["after"] == passes[1]["before"] == passes[1]["after"]
        )
        plan_match = None
        if planned and passes[0].get("ok"):
            plan_match = {
                "logical_size": int(passes[0]["bytes_read"]) == int(planned[0]),
                "volume_serial": str(passes[0]["before"]["volume_serial"]) == str(planned[1]),
                "file_id": str(passes[0]["before"]["file_id"]) == str(planned[2]),
                "plan_has_content_sha": False,
                "plan_has_mtime": False,
            }
        rows.append({
            "kind": item["kind"],
            "inventory_path": item["inventory_path"],
            "expected_bytes": 6849 if item["kind"] == "e" else 2463,
            "plan_row": None if not planned else {"logical_size": planned[0], "volume_serial": planned[1], "file_id": planned[2]},
            "reads": passes,
            "stable": stable,
            "plan_match": plan_match,
        })
    plan.close()
    report = {
        "context": "zhangwei\\admin current unelevated process",
        "plan_sha256": digest,
        "plan_sha_matches_frozen_evidence": digest == EXPECTED_PLAN,
        "plan_freeze": freeze,
        "files": rows,
        "bytes_read_total": total,
        "scope": "TWO_REPRESENTATIVE_FILES_ONLY",
        "payload_saved": False,
        "production_reader_used": False,
        "note": "probe read passed; production copy body was not called",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "plan_ok": report["plan_sha_matches_frozen_evidence"],
        "stable": [row["stable"] for row in rows],
        "plan_match": [row["plan_match"] for row in rows],
        "bytes": total,
    }))


if __name__ == "__main__":
    main()
