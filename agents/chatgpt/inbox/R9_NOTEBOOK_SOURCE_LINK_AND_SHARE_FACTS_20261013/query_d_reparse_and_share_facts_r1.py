# -*- coding: utf-8 -*-
"""R9_NOTEBOOK_SOURCE_LINK_AND_SHARE_FACTS_20261013_1957 — read-only."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import socket
import struct
import subprocess
import sys
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT")
import r9_pilot_common_r9fix as r9  # noqa: E402

WORK = Path(r"C:\LAN_SHARE_REPORT\R9_NOTEBOOK_SOURCE_LINK_AND_SHARE_FACTS_20261013")
MAP = WORK / "input" / "R9_SAM_DEPENDENCY_MAP_R3.json"
TASK_ID = "R9_NOTEBOOK_SOURCE_LINK_AND_SHARE_FACTS_20261013_1957"
EXPECT_MAP_SHA = "1c00ece5db519bf39de33473b5cbb81728cbdd65d8d38d6e00532f4a136084fe"
D_SNAP_SHA = "4c094df43ca348acdc89498a49660ad9120d7ca3ef9bfe21f8b3c9e414257795"
E_DELTA_SHA = "aa58ed8bd7b22e015a041133007a9b031514eb82baf27d80ace0e48f2a48bd1c"

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
IO_REPARSE_TAG_APPEXECLINK = 0x8000001B

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


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def kind_from_tag(tag: int | None) -> str:
    if tag is None:
        return "UNKNOWN"
    if tag == IO_REPARSE_TAG_MOUNT_POINT:
        return "junction_or_mount_point"
    if tag == IO_REPARSE_TAG_SYMLINK:
        return "symlink"
    if tag == IO_REPARSE_TAG_APPEXECLINK:
        return "appexeclink"
    return f"other_tag_{tag}"


def parse_reparse_buffer(buf: bytes) -> dict:
    """Parse REPARSE_DATA_BUFFER minimally for mount point / symlink."""
    if len(buf) < 8:
        return {"parse_error": "buffer_too_short", "raw_len": len(buf)}
    tag = struct.unpack_from("<I", buf, 0)[0]
    data_len = struct.unpack_from("<H", buf, 4)[0]
    # reserved = struct.unpack_from("<H", buf, 6)[0]
    out = {"reparse_tag": tag, "reparse_tag_hex": hex(tag), "data_length": data_len}
    # Path buffer starts at offset 8 for both mount point and symlink, with extra flags for symlink
    try:
        if tag == IO_REPARSE_TAG_MOUNT_POINT:
            # ReparseDataLength path fields at offset 8
            sub_off, sub_len, print_off, print_len = struct.unpack_from("<HHHH", buf, 8)
            path_buf = buf[16 : 16 + data_len - 8]
            sub = path_buf[sub_off : sub_off + sub_len].decode("utf-16-le", errors="replace").rstrip("\x00")
            prn = path_buf[print_off : print_off + print_len].decode("utf-16-le", errors="replace").rstrip("\x00")
            out.update({"substitute_name": sub, "print_name": prn, "flags": None})
        elif tag == IO_REPARSE_TAG_SYMLINK:
            sub_off, sub_len, print_off, print_len, flags = struct.unpack_from("<HHHHH", buf, 8)
            # flags is 4 bytes actually in SYMLINK_REPARSE_BUFFER — layout: 4xUSHORT + ULONG
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


def normalize_nt_path(p: str | None) -> str | None:
    if not p:
        return None
    s = p
    if s.startswith("\\??\\"):
        s = s[4:]
    if s.startswith("\\\\?\\"):
        s = s[4:]
    return s


def query_one(path: str, map_id: int, expected_target: str | None, final_target: str | None) -> dict:
    rec = {
        "map_id": map_id,
        "source_path": path,
        "hostname": socket.gethostname(),
        "queried_at_utc": utc(),
        "queried_at_local": datetime.now().astimezone().isoformat(),
        "exists": None,
        "win32_attrs": None,
        "reparse_tag": None,
        "reparse_tag_hex": None,
        "kind": None,
        "raw_target": None,
        "print_name": None,
        "flags": None,
        "normalized_target": None,
        "expected_target": expected_target,
        "final_resolved_target_map": final_target,
        "matches_map": None,
        "source_volume_serial": None,
        "source_volume_serial_dword": None,
        "link_file_id": None,
        "mtime_ft": None,
        "size": None,
        "nlinks": None,
        "file_attribute_tag_info": None,
        "fsctl_get_reparse_point": None,
        "status": "ERROR",
        "errors": [],
    }
    p = Path(path)
    if not p.exists():
        # exists() may follow; use GetFileAttributes
        pass
    attrs = r9.GetFileAttributesW(path)
    if attrs == 0xFFFFFFFF:
        err = ctypes.get_last_error()
        rec["errors"].append(f"GetFileAttributesW_fail winerror={err}")
        rec["exists"] = False
        return rec
    rec["exists"] = True
    rec["win32_attrs"] = int(attrs)
    is_reparse = bool(attrs & 0x400)
    if not is_reparse:
        rec["errors"].append("NOT_REPARSE_POINT")
        rec["kind"] = "not_reparse"
        # still try identity without OPEN_REPARSE? use open_source_stable which opens reparse
    # open handle
    try:
        h = r9.CreateFileW(
            path,
            GENERIC_READ,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            None,
            OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
            None,
        )
        if h == INVALID_HANDLE_VALUE or h is None:
            err = ctypes.get_last_error()
            rec["errors"].append(f"CreateFileW_fail winerror={err}")
            return rec
        try:
            # identity
            try:
                ident = r9.handle_identity(h)
                # handle_identity raises if reparse — catch and use raw GetFileInformationByHandle
            except RuntimeError as e:
                if "SOURCE_IS_REPARSE" in str(e):
                    info = r9.BY_HANDLE_FILE_INFORMATION()
                    if not r9.GetFileInformationByHandle(h, ctypes.byref(info)):
                        err = ctypes.get_last_error()
                        rec["errors"].append(f"GetFileInformationByHandle_fail winerror={err}")
                    else:
                        fid = (info.nFileIndexHigh << 32) | info.nFileIndexLow
                        size = (info.nFileSizeHigh << 32) | info.nFileSizeLow
                        mtime = (info.ftLastWriteTime.dwHighDateTime << 32) | info.ftLastWriteTime.dwLowDateTime
                        rec["source_volume_serial"] = str(info.dwVolumeSerialNumber)
                        rec["source_volume_serial_dword"] = int(info.dwVolumeSerialNumber)
                        rec["link_file_id"] = str(fid)
                        rec["mtime_ft"] = str(mtime)
                        rec["size"] = int(size)
                        rec["nlinks"] = int(info.nNumberOfLinks)
                        rec["win32_attrs"] = int(info.dwFileAttributes)
                else:
                    rec["errors"].append(f"identity:{e}")
            else:
                rec["source_volume_serial"] = ident.get("volume_serial")
                rec["source_volume_serial_dword"] = ident.get("volume_serial_dword")
                rec["link_file_id"] = ident.get("file_id")
                rec["mtime_ft"] = ident.get("mtime_ft")
                rec["size"] = ident.get("size")
                rec["nlinks"] = ident.get("nlinks")

            # FileAttributeTagInfo
            tag_info = FILE_ATTRIBUTE_TAG_INFO()
            if GetFileInformationByHandleEx(h, FileAttributeTagInfo, ctypes.byref(tag_info), ctypes.sizeof(tag_info)):
                rec["file_attribute_tag_info"] = {
                    "FileAttributes": int(tag_info.FileAttributes),
                    "ReparseTag": int(tag_info.ReparseTag),
                    "ReparseTag_hex": hex(int(tag_info.ReparseTag)),
                }
                rec["reparse_tag"] = int(tag_info.ReparseTag)
                rec["reparse_tag_hex"] = hex(int(tag_info.ReparseTag))
            else:
                err = ctypes.get_last_error()
                rec["errors"].append(f"FileAttributeTagInfo_fail winerror={err}")

            # FSCTL_GET_REPARSE_POINT
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
                raw = outbuf.raw[: ret.value]
                parsed = parse_reparse_buffer(raw)
                rec["fsctl_get_reparse_point"] = {
                    "bytes_returned": int(ret.value),
                    **parsed,
                }
                if rec["reparse_tag"] is None and "reparse_tag" in parsed:
                    rec["reparse_tag"] = parsed["reparse_tag"]
                    rec["reparse_tag_hex"] = parsed.get("reparse_tag_hex")
                rec["raw_target"] = parsed.get("substitute_name")
                rec["print_name"] = parsed.get("print_name")
                rec["flags"] = parsed.get("flags")
                rec["normalized_target"] = normalize_nt_path(parsed.get("substitute_name")) or normalize_nt_path(
                    parsed.get("print_name")
                )
            else:
                err = ctypes.get_last_error()
                rec["errors"].append(f"FSCTL_GET_REPARSE_POINT_fail winerror={err}")
                rec["fsctl_get_reparse_point"] = {"ok": False, "winerror": err}
        finally:
            r9.CloseHandle(h)
    except Exception as e:
        rec["errors"].append(f"{type(e).__name__}:{e}")

    rec["kind"] = kind_from_tag(rec["reparse_tag"])
    # match map targets
    norm = (rec.get("normalized_target") or "").replace("/", "\\").rstrip("\\").lower()
    exp = (expected_target or "").replace("/", "\\").rstrip("\\").lower()
    fin = (final_target or "").replace("/", "\\").rstrip("\\").lower()
    rec["matches_map"] = bool(norm) and (norm == exp or norm == fin)
    if rec["reparse_tag"] is not None and isinstance(rec["reparse_tag"], int) and rec["reparse_tag"] != 0:
        # valid numeric tag obtained
        if not any("CreateFileW_fail" in e or "GetFileAttributesW_fail" in e for e in rec["errors"]):
            # ERROR status only if critical; soft parse issues stay but status OK if tag present
            critical = [e for e in rec["errors"] if "fail winerror" in e and "FileAttributeTagInfo" not in e]
            # if we have tag from either API, OK
            rec["status"] = "OK" if rec["reparse_tag"] else "ERROR"
            if rec["status"] == "OK" and critical and "FSCTL_GET_REPARSE_POINT_fail" in critical[0] and rec["reparse_tag"]:
                rec["status"] = "OK"  # tag from FileAttributeTagInfo enough for LINK_TYPES_VERIFIED numeric tag
    return rec


def collect_share_facts(selected_paths: list[str]) -> dict:
    host = socket.gethostname()
    # IPs
    ips = []
    try:
        for info in socket.getaddrinfo(host, None):
            ip = info[4][0]
            if ":" not in ip and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    # also adapters via ipconfig parse light
    try:
        out = subprocess.check_output(["ipconfig"], text=True, encoding="utf-8", errors="replace")
        for line in out.splitlines():
            if "IPv4" in line or "IP Address" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    ip = parts[-1].strip()
                    if ip and ip not in ips:
                        ips.append(ip)
    except Exception:
        pass

    shares = []
    smb_err = None
    try:
        ps = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-SmbShare | Select-Object Name,Path,Description | ConvertTo-Json -Compress",
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        data = json.loads(ps) if ps.strip() else []
        if isinstance(data, dict):
            data = [data]
        for s in data:
            shares.append({"Name": s.get("Name"), "Path": s.get("Path"), "Description": s.get("Description")})
    except Exception as e:
        smb_err = f"{type(e).__name__}:{e}"

    def vol_serial(letter: str) -> dict:
        try:
            # GetVolumeInformationW
            root = f"{letter}\\"
            vol_name = ctypes.create_unicode_buffer(261)
            fs_name = ctypes.create_unicode_buffer(261)
            serial = wintypes.DWORD()
            max_comp = wintypes.DWORD()
            flags = wintypes.DWORD()
            ok = kernel32.GetVolumeInformationW(
                root, vol_name, 261, ctypes.byref(serial), ctypes.byref(max_comp), ctypes.byref(flags), fs_name, 261
            )
            if not ok:
                return {"letter": letter, "error": f"winerror={ctypes.get_last_error()}"}
            return {
                "letter": letter,
                "volume_name": vol_name.value,
                "file_system": fs_name.value,
                "volume_serial_dword": int(serial.value),
                "volume_serial_hex": format(int(serial.value), "X"),
            }
        except Exception as e:
            return {"letter": letter, "error": str(e)}

    e_vol = vol_serial("E:")
    d_vol = vol_serial("D:")

    e_share = None
    for s in shares:
        name = (s.get("Name") or "").upper()
        path = (s.get("Path") or "").replace("/", "\\")
        if name == "E_DRIVE" or path.upper().rstrip("\\") in ("E:", "E:\\") or path.upper().startswith("E:\\BLACKBOX"):
            e_share = s
            break
    # also match Path E:\
    if e_share is None:
        for s in shares:
            path = (s.get("Path") or "").replace("/", "\\").upper()
            if path.rstrip("\\") == "E:" or path.startswith("E:\\"):
                if (s.get("Name") or "").upper() == "E_DRIVE" or e_share is None:
                    e_share = s

    # D coverage for selected paths
    d_share_candidates = []
    for s in shares:
        sp = (s.get("Path") or "").replace("/", "\\")
        if not sp:
            continue
        sp_norm = sp.rstrip("\\")
        for sel in selected_paths:
            sel_n = sel.replace("/", "\\")
            if sel_n.upper().startswith(sp_norm.upper() + "\\") or sel_n.upper().rstrip("\\") == sp_norm.upper():
                d_share_candidates.append(s)
                break

    # unique by name
    seen = set()
    d_shares = []
    for s in d_share_candidates:
        n = s.get("Name")
        if n not in seen:
            seen.add(n)
            d_shares.append(s)

    unc_examples = []
    for s in d_shares:
        root = (s.get("Path") or "").replace("/", "\\").rstrip("\\")
        name = s.get("Name")
        # pick one selected path under this share
        for sel in selected_paths:
            sel_n = sel.replace("/", "\\")
            if sel_n.upper().startswith(root.upper() + "\\") or sel_n.upper().rstrip("\\") == root.upper():
                rel = sel_n[len(root) :].lstrip("\\")
                unc = f"\\\\{host}\\{name}\\{rel}" if rel else f"\\\\{host}\\{name}"
                # also IP example if 192.168.100.2 present
                unc_examples.append(
                    {
                        "share_name": name,
                        "share_local_root": root,
                        "source_local": sel_n,
                        "unc_hostname": unc,
                        "unc_ip_192_168_100_2": (
                            f"\\\\192.168.100.2\\{name}\\{rel}" if "192.168.100.2" in ips else None
                        ),
                    }
                )
                break

    e_covers_blackbox = False
    if e_share and e_share.get("Path"):
        ep = e_share["Path"].replace("/", "\\").rstrip("\\").upper()
        e_covers_blackbox = ep in ("E:", "E:\\") or ep == "E:\\BLACKBOX" or "E:\\BLACKBOX".startswith(ep + "\\") or ep.startswith("E:\\BLACKBOX")
        # if share is E:\, it covers E:\BLACKBOX
        if ep.rstrip("\\") == "E:":
            e_covers_blackbox = True

    facts = {
        "task_id": TASK_ID,
        "host": host,
        "ips": ips,
        "has_ip_192_168_100_2": "192.168.100.2" in ips,
        "observed_at": utc(),
        "smb_query_error": smb_err,
        "shares_relevant": [s for s in shares if (s.get("Name") or "").upper() in ("E_DRIVE",) or (s.get("Path") or "").upper().startswith("D:") or (s.get("Path") or "").upper().startswith("E:")],
        "E_DRIVE_share": e_share,
        "E_SHARE_EXISTS": e_share is not None,
        "E_share_covers_E_BLACKBOX": e_covers_blackbox,
        "D_shares_covering_selected_paths": d_shares,
        "D_SHARE_EXISTS": len(d_shares) > 0,
        "D_SOURCE_UNC_RESOLVED": len(unc_examples) > 0,
        "unc_mapping_examples": unc_examples,
        "volume_serials": {"E": e_vol, "D": d_vol},
        "volume_serial_reference_only": {"E_historical": "2387166462", "D_historical": "3187598165"},
        "DESKTOP_SMB_ACCESS_VERIFIED": False,
        "errors": [smb_err] if smb_err else [],
        "notes": [
            "Local share visibility ≠ desktop authenticated access",
            "No net use / ACL / password / network changes performed",
            "WinError1326 not solved this round",
        ],
    }
    return facts


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "reports").mkdir(exist_ok=True)
    (WORK / "logs").mkdir(exist_ok=True)

    b = MAP.read_bytes()
    map_sha = hashlib.sha256(b).hexdigest()
    assert map_sha == EXPECT_MAP_SHA, f"map sha mismatch {map_sha}"
    j = json.loads(b.decode("utf-8"))
    links = j["links"]
    sel = [L for L in links if L.get("direction") == "D_TO_E" and 25 <= int(L["id"]) <= 40]
    assert len(sel) == 16, len(sel)

    records = []
    for L in sorted(sel, key=lambda x: int(x["id"])):
        print(f"query id={L['id']} path={L['source_path']}", flush=True)
        rec = query_one(
            L["source_path"],
            int(L["id"]),
            L.get("current_readlink_target"),
            L.get("final_resolved_target"),
        )
        records.append(rec)

    ok_n = sum(1 for r in records if r["status"] == "OK" and r.get("reparse_tag"))
    err_n = sum(1 for r in records if r["status"] != "OK" or not r.get("reparse_tag"))
    link_types_verified = ok_n == 16 and all(
        isinstance(r.get("reparse_tag"), int) and r["reparse_tag"] != 0 for r in records
    )

    overlay = {
        "schema_version": "D_REPARSE_TYPE_OVERLAY_V1",
        "task_id": TASK_ID,
        "host": socket.gethostname(),
        "queried_at": utc(),
        "map_file": str(MAP),
        "map_file_sha256": map_sha,
        "d_snapshot_sha256": D_SNAP_SHA,
        "e_delta_canonical_sha256_retained": E_DELTA_SHA,
        "LINK_TYPES_VERIFIED": link_types_verified,
        "stats": {"expected": 16, "observed": len(records), "ok": ok_n, "errors": err_n},
        "records": records,
    }
    overlay_path = WORK / "reports" / "D_REPARSE_TYPE_OVERLAY.json"
    overlay_path.write_text(json.dumps(overlay, ensure_ascii=False, indent=2), encoding="utf-8")

    facts = collect_share_facts([L["source_path"] for L in sel])
    facts_path = WORK / "reports" / "SOURCE_SHARE_FACTS.json"
    facts_path.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")

    # tag summary
    tag_counts = {}
    for r in records:
        k = r.get("kind") or "UNKNOWN"
        tag_counts[k] = tag_counts.get(k, 0) + 1

    report = f"""# SAM_REPORT — {TASK_ID}

generated_at: {utc()}
hostname: {socket.gethostname()}
phase: SOURCE_METADATA_READONLY
desktop_ZHANGWEI: HOLD

COPY_AUTHORIZED: false
FORMAT_DONE: false
FULL_MIGRATION: false
DESKTOP_SMB_ACCESS_VERIFIED: false
WRITE_TESTS_NOT_RUN: true

## Map
- file: R9_SAM_DEPENDENCY_MAP_R3.json
- sha256: `{map_sha}` (match expected)
- selected: D_TO_E id 25–40 = 16

## Link types
- LINK_TYPES_VERIFIED: {link_types_verified}
- ok/errors: {ok_n}/{err_n}
- kind counts: {json.dumps(tag_counts, ensure_ascii=False)}
- numeric tags from FileAttributeTagInfo and/or FSCTL_GET_REPARSE_POINT
- D snapshot / E delta SHAs retained unchanged ({D_SNAP_SHA[:16]}… / {E_DELTA_SHA[:16]}…)

## Share facts
- E_SHARE_EXISTS: {facts.get('E_SHARE_EXISTS')}
- E_share_covers_E_BLACKBOX: {facts.get('E_share_covers_E_BLACKBOX')}
- D_SHARE_EXISTS: {facts.get('D_SHARE_EXISTS')}
- D_SOURCE_UNC_RESOLVED: {facts.get('D_SOURCE_UNC_RESOLVED')}
- has_ip_192_168_100_2: {facts.get('has_ip_192_168_100_2')}
- ips: {facts.get('ips')}
- DESKTOP_SMB_ACCESS_VERIFIED: false (not tested)

## Artifacts
- D_REPARSE_TYPE_OVERLAY.json
- SOURCE_SHARE_FACTS.json
- query script + FILE_SHA256.json

## Notes
- No business copy/hash, no SMB/network changes, no desktop E write tests.
- 37 desktop unit tests PASS ≠ IMPLEMENTATION_READY / real IO.
"""
    (WORK / "reports" / "SAM_REPORT.md").write_text(report, encoding="utf-8")

    files = {
        "D_REPARSE_TYPE_OVERLAY.json": overlay_path,
        "SOURCE_SHARE_FACTS.json": facts_path,
        "SAM_REPORT.md": WORK / "reports" / "SAM_REPORT.md",
        "query_d_reparse_and_share_facts_r1.py": WORK / "src" / "query_d_reparse_and_share_facts_r1.py",
    }
    sha_doc = {name: {"path": str(p), "sha256": sha256_file(p), "bytes": p.stat().st_size} for name, p in files.items()}
    (WORK / "reports" / "FILE_SHA256.json").write_text(json.dumps(sha_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"LINK_TYPES_VERIFIED": link_types_verified, "ok": ok_n, "errors": err_n, "D_SHARE_EXISTS": facts.get("D_SHARE_EXISTS"), "E_SHARE_EXISTS": facts.get("E_SHARE_EXISTS")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
