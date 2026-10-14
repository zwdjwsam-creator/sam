# -*- coding: utf-8 -*-
"""No-follow reparse tag/target reader — adapted from query_d_reparse_and_share_facts_r1."""
from __future__ import annotations

import ctypes
import struct
import sys
from ctypes import wintypes

sys.path.insert(0, r"C:\LAN_SHARE_REPORT")
import r9_pilot_common_r9fix as r9  # noqa: E402

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value
FSCTL_GET_REPARSE_POINT = 0x000900A8
FileAttributeTagInfo = 9
IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
IO_REPARSE_TAG_SYMLINK = 0xA000000C

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
DeviceIoControl = kernel32.DeviceIoControl
DeviceIoControl.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID,
]
DeviceIoControl.restype = wintypes.BOOL
GetFileInformationByHandleEx = kernel32.GetFileInformationByHandleEx


class FILE_ATTRIBUTE_TAG_INFO(ctypes.Structure):
    _fields_ = [("FileAttributes", wintypes.DWORD), ("ReparseTag", wintypes.DWORD)]


def normalize_nt_path(p: str | None) -> str | None:
    if not p:
        return None
    s = p
    if s.startswith("\\??\\"):
        s = s[4:]
    if s.startswith("\\\\?\\"):
        s = s[4:]
    return s


def parse_reparse_buffer(buf: bytes) -> dict:
    if len(buf) < 8:
        return {"parse_error": "buffer_too_short", "raw_len": len(buf)}
    tag = struct.unpack_from("<I", buf, 0)[0]
    data_len = struct.unpack_from("<H", buf, 4)[0]
    out = {"reparse_tag": tag, "reparse_tag_hex": hex(tag), "data_length": data_len}
    try:
        if tag == IO_REPARSE_TAG_MOUNT_POINT:
            sub_off, sub_len, print_off, print_len = struct.unpack_from("<HHHH", buf, 8)
            path_buf = buf[16 : 16 + data_len - 8]
            sub = path_buf[sub_off : sub_off + sub_len].decode("utf-16-le", errors="replace").rstrip("\x00")
            prn = path_buf[print_off : print_off + print_len].decode("utf-16-le", errors="replace").rstrip("\x00")
            out.update({"substitute_name": sub, "print_name": prn, "flags": None})
        elif tag == IO_REPARSE_TAG_SYMLINK:
            sub_off, sub_len, print_off, print_len, flags = struct.unpack_from("<HHHHI", buf, 8)
            path_buf = buf[20 : 20 + data_len - 12]
            sub = path_buf[sub_off : sub_off + sub_len].decode("utf-16-le", errors="replace").rstrip("\x00")
            prn = path_buf[print_off : print_off + print_len].decode("utf-16-le", errors="replace").rstrip("\x00")
            out.update({"substitute_name": sub, "print_name": prn, "flags": int(flags)})
        else:
            out["raw_head_hex"] = buf[:64].hex()
    except Exception as e:
        out["parse_error"] = f"{type(e).__name__}:{e}"
    return out


def read_reparse_nofollow(path: str) -> dict:
    """Open as reparse point; do not follow. Return tag + raw/normalized target + optional identity."""
    rec = {
        "reparse_tag": None,
        "raw_target": None,
        "print_name": None,
        "normalized_target": None,
        "volume_serial": None,
        "file_id": None,
        "logical_size": None,
        "nlinks": None,
        "mtime_ft": None,
        "error": None,
    }
    h = r9.CreateFileW(
        r9.to_win_long_path(path),
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if h == INVALID_HANDLE_VALUE or h is None:
        err = ctypes.get_last_error()
        rec["error"] = f"CreateFileW_fail winerror={err}"
        return rec
    try:
        info = r9.BY_HANDLE_FILE_INFORMATION()
        if r9.GetFileInformationByHandle(h, ctypes.byref(info)):
            fid = (info.nFileIndexHigh << 32) | info.nFileIndexLow
            size = (info.nFileSizeHigh << 32) | info.nFileSizeLow
            mtime = (info.ftLastWriteTime.dwHighDateTime << 32) | info.ftLastWriteTime.dwLowDateTime
            rec["volume_serial"] = str(info.dwVolumeSerialNumber)
            rec["file_id"] = str(fid)
            rec["logical_size"] = int(size)
            rec["nlinks"] = int(info.nNumberOfLinks)
            rec["mtime_ft"] = str(mtime)

        tag_info = FILE_ATTRIBUTE_TAG_INFO()
        if GetFileInformationByHandleEx(h, FileAttributeTagInfo, ctypes.byref(tag_info), ctypes.sizeof(tag_info)):
            rec["reparse_tag"] = int(tag_info.ReparseTag)

        outbuf = ctypes.create_string_buffer(16 * 1024)
        ret = wintypes.DWORD(0)
        ok = DeviceIoControl(
            h,
            FSCTL_GET_REPARSE_POINT,
            None,
            0,
            outbuf,
            ctypes.sizeof(outbuf),
            ctypes.byref(ret),
            None,
        )
        if ok:
            parsed = parse_reparse_buffer(outbuf.raw[: ret.value])
            if rec["reparse_tag"] is None and "reparse_tag" in parsed:
                rec["reparse_tag"] = parsed["reparse_tag"]
            rec["raw_target"] = parsed.get("substitute_name")
            rec["print_name"] = parsed.get("print_name")
            rec["normalized_target"] = normalize_nt_path(parsed.get("substitute_name")) or normalize_nt_path(
                parsed.get("print_name")
            )
        else:
            err = ctypes.get_last_error()
            if not rec["error"]:
                rec["error"] = f"FSCTL_GET_REPARSE_POINT_fail winerror={err}"
    except Exception as e:
        rec["error"] = f"{type(e).__name__}:{e}"
    finally:
        r9.safe_close(h)
    return rec
