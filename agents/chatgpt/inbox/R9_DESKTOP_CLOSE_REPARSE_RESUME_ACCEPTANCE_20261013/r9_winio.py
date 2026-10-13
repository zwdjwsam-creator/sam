# -*- coding: utf-8 -*-
"""Windows IO backend. Importing this module does not create or write a file.

Tests must not call stream_copy_handles. The scheduler uses a fake backend until a
future authorized task binds a formatted destination.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import r9_pilot_common_r9fix as common

if getattr(common.kernel32.MoveFileW, "argtypes", None) is None:
    common.kernel32.MoveFileW.argtypes = [common.wintypes.LPCWSTR, common.wintypes.LPCWSTR]
    common.kernel32.MoveFileW.restype = common.wintypes.BOOL

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


def observe_via_winapi(api, path: str) -> dict:
    """Field-complete observe. Only Win32 2/3 are MISSING. Other codes are ERROR."""
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
        kind = "directory" if is_dir else "file"
        if is_reparse:
            parsed = api.read_reparse(handle)
            reparse_target = parsed.get("target")
            kind = parsed.get("kind") or "junction"
        digest = None
        if kind == "file":
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
        return observe_via_winapi(_RealKernel(), path)

    def create_reparse(self, link_path, target, kind="junction"):
        type(self).write_calls += 1
        if not apply_reparse(_RealKernel(), link_path, target, kind):
            raise OSError(common.ctypes.get_last_error(), "create_reparse failed")
        return True

    def list_nofollow(self, root):
        return enumerate_nofollow(_RealKernel(), root)

    def ensure_directory(self, path):
        type(self).write_calls += 1
        ok = common.kernel32.CreateDirectoryW(common.to_win_long_path(path), None)
        if not ok and common.ctypes.get_last_error() not in (183,):
            raise OSError(common.ctypes.get_last_error(), "CreateDirectoryW failed")

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
        data = bytes(self.files.pop(temp))
        self.files[dest] = data
        self.identities[dest] = {
            "file_id": f"dest-{self.next_id}",
            "volume_serial": "DEST",
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
            "volume_serial": "DEST",
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
            "volume_serial": "DEST",
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
                "sha256": hashlib.sha256(data).hexdigest(),
            })
        return found


class WindowsBackend:
    def __init__(self, syscalls=None):
        self.sc = syscalls if syscalls is not None else Win32Syscalls()
        self.calls = 0

    def copy_entity(self, entity, before_commit=None):
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
            after = self.sc.identity(handle)
            if (
                after.get("file_id") != ident.get("file_id")
                or after.get("volume_serial") != ident.get("volume_serial")
                or int(after.get("size")) != int(ident.get("size"))
                or after.get("mtime") != ident.get("mtime")
            ):
                raise RuntimeError("SOURCE_CHANGED_DURING_COPY")
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
            if before_commit is not None:
                before_commit({"sha256": digest, "bytes": total, "temp": temp})
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

    def assert_no_reparse_ancestor(self, path):
        current = Path(str(path))
        parent = current.parent
        while parent != current:
            observed = self.sc.observe(str(parent))
            if observed.get("object_type") in ("junction", "symlink"):
                raise RuntimeError("REPARSE_ANCESTOR")
            text = str(parent)
            if len(text) <= 3:
                break
            current = parent
            parent = current.parent


class _RealKernel:
    """Win32 calls used by observe/reparse/enum. Unit tests pass a fake kernel instead."""

    def last_error(self):
        return common.ctypes.get_last_error()

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

    def read_reparse(self, handle):
        buf = common.ctypes.create_string_buffer(16 * 1024)
        returned = common.wintypes.DWORD(0)
        ok = common.kernel32.DeviceIoControl(handle, 0x000900A8, None, 0, buf, len(buf), common.ctypes.byref(returned), None)
        if not ok:
            raise OSError(common.ctypes.get_last_error(), "FSCTL_GET_REPARSE_POINT failed")
        raw = bytes(buf[: returned.value])
        tag = int.from_bytes(raw[0:4], "little")
        name_len = int.from_bytes(raw[10:12], "little")
        name = raw[16:16 + name_len].decode("utf-16le").replace("\\??\\", "")
        kind = "symlink" if tag == IO_REPARSE_TAG_SYMLINK else "junction"
        return {"target": name, "kind": kind}

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
                break
    finally:
        close(handle)
    return found
