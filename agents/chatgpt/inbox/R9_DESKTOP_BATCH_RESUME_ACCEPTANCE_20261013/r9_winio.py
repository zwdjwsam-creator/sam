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


class Win32Syscalls:
    """Real Win32 entry points. This phase must not call write/create."""

    write_calls = 0

    def open_source(self, path):
        return common.open_source_stable(path)

    def identity(self, handle):
        return common.handle_identity(handle)

    def read(self, handle, n):
        buf = common.ctypes.create_string_buffer(n)
        got = common.wintypes.DWORD(0)
        ok = common.ReadFile(handle, buf, n, common.ctypes.byref(got), None)
        if not ok:
            raise OSError(common.ctypes.get_last_error(), "ReadFile failed")
        return bytes(buf[: got.value])

    def close(self, handle):
        common.safe_close(handle)

    def create_temp(self, path):
        type(self).write_calls += 1
        handle = common.CreateFileW(common.to_win_long_path(path), common.GENERIC_WRITE, 0, None, common.CREATE_NEW, common.FILE_ATTRIBUTE_NORMAL, None)
        if handle == common.INVALID_HANDLE_VALUE or handle is None:
            raise OSError(common.ctypes.get_last_error(), "create_temp failed")
        return handle

    def write(self, handle, data: bytes) -> int:
        type(self).write_calls += 1
        got = common.wintypes.DWORD(0)
        ok = common.WriteFile(handle, data, len(data), common.ctypes.byref(got), None)
        if not ok:
            raise OSError(common.ctypes.get_last_error(), "WriteFile failed")
        return int(got.value)

    def flush(self, handle):
        if not common.FlushFileBuffers(handle):
            raise OSError(common.ctypes.get_last_error(), "Flush failed")
        return True

    def observe(self, path):
        try:
            if not common.path_exists_win(path):
                return {"status": "MISSING"}
        except OSError:
            return {"status": "MISSING"}
        return {"status": "PRESENT", "path": path}

    def hardlink(self, dest_representative, alias_path):
        type(self).write_calls += 1
        if common.path_exists_win(alias_path):
            return False
        ok = common.CreateHardLinkW(common.to_win_long_path(alias_path), common.to_win_long_path(dest_representative), None)
        if not ok:
            raise OSError(common.ctypes.get_last_error(), "CreateHardLinkW failed")
        return True

    def commit_no_replace(self, temp, dest) -> bool:
        type(self).write_calls += 1
        if common.path_exists_win(dest):
            return False
        if not common.kernel32.MoveFileW(common.to_win_long_path(temp), common.to_win_long_path(dest)):
            raise OSError(common.ctypes.get_last_error(), "MoveFileW failed")
        return True


class VirtualSyscalls:
    """Same method names as Win32Syscalls. Stores bytes in memory for tests."""

    def __init__(self, files=None, identities=None):
        self.files = dict(files or {})
        self.identities = dict(identities or {})
        self.handles = {}
        self.next_id = 1
        self.write_calls = 0
        self.calls = 0

    def open_source(self, path):
        self.calls += 1
        if path not in self.files:
            raise FileNotFoundError(path)
        hid = self.next_id
        self.next_id += 1
        self.handles[hid] = {"path": path, "pos": 0}
        return hid

    def identity(self, handle):
        path = self.handles[handle]["path"]
        meta = dict(self.identities[path])
        meta["size"] = len(self.files[path])
        return meta

    def read(self, handle, n):
        slot = self.handles[handle]
        data = self.files[slot["path"]]
        piece = data[slot["pos"]: slot["pos"] + n]
        slot["pos"] += len(piece)
        return bytes(piece)

    def close(self, handle):
        self.handles.pop(handle, None)

    def create_temp(self, path):
        self.write_calls += 1
        if path in self.files:
            raise FileExistsError(path)
        self.files[path] = bytearray()
        hid = self.next_id
        self.next_id += 1
        self.handles[hid] = {"path": path, "pos": 0}
        return hid

    def write(self, handle, data: bytes) -> int:
        self.write_calls += 1
        self.files[self.handles[handle]["path"]].extend(data)
        return len(data)

    def flush(self, handle):
        return True

    def commit_no_replace(self, temp, dest) -> bool:
        self.write_calls += 1
        if dest in self.files:
            return False
        self.files[dest] = bytes(self.files.pop(temp))
        self.identities[dest] = {"file_id": f"dest-{self.next_id}", "volume_serial": "DEST", "mtime": "committed"}
        self.next_id += 1
        return True

    def hardlink(self, dest_representative, alias_path):
        self.write_calls += 1
        if alias_path in self.files:
            return False
        if dest_representative not in self.files:
            raise FileNotFoundError(dest_representative)
        self.files[alias_path] = self.files[dest_representative]
        self.identities[alias_path] = dict(self.identities[dest_representative])
        return True

    def observe(self, path):
        if path not in self.files:
            return {"status": "MISSING"}
        data = bytes(self.files[path])
        ident = self.identities.get(path, {})
        return {
            "status": "PRESENT",
            "logical_size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "object_type": "file",
            "file_id": ident.get("file_id"),
            "volume_serial": ident.get("volume_serial"),
        }


class WindowsBackend:
    def __init__(self, syscalls=None):
        self.sc = syscalls if syscalls is not None else Win32Syscalls()
        self.calls = 0

    def copy_entity(self, entity):
        handle = None
        dest_handle = None
        temp = entity["dest_path"] + ".partial"
        try:
            handle = self.sc.open_source(entity["source_path"])
            ident = self.sc.identity(handle)
            if ident.get("file_id") != entity["file_id"] or ident.get("volume_serial") != entity["volume_serial"]:
                raise RuntimeError("SOURCE_CHANGED")
            if int(ident.get("size")) != int(entity["logical_size"]):
                raise RuntimeError("SOURCE_SIZE")
            if entity.get("mtime") is not None and ident.get("mtime") != entity["mtime"]:
                raise RuntimeError("SOURCE_MTIME")
            dest_handle = self.sc.create_temp(temp)
            hasher = hashlib.sha256()
            total = 0
            while total < int(entity["logical_size"]):
                piece = self.sc.read(handle, min(1024, int(entity["logical_size"]) - total))
                if piece is None:
                    raise RuntimeError("EOF_READ_FAILED")
                if piece == b"":
                    raise RuntimeError("SHORT_READ")
                written = self.sc.write(dest_handle, piece)
                if written != len(piece):
                    raise RuntimeError("SHORT_WRITE")
                hasher.update(piece)
                total += written
            if self.sc.read(handle, 1):
                raise RuntimeError("SOURCE_LONGER")
            self.sc.flush(dest_handle)
            self.sc.close(dest_handle)
            dest_handle = None
            digest = hasher.hexdigest()
            check = self.sc.open_source(temp)
            try:
                again = hashlib.sha256()
                seen = 0
                while seen < total:
                    part = self.sc.read(check, min(1024, total - seen))
                    if not part:
                        raise RuntimeError("DEST_SHORT")
                    again.update(part)
                    seen += len(part)
                if again.hexdigest() != digest:
                    raise RuntimeError("DEST_HASH")
            finally:
                self.sc.close(check)
            if not self.sc.commit_no_replace(temp, entity["dest_path"]):
                raise RuntimeError("UNKNOWN_TARGET_EXISTS")
            observed = self.sc.observe(entity["dest_path"])
            self.calls += 1
            return {
                "sha256": digest,
                "bytes": total,
                "dest_path": entity["dest_path"],
                "dest_file_id": observed.get("file_id"),
                "dest_volume_serial": observed.get("volume_serial"),
            }
        finally:
            if dest_handle is not None:
                self.sc.close(dest_handle)
            if handle is not None:
                self.sc.close(handle)

    def hardlink(self, dest_representative, alias_path):
        observed = self.sc.observe(dest_representative)
        if observed.get("status") == "MISSING":
            raise RuntimeError("MISSING_REPRESENTATIVE")
        if not self.sc.hardlink(dest_representative, alias_path):
            raise RuntimeError("UNKNOWN_ALIAS_EXISTS")
        alias = self.sc.observe(alias_path)
        if alias.get("status") == "MISSING":
            raise RuntimeError("ALIAS_MISSING")
        self.calls += 1
        return {"dest_path": alias_path, "dest_file_id": alias.get("file_id"), "dest_volume_serial": alias.get("volume_serial")}

    def observe_destination(self, path):
        return self.sc.observe(path)
