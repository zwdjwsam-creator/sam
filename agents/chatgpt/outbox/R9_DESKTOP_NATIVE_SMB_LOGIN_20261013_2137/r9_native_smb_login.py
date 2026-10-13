# -*- coding: utf-8 -*-
"""One Windows-owned credential prompt; then metadata-only source-root checks.
No password parameter, password buffer, saved credential access, drive mapping,
account/policy changes, business file read/copy, or destination disk writes.
"""
import ctypes
import json
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

TASK = "R9_DESKTOP_NATIVE_SMB_LOGIN_20261013_2137"
ACCOUNT = r"SAM\ThinkPad"
SHARE = r"\\192.168.100.2\E_DRIVE"
STATUS = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_NATIVE_SMB_LOGIN_20261013\STATUS.json")
ROOTS = (
    (r"\\192.168.100.2\E_DRIVE\BLACKBOX", 2387166462),
    (r"\\192.168.100.2\D_DRIVE", 3187598165),
)

def record(state, **extra):
    payload = {
        "task_id": TASK, "host": socket.gethostname(),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "state": state, "source_account_candidate": ACCOUNT,
        "format_done": False, "copy_authorized": False,
        "full_migration": False, "business_payload_read": False,
        **extra,
    }
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    temp = STATUS.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, STATUS)

def main():
    if os.name != "nt" or socket.gethostname().upper() != "ZHANGWEI":
        raise SystemExit("RUN_ONLY_ON_WINDOWS_ZHANGWEI")
    from ctypes import wintypes as wt
    DWORD = ctypes.c_uint32
    HANDLE = wt.HANDLE
    BOOL = ctypes.c_int

    class NETRESOURCEW(ctypes.Structure):
        _fields_ = [
            ("dwScope", DWORD), ("dwType", DWORD),
            ("dwDisplayType", DWORD), ("dwUsage", DWORD),
            ("lpLocalName", wt.LPWSTR), ("lpRemoteName", wt.LPWSTR),
            ("lpComment", wt.LPWSTR), ("lpProvider", wt.LPWSTR),
        ]

    class FILETIME(ctypes.Structure):
        _fields_ = [("low", DWORD), ("high", DWORD)]

    class FILEINFO(ctypes.Structure):
        _fields_ = [
            ("attrs", DWORD), ("creation", FILETIME), ("access", FILETIME),
            ("write", FILETIME), ("volume", DWORD), ("size_high", DWORD),
            ("size_low", DWORD), ("links", DWORD), ("id_high", DWORD),
            ("id_low", DWORD),
        ]

    mpr = ctypes.WinDLL("mpr", use_last_error=True)
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    login = mpr.WNetUseConnectionW
    login.argtypes = [wt.HWND, ctypes.POINTER(NETRESOURCEW), wt.LPCWSTR,
                      wt.LPCWSTR, DWORD, wt.LPWSTR,
                      ctypes.POINTER(DWORD), ctypes.POINTER(DWORD)]
    login.restype = DWORD
    user.GetForegroundWindow.argtypes = []
    user.GetForegroundWindow.restype = wt.HWND
    kernel.GetFileAttributesW.argtypes = [wt.LPCWSTR]
    kernel.GetFileAttributesW.restype = DWORD
    kernel.CreateFileW.argtypes = [wt.LPCWSTR, DWORD, DWORD, ctypes.c_void_p,
                                   DWORD, DWORD, HANDLE]
    kernel.CreateFileW.restype = HANDLE
    kernel.GetFileInformationByHandle.argtypes = [HANDLE, ctypes.POINTER(FILEINFO)]
    kernel.GetFileInformationByHandle.restype = BOOL
    kernel.CloseHandle.argtypes = [HANDLE]
    kernel.CloseHandle.restype = BOOL

    resource = NETRESOURCEW()
    resource.dwType = 1  # RESOURCETYPE_DISK
    resource.lpLocalName = None  # no mapped drive
    resource.lpRemoteName = SHARE
    access = ctypes.create_unicode_buffer(1024)
    length = DWORD(len(access))
    result = DWORD(0)
    record("LOCAL_WINDOWS_INPUT_PENDING", authenticated=False,
           source_root_metadata_valid=False)
    # Password remains NULL. The Windows network provider owns credential UI.
    # CONNECT_INTERACTIVE | CONNECT_PROMPT. No save-credential/profile flag.
    rc = int(login(user.GetForegroundWindow(), ctypes.byref(resource), None,
                   ACCOUNT, 0x18, access, ctypes.byref(length), ctypes.byref(result)))
    if rc != 0:
        record("USER_CANCELLED" if rc == 1223 else "AUTH_NOT_COMPLETE",
               authenticated=False, winerror=rc, source_root_metadata_valid=False)
        return 2

    probes = []
    for root, expected in ROOTS:
        path = r"\\?\UNC" + "\\" + root[2:]
        attrs = int(kernel.GetFileAttributesW(path))
        if attrs == 0xFFFFFFFF:
            probes.append({"path": root, "ok": False,
                           "winerror": ctypes.get_last_error()})
            break
        handle = kernel.CreateFileW(path, 0, 7, None, 3, 0x02000000 | 0x00200000, None)
        if handle is None or handle == ctypes.c_void_p(-1).value:
            probes.append({"path": root, "ok": False,
                           "winerror": ctypes.get_last_error()})
            break
        try:
            info = FILEINFO()
            if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
                probes.append({"path": root, "ok": False,
                               "winerror": ctypes.get_last_error()})
                break
            valid = int(info.volume) == expected and bool(int(info.attrs) & 0x10)
            probes.append({"path": root, "ok": valid,
                           "volume_serial": int(info.volume), "expected_volume": expected,
                           "file_id": str((int(info.id_high) << 32) | int(info.id_low)),
                           "attrs": int(info.attrs)})
            if not valid:
                break
        finally:
            kernel.CloseHandle(handle)
    valid = len(probes) == len(ROOTS) and all(row["ok"] for row in probes)
    record("SOURCE_ROOT_METADATA_OK" if valid else "SOURCE_METADATA_BLOCKED",
           authenticated=True, probes=probes, source_root_metadata_valid=valid,
           stable_business_file_read="NOT_RUN")
    return 0 if valid else 2

if __name__ == "__main__":
    sys.exit(main())
