# -*- coding: utf-8 -*-
"""Shared path / WinAPI helpers for R9 1GiB pilot (post code-review fix)."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import socket
import sqlite3
from ctypes import wintypes
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

TZ = timezone(timedelta(hours=8))

# Desktop UNC source root (laptop E:\\BLACKBOX is inventory provenance only)
DESKTOP_UNC_SOURCE_ROOT = r"\\192.168.100.2\E_DRIVE\BLACKBOX"
ALLOWED_DEST = Path(r"E:\BLACKBOX_MANIFEST_PILOT_R9_1G")
REQUIRED_HOSTNAME = "ZHANGWEI"
EXPECTED_MANIFEST_SHA256 = (
    "cfb831ecc0a85fec0137b74a12162e169828d708ff57961df906deffb185c041"
)
EXPECTED_ENTITY_COUNT = 662
EXPECTED_PATH_COUNT = 22998
EXPECTED_UNIQUE_BYTES = 1_064_950_668
UNIQUE_CAP = 1_073_741_824

# From BLACKBOX_R8_DESKTOP_READY.md (desktop ZHANGWEI MarketData E:)
EXPECTED_DEST_VOLUME = {
    "VolumeSerialNumber_hex": "806508DF",
    "VolumeSerialNumber_dword": int("806508DF", 16),
    "UniqueId": "\\\\?\\Volume{b8545ee8-e403-48c6-9d3f-09afd3e0349f}\\",
    "FileSystem": "NTFS",
    "FileSystemLabel": "MarketData",
}

# Historical R8 freeze run — live cmdline must not still host these writers/monitors.
R8_LEGACY_RUN_ID = "20261010_173201_R8_3B85D677"
R8_REQUIRED_STOP_FIELDS = (
    "OLD_LN_STOPPED",
    "OLD_WRAPPER_STOPPED",
    "OLD_MONITORS_INACTIVE",
)
R8_PROC_CMDLINE_MARKERS = (
    R8_LEGACY_RUN_ID,
    "BLACKBOX_R8_SOURCE_FREEZE_MONITOR",
    "BLACKBOX_R8_SOURCE_FREEZE_MONITOR_V2",
    "BLACKBOX_R8_SOURCE_FREEZE_FINALIZE",
    "BLACKBOX_R8_FREEZE_STATE_REPAIR",
    "BLACKBOX_R8_SOURCE_FREEZE_T0_COLLECT",
)
SHA256_HEX_RE = re.compile(r"^[0-9a-fA-F]{64}$")
FILETIME_EPOCH_UTC = datetime(1601, 1, 1, tzinfo=timezone.utc)

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_NONE = 0
OPEN_EXISTING = 3
CREATE_NEW = 1
FILE_ATTRIBUTE_NORMAL = 0x80
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_COMPRESSED = 0x800
FILE_ATTRIBUTE_SPARSE_FILE = 0x200
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
FileStandardInfo = 1
FILE_BEGIN = 0
ERROR_SHARING_VIOLATION = 32
ERROR_LOCK_VIOLATION = 33

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", FILETIME),
        ("ftLastAccessTime", FILETIME),
        ("ftLastWriteTime", FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    ]


class FILE_STANDARD_INFO(ctypes.Structure):
    _fields_ = [
        ("AllocationSize", ctypes.c_int64),
        ("EndOfFile", ctypes.c_int64),
        ("NumberOfLinks", wintypes.DWORD),
        ("DeletePending", wintypes.BOOLEAN),
        ("Directory", wintypes.BOOLEAN),
    ]


class ULARGE_INTEGER(ctypes.Structure):
    _fields_ = [("QuadPart", ctypes.c_ulonglong)]


CreateFileW = kernel32.CreateFileW
CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]
CreateFileW.restype = wintypes.HANDLE

GetFileInformationByHandle = kernel32.GetFileInformationByHandle
GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(BY_HANDLE_FILE_INFORMATION)]
GetFileInformationByHandle.restype = wintypes.BOOL

GetFileInformationByHandleEx = kernel32.GetFileInformationByHandleEx
GetFileInformationByHandleEx.argtypes = [
    wintypes.HANDLE,
    ctypes.c_int,
    wintypes.LPVOID,
    wintypes.DWORD,
]
GetFileInformationByHandleEx.restype = wintypes.BOOL

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

GetFileAttributesW = kernel32.GetFileAttributesW
GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
GetFileAttributesW.restype = wintypes.DWORD

CreateHardLinkW = kernel32.CreateHardLinkW
CreateHardLinkW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPVOID]
CreateHardLinkW.restype = wintypes.BOOL

GetDiskFreeSpaceExW = kernel32.GetDiskFreeSpaceExW
GetDiskFreeSpaceExW.argtypes = [
    wintypes.LPCWSTR,
    ctypes.POINTER(ctypes.c_ulonglong),
    ctypes.POINTER(ctypes.c_ulonglong),
    ctypes.POINTER(ctypes.c_ulonglong),
]
GetDiskFreeSpaceExW.restype = wintypes.BOOL

GetVolumeInformationW = kernel32.GetVolumeInformationW
GetVolumeInformationW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPWSTR,
    wintypes.DWORD,
]
GetVolumeInformationW.restype = wintypes.BOOL

ReadFile = kernel32.ReadFile
ReadFile.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID,
]
ReadFile.restype = wintypes.BOOL

WriteFile = kernel32.WriteFile
WriteFile.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID,
]
WriteFile.restype = wintypes.BOOL

FlushFileBuffers = kernel32.FlushFileBuffers
FlushFileBuffers.argtypes = [wintypes.HANDLE]
FlushFileBuffers.restype = wintypes.BOOL

SetFilePointerEx = kernel32.SetFilePointerEx
SetFilePointerEx.argtypes = [
    wintypes.HANDLE,
    ctypes.c_int64,
    ctypes.POINTER(ctypes.c_int64),
    wintypes.DWORD,
]
SetFilePointerEx.restype = wintypes.BOOL


def now_iso() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file_path(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def to_win_long_path(path: str) -> str:
    """Extend local / UNC / already-extended paths correctly."""
    if not path:
        raise ValueError("EMPTY_PATH")
    if path.startswith("\\\\?\\"):
        return path
    if path.startswith("\\\\"):
        # \\server\share\... -> \\?\UNC\server\share\...
        return "\\\\?\\UNC\\" + path[2:]
    return "\\\\?\\" + path


def validate_relative_path(rel: str) -> str:
    """Reject absolute/UNC/drive/.. /ADS/empty before any cleanup. Never lstrip into legality."""
    if rel is None:
        raise ValueError("REL_NONE")
    if not isinstance(rel, str) or rel == "":
        raise ValueError("REL_EMPTY")
    if rel != rel.strip():
        raise ValueError(f"REL_EDGE_WHITESPACE:{rel!r}")
    # absolute / UNC / drive
    if rel.startswith("\\\\") or rel.startswith("//"):
        raise ValueError(f"REL_UNC_OR_ABS:{rel}")
    if len(rel) >= 2 and rel[1] == ":":
        raise ValueError(f"REL_DRIVE:{rel}")
    if rel.startswith("/") or rel.startswith("\\"):
        raise ValueError(f"REL_ROOTED:{rel}")
    # normalize separators for checks only
    norm = rel.replace("/", "\\")
    if ":" in norm:
        raise ValueError(f"REL_COLON_ADS:{rel}")
    parts = norm.split("\\")
    if any(p == "" for p in parts):
        raise ValueError(f"REL_EMPTY_SEGMENT:{rel}")
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    for p in parts:
        if p in (".", ".."):
            raise ValueError(f"REL_DOT_SEGMENT:{rel}")
        if p.upper().split(".")[0] in reserved:
            raise ValueError(f"REL_RESERVED:{rel}")
        if p.endswith(" ") or p.endswith("."):
            raise ValueError(f"REL_TRAILING_BAD:{rel}")
    return norm


def join_unc_source(rel: str, source_root: str = DESKTOP_UNC_SOURCE_ROOT) -> str:
    rel_n = validate_relative_path(rel)
    root = source_root.rstrip("\\")
    return root + "\\" + rel_n


def dest_under_root(dest_root: Path, rel: str) -> Path:
    rel_n = validate_relative_path(rel)
    parts = rel_n.split("\\")
    dest = dest_root.joinpath(*parts)
    root_s = str(dest_root).rstrip("\\") + "\\"
    if not str(dest).lower().startswith(root_s.lower()):
        raise ValueError(f"DEST_OUTSIDE_ROOT:{dest}")
    return dest


def safe_close(handle) -> None:
    if handle is None:
        return
    try:
        if handle != INVALID_HANDLE_VALUE and handle != 0:
            CloseHandle(handle)
    except Exception:
        pass


# Win32 codes used by GetFileAttributesW / CreateFileW (also appear in OSError.errno
# when raised as OSError(win32_code, msg) from this module).
ERROR_FILE_NOT_FOUND = 2
ERROR_PATH_NOT_FOUND = 3


def get_attrs(path: str) -> int:
    attrs = GetFileAttributesW(to_win_long_path(path))
    if attrs == 0xFFFFFFFF:
        err = ctypes.get_last_error()
        raise OSError(err, f"GetFileAttributesW failed path={path} winerror={err}")
    return int(attrs)


def win32_error_code(exc: BaseException) -> int | None:
    """Read Win32 code from OSError; get_attrs stores it in errno (not only winerror)."""
    if not isinstance(exc, OSError):
        return None
    for attr in ("winerror", "errno"):
        v = getattr(exc, attr, None)
        if isinstance(v, int) and v > 0:
            return v
    return None


def strip_win_long_prefix(path: str) -> str:
    """Inverse of to_win_long_path for local/UNC; no other string mutation."""
    if path.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path[8:]
    if path.startswith("\\\\?\\"):
        return path[4:]
    return path


def relative_under_root(path: str | Path, root: str | Path) -> str:
    """Relative path under root using comparable non-prefixed forms; enforce boundary."""
    p = strip_win_long_prefix(str(path)).replace("/", "\\")
    r = strip_win_long_prefix(str(root)).replace("/", "\\").rstrip("\\")
    pref = r + "\\"
    if p.rstrip("\\").lower() == r.lower():
        raise ValueError(f"PATH_IS_ROOT:{path}")
    if not p.lower().startswith(pref.lower()):
        raise ValueError(f"DEST_OUTSIDE_ROOT:{path}")
    return p[len(pref) :]


def classify_path_presence(path: str) -> str:
    """Return 'present' or 'missing'. Other attr/API failures raise OSError."""
    try:
        get_attrs(path)
        return "present"
    except OSError as e:
        code = win32_error_code(e)
        if code in (ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND):
            return "missing"
        raise


def path_exists_win(path: str) -> bool:
    """Long-path-aware existence; missing => False; other errors raise."""
    return classify_path_presence(path) == "present"


def is_reparse_path(path: str) -> bool:
    return bool(get_attrs(path) & FILE_ATTRIBUTE_REPARSE_POINT)


def ensure_no_reparse_ancestors(path: Path, stop_at: Path | None = None) -> None:
    """Fail if path or any ancestor (down to stop_at or drive root) is reparse. Attr fail ≠ safe."""
    cur = Path(str(path))
    stop = Path(str(stop_at)).resolve() if stop_at else None
    seen = set()
    while True:
        key = str(cur).rstrip("\\").lower()
        if key in seen:
            break
        seen.add(key)
        try:
            if is_reparse_path(str(cur)):
                raise RuntimeError(f"REPARSE_PATH:{cur}")
        except OSError as e:
            raise RuntimeError(f"ATTR_QUERY_FAIL_NOT_SAFE:{cur}:{e}") from e
        if stop and key == str(stop).rstrip("\\").lower():
            break
        parent = cur.parent
        if parent == cur:
            break
        # stop at drive root
        if len(str(cur)) <= 3 and str(cur)[1:2] == ":":
            break
        cur = parent


def open_source_stable(path: str):
    """Read-only handle denying concurrent write/delete; open reparse point (do not follow).

    If SMB/local cannot grant FILE_SHARE_READ-only open (writers present), fail closed —
    do not relax share mode or change source ACLs.
    """
    h = CreateFileW(
        to_win_long_path(path),
        GENERIC_READ,
        FILE_SHARE_READ,  # deny WRITE/DELETE
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if h == INVALID_HANDLE_VALUE or h is None:
        err = ctypes.get_last_error()
        if err in (ERROR_SHARING_VIOLATION, ERROR_LOCK_VIOLATION):
            raise RuntimeError(
                f"SMB_STABLE_READ_UNAVAILABLE path={path} winerror={err} "
                "(refusing share-mode downgrade)"
            )
        raise OSError(err, f"open_source_fail path={path} winerror={err}")
    return h


def seek_begin(h) -> None:
    newpos = ctypes.c_int64(0)
    if not SetFilePointerEx(h, ctypes.c_int64(0), ctypes.byref(newpos), FILE_BEGIN):
        err = ctypes.get_last_error()
        raise OSError(err, f"SetFilePointerEx fail winerror={err}")


def handle_identity(h) -> dict:
    info = BY_HANDLE_FILE_INFORMATION()
    if not GetFileInformationByHandle(h, ctypes.byref(info)):
        err = ctypes.get_last_error()
        raise OSError(err, f"GetFileInformationByHandle fail winerror={err}")
    if info.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT:
        raise RuntimeError("SOURCE_IS_REPARSE")
    fid = (info.nFileIndexHigh << 32) | info.nFileIndexLow
    size = (info.nFileSizeHigh << 32) | info.nFileSizeLow
    mtime = (info.ftLastWriteTime.dwHighDateTime << 32) | info.ftLastWriteTime.dwLowDateTime
    std = FILE_STANDARD_INFO()
    alloc = None
    if not GetFileInformationByHandleEx(h, FileStandardInfo, ctypes.byref(std), ctypes.sizeof(std)):
        err = ctypes.get_last_error()
        raise OSError(err, f"FileStandardInfo/AllocationSize unavailable winerror={err}")
    alloc = int(std.AllocationSize)
    attrs = int(info.dwFileAttributes)
    return {
        "volume_serial": str(info.dwVolumeSerialNumber),
        "volume_serial_dword": int(info.dwVolumeSerialNumber),
        "file_id": str(fid),
        "size": int(size),
        "nlinks": int(info.nNumberOfLinks),
        "attrs": attrs,
        "mtime_ft": str(mtime),
        "allocation_size": alloc,
        "is_compressed": bool(attrs & FILE_ATTRIBUTE_COMPRESSED),
        "is_sparse": bool(attrs & FILE_ATTRIBUTE_SPARSE_FILE),
    }


def read_exact_hash(h, expect_size: int) -> tuple[bytes, str]:
    """Bounded read of expect_size bytes; fail if short/long stream."""
    if expect_size < 0:
        raise ValueError("NEG_SIZE")
    hsh = hashlib.sha256()
    remaining = expect_size
    buf_size = 1024 * 1024
    total = 0
    while remaining > 0:
        chunk_n = min(buf_size, remaining)
        buf = ctypes.create_string_buffer(chunk_n)
        read = wintypes.DWORD(0)
        ok = ReadFile(h, buf, chunk_n, ctypes.byref(read), None)
        if not ok:
            err = ctypes.get_last_error()
            raise OSError(err, f"ReadFile fail winerror={err}")
        if read.value == 0:
            raise RuntimeError(f"SOURCE_SHORT expect={expect_size} got={total}")
        data = buf.raw[: read.value]
        hsh.update(data)
        total += read.value
        remaining -= read.value
    # probe one more byte — must be EOF; ReadFile failure ≠ EOF success
    probe = ctypes.create_string_buffer(1)
    read2 = wintypes.DWORD(0)
    ok2 = ReadFile(h, probe, 1, ctypes.byref(read2), None)
    if not ok2:
        err = ctypes.get_last_error()
        raise OSError(err, f"EOF_PROBE_ReadFile_fail winerror={err}")
    if read2.value != 0:
        raise RuntimeError(f"SOURCE_GREW_OR_LONGER expect={expect_size}")
    return b"", hsh.hexdigest()  # content not retained; hash only


def copy_bounded(src_h, dest_path: str, expect_size: int, unique_budget_left: int) -> dict:
    if expect_size > unique_budget_left:
        raise RuntimeError(f"UNIQUE_CAP_BREACH need={expect_size} left={unique_budget_left}")
    # exclusive create
    dh = CreateFileW(
        to_win_long_path(dest_path),
        GENERIC_WRITE,
        FILE_SHARE_NONE,
        None,
        CREATE_NEW,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if dh == INVALID_HANDLE_VALUE or dh is None:
        err = ctypes.get_last_error()
        raise OSError(err, f"CREATE_NEW_FAIL path={dest_path} winerror={err}")
    hsh = hashlib.sha256()
    remaining = expect_size
    total = 0
    try:
        buf_size = 1024 * 1024
        while remaining > 0:
            chunk_n = min(buf_size, remaining)
            buf = ctypes.create_string_buffer(chunk_n)
            read = wintypes.DWORD(0)
            if not ReadFile(src_h, buf, chunk_n, ctypes.byref(read), None):
                err = ctypes.get_last_error()
                raise OSError(err, f"ReadFile fail winerror={err}")
            if read.value == 0:
                raise RuntimeError(f"SOURCE_SHORT expect={expect_size} got={total}")
            written = wintypes.DWORD(0)
            if not WriteFile(dh, buf, read.value, ctypes.byref(written), None):
                err = ctypes.get_last_error()
                raise OSError(err, f"WriteFile fail winerror={err}")
            if written.value != read.value:
                raise RuntimeError("SHORT_WRITE")
            hsh.update(buf.raw[: read.value])
            total += read.value
            remaining -= read.value
        probe = ctypes.create_string_buffer(1)
        read2 = wintypes.DWORD(0)
        ok2 = ReadFile(src_h, probe, 1, ctypes.byref(read2), None)
        if not ok2:
            err = ctypes.get_last_error()
            raise OSError(err, f"EOF_PROBE_ReadFile_fail winerror={err}")
        if read2.value != 0:
            raise RuntimeError("SOURCE_LONGER_THAN_MANIFEST")
        if not FlushFileBuffers(dh):
            err = ctypes.get_last_error()
            raise OSError(err, f"FlushFileBuffers fail winerror={err}")
        return {"sha256": hsh.hexdigest(), "bytes": total}
    finally:
        safe_close(dh)


def volume_free_bytes(root_path: str) -> int:
    # use drive root for local paths
    p = root_path
    if len(p) >= 2 and p[1] == ":":
        p = p[:2] + "\\"
    avail = ctypes.c_ulonglong(0)
    total = ctypes.c_ulonglong(0)
    free_total = ctypes.c_ulonglong(0)
    if not GetDiskFreeSpaceExW(
        to_win_long_path(p) if not p.startswith("\\\\") else to_win_long_path(p),
        ctypes.byref(avail),
        ctypes.byref(total),
        ctypes.byref(free_total),
    ):
        # try without long path for drive root
        if not GetDiskFreeSpaceExW(p, ctypes.byref(avail), ctypes.byref(total), ctypes.byref(free_total)):
            err = ctypes.get_last_error()
            raise OSError(err, f"GetDiskFreeSpaceExW fail winerror={err}")
    return int(avail.value)


def get_volume_identity(root: str = "E:\\") -> dict:
    vol_name = ctypes.create_unicode_buffer(261)
    fs_name = ctypes.create_unicode_buffer(261)
    serial = wintypes.DWORD(0)
    max_comp = wintypes.DWORD(0)
    flags = wintypes.DWORD(0)
    root_path = root if root.endswith("\\") else root + "\\"
    ok = GetVolumeInformationW(
        root_path,
        vol_name,
        261,
        ctypes.byref(serial),
        ctypes.byref(max_comp),
        ctypes.byref(flags),
        fs_name,
        261,
    )
    if not ok:
        err = ctypes.get_last_error()
        raise OSError(err, f"GetVolumeInformationW fail winerror={err}")
    return {
        "root": root_path,
        "VolumeSerialNumber_dword": int(serial.value),
        "VolumeSerialNumber_hex": f"{int(serial.value):08X}",
        "FileSystem": fs_name.value,
        "VolumeName": vol_name.value,
    }


def hostname_ok() -> tuple[bool, str]:
    name = socket.gethostname()
    return name.upper() == REQUIRED_HOSTNAME.upper(), name


def _normalize_r8_token(v: Any) -> str:
    if v is True or v is False:
        return "TRUE" if v is True else "FALSE"
    if isinstance(v, (int, float)) and v in (0, 1):
        return "TRUE" if int(v) == 1 else "FALSE"
    if isinstance(v, str):
        s = v.strip().upper()
        if s in ("TRUE", "1", "YES"):
            return "TRUE"
        if s in ("FALSE", "0", "NO"):
            return "FALSE"
        if s in ("UNKNOWN", "NULL", "NONE", ""):
            return "UNKNOWN"
        return s
    return "UNKNOWN"


def parse_r8_stop_report(path: Path) -> dict:
    """Require OLD_LN/WRAPPER/MONITORS fields complete, conflict-free, exactly TRUE.

    Accepts JSON object or KEY=VALUE / KEY: VALUE text (real report styles).
    Historical READY / DESKTOP_READY / WRITERS_STOPPED alone is NEVER sufficient.
    Duplicate keys with conflicting values → reject.
    """
    if not path.exists():
        return {"ok": False, "reason": "MISSING_FILE", "fields": {}}
    text = path.read_text(encoding="utf-8", errors="replace")
    collected: dict[str, list[str]] = {k: [] for k in R8_REQUIRED_STOP_FIELDS}

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            for k in R8_REQUIRED_STOP_FIELDS:
                if k in obj:
                    collected[k].append(_normalize_r8_token(obj[k]))
    except json.JSONDecodeError:
        pass

    for k in R8_REQUIRED_STOP_FIELDS:
        for m in re.finditer(
            rf"(?im)^\s*{re.escape(k)}\s*[=:]\s*([A-Za-z0-9_]+)\s*$",
            text,
        ):
            collected[k].append(_normalize_r8_token(m.group(1)))
        # markdown / bullet: **OLD_LN_STOPPED** = `TRUE` or - OLD_LN_STOPPED: TRUE
        for m in re.finditer(
            rf"(?im){re.escape(k)}\s*[=:]\s*`?(TRUE|FALSE|UNKNOWN|1|0)`?",
            text,
        ):
            collected[k].append(_normalize_r8_token(m.group(1)))

    fields: dict[str, str] = {}
    conflicts = []
    missing = []
    for k in R8_REQUIRED_STOP_FIELDS:
        vals = collected[k]
        if not vals:
            missing.append(k)
            continue
        uniq = sorted(set(vals))
        if len(uniq) > 1:
            conflicts.append({"field": k, "values": uniq})
            continue
        fields[k] = uniq[0]

    if conflicts:
        return {"ok": False, "reason": "FIELD_VALUE_CONFLICT", "conflicts": conflicts, "fields": fields}
    if missing:
        return {"ok": False, "reason": "FIELDS_MISSING", "missing": missing, "fields": fields}
    bad = [k for k, v in fields.items() if v != "TRUE"]
    if bad:
        return {
            "ok": False,
            "reason": "NOT_ALL_TRUE",
            "falsy": bad,
            "fields": fields,
            "note": "FALSE/UNKNOWN/other rejected; historical READY alone insufficient",
        }
    return {"ok": True, "fields": {k: True for k in R8_REQUIRED_STOP_FIELDS}, "path": str(path)}


_R8_CMDLINE_REQUIRED_NAMES = frozenset(
    {"ln.exe", "powershell.exe", "pwsh.exe", "cmd.exe"}
)


def live_r8_process_check(
    *,
    allow_env_skip: bool = False,
    proc_snapshot: list | None = None,
) -> dict:
    """Reject if legacy R8 RUN_ID / freeze scripts / ln wrapper still live in cmdline.

    Uses Win32_Process CommandLine + CreationDate + ParentProcessId (not process-name-only).
    Fail-closed: query errors, empty/non-list data, malformed rows, or unreadable
    CommandLine on ln/powershell/pwsh/cmd ⇒ ok=false (UNKNOWN), never "no old task".
    R9_SKIP_PROC_CHECK / forged empty snapshot cannot pass the gate.
    proc_snapshot: test injection only; same validation rules apply (non-empty list).
    """
    import subprocess

    # Skip is never a PASS — copy preflight must call allow_env_skip=False; even if
    # env is set, returning ok=true would forge a clean process plane.
    if allow_env_skip and os.environ.get("R9_SKIP_PROC_CHECK") == "1":
        return {
            "ok": False,
            "reason": "PROC_CHECK_SKIP_NOT_ALLOWED",
            "suspicious": [],
            "skipped": True,
        }

    suspicious: list[dict[str, Any]] = []
    try:
        if proc_snapshot is not None:
            data = proc_snapshot
        else:
            ps = (
                "$ErrorActionPreference='Stop'; "
                "Get-CimInstance Win32_Process -ErrorAction Stop | "
                "Select-Object ProcessId,ParentProcessId,Name,CommandLine,CreationDate | "
                "ConvertTo-Json -Compress -Depth 3"
            )
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps],
                text=True,
                errors="replace",
                timeout=45,
            )
            if not (out or "").strip():
                return {
                    "ok": False,
                    "reason": "PROC_CHECK_EMPTY_OUTPUT",
                    "suspicious": [],
                }
            try:
                data = json.loads(out)
            except json.JSONDecodeError as e:
                return {
                    "ok": False,
                    "reason": f"PROC_CHECK_JSON_FAIL:{e}",
                    "suspicious": [],
                }
            if isinstance(data, dict):
                data = [data]

        if not isinstance(data, list) or len(data) == 0:
            return {
                "ok": False,
                "reason": "PROC_CHECK_EMPTY_OR_NOT_LIST",
                "suspicious": [],
                "detail": f"type={type(data).__name__}",
            }

        markers = tuple(m.lower() for m in R8_PROC_CMDLINE_MARKERS)
        for proc in data:
            if not isinstance(proc, dict):
                return {
                    "ok": False,
                    "reason": "PROC_CHECK_MALFORMED_ROW",
                    "suspicious": [],
                }
            name_raw = proc.get("Name")
            if name_raw is None or not str(name_raw).strip():
                return {
                    "ok": False,
                    "reason": "PROC_CHECK_MALFORMED_ROW",
                    "suspicious": [],
                    "detail": "missing Name",
                }
            name = str(name_raw).lower()
            cmd_raw = proc.get("CommandLine")
            # Sensitive shells/tools: unreadble cmdline ⇒ UNKNOWN, not clean.
            if name in _R8_CMDLINE_REQUIRED_NAMES:
                if cmd_raw is None or (isinstance(cmd_raw, str) and not cmd_raw.strip()):
                    return {
                        "ok": False,
                        "reason": "PROC_CMDLINE_UNREADABLE",
                        "status": "UNKNOWN",
                        "suspicious": [
                            {
                                "ProcessId": proc.get("ProcessId"),
                                "ParentProcessId": proc.get("ParentProcessId"),
                                "Name": proc.get("Name"),
                                "CreationDate": str(proc.get("CreationDate") or ""),
                                "CommandLine": None,
                            }
                        ],
                    }

            cmd = str(cmd_raw) if cmd_raw is not None else ""
            low = cmd.lower()
            hit = None
            for mk in markers:
                if mk in low:
                    hit = mk
                    break
            if hit is None and name == "ln.exe":
                if "blackbox" in low or R8_LEGACY_RUN_ID.lower() in low or "freeze" in low:
                    hit = "ln.exe+blackbox_context"
            if hit is None:
                continue
            if "live_r8_process_check" in low or "_hub_upload_r9" in low:
                continue
            if "run_r9fix_lean_tests" in low or "r9_pilot_common_r9fix" in low:
                continue
            suspicious.append(
                {
                    "ProcessId": proc.get("ProcessId"),
                    "ParentProcessId": proc.get("ParentProcessId"),
                    "Name": proc.get("Name"),
                    "CreationDate": str(proc.get("CreationDate") or ""),
                    "marker": hit,
                    "CommandLine": cmd[:500],
                }
            )
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "PROC_CHECK_TIMEOUT", "suspicious": []}
    except Exception as e:
        return {"ok": False, "reason": f"PROC_CHECK_FAIL:{e}", "suspicious": []}
    if suspicious:
        return {
            "ok": False,
            "reason": "R8_LEGACY_TASK_STILL_RUNNING",
            "run_id": R8_LEGACY_RUN_ID,
            "suspicious": suspicious,
        }
    return {"ok": True, "suspicious": [], "run_id": R8_LEGACY_RUN_ID}


def is_valid_sha256_hex(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_HEX_RE.fullmatch(value))


def filetime_to_utc_datetime(mtime_ft: int | str) -> datetime:
    ft = int(mtime_ft)
    if ft < 0:
        raise ValueError("NEG_FILETIME")
    # 100-ns intervals → microseconds (floor)
    return FILETIME_EPOCH_UTC + timedelta(microseconds=ft // 10)


def parse_manifest_last_write_time(raw: Any) -> datetime:
    """Parse manifest source_last_write_time (ISO UTC text). Unparseable → raise."""
    if raw is None:
        raise ValueError("MTIME_NONE")
    s = str(raw).strip()
    if not s:
        raise ValueError("MTIME_EMPTY")
    if s.isdigit():
        # Rare numeric FILETIME form — still accepted if present
        return filetime_to_utc_datetime(s)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        raise ValueError(f"MTIME_UNPARSEABLE:{raw!r}") from e
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def manifest_mtime_precision_seconds(raw: Any) -> int:
    """Infer compare precision from textual form (default seconds for ...Z / no fraction)."""
    s = str(raw).strip()
    if s.isdigit():
        return 0  # full FILETIME tick compare via exact int equality elsewhere
    # fractional seconds after '.' before tz
    m = re.search(r"\.(\d+)", s)
    if not m:
        return 0  # whole seconds
    return min(len(m.group(1)), 6)


def compare_mtime_manifest_vs_handle(manifest_raw: Any, mtime_ft: int | str) -> None:
    """Compare at manifest precision; raise RuntimeError on drift / unparseable."""
    try:
        m_dt = parse_manifest_last_write_time(manifest_raw)
    except ValueError as e:
        raise RuntimeError(f"SOURCE_MTIME_UNPARSEABLE:{e}") from e
    s = str(manifest_raw).strip()
    if s.isdigit():
        if str(int(mtime_ft)) != str(int(s)):
            raise RuntimeError(
                f"SOURCE_MTIME_DRIFT manifest_ft={s} live_ft={mtime_ft}"
            )
        return
    live_dt = filetime_to_utc_datetime(mtime_ft)
    frac = manifest_mtime_precision_seconds(manifest_raw)
    if frac <= 0:
        if m_dt.replace(microsecond=0) != live_dt.replace(microsecond=0):
            raise RuntimeError(
                f"SOURCE_MTIME_DRIFT manifest={m_dt.strftime('%Y-%m-%dT%H:%M:%SZ')} "
                f"live={live_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}"
            )
    else:
        # truncate both to frac decimal digits of seconds
        scale = 10 ** (6 - frac)
        m_us = (m_dt.microsecond // scale) * scale
        l_us = (live_dt.microsecond // scale) * scale
        if m_dt.replace(microsecond=m_us) != live_dt.replace(microsecond=l_us):
            raise RuntimeError(
                f"SOURCE_MTIME_DRIFT manifest={m_dt.isoformat()} live={live_dt.isoformat()}"
            )


def norm_vol_serial(v: Any) -> str:
    if v is None:
        raise ValueError("VOL_NONE")
    s = str(v).strip()
    if not s:
        raise ValueError("VOL_EMPTY")
    if re.fullmatch(r"[0-9]+", s):
        return str(int(s))
    if re.fullmatch(r"[0-9a-fA-F]+", s):
        return str(int(s, 16))
    raise ValueError(f"VOL_BAD:{v!r}")


def compare_identity_vol_fid_size(
    *,
    manifest_volume_serial: Any,
    manifest_file_id: Any,
    manifest_size: Any,
    live: dict,
    label: str = "source",
) -> None:
    try:
        mv = norm_vol_serial(manifest_volume_serial)
        lv = norm_vol_serial(live.get("volume_serial_dword", live.get("volume_serial")))
    except ValueError as e:
        raise RuntimeError(f"IDENTITY_VOL_PARSE:{label}:{e}") from e
    mf = str(manifest_file_id).strip()
    lf = str(live.get("file_id")).strip()
    ms = int(manifest_size)
    ls = int(live.get("size"))
    if mv != lv or mf != lf or ms != ls:
        raise RuntimeError(
            f"SOURCE_IDENTITY_DRIFT:{label} "
            f"manifest=(vol={mv},fid={mf},size={ms}) live=(vol={lv},fid={lf},size={ls})"
        )


def compare_hardlink_sibling_identity(primary: dict, sibling: dict, path: str) -> None:
    try:
        pv = norm_vol_serial(primary.get("volume_serial_dword", primary.get("volume_serial")))
        sv = norm_vol_serial(sibling.get("volume_serial_dword", sibling.get("volume_serial")))
    except ValueError as e:
        raise RuntimeError(f"HL_VOL_PARSE:{path}:{e}") from e
    if pv != sv or str(primary.get("file_id")) != str(sibling.get("file_id")):
        raise RuntimeError(
            f"HL_SPLIT path={path} primary=(vol={pv},fid={primary.get('file_id')}) "
            f"sib=(vol={sv},fid={sibling.get('file_id')})"
        )


def validate_copy_record_integrity(
    crec: dict,
    expected_entity_ids: set[int],
    *,
    require_full_pilot_counts: bool = True,
) -> list[str]:
    """Acceptance binding: unique entity_id set match, SHA256, run_id, space evidence."""
    deficits: list[str] = []
    run_id = crec.get("run_id")
    if run_id is None or (isinstance(run_id, str) and not run_id.strip()) or run_id == "":
        deficits.append("COPY_RECORD_RUN_ID_MISSING")
    for key in ("volume_free_before", "volume_free_after"):
        v = crec.get(key)
        if v is None or not isinstance(v, (int, float)) or isinstance(v, bool):
            deficits.append(f"COPY_RECORD_SPACE_EVIDENCE_MISSING:{key}")
        elif int(v) < 0:
            deficits.append(f"COPY_RECORD_SPACE_EVIDENCE_INVALID:{key}")
    ents = crec.get("entities")
    if not isinstance(ents, list) or not ents:
        deficits.append("COPY_RECORD_ENTITIES_MISSING")
        return deficits
    ids: list[int] = []
    for i, e in enumerate(ents):
        if not isinstance(e, dict) or "entity_id" not in e:
            deficits.append(f"COPY_RECORD_ENTITY_MALFORMED:{i}")
            continue
        try:
            eid = int(e["entity_id"])
        except (TypeError, ValueError):
            deficits.append(f"COPY_RECORD_ENTITY_ID_BAD:{i}")
            continue
        ids.append(eid)
        sha = e.get("sha256")
        if not is_valid_sha256_hex(sha):
            deficits.append(f"COPY_RECORD_SHA_INVALID:entity={eid}")
    if len(ids) != len(set(ids)):
        deficits.append("COPY_RECORD_ENTITY_ID_DUPLICATE")
    id_set = set(ids)
    if id_set != set(expected_entity_ids):
        missing = sorted(set(expected_entity_ids) - id_set)
        extra = sorted(id_set - set(expected_entity_ids))
        if missing:
            deficits.append(f"COPY_RECORD_ENTITY_MISSING:{len(missing)}")
        if extra:
            deficits.append(f"COPY_RECORD_ENTITY_EXTRA:{len(extra)}")
    if require_full_pilot_counts:
        if len(id_set) != EXPECTED_ENTITY_COUNT:
            deficits.append(f"COPY_RECORD_ENTITY_COUNT={len(id_set)} expected={EXPECTED_ENTITY_COUNT}")
        if crec.get("path_count") != EXPECTED_PATH_COUNT:
            deficits.append(f"COPY_RECORD_PATH_COUNT={crec.get('path_count')}")
        if crec.get("unique_bytes") != EXPECTED_UNIQUE_BYTES:
            deficits.append(f"COPY_RECORD_UNIQUE={crec.get('unique_bytes')}")
    return deficits


def validate_manifest_structure(con: sqlite3.Connection) -> dict:
    n_ent = con.execute("select count(*) from entities").fetchone()[0]
    n_path = con.execute("select count(*) from hardlink_paths").fetchone()[0]
    sum_u = con.execute("select coalesce(sum(unique_file_bytes),0) from entities").fetchone()[0]
    issues = []
    if n_ent == 0 or n_path == 0:
        issues.append("EMPTY_MANIFEST")
    if n_ent != EXPECTED_ENTITY_COUNT:
        issues.append(f"ENTITY_COUNT={n_ent} expected={EXPECTED_ENTITY_COUNT}")
    if n_path != EXPECTED_PATH_COUNT:
        issues.append(f"PATH_COUNT={n_path} expected={EXPECTED_PATH_COUNT}")
    if int(sum_u) != EXPECTED_UNIQUE_BYTES:
        issues.append(f"UNIQUE_BYTES={sum_u} expected={EXPECTED_UNIQUE_BYTES}")
    if int(sum_u) > UNIQUE_CAP:
        issues.append("OVER_UNIQUE_CAP")
    # orphan paths
    orphans = con.execute(
        "select count(*) from hardlink_paths h left join entities e on e.entity_id=h.entity_id where e.entity_id is null"
    ).fetchone()[0]
    if orphans:
        issues.append(f"ORPHAN_PATHS={orphans}")
    # entities without paths
    empty_e = con.execute(
        "select count(*) from entities e where not exists (select 1 from hardlink_paths h where h.entity_id=e.entity_id)"
    ).fetchone()[0]
    if empty_e:
        issues.append(f"ENTITIES_WITHOUT_PATHS={empty_e}")
    # duplicate entity keys
    dup_keys = con.execute(
        "select volume_serial, file_id, count(*) c from entities group by volume_serial, file_id having c>1"
    ).fetchall()
    if dup_keys:
        issues.append(f"DUP_ENTITY_KEYS={len(dup_keys)}")
    # path conflicts (same abs path -> different entity)
    dup_abs = con.execute(
        "select source_absolute_path, count(distinct entity_id) c from hardlink_paths group by source_absolute_path having c>1"
    ).fetchall()
    if dup_abs:
        issues.append(f"ABS_PATH_MULTI_ENTITY={len(dup_abs)}")
    dup_rel = con.execute(
        "select source_relative_path, count(distinct entity_id) c from hardlink_paths group by source_relative_path having c>1"
    ).fetchall()
    if dup_rel:
        issues.append(f"REL_PATH_MULTI_ENTITY={len(dup_rel)}")
    # size fields
    bad_size = con.execute(
        "select count(*) from entities where unique_file_bytes is null or unique_file_bytes < 0 "
        "or source_file_size is null or source_file_size < 0 "
        "or unique_file_bytes != source_file_size"
    ).fetchone()[0]
    if bad_size:
        issues.append(f"SIZE_FIELD_INCONSISTENT={bad_size}")
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "entity_count": n_ent,
        "path_count": n_path,
        "unique_bytes": int(sum_u),
    }


def bind_manifest(path: Path) -> tuple[sqlite3.Connection, dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    digest = sha256_file_path(path)
    if digest != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError(
            f"MANIFEST_SHA_MISMATCH got={digest} expected={EXPECTED_MANIFEST_SHA256} "
            "(regenerate + re-review; do not silent-replace)"
        )
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    struct = validate_manifest_structure(con)
    if not struct["ok"]:
        con.close()
        raise RuntimeError("MANIFEST_STRUCT_FAIL:" + ",".join(struct["issues"]))
    return con, {"sha256": digest, "path": str(path), **struct}
