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


class VirtualSyscalls:
    """In-memory stand-in used only by tests. Real Win32 functions are not called."""

    def __init__(self):
        self.files = {}
        self.calls = 0

    def open_source(self, path, payload: bytes, identity: dict):
        self.calls += 1
        return {"path": path, "payload": payload, "identity": identity, "pos": 0}

    def read(self, handle, n):
        self.calls += 1
        start = handle["pos"]
        piece = handle["payload"][start:start + n]
        handle["pos"] = start + len(piece)
        return piece

    def create_temp(self, path):
        self.calls += 1
        if path in self.files:
            raise FileExistsError(path)
        self.files[path] = bytearray()
        return path

    def write(self, handle, data: bytes) -> int:
        self.calls += 1
        self.files[handle].extend(data)
        return len(data)

    def flush(self, handle):
        self.calls += 1
        return True

    def commit(self, temp, dest) -> bool:
        self.calls += 1
        if dest in self.files and self.files[dest] is not self.files.get(temp):
            return False
        self.files[dest] = self.files.pop(temp)
        return True


class WindowsBackend:
    """Production backend. Tests pass VirtualSyscalls; the CLI does not call copy_entity."""

    def __init__(self, syscalls=None):
        self.sc = syscalls if syscalls is not None else "REAL_NOT_RUN"
        self.calls = 0

    def stable_open_source(self, path, payload=None, identity=None):
        self._real_blocked()
        return self.sc.open_source(path, payload, identity)

    def copy_entity(self, entity, payload: bytes, identity: dict):
        self._real_blocked()
        handle = self.stable_open_source(entity["representative"], payload, identity)
        if handle["identity"] != identity:
            raise RuntimeError("SOURCE_CHANGED")
        temp = entity["dest"] + ".partial"
        self.sc.create_temp(temp)
        total = 0
        hasher = hashlib.sha256()
        while total < len(payload):
            piece = self.sc.read(handle, min(1024, len(payload) - total))
            if not piece:
                raise RuntimeError("SHORT_READ")
            written = self.sc.write(temp, piece)
            if written != len(piece):
                raise RuntimeError("SHORT_WRITE")
            hasher.update(piece)
            total += len(piece)
        self.sc.flush(temp)
        if hasher.hexdigest() != hashlib.sha256(self.sc.files[temp]).hexdigest():
            raise RuntimeError("DEST_HASH")
        if not self.sc.commit(temp, entity["dest"]):
            raise RuntimeError("COMMIT_FAILED")
        self.calls += 1
        return {"sha256": hasher.hexdigest(), "bytes": total, "dest": entity["dest"], "dest_identity": identity}

    def hardlink(self, source, dest, volume):
        self._real_blocked()
        self.sc.calls += 1
        self.calls += 1
        return {"source": source, "dest": dest, "volume": volume}

    def rebuild_reparse(self, link_path, target):
        self._real_blocked()
        self.sc.calls += 1
        self.calls += 1
        return {"link_path": link_path, "target": target, "type": "junction"}

    def observe_destination(self, path):
        self._real_blocked()
        data = bytes(self.sc.files.get(path, b""))
        return {"path": path, "logical_size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "object_type": "file"}

    def enumerate_destination_no_follow(self):
        self._real_blocked()
        return list(self.sc.files)

    def close_handle(self, handle):
        self._real_blocked()
        handle["closed"] = True

    def _real_blocked(self):
        if self.sc == "REAL_NOT_RUN":
            raise RuntimeError("REAL_IO_NOT_RUN")
