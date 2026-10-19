# -*- coding: utf-8 -*-
"""C-only near-limit formal backend proof. Does not write E: or the real state."""
from __future__ import annotations

import hashlib
import json
import sys
import traceback
from pathlib import Path

CODE = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019\code")
sys.path.insert(0, str(CODE))

import r9_access_alias as alias
import r9_pilot_common_r9fix as common
import r9_temp_name as temp_name
from r9_winio import Win32Syscalls, WindowsBackend

ROOT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_1938_BOUNDARY_AND_REGRESSION_20261019_1950\fixture")
OUT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_1938_BOUNDARY_AND_REGRESSION_20261019_1950\BOUNDARY_TEST.json")
PAYLOAD = b"r9-1950-boundary-proof"
CREATED_DIRS: list[str] = []
CREATED_FILES: list[str] = []


def api_of(path: str) -> int:
    return temp_name.api_utf16(path)


def fill_middle(n: int, width: int = 50) -> str:
    if n < 0:
        raise RuntimeError("NEGATIVE_MIDDLE")
    if n == 0:
        return ""
    parts = []
    left = n
    while left:
        room = min(width, left)
        if left > width and left - room < 2:
            room = left - 2
        if room <= 0:
            raise RuntimeError("COMPONENT_SPLIT")
        parts.append("a" * room)
        left -= room
        if left:
            parts.append("\\")
            left -= 1
    text = "".join(parts)
    if len(text) != n or any(part in ("", ".", "..") or len(part) > width for part in text.split("\\")):
        raise RuntimeError("MIDDLE_SHAPE")
    return text


def dest_for(root: str, api_target: int, leaf: str) -> str:
    need = api_target - 4
    prefix = root.rstrip("\\") + "\\"
    middle_len = need - len(prefix) - len(leaf)
    if middle_len <= 1:
        raise RuntimeError("ROOT_TOO_LONG")
    middle = fill_middle(middle_len - 1)
    dest = prefix + middle + "\\" + leaf
    if api_of(dest) != api_target:
        raise RuntimeError(f"API_LEN {api_of(dest)} != {api_target}")
    if dest.rsplit("\\", 1)[1] != leaf:
        raise RuntimeError("LEAF")
    return dest


def ensure_parent(path: str) -> None:
    parent = path.rsplit("\\", 1)[0]
    acc = parent[:2]
    rest = parent[3:]
    for part in rest.split("\\"):
        acc = acc + "\\" + part
        if acc not in CREATED_DIRS:
            CREATED_DIRS.append(acc)
        wide = common.to_win_long_path(acc)
        ok = common.kernel32.CreateDirectoryW(wide, None)
        if not ok and common.ctypes.get_last_error() not in (183,):
            err = int(common.ctypes.get_last_error() or 0)
            raise OSError(err, f"CreateDirectoryW winerror={err} api={api_of(acc)}")


def delete_created() -> None:
    for path in reversed(CREATED_FILES):
        common.kernel32.DeleteFileW(common.to_win_long_path(path))
    for path in reversed(CREATED_DIRS):
        common.kernel32.RemoveDirectoryW(common.to_win_long_path(path))


def entity_from(source: str, dest: str) -> dict:
    handle = common.open_source_stable(source)
    try:
        ident = common.handle_identity(handle)
    finally:
        common.CloseHandle(handle)
    return {
        "source_path": source,
        "access_path": source,
        "dest_path": dest,
        "entity_key": hashlib.sha256(dest.encode("utf-8")).hexdigest()[:16],
        "file_id": ident["file_id"],
        "volume_serial": ident["volume_serial"],
        "logical_size": int(ident["size"]),
        "mtime": ident["mtime_ft"],
        "mtime_status": "PRESENT",
    }


def read_bytes(path: str) -> bytes:
    handle = common.open_source_stable(path)
    try:
        ident = common.handle_identity(handle)
        size = int(ident["size"])
        buf = common.ctypes.create_string_buffer(size)
        got = common.wintypes.DWORD(0)
        ok = common.ReadFile(handle, buf, size, common.ctypes.byref(got), None)
        if not ok or int(got.value) != size:
            raise RuntimeError("READ")
        return bytes(buf[:size])
    finally:
        common.CloseHandle(handle)


def main() -> None:
    results = []

    def record(name, **fields):
        row = {"name": name, **fields}
        results.append(row)
        print(name, json.dumps(fields, ensure_ascii=False)[:500], flush=True)

    leaf_a = "L" * 51
    leaf_b = "M" * 50
    made_a = dest_for(r"C:\synthetic\near", 32742, leaf_a)
    made_b = dest_for(r"C:\synthetic\near", 32746, leaf_b)
    short_a = temp_name.temp_path(made_a)
    short_b = temp_name.temp_path(made_b)
    record(
        "string_32742",
        dest_api=api_of(made_a),
        leaf=51,
        temp=short_a.rsplit("\\", 1)[1],
        temp_api=api_of(short_a),
        raised=False,
    )
    record(
        "string_32746",
        dest_api=api_of(made_b),
        leaf=50,
        temp=short_b.rsplit("\\", 1)[1],
        temp_api=api_of(short_b),
        raised=False,
    )
    if api_of(short_a) != 32718 or api_of(short_b) != 32723:
        raise SystemExit("SHORT_TEMP_LENGTH")
    too_long = "C:\\" + ("p" * 40 + "\\") * 800 + ("z" * 200)
    raised = False
    try:
        temp_name.temp_path(too_long)
    except ValueError as exc:
        raised = str(exc) == "TEMP_STILL_TOO_LONG"
    record("still_too_long", raised=raised, dest_api=api_of(too_long))

    common.kernel32.DeleteFileW.argtypes = [common.wintypes.LPCWSTR]
    common.kernel32.DeleteFileW.restype = common.wintypes.BOOL
    common.kernel32.RemoveDirectoryW.argtypes = [common.wintypes.LPCWSTR]
    common.kernel32.RemoveDirectoryW.restype = common.wintypes.BOOL
    source = str(ROOT / "source.bin")
    ensure_parent(source)
    src_wide = common.to_win_long_path(source)
    handle = common.CreateFileW(src_wide, common.GENERIC_WRITE, 0, None, 2, common.FILE_ATTRIBUTE_NORMAL, None)
    if handle in (None, common.INVALID_HANDLE_VALUE):
        raise OSError(common.ctypes.get_last_error(), "source create")
    got = common.wintypes.DWORD(0)
    if not common.WriteFile(handle, PAYLOAD, len(PAYLOAD), common.ctypes.byref(got), None):
        raise OSError(common.ctypes.get_last_error(), "source write")
    common.CloseHandle(handle)
    CREATED_FILES.append(source)

    backend = WindowsBackend(Win32Syscalls())
    cases = [
        ("copy_32742", dest_for(str(ROOT / "a"), 32742, leaf_a)),
        ("copy_32746", dest_for(str(ROOT / "b"), 32746, leaf_b)),
        ("copy_short", str(ROOT / "short" / "file.bin")),
    ]
    for name, dest in cases:
        ensure_parent(dest)
        entity = entity_from(source, dest)
        seen = {}

        def before(info, box=seen):
            box.update(info)

        copied = backend.copy_entity(entity, before_commit=before)
        CREATED_FILES.append(dest)
        observed = backend.observe_destination(dest)
        listed = backend.list_nofollow(dest.rsplit("\\", 1)[0])
        digest = backend.content_sha(dest)
        names = [item.get("name") or item.get("path") for item in listed]
        record(
            name,
            function="WindowsBackend.copy_entity",
            dest_api=api_of(dest),
            temp_api=api_of(seen["temp"]),
            temp_name=seen["temp"].rsplit("\\", 1)[1],
            sha256=copied["sha256"],
            bytes=copied["bytes"],
            observe_status=observed.get("status"),
            observe_file_id=observed.get("file_id"),
            content_sha=digest,
            list_contains_leaf=dest.rsplit("\\", 1)[1] in {str(x).rsplit("\\", 1)[-1] for x in names},
            payload_match=read_bytes(dest) == PAYLOAD,
        )

    final = cases[0][1]
    other = str(ROOT / "other.bin")
    other_h = common.CreateFileW(common.to_win_long_path(other), common.GENERIC_WRITE, 0, None, 2, common.FILE_ATTRIBUTE_NORMAL, None)
    if not common.WriteFile(other_h, b"OTHER", 5, common.ctypes.byref(got), None):
        raise OSError(common.ctypes.get_last_error(), "other")
    common.CloseHandle(other_h)
    CREATED_FILES.append(other)
    sc = Win32Syscalls()
    refused = sc.commit_no_replace(other, final)
    record("final_exists_no_replace", commit_returned=refused, dest_unchanged=read_bytes(final) == PAYLOAD)

    conflict_dest = dest_for(str(ROOT / "c"), 32742, "C" * 51)
    ensure_parent(conflict_dest)
    conflict_temp = temp_name.temp_path(conflict_dest)
    ensure_parent(conflict_temp)
    ch = common.CreateFileW(common.to_win_long_path(conflict_temp), common.GENERIC_WRITE, 0, None, common.CREATE_NEW, common.FILE_ATTRIBUTE_NORMAL, None)
    if ch in (None, common.INVALID_HANDLE_VALUE):
        raise OSError(common.ctypes.get_last_error(), "conflict temp")
    if not common.WriteFile(ch, b"KEEP", 4, common.ctypes.byref(got), None):
        raise OSError(common.ctypes.get_last_error(), "keep")
    common.CloseHandle(ch)
    CREATED_FILES.append(conflict_temp)
    conflict_error = ""
    try:
        backend.copy_entity(entity_from(source, conflict_dest))
    except OSError as exc:
        conflict_error = f"OSError winerror={exc.winerror or exc.errno}"
    record("temp_conflict_no_replace", error=conflict_error, temp_unchanged=read_bytes(conflict_temp) == b"KEEP")

    interrupt_dest = str(ROOT / "interrupt" / "file.bin")
    ensure_parent(interrupt_dest)
    interrupted = False
    try:
        def boom(info):
            raise RuntimeError("INTERRUPT")
        backend.copy_entity(entity_from(source, interrupt_dest), before_commit=boom)
    except RuntimeError as exc:
        interrupted = str(exc) == "INTERRUPT"
    itemp = temp_name.temp_path(interrupt_dest)
    CREATED_FILES.append(itemp)
    second = ""
    try:
        backend.copy_entity(entity_from(source, interrupt_dest))
    except OSError as exc:
        second = f"OSError winerror={exc.winerror or exc.errno}"
    record(
        "interrupt_resume_refuses_existing_temp",
        interrupted=interrupted,
        temp_api=api_of(itemp),
        temp_payload=read_bytes(itemp) == PAYLOAD,
        second_error=second,
    )

    bad_tail = False
    try:
        alias.tail_after_anchor(alias.load_anchor() + "\\..\\x", alias.load_anchor())
    except ValueError as exc:
        bad_tail = str(exc) == "ACCESS_TAIL_REJECTED"
    outside = alias.access_path(r"D:\not-anchor\file", r"\\192.168.100.2\E_DRIVE\BLACKBOX\file")
    bad_contract = alias.verify_anchor({"access_unc": alias.ALIAS_UNC, "facts_content_sha256": "0" * 64, "inventory_anchor": "x", "anchor_file_id": alias.EXPECTED_FILE_ID, "source_volume_serial": alias.EXPECTED_VOLUME})
    good = alias.verify_anchor({
        "access_unc": alias.ALIAS_UNC,
        "facts_content_sha256": alias.FACTS_CONTENT_SHA256,
        "inventory_anchor": alias.load_anchor(),
        "anchor_file_id": alias.EXPECTED_FILE_ID,
        "source_volume_serial": alias.EXPECTED_VOLUME,
    })
    record("alias_checks", bad_tail=bad_tail, outside_unchanged=outside.endswith("BLACKBOX\\file"), bad_contract=bad_contract is False, good_anchor=good is True)

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    required = {
        "string_32742": True,
        "string_32746": True,
        "still_too_long": True,
        "copy_32742": True,
        "copy_32746": True,
        "copy_short": True,
        "final_exists_no_replace": True,
        "temp_conflict_no_replace": True,
        "interrupt_resume_refuses_existing_temp": True,
        "alias_checks": True,
    }
    by_name = {row["name"]: row for row in results}
    ok = all(name in by_name for name in required)
    ok = ok and by_name["copy_32742"]["payload_match"] and by_name["copy_32746"]["payload_match"] and by_name["copy_short"]["payload_match"]
    ok = ok and by_name["copy_32742"]["content_sha"] == hashlib.sha256(PAYLOAD).hexdigest()
    ok = ok and by_name["final_exists_no_replace"]["commit_returned"] is False and by_name["final_exists_no_replace"]["dest_unchanged"]
    ok = ok and by_name["temp_conflict_no_replace"]["temp_unchanged"] and "winerror=80" in by_name["temp_conflict_no_replace"]["error"]
    ok = ok and by_name["interrupt_resume_refuses_existing_temp"]["temp_payload"] and "winerror=80" in by_name["interrupt_resume_refuses_existing_temp"]["second_error"]
    ok = ok and by_name["alias_checks"]["good_anchor"] and by_name["alias_checks"]["bad_contract"] and by_name["alias_checks"]["bad_tail"] and by_name["alias_checks"]["outside_unchanged"]
    ok = ok and by_name["still_too_long"]["raised"]
    print("BOUNDARY_OK" if ok else "BOUNDARY_FAIL")
    if not ok:
        raise SystemExit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
    finally:
        try:
            delete_created()
        except Exception:
            traceback.print_exc()
