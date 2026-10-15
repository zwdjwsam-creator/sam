# -*- coding: utf-8 -*-
"""Windows IO backend. Importing this module does not create or write a file.

Tests must not call stream_copy_handles. The scheduler uses a fake backend until a
future authorized task binds a formatted destination.
"""
from __future__ import annotations

import hashlib
import sys
import threading
import time
from pathlib import Path, PureWindowsPath

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import r9_pilot_common_r9fix as common

def ensure_win32_prototypes(kernel=None) -> None:
    kernel = kernel or common.kernel32
    w = common.wintypes
    c = common.ctypes
    specs = {
        "CreateDirectoryW": ([w.LPCWSTR, w.LPVOID], w.BOOL),
        "MoveFileW": ([w.LPCWSTR, w.LPCWSTR], w.BOOL),
        "DeviceIoControl": ([w.HANDLE, w.DWORD, w.LPVOID, w.DWORD, w.LPVOID, w.DWORD, c.POINTER(w.DWORD), w.LPVOID], w.BOOL),
        "CreateSymbolicLinkW": ([w.LPCWSTR, w.LPCWSTR, w.DWORD], w.BOOLEAN),
        "CloseHandle": ([w.HANDLE], w.BOOL),
        "CreateFileW": ([w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID, w.DWORD, w.DWORD, w.HANDLE], w.HANDLE),
        "FindClose": ([w.HANDLE], w.BOOL),
    }
    for name, (args, restype) in specs.items():
        fn = getattr(kernel, name, None)
        if fn is None or not hasattr(fn, "argtypes"):
            continue
        fn.argtypes = args
        fn.restype = restype


ensure_win32_prototypes()


def mtime_evidence(meta: dict):
    if not isinstance(meta, dict):
        raise RuntimeError("MTIME_DEFICIT")
    if meta.get("mtime_ft") not in (None, ""):
        return ("ft", str(meta["mtime_ft"]))
    if meta.get("mtime") not in (None, ""):
        return ("token", str(meta["mtime"]))
    raise RuntimeError("MTIME_DEFICIT")


def assert_manifest_mtime(manifest, ident: dict) -> None:
    if manifest in (None, ""):
        raise RuntimeError("MTIME_DEFICIT")
    if ident.get("mtime_ft") not in (None, ""):
        common.compare_mtime_manifest_vs_handle(manifest, ident["mtime_ft"])
        return
    if ident.get("mtime") in (None, ""):
        raise RuntimeError("MTIME_DEFICIT")
    if str(ident.get("mtime")) != str(manifest):
        raise RuntimeError("SOURCE_MTIME")

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


FSCTL_SET_REPARSE_POINT = 0x000900A4
IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
IO_REPARSE_TAG_SYMLINK = 0xA000000C
SYMBOLIC_LINK_FLAG_DIRECTORY = 0x1


def parse_reparse_buffer(raw: bytes) -> dict:
    """Parse FSCTL_GET_REPARSE_POINT bytes using the tag-specific name offset."""
    if len(raw) < 8:
        raise RuntimeError("REPARSE_BUFFER_SHORT")
    tag = int.from_bytes(raw[0:4], "little")
    data_len = int.from_bytes(raw[4:6], "little")
    if len(raw) < 8 + data_len:
        raise RuntimeError("REPARSE_BUFFER_SHORT")
    if tag == IO_REPARSE_TAG_MOUNT_POINT:
        base = 16
        if len(raw) < base:
            raise RuntimeError("REPARSE_BUFFER_SHORT")
        kind = "junction"
        flags = None
    elif tag == IO_REPARSE_TAG_SYMLINK:
        base = 20
        if len(raw) < base:
            raise RuntimeError("REPARSE_BUFFER_SHORT")
        flags = int.from_bytes(raw[16:20], "little")
        kind = "symlink"
    else:
        raise RuntimeError(f"REPARSE_TAG_UNKNOWN:{tag}")
    sub_off = int.from_bytes(raw[8:10], "little")
    sub_len = int.from_bytes(raw[10:12], "little")
    start = base + sub_off
    end = start + sub_len
    if end > len(raw):
        raise RuntimeError("REPARSE_BUFFER_SHORT")
    name = raw[start:end].decode("utf-16le").rstrip("\x00")
    relative = bool(flags) and bool(flags & 1)
    if not relative:
        name = name.replace("\\??\\", "")
    return {"kind": kind, "target": name, "flags": flags, "tag": tag, "relative": relative}


def symlink_buffer(target: str, relative: bool = False) -> bytes:
    prefix = "" if relative else "\\??\\"
    substitute = (prefix + str(target).replace("/", "\\")).encode("utf-16le")
    printable = str(target).replace("/", "\\").encode("utf-16le")
    # Non-zero substitute offset so a fixed raw[16:] slice is the wrong name.
    pad = b"\x00\x00"
    path_buffer = pad + substitute + b"\x00\x00" + printable + b"\x00\x00"
    flags = 1 if relative else 0
    data_len = 12 + len(path_buffer)
    header = IO_REPARSE_TAG_SYMLINK.to_bytes(4, "little") + data_len.to_bytes(2, "little") + (0).to_bytes(2, "little")
    names = (
        len(pad).to_bytes(2, "little")
        + len(substitute).to_bytes(2, "little")
        + (len(pad) + len(substitute) + 2).to_bytes(2, "little")
        + len(printable).to_bytes(2, "little")
        + flags.to_bytes(4, "little")
    )
    return header + names + path_buffer


def mount_point_buffer(target: str) -> bytes:
    """FSCTL_SET_REPARSE_POINT payload for a directory junction. Not written here."""
    substitute = ("\\??\\" + str(target).replace("/", "\\")).encode("utf-16le")
    printable = str(target).replace("/", "\\").encode("utf-16le")
    path_buffer = substitute + b"\x00\x00" + printable + b"\x00\x00"
    data_len = 8 + len(path_buffer)
    tag = IO_REPARSE_TAG_MOUNT_POINT.to_bytes(4, "little")
    header = tag + data_len.to_bytes(2, "little") + (0).to_bytes(2, "little")
    names = (
        (0).to_bytes(2, "little")
        + len(substitute).to_bytes(2, "little")
        + (len(substitute) + 2).to_bytes(2, "little")
        + len(printable).to_bytes(2, "little")
    )
    return header + names + path_buffer


def observe_via_winapi(api, path: str, include_hash: bool = False) -> dict:
    """Metadata observe. Content hash is explicit via content_sha, not every alias."""
    attrs = api.GetFileAttributesW(path)
    if attrs == 0xFFFFFFFF:
        err = api.last_error()
        if err in (2, 3):
            return {"status": "MISSING"}
        return {"status": "ERROR", "winerror": err}
    handle = api.CreateFileW(path, common.FILE_FLAG_BACKUP_SEMANTICS | common.FILE_FLAG_OPEN_REPARSE_POINT)
    try:
        info = api.GetFileInformationByHandle(handle)
        standard = api.GetFileInformationByHandleEx(handle)
        is_reparse = bool(attrs & common.FILE_ATTRIBUTE_REPARSE_POINT)
        is_dir = bool(attrs & common.FILE_ATTRIBUTE_DIRECTORY)
        reparse_target = None
        reparse_tag = None
        kind = "directory" if is_dir else "file"
        if is_reparse:
            parsed = api.read_reparse(handle)
            reparse_target = parsed.get("target")
            reparse_tag = parsed.get("tag")
            kind = parsed.get("kind") or "junction"
        digest = None
        if include_hash and kind == "file":
            digest = api.hash_handle(handle, int(info["size"]))
        return {
            "status": "PRESENT",
            "path": path,
            "file_id": str(info["file_id"]),
            "volume_serial": str(info["volume_serial"]),
            "logical_size": int(info["size"]),
            "allocation_size": int(standard["allocation_size"]),
            "mtime": info.get("mtime"),
            "object_type": kind,
            "reparse_target": reparse_target,
            "reparse_tag": reparse_tag,
            "sha256": digest,
            "nlinks": int(info.get("nlinks") or 0),
        }
    finally:
        api.close(handle)


def apply_reparse(api, link_path: str, target: str, kind: str = "junction") -> bool:
    """Create a junction or symlink through the given Win32 API. Tests pass a fake API."""
    if kind == "symlink":
        ok = api.CreateSymbolicLinkW(link_path, target, 0)
        return bool(ok)
    handle = api.CreateFileW(link_path, common.FILE_FLAG_BACKUP_SEMANTICS | common.FILE_FLAG_OPEN_REPARSE_POINT)
    try:
        ok = api.DeviceIoControl(handle, FSCTL_SET_REPARSE_POINT, mount_point_buffer(target))
        return bool(ok)
    finally:
        api.close(handle)


def enumerate_nofollow(api, root: str) -> list[dict]:
    """One directory level. Reparse children are listed and not opened for descent."""
    return list(api.list_directory_nofollow(root))


class Win32Syscalls:
    """Win32 entry points. api=None calls the process kernel. A test api replaces OS data only."""

    write_calls = 0

    def __init__(self, api=None, kernel=None):
        self.api = api
        self.kernel = kernel
        self.hash_calls = 0
        self.recorded_writes = 0

    def open_source(self, path):
        if self.api is not None:
            return self.api.open_source(path)
        return common.open_source_stable(path)

    def identity(self, handle):
        if self.api is not None:
            return self.api.identity(handle)
        return common.handle_identity(handle)

    def read(self, handle, n):
        if self.api is not None:
            return self.api.read(handle, n)
        buf = common.ctypes.create_string_buffer(n)
        got = common.wintypes.DWORD(0)
        ok = common.ReadFile(handle, buf, n, common.ctypes.byref(got), None)
        if not ok:
            raise OSError(common.ctypes.get_last_error(), "ReadFile failed")
        return bytes(buf[: got.value])

    def close(self, handle):
        if self.api is not None:
            return self.api.close(handle)
        common.safe_close(handle)

    def create_temp(self, path):
        if self.api is not None:
            self.recorded_writes += 1
            return self.api.create_temp(path)
        type(self).write_calls += 1
        handle = common.CreateFileW(common.to_win_long_path(path), common.GENERIC_WRITE, 0, None, common.CREATE_NEW, common.FILE_ATTRIBUTE_NORMAL, None)
        if handle == common.INVALID_HANDLE_VALUE or handle is None:
            raise OSError(common.ctypes.get_last_error(), "create_temp failed")
        return handle

    def write(self, handle, data: bytes) -> int:
        if self.api is not None:
            self.recorded_writes += 1
            return self.api.write(handle, data)
        type(self).write_calls += 1
        got = common.wintypes.DWORD(0)
        ok = common.WriteFile(handle, data, len(data), common.ctypes.byref(got), None)
        if not ok:
            raise OSError(common.ctypes.get_last_error(), "WriteFile failed")
        return int(got.value)

    def flush(self, handle):
        if self.api is not None:
            return self.api.flush(handle)
        if not common.FlushFileBuffers(handle):
            raise OSError(common.ctypes.get_last_error(), "Flush failed")
        return True

    def observe(self, path):
        if self.kernel is not None:
            seen = observe_via_winapi(self.kernel, path)
            if seen.get("status") == "PRESENT":
                return seen
        if self.api is not None:
            return self.api.observe(path)
        return observe_via_winapi(_RealKernel(), path)

    def create_reparse(self, link_path, target, kind="junction"):
        if self.kernel is not None or self.api is None:
            if self.api is None:
                type(self).write_calls += 1
            else:
                self.recorded_writes += 1
            real = _RealKernel(self.kernel)
            if kind == "junction":
                return real.create_junction(link_path, target)
            return real.create_directory_symlink(link_path, target)
        self.recorded_writes += 1
        return self.api.create_reparse(link_path, target, kind)

    def list_nofollow(self, root):
        if self.api is not None:
            return self.api.list_nofollow(root)
        return enumerate_nofollow(_RealKernel(), root)

    def follow_identity(self, path):
        """Read the object reached by following reparse points. Does not hash every alias."""
        if self.kernel is not None and hasattr(self.kernel, "follow_open"):
            return self.kernel.follow_open(path)
        if self.api is not None:
            raise RuntimeError("FOLLOW_NOT_REAL")
        wide = common.to_win_long_path(path)
        handle = common.CreateFileW(
            wide,
            common.GENERIC_READ,
            common.FILE_SHARE_READ,
            None,
            common.OPEN_EXISTING,
            common.FILE_FLAG_BACKUP_SEMANTICS,
            None,
        )
        if handle in (None, common.INVALID_HANDLE_VALUE):
            raise OSError(common.ctypes.get_last_error(), "follow open failed")
        try:
            ident = common.handle_identity(handle)
            digest = hashlib.sha256()
            size = int(ident["size"])
            seen = 0
            while seen < size:
                piece = self.read(handle, min(1024 * 1024, size - seen))
                if not piece:
                    raise RuntimeError("SHORT_READ")
                digest.update(piece)
                seen += len(piece)
            return {
                "file_id": str(ident["file_id"]),
                "volume_serial": str(ident["volume_serial"]),
                "logical_size": size,
                "sha256": digest.hexdigest(),
            }
        finally:
            self.close(handle)

    def content_sha(self, path):
        """Hash one destination once. Aliases are not read again by this method."""
        self.hash_calls += 1
        handle = self.open_source(path)
        try:
            ident = self.identity(handle)
            if ident.get("size") is None:
                raise RuntimeError("CONTENT_HASH_NOT_RUN")
            size = int(ident["size"])
            hasher = hashlib.sha256()
            seen = 0
            while seen < size:
                piece = self.read(handle, min(1024 * 1024, size - seen))
                if not piece:
                    raise RuntimeError("SHORT_READ")
                hasher.update(piece)
                seen += len(piece)
            if self.read(handle, 1):
                raise RuntimeError("SOURCE_LONGER")
            return hasher.hexdigest()
        finally:
            self.close(handle)

    def ensure_directory(self, path):
        if self.api is not None:
            current = self.api.observe(path)
            self.api.ensure_directory(path)
            if not (current.get("status") == "PRESENT" and current.get("object_type") == "directory"):
                self.recorded_writes += 1
            return
        type(self).write_calls += 1
        ok = common.kernel32.CreateDirectoryW(common.to_win_long_path(path), None)
        if not ok and common.ctypes.get_last_error() not in (183,):
            raise OSError(common.ctypes.get_last_error(), "CreateDirectoryW failed")

    def hardlink(self, dest_representative, alias_path):
        if self.api is not None:
            ok = self.api.hardlink(dest_representative, alias_path)
            if ok:
                self.recorded_writes += 1
            return ok
        type(self).write_calls += 1
        if common.path_exists_win(alias_path):
            return False
        ok = common.CreateHardLinkW(common.to_win_long_path(alias_path), common.to_win_long_path(dest_representative), None)
        if not ok:
            raise OSError(common.ctypes.get_last_error(), "CreateHardLinkW failed")
        return True

    def commit_no_replace(self, temp, dest) -> bool:
        if self.api is not None:
            ok = self.api.commit_no_replace(temp, dest)
            if ok:
                self.recorded_writes += 1
            return ok
        type(self).write_calls += 1
        if common.path_exists_win(dest):
            return False
        if not common.kernel32.MoveFileW(common.to_win_long_path(temp), common.to_win_long_path(dest)):
            raise OSError(common.ctypes.get_last_error(), "MoveFileW failed")
        return True


class VirtualSyscalls:
    """Same method names as Win32Syscalls. Stores bytes in memory for tests."""

    def __init__(self, files=None, identities=None, dest_volume="DEST"):
        self.files = dict(files or {})
        self.identities = dict(identities or {})
        self.handles = {}
        self.next_id = 1
        self.write_calls = 0
        self.calls = 0
        self.hash_calls = 0
        self.dest_volume = dest_volume
        self.opened_sources = []

    def open_source(self, path):
        self.calls += 1
        self.opened_sources.append(str(path))
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
        data = bytes(self.files.pop(temp))
        self.files[dest] = data
        self.identities[dest] = {
            "file_id": f"dest-{self.next_id}",
            "volume_serial": self.dest_volume,
            "mtime": "committed",
            "object_type": "file",
            "allocation_size": ((len(data) + 4095) // 4096) * 4096,
        }
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
            "path": path,
            "logical_size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "object_type": ident.get("object_type", "file"),
            "file_id": ident.get("file_id"),
            "volume_serial": ident.get("volume_serial"),
            "allocation_size": ident.get("allocation_size", 0),
            "reparse_target": ident.get("reparse_target"),
            "reparse_tag": ident.get(
                "reparse_tag",
                0xA0000003 if ident.get("object_type") == "junction" else None,
            ),
            "mtime": ident.get("mtime"),
        }

    def ensure_directory(self, path):
        if path in self.files:
            if self.identities.get(path, {}).get("object_type", "file") != "directory":
                raise RuntimeError("TYPE_CONFLICT")
            return
        self.write_calls += 1
        self.files[path] = b""
        self.identities[path] = {
            "file_id": f"dir-{self.next_id}",
            "volume_serial": self.dest_volume,
            "mtime": "dir",
            "object_type": "directory",
            "allocation_size": 0,
        }
        self.next_id += 1

    def create_reparse(self, link_path, target, kind="junction"):
        if link_path in self.files:
            return False
        self.write_calls += 1
        self.files[link_path] = b""
        self.identities[link_path] = {
            "file_id": f"reparse-{self.next_id}",
            "volume_serial": self.dest_volume,
            "mtime": "reparse",
            "object_type": kind,
            "reparse_target": target,
            "allocation_size": 0,
        }
        self.next_id += 1
        return True

    def list_nofollow(self, root):
        prefix = str(root).rstrip("\\") + "\\"
        found = []
        for path, ident in self.identities.items():
            if not str(path).startswith(prefix):
                continue
            rest = str(path)[len(prefix):]
            if "\\" in rest:
                continue
            data = bytes(self.files.get(path, b""))
            found.append({
                "path": path,
                "object_type": ident.get("object_type", "file"),
                "file_id": ident.get("file_id"),
                "volume_serial": ident.get("volume_serial"),
                "logical_size": len(data),
                "allocation_size": ident.get("allocation_size", 0),
                "reparse_target": ident.get("reparse_target"),
                "sha256": None,
            })
        return found

    def content_sha(self, path):
        self.hash_calls += 1
        if path not in self.files:
            raise FileNotFoundError(path)
        return hashlib.sha256(bytes(self.files[path])).hexdigest()


class WindowsBackend:
    def __init__(self, syscalls=None, chunk: int = 1024 * 1024):
        self.sc = syscalls if syscalls is not None else Win32Syscalls()
        self.calls = 0
        self.chunk = chunk
        self._phase_lock = threading.Lock()
        self._entity_phase_wall_seconds = "NOT_RUN"
        self._state_commit_calls = "NOT_RUN"
        self._state_commit_seconds = "NOT_RUN"
        self.phase_stats = {
            "source_open_calls": "NOT_RUN",
            "source_open_seconds": "NOT_RUN",
            "source_identity_calls": "NOT_RUN",
            "source_identity_seconds": "NOT_RUN",
            "stream_read_calls": "NOT_RUN",
            "stream_read_bytes": "NOT_RUN",
            "stream_read_seconds": "NOT_RUN",
            "stream_write_calls": "NOT_RUN",
            "stream_write_bytes": "NOT_RUN",
            "stream_write_seconds": "NOT_RUN",
            "flush_calls": "NOT_RUN",
            "flush_seconds": "NOT_RUN",
            "readback_open_calls": "NOT_RUN",
            "readback_open_seconds": "NOT_RUN",
            "readback_calls": "NOT_RUN",
            "readback_bytes": "NOT_RUN",
            "readback_seconds": "NOT_RUN",
            "commit_no_replace_calls": "NOT_RUN",
            "commit_no_replace_seconds": "NOT_RUN",
            "observe_calls": "NOT_RUN",
            "observe_seconds": "NOT_RUN",
        }

    def _phase(self, name, byte_key=None):
        """Count one attempt, including a failed attempt. Leave later phases at NOT_RUN."""
        calls_key = name + "_calls"
        seconds_key = name + "_seconds"
        stats = self.phase_stats
        started = time.perf_counter()

        class _Attempt:
            def add(self, amount):
                if byte_key is not None and amount:
                    with backend_lock:
                        if stats[byte_key] == "NOT_RUN":
                            stats[byte_key] = 0
                        stats[byte_key] += int(amount)

            def __enter__(self):
                with backend_lock:
                    if stats[calls_key] == "NOT_RUN":
                        stats[calls_key] = 0
                        stats[seconds_key] = 0.0
                    if byte_key is not None and stats[byte_key] == "NOT_RUN":
                        stats[byte_key] = 0
                return self

            def __exit__(self, exc_type, exc, tb):
                with backend_lock:
                    stats[calls_key] += 1
                    stats[seconds_key] += time.perf_counter() - started
                return False

        backend_lock = self._phase_lock
        return _Attempt()

    def copy_entity(self, entity, before_commit=None, prepared=None):
        handle = None
        dest_handle = None
        temp = entity["dest_path"] + ".partial"
        try:
            if prepared is None:
                with self._phase("source_open"):
                    handle = self.sc.open_source(entity["source_path"])
                with self._phase("source_identity"):
                    ident = self.sc.identity(handle)
            else:
                if prepared.get("source_path") != entity["source_path"] or prepared.get("entity_key") != entity["entity_key"]:
                    raise RuntimeError("PREFETCH_ENTITY_MISMATCH")
                handle = prepared.pop("handle")
                ident = prepared["identity"]
            if ident.get("file_id") != entity["file_id"] or ident.get("volume_serial") != entity["volume_serial"]:
                raise RuntimeError("SOURCE_CHANGED")
            if int(ident.get("size")) != int(entity["logical_size"]):
                raise RuntimeError("SOURCE_SIZE")
            if entity.get("mtime") in (None, "") or entity.get("mtime_status") in ("ABSENT_IN_PLAN", "MTIME_DEFICIT"):
                if entity.get("allow_observed_mtime") is not True:
                    raise RuntimeError("MTIME_DEFICIT")
                observed_mtime = ident.get("mtime_ft")
                if observed_mtime in (None, ""):
                    observed_mtime = ident.get("mtime")
                if observed_mtime in (None, ""):
                    raise RuntimeError("MTIME_DEFICIT")
                entity["mtime"] = str(observed_mtime)
                entity["mtime_status"] = "OBSERVED_THIS_RUN"
            assert_manifest_mtime(entity.get("mtime"), ident)
            dest_handle = self.sc.create_temp(temp)
            hasher = hashlib.sha256()
            total = 0
            while total < int(entity["logical_size"]):
                with self._phase("stream_read", "stream_read_bytes") as read_span:
                    piece = self.sc.read(handle, min(self.chunk, int(entity["logical_size"]) - total))
                    read_span.add(0 if not piece else len(piece))
                if piece is None:
                    raise RuntimeError("EOF_READ_FAILED")
                if piece == b"":
                    raise RuntimeError("SHORT_READ")
                with self._phase("stream_write", "stream_write_bytes") as write_span:
                    written = self.sc.write(dest_handle, piece)
                    write_span.add(0 if written is None else int(written))
                if written != len(piece):
                    raise RuntimeError("SHORT_WRITE")
                hasher.update(piece)
                total += written
            if self.sc.read(handle, 1):
                raise RuntimeError("SOURCE_LONGER")
            with self._phase("source_identity"):
                after = self.sc.identity(handle)
            if (
                after.get("file_id") != ident.get("file_id")
                or after.get("volume_serial") != ident.get("volume_serial")
                or int(after.get("size")) != int(ident.get("size"))
                or mtime_evidence(after) != mtime_evidence(ident)
            ):
                raise RuntimeError("SOURCE_CHANGED_DURING_COPY")
            with self._phase("flush"):
                self.sc.flush(dest_handle)
            self.sc.close(dest_handle)
            dest_handle = None
            digest = hasher.hexdigest()
            with self._phase("readback_open"):
                check = self.sc.open_source(temp)
            try:
                again = hashlib.sha256()
                seen = 0
                while seen < total:
                    requested = min(self.chunk, total - seen)
                    with self._phase("readback", "readback_bytes") as readback_span:
                        part = self.sc.read(check, requested)
                        readback_span.add(0 if not part else len(part))
                    if not part:
                        raise RuntimeError("DEST_SHORT")
                    again.update(part)
                    seen += len(part)
                if again.hexdigest() != digest:
                    raise RuntimeError("DEST_HASH")
            finally:
                self.sc.close(check)
            if before_commit is not None:
                before_commit({"sha256": digest, "bytes": total, "temp": temp})
            with self._phase("commit_no_replace"):
                committed = self.sc.commit_no_replace(temp, entity["dest_path"])
            if not committed:
                raise RuntimeError("UNKNOWN_TARGET_EXISTS")
            with self._phase("observe"):
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

    def ensure_directory(self, path):
        self.assert_no_reparse_ancestor(path)
        self.sc.ensure_directory(path)
        self.calls += 1

    def create_reparse(self, link_path, target, kind="junction"):
        self.assert_no_reparse_ancestor(link_path)
        if not self.sc.create_reparse(link_path, target, kind):
            raise RuntimeError("UNKNOWN_LINK_EXISTS")
        observed = self.sc.observe(link_path)
        if observed.get("status") != "PRESENT" or observed.get("reparse_target") != target or observed.get("object_type") != kind:
            raise RuntimeError("REPARSE_OBSERVE_FAILED")
        self.calls += 1
        return observed

    def list_nofollow(self, root):
        return self.sc.list_nofollow(root)

    def content_sha(self, path):
        return self.sc.content_sha(path)

    def assert_no_reparse_ancestor(self, path):
        current = PureWindowsPath(str(path))
        parent = current.parent
        while parent != current:
            observed = self.sc.observe(str(parent))
            status = observed.get("status")
            if status != "MISSING":
                if status != "PRESENT":
                    raise RuntimeError("REPARSE_QUERY_UNKNOWN")
                if observed.get("object_type") in ("junction", "symlink") or observed.get("reparse_target"):
                    raise RuntimeError("REPARSE_ANCESTOR")
                if observed.get("object_type") != "directory":
                    raise RuntimeError("REPARSE_QUERY_UNKNOWN")
            text = str(parent)
            if len(text) <= 3:
                break
            current = parent
            parent = current.parent


class _RealKernel:
    """Win32 calls used by observe/reparse/enum. Unit tests pass a fake kernel instead."""

    def __init__(self, kernel=None):
        self.k = kernel or common.kernel32

    def last_error(self):
        fn = getattr(self.k, "get_last_error", None)
        if callable(fn):
            return int(fn())
        return int(common.ctypes.get_last_error() or 0)

    def GetFileAttributesW(self, path):
        return common.GetFileAttributesW(common.to_win_long_path(path))

    def CreateFileW(self, path, flags):
        handle = common.CreateFileW(
            common.to_win_long_path(path),
            common.GENERIC_READ,
            common.FILE_SHARE_READ,
            None,
            common.OPEN_EXISTING,
            flags,
            None,
        )
        if handle == common.INVALID_HANDLE_VALUE or handle is None:
            raise OSError(common.ctypes.get_last_error(), "CreateFileW failed")
        return handle

    def close(self, handle):
        common.safe_close(handle)

    def GetFileInformationByHandle(self, handle):
        info = common.BY_HANDLE_FILE_INFORMATION()
        if not common.GetFileInformationByHandle(handle, common.ctypes.byref(info)):
            raise OSError(common.ctypes.get_last_error(), "GetFileInformationByHandle failed")
        size = (info.nFileSizeHigh << 32) | info.nFileSizeLow
        file_id = (info.nFileIndexHigh << 32) | info.nFileIndexLow
        mtime = (info.ftLastWriteTime.dwHighDateTime << 32) | info.ftLastWriteTime.dwLowDateTime
        return {"file_id": file_id, "volume_serial": int(info.dwVolumeSerialNumber), "size": size, "mtime": str(mtime), "nlinks": int(info.nNumberOfLinks)}

    def GetFileInformationByHandleEx(self, handle):
        standard = common.FILE_STANDARD_INFO()
        if not common.GetFileInformationByHandleEx(handle, common.FileStandardInfo, common.ctypes.byref(standard), common.ctypes.sizeof(standard)):
            raise OSError(common.ctypes.get_last_error(), "FileStandardInfo failed")
        return {"allocation_size": int(standard.AllocationSize)}

    def hash_handle(self, handle, size: int):
        common.seek_begin(handle)
        digest = hashlib.sha256()
        left = size
        while left:
            piece = common.ctypes.create_string_buffer(min(1024 * 1024, left))
            got = common.wintypes.DWORD(0)
            ok = common.ReadFile(handle, piece, len(piece), common.ctypes.byref(got), None)
            if not ok or got.value == 0:
                raise OSError(common.ctypes.get_last_error(), "hash read failed")
            digest.update(bytes(piece[: got.value]))
            left -= got.value
        return digest.hexdigest()

    def _device(self, handle, code, payload, outbuf, returned):
        fn = self.k.DeviceIoControl
        if getattr(fn, "argtypes", None):
            return fn(handle, code, payload, len(payload) if payload else 0, outbuf, len(outbuf) if outbuf else 0, common.ctypes.byref(returned), None)
        return fn(handle, code, payload, len(payload) if payload else 0, outbuf, len(outbuf) if outbuf else 0, returned, None)

    def create_junction(self, link_path, target):
        wide = common.to_win_long_path(link_path)
        ok = self.k.CreateDirectoryW(wide, None)
        if not ok and self.last_error() != 183:
            raise OSError(self.last_error(), "CreateDirectoryW failed")
        if not ok:
            attrs = self.k.GetFileAttributesW(wide)
            if attrs == 0xFFFFFFFF or not (int(attrs) & common.FILE_ATTRIBUTE_DIRECTORY) or (int(attrs) & common.FILE_ATTRIBUTE_REPARSE_POINT):
                raise RuntimeError("PLACEHOLDER_TYPE")
        handle = self.k.CreateFileW(
            wide,
            common.GENERIC_WRITE,
            0,
            None,
            common.OPEN_EXISTING,
            common.FILE_FLAG_BACKUP_SEMANTICS | common.FILE_FLAG_OPEN_REPARSE_POINT,
            None,
        )
        if handle in (None, 0, common.INVALID_HANDLE_VALUE, -1):
            raise OSError(self.last_error(), "reparse write open failed")
        try:
            returned = common.wintypes.DWORD(0)
            payload = mount_point_buffer(target)
            if not self._device(handle, FSCTL_SET_REPARSE_POINT, payload, None, returned):
                raise OSError(self.last_error(), "FSCTL_SET_REPARSE_POINT failed")
        finally:
            self.k.CloseHandle(handle)
        return True

    def create_directory_symlink(self, link_path, target, relative: bool = False):
        flags = SYMBOLIC_LINK_FLAG_DIRECTORY
        ok = self.k.CreateSymbolicLinkW(common.to_win_long_path(link_path), target if relative else target, flags)
        if not ok:
            raise OSError(self.last_error(), "CreateSymbolicLinkW failed")
        return True

    def read_reparse(self, handle):
        buf = common.ctypes.create_string_buffer(16 * 1024)
        returned = common.wintypes.DWORD(0)
        if not self._device(handle, 0x000900A8, None, buf, returned):
            raise OSError(self.last_error(), "FSCTL_GET_REPARSE_POINT failed")
        return parse_reparse_buffer(bytes(buf[: returned.value]))

    def CreateSymbolicLinkW(self, link, target, flags):
        fn = common.kernel32.CreateSymbolicLinkW
        if fn.argtypes is None:
            fn.argtypes = [common.wintypes.LPCWSTR, common.wintypes.LPCWSTR, common.wintypes.DWORD]
            fn.restype = common.wintypes.BOOLEAN
        return fn(common.to_win_long_path(link), target, flags)

    def DeviceIoControl(self, handle, code, payload: bytes):
        fn = common.kernel32.DeviceIoControl
        if fn.argtypes is None:
            fn.argtypes = [
                common.wintypes.HANDLE,
                common.wintypes.DWORD,
                common.wintypes.LPVOID,
                common.wintypes.DWORD,
                common.wintypes.LPVOID,
                common.wintypes.DWORD,
                common.ctypes.POINTER(common.wintypes.DWORD),
                common.wintypes.LPVOID,
            ]
            fn.restype = common.wintypes.BOOL
        returned = common.wintypes.DWORD(0)
        ok = fn(handle, code, payload, len(payload), None, 0, common.ctypes.byref(returned), None)
        return bool(ok)

    def list_directory_nofollow(self, root):
        return _find_children(root)


class _WIN32_FIND_DATAW(common.ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", common.wintypes.DWORD),
        ("ftCreationTime", common.FILETIME),
        ("ftLastAccessTime", common.FILETIME),
        ("ftLastWriteTime", common.FILETIME),
        ("nFileSizeHigh", common.wintypes.DWORD),
        ("nFileSizeLow", common.wintypes.DWORD),
        ("dwReserved0", common.wintypes.DWORD),
        ("dwReserved1", common.wintypes.DWORD),
        ("cFileName", common.wintypes.WCHAR * 260),
        ("cAlternateFileName", common.wintypes.WCHAR * 14),
    ]


def classify_find_next(ok, err) -> str:
    if ok:
        return "entry"
    if int(err or 0) in (0, 18):
        return "end"
    raise OSError(int(err), "FindNextFileW failed")


def _find_children(root: str) -> list[dict]:
    pattern = common.to_win_long_path(str(root).rstrip("\\") + "\\*")
    data = _WIN32_FIND_DATAW()
    find = common.kernel32.FindFirstFileW
    nxt = common.kernel32.FindNextFileW
    close = common.kernel32.FindClose
    if find.argtypes is None:
        find.argtypes = [common.wintypes.LPCWSTR, common.ctypes.POINTER(_WIN32_FIND_DATAW)]
        find.restype = common.wintypes.HANDLE
        nxt.argtypes = [common.wintypes.HANDLE, common.ctypes.POINTER(_WIN32_FIND_DATAW)]
        nxt.restype = common.wintypes.BOOL
        close.argtypes = [common.wintypes.HANDLE]
        close.restype = common.wintypes.BOOL
    handle = find(pattern, common.ctypes.byref(data))
    if handle == common.INVALID_HANDLE_VALUE or handle is None:
        err = common.ctypes.get_last_error()
        if err in (2, 3):
            return []
        raise OSError(err, "FindFirstFileW failed")
    found = []
    try:
        while True:
            name = data.cFileName
            if name not in (".", ".."):
                attrs = int(data.dwFileAttributes)
                if attrs & common.FILE_ATTRIBUTE_REPARSE_POINT:
                    kind = "junction"
                elif attrs & common.FILE_ATTRIBUTE_DIRECTORY:
                    kind = "directory"
                else:
                    kind = "file"
                found.append({"path": str(root).rstrip("\\") + "\\" + name, "object_type": kind})
            if not nxt(handle, common.ctypes.byref(data)):
                if classify_find_next(False, common.ctypes.get_last_error()) == "end":
                    break
    finally:
        close(handle)
    return found
