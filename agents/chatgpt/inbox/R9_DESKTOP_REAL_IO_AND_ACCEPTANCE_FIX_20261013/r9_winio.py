# -*- coding: utf-8 -*-
"""Windows IO backend. Importing this module does not create or write a file.

Tests must not call stream_copy_handles. The scheduler uses a fake backend until a
future authorized task binds a formatted destination.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(r"C:\LAN_SHARE_REPORT")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import r9_pilot_common_r9fix as common

CHUNK = 1024 * 1024
PILOT_COMMON_SHA256 = "bc969b160ca161b682637e839f283370ff1e41b4cf4f94ae1d8c208334259a87"


def declarations_ready() -> dict:
    needed = ("CreateFileW", "ReadFile", "WriteFile", "FlushFileBuffers", "CloseHandle", "CreateHardLinkW")
    ready = {}
    for name in needed:
        fn = getattr(common, name)
        ready[name] = fn.argtypes is not None and fn.restype is not None
    return {"ready": all(ready.values()), "functions": ready, "pilot_common_sha256": PILOT_COMMON_SHA256}


def stream_copy_handles(src_handle, dest_handle, expected_size: int) -> dict:
    """Read and write in chunks. The full entity is never assembled in one buffer."""
    hasher = hashlib.sha256()
    total = 0
    while total < expected_size:
        buf = ctypes_buf(min(CHUNK, expected_size - total))
        got = common.wintypes.DWORD(0)
        ok = common.ReadFile(src_handle, buf, len(buf), common.ctypes.byref(got), None)
        if not ok:
            raise OSError(common.ctypes.get_last_error(), "ReadFile failed")
        if got.value == 0:
            raise RuntimeError("SHORT_READ")
        piece = bytes(buf[: got.value])
        wrote = common.wintypes.DWORD(0)
        ok = common.WriteFile(dest_handle, piece, len(piece), common.ctypes.byref(wrote), None)
        if not ok or wrote.value != len(piece):
            raise OSError(common.ctypes.get_last_error(), "WriteFile short")
        hasher.update(piece)
        total += len(piece)
    extra = ctypes_buf(1)
    probe = common.wintypes.DWORD(0)
    ok = common.ReadFile(src_handle, extra, 1, common.ctypes.byref(probe), None)
    if not ok:
        raise OSError(common.ctypes.get_last_error(), "EOF probe failed")
    if probe.value != 0:
        raise RuntimeError("SOURCE_LONGER_THAN_EXPECTED")
    if not common.FlushFileBuffers(dest_handle):
        raise OSError(common.ctypes.get_last_error(), "FlushFileBuffers failed")
    return {"bytes": total, "sha256": hasher.hexdigest()}


def ctypes_buf(n: int):
    return common.ctypes.create_string_buffer(n)
