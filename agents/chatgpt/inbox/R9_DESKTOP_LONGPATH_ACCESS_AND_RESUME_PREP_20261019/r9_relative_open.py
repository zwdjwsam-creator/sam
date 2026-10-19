# -*- coding: utf-8 -*-
"""Read-only relative NtCreateFile walk. Does not follow reparse points."""
from __future__ import annotations

import ctypes
from ctypes import wintypes

ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

FILE_OPEN = 1
FILE_SHARE_READ = 0x00000001
FILE_DIRECTORY_FILE = 0x00000001
FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020
FILE_NON_DIRECTORY_FILE = 0x00000040
FILE_OPEN_REPARSE_POINT = 0x00200000
FILE_READ_ATTRIBUTES = 0x00000080
FILE_LIST_DIRECTORY = 0x00000001
FILE_READ_DATA = 0x00000001
SYNCHRONIZE = 0x00100000
OBJ_CASE_INSENSITIVE = 0x00000040
FileAttributeTagInformation = 35
STATUS_SUCCESS = 0


class UNICODE_STRING(ctypes.Structure):
    _fields_ = (
        ("Length", wintypes.USHORT),
        ("MaximumLength", wintypes.USHORT),
        ("Buffer", wintypes.LPWSTR),
    )


class OBJECT_ATTRIBUTES(ctypes.Structure):
    _fields_ = (
        ("Length", wintypes.ULONG),
        ("RootDirectory", wintypes.HANDLE),
        ("ObjectName", ctypes.POINTER(UNICODE_STRING)),
        ("Attributes", wintypes.ULONG),
        ("SecurityDescriptor", ctypes.c_void_p),
        ("SecurityQualityOfService", ctypes.c_void_p),
    )


class IO_STATUS_BLOCK(ctypes.Structure):
    _fields_ = (("Status", ctypes.c_ulong), ("Information", ctypes.c_void_p))


class FILE_ATTRIBUTE_TAG_INFORMATION(ctypes.Structure):
    _fields_ = (("FileAttributes", wintypes.ULONG), ("ReparseTag", wintypes.ULONG))


ntdll.NtCreateFile.argtypes = [
    ctypes.POINTER(wintypes.HANDLE),
    wintypes.ULONG,
    ctypes.POINTER(OBJECT_ATTRIBUTES),
    ctypes.POINTER(IO_STATUS_BLOCK),
    ctypes.c_void_p,
    wintypes.ULONG,
    wintypes.ULONG,
    wintypes.ULONG,
    wintypes.ULONG,
    ctypes.c_void_p,
    wintypes.ULONG,
]
ntdll.NtCreateFile.restype = ctypes.c_ulong
ntdll.NtQueryInformationFile.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(IO_STATUS_BLOCK),
    ctypes.c_void_p,
    wintypes.ULONG,
    ctypes.c_int,
]
ntdll.NtQueryInformationFile.restype = ctypes.c_ulong
ntdll.RtlNtStatusToDosError.argtypes = [ctypes.c_ulong]
ntdll.RtlNtStatusToDosError.restype = wintypes.ULONG


class RelativeOpenError(OSError):
    def __init__(self, status: int, stage: str, component: str):
        winerror = int(ntdll.RtlNtStatusToDosError(status))
        super().__init__(winerror, f"relative_open stage={stage} ntstatus={status:#010x} winerror={winerror}")
        self.ntstatus = int(status)
        self.stage = stage
        self.component = component
        self.winerror = winerror


def _name(text: str):
    if text in ("", ".", "..") or "\\" in text or "/" in text or ":" in text:
        raise ValueError("BAD_COMPONENT")
    buf = ctypes.create_unicode_buffer(text)
    uni = UNICODE_STRING()
    uni.Length = len(text) * 2
    uni.MaximumLength = (len(text) + 1) * 2
    uni.Buffer = ctypes.cast(buf, wintypes.LPWSTR)
    return uni, buf


def nt_open_child(parent, component: str, directory: bool):
    uni, buf = _name(component)
    attrs = OBJECT_ATTRIBUTES()
    attrs.Length = ctypes.sizeof(OBJECT_ATTRIBUTES)
    attrs.RootDirectory = parent
    attrs.ObjectName = ctypes.pointer(uni)
    attrs.Attributes = OBJ_CASE_INSENSITIVE
    ios = IO_STATUS_BLOCK()
    handle = wintypes.HANDLE()
    access = (FILE_LIST_DIRECTORY if directory else FILE_READ_DATA) | FILE_READ_ATTRIBUTES | SYNCHRONIZE
    options = FILE_SYNCHRONOUS_IO_NONALERT | FILE_OPEN_REPARSE_POINT
    options |= FILE_DIRECTORY_FILE if directory else FILE_NON_DIRECTORY_FILE
    status = int(ntdll.NtCreateFile(
        ctypes.byref(handle),
        access,
        ctypes.byref(attrs),
        ctypes.byref(ios),
        None,
        0,
        FILE_SHARE_READ,
        FILE_OPEN,
        options,
        None,
        0,
    ))
    del buf
    if status != STATUS_SUCCESS:
        raise RelativeOpenError(status, "directory" if directory else "file", component)
    tag = FILE_ATTRIBUTE_TAG_INFORMATION()
    qios = IO_STATUS_BLOCK()
    qstatus = int(ntdll.NtQueryInformationFile(
        handle,
        ctypes.byref(qios),
        ctypes.byref(tag),
        ctypes.sizeof(tag),
        FileAttributeTagInformation,
    ))
    if qstatus != STATUS_SUCCESS:
        kernel32.CloseHandle(handle)
        raise RelativeOpenError(qstatus, "query", component)
    if tag.ReparseTag:
        kernel32.CloseHandle(handle)
        raise RelativeOpenError(0xC0000010, "reparse", component)
    return handle
