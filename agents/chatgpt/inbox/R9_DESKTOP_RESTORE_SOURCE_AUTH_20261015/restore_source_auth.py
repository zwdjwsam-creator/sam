# -*- coding: utf-8 -*-
"""Reuse an existing source SMB session or one saved credential. Never writes secrets."""
from __future__ import annotations

import ctypes
import json
import socket
import sqlite3
import subprocess
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
import r9_pilot_common_r9fix as common

ROOT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_RESTORE_SOURCE_AUTH_20261015")
PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\FINAL_CANDIDATE.sqlite")
E_ROOT = r"\\192.168.100.2\E_DRIVE\BLACKBOX"
D_ROOT = r"\\192.168.100.2\D_DRIVE"
E_FILE = r"\\192.168.100.2\E_DRIVE\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R9_ASOF_20260805_20260806_004303\standard\fund\ETF_NAV\ETF_NAV__fund_etf_nav__150306.XSHE_150310.XSHE__2018__v1__20260712_103337.parquet"
D_FILE = r"\\192.168.100.2\D_DRIVE\backtest_lab\02_blackbox_jq_compat_engine\rule_library\jq_official_canonical_R1\CN_A_SHARE_FEE_SCHEDULE_R1.json"
E_INV = r"E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R9_ASOF_20260805_20260806_004303\standard\fund\ETF_NAV\ETF_NAV__fund_etf_nav__150306.XSHE_150310.XSHE__2018__v1__20260712_103337.parquet"
D_INV = r"D:\backtest_lab\02_blackbox_jq_compat_engine\rule_library\jq_official_canonical_R1\CN_A_SHARE_FEE_SCHEDULE_R1.json"
EXPECTED = {"e": 2387166462, "d": 3187598165}


class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class NETRESOURCE(ctypes.Structure):
    _fields_ = [
        ("dwScope", wintypes.DWORD),
        ("dwType", wintypes.DWORD),
        ("dwDisplayType", wintypes.DWORD),
        ("dwUsage", wintypes.DWORD),
        ("lpLocalName", wintypes.LPWSTR),
        ("lpRemoteName", wintypes.LPWSTR),
        ("lpComment", wintypes.LPWSTR),
        ("lpProvider", wintypes.LPWSTR),
    ]


def now_pair() -> dict:
    local = datetime.now().astimezone()
    return {"local": local.isoformat(timespec="seconds"), "utc": local.astimezone(timezone.utc).isoformat(timespec="seconds")}


def run(args: list[str]) -> dict:
    proc = subprocess.run(args, capture_output=True, timeout=30)
    return {
        "exit": proc.returncode,
        "stdout": proc.stdout.decode("utf-8", errors="replace"),
        "stderr": proc.stderr.decode("utf-8", errors="replace"),
    }


def relevant(target: str) -> bool:
    text = str(target or "")
    upper = text.upper()
    if "TERMSRV/" in upper or "LEGACYGENERIC:TARGET=TERMSRV" in upper:
        return False
    return "192.168.100.2" in text or upper.endswith("\\SAM") or "TARGET=SAM" in upper or upper.endswith("/SAM")


def list_credentials() -> dict:
    adv = ctypes.WinDLL("advapi32")
    adv.CredEnumerateW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(ctypes.POINTER(ctypes.POINTER(CREDENTIAL)))]
    adv.CredEnumerateW.restype = wintypes.BOOL
    adv.CredFree.argtypes = [ctypes.c_void_p]
    count = wintypes.DWORD()
    array = ctypes.POINTER(ctypes.POINTER(CREDENTIAL))()
    ok = adv.CredEnumerateW(None, 0, ctypes.byref(count), ctypes.byref(array))
    if not ok:
        err = ctypes.windll.kernel32.GetLastError()
        return {"ok": False, "winerror": int(err), "relevant": []}
    found = []
    try:
        for index in range(count.value):
            item = array[index].contents
            target = item.TargetName or ""
            if not relevant(target):
                continue
            found.append({
                "target": target,
                "user": item.UserName or "",
                "type": int(item.Type),
                "has_secret": int(item.CredentialBlobSize) > 0,
                "last_written": int((item.LastWritten.dwHighDateTime << 32) | item.LastWritten.dwLowDateTime),
            })
    finally:
        adv.CredFree(array)
    return {"ok": True, "winerror": 0, "relevant": found}


def connect_saved(target: str, cred_type: int, remote: str) -> dict:
    adv = ctypes.WinDLL("advapi32")
    adv.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
    adv.CredReadW.restype = wintypes.BOOL
    adv.CredFree.argtypes = [ctypes.c_void_p]
    cred = ctypes.POINTER(CREDENTIAL)()
    if not adv.CredReadW(target, cred_type, 0, ctypes.byref(cred)):
        return {"attempted": False, "winerror": ctypes.get_last_error(), "reason": "CRED_READ_FAILED"}
    info = cred.contents
    if int(info.CredentialBlobSize) <= 0:
        adv.CredFree(cred)
        return {"attempted": False, "winerror": None, "reason": "SAVED_RECORD_HAS_NO_SECRET"}
    raw = ctypes.string_at(info.CredentialBlob, info.CredentialBlobSize)
    user = info.UserName or ""
    secret = raw.decode("utf-16-le", errors="ignore").split("\x00", 1)[0]
    adv.CredFree(cred)
    resource = NETRESOURCE()
    resource.dwType = 1
    resource.lpRemoteName = remote
    mpr = ctypes.WinDLL("mpr")
    mpr.WNetAddConnection2W.argtypes = [ctypes.POINTER(NETRESOURCE), wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
    mpr.WNetAddConnection2W.restype = wintypes.DWORD
    try:
        code = int(mpr.WNetAddConnection2W(ctypes.byref(resource), user, secret, 0))
    finally:
        secret = "\x00" * len(secret)
        del secret
        del raw
    return {"attempted": True, "winerror": code, "user": user, "target": target, "remote": remote, "flags": "NONINTERACTIVE"}


def open_meta(path: str) -> dict:
    handle = None
    try:
        handle = common.open_source_stable(path)
        meta = common.handle_identity(handle)
        meta.update({"ok": True, "winerror": 0, "path": path, "payload_read": False, "opened_with": "open_source_stable"})
        return meta
    except OSError as exc:
        code = exc.winerror if exc.winerror else exc.errno
        return {"ok": False, "winerror": code, "error": "OPEN_FAILED", "path": path, "payload_read": False}
    except RuntimeError as exc:
        text = str(exc)
        return {"ok": False, "winerror": None, "error": text.split(" ", 1)[0], "path": path, "payload_read": False}
    finally:
        if handle:
            common.safe_close(handle)


def plan_row(path: str) -> dict:
    conn = sqlite3.connect(f"file:{PLAN.resolve().as_posix()}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT is_dir, is_reparse, logical_size, volume_serial, file_id FROM paths WHERE path=?",
            (path,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"present": False}
    return {
        "present": True,
        "is_dir": int(row[0]),
        "is_reparse": int(row[1]),
        "logical_size": row[2],
        "volume_serial": row[3],
        "file_id": row[4],
    }


def compare(meta: dict, expected_volume: int, inventory: str) -> dict:
    row = plan_row(inventory)
    out = {"inventory_path": inventory, "plan": row, "metadata_matches_plan": None}
    if not meta.get("ok") or not row.get("present"):
        out["metadata_matches_plan"] = False
        return out
    out["metadata_matches_plan"] = (
        str(meta.get("volume_serial_dword")) == str(row.get("volume_serial"))
        and str(meta.get("file_id")) == str(row.get("file_id"))
        and int(meta.get("size")) == int(row.get("logical_size"))
        and int(meta.get("volume_serial_dword")) == expected_volume
    )
    return out


def main() -> None:
    identity = run(["whoami"])
    elevated = bool(ctypes.windll.shell32.IsUserAnAdmin())
    net = run(["net", "use"])
    net_lines = [line.strip() for line in net["stdout"].splitlines() if "192.168.100.2" in line]
    smb = run(["powershell", "-NoProfile", "-Command", "Get-SmbConnection | Where-Object { $_.ServerName -eq '192.168.100.2' } | Select-Object ServerName, ShareName | Format-List"])
    smb_class = "ACCESS_DENIED" if "Access is denied" in smb["stderr"] or "拒绝访问" in smb["stderr"] else ("OK" if smb["exit"] == 0 else "OTHER")
    port = {"reachable": False, "not_source_read": True}
    try:
        with socket.create_connection(("192.168.100.2", 445), 3):
            port["reachable"] = True
    except OSError as exc:
        port["error"] = type(exc).__name__
    cmdkey = run(["cmdkey", "/list"])
    cmdkey_relevant = []
    current_target = ""
    for line in cmdkey["stdout"].splitlines():
        if "Target:" in line:
            current_target = line.split("Target:", 1)[1].strip()
        elif "User:" in line and relevant(current_target):
            cmdkey_relevant.append({"target": current_target, "user": line.split("User:", 1)[1].strip()})
            current_target = ""
    creds = list_credentials()
    started = now_pair()
    probes = {
        "e_root": open_meta(E_ROOT),
        "d_root": open_meta(D_ROOT),
        "e_file": open_meta(E_FILE),
        "d_file": open_meta(D_FILE),
    }
    attempts = []
    logon_failed = any(item.get("winerror") == 1326 for item in probes.values())
    records = list(creds.get("relevant") or [])
    if not records:
        records = [{"target": item["target"], "type": 2, "has_secret": True, "user": item["user"]} for item in cmdkey_relevant]
    if logon_failed and records:
        for item in records:
            if not item["has_secret"]:
                attempts.append({"target": item["target"], "attempted": False, "reason": "SAVED_RECORD_HAS_NO_SECRET"})
                continue
            result = connect_saved(item["target"], item["type"], r"\\192.168.100.2\E_DRIVE")
            if result.get("reason") == "CRED_READ_FAILED" and item["type"] == 2:
                result = connect_saved(item["target"], 1, r"\\192.168.100.2\E_DRIVE")
            attempts.append({key: result[key] for key in ("attempted", "winerror", "reason", "target", "remote", "flags", "user") if key in result})
            if result.get("winerror") == 1909:
                break
            if result.get("winerror") == 0:
                probes = {
                    "e_root": open_meta(E_ROOT),
                    "d_root": open_meta(D_ROOT),
                    "e_file": open_meta(E_FILE),
                    "d_file": open_meta(D_FILE),
                }
                break
            if result.get("winerror") == 1219:
                break
    finished = now_pair()
    checks = {
        "e_root": {"expected_volume": EXPECTED["e"], "is_dir": True, **probes["e_root"]},
        "d_root": {"expected_volume": EXPECTED["d"], "is_dir": True, **probes["d_root"]},
        "e_file": {"expected_volume": EXPECTED["e"], **probes["e_file"], **compare(probes["e_file"], EXPECTED["e"], E_INV)},
        "d_file": {"expected_volume": EXPECTED["d"], **probes["d_file"], **compare(probes["d_file"], EXPECTED["d"], D_INV)},
    }
    for key in ("e_root", "d_root"):
        item = checks[key]
        item["volume_ok"] = item.get("ok") and int(item.get("volume_serial_dword") or -1) == item["expected_volume"] and int(item.get("attrs") or 0) & 16 == 16
    valid = all(item.get("ok") for item in checks.values()) and checks["e_root"]["volume_ok"] and checks["d_root"]["volume_ok"]
    status = {
        "task_id": "R9_DESKTOP_RESTORE_SOURCE_AUTH_20261015_1005",
        "host": "ZHANGWEI",
        "identity": identity["stdout"].strip(),
        "elevated": elevated,
        "started": started,
        "finished": finished,
        "port_445_reachable": port["reachable"],
        "port_445_is_not_source_read": True,
        "net_use_exit": net["exit"],
        "net_use_192_168_100_2": net_lines,
        "smb_connection_class": smb_class,
        "cmdkey_exit": cmdkey["exit"],
        "cmdkey_relevant": cmdkey_relevant,
        "credential_enum_ok": creds.get("ok"),
        "credential_enum_winerror": creds.get("winerror"),
        "relevant_credentials": [{key: item[key] for key in ("target", "user", "type", "has_secret")} for item in creds.get("relevant") or []],
        "auth_attempts": attempts,
        "checks": checks,
        "SOURCE_ACCESS_VALID": valid,
        "COPY_AUTHORIZED": False,
        "business_payload_read": False,
        "password_recorded": False,
        "candidate_modified": False,
        "code_modified": False,
    }
    (ROOT / "SOURCE_AUTH_STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    request = {
        "task_id": "R9_DESKTOP_RESTORE_SOURCE_AUTH_20261015_1005",
        "from": "ZHANGWEI",
        "to": "SAM",
        "probe_window_start": started,
        "probe_window_end": finished,
        "mode": "SAVED_CREDENTIAL" if attempts else "CURRENT_CONTEXT",
        "source_access_valid": valid,
        "ask": "Read existing authentication events for ZHANGWEI or 192.168.100.1 inside this short window only.",
    }
    (ROOT / "SOURCE_AUTH_PROBE_REQUEST.json").write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"SOURCE_ACCESS_VALID": valid, "attempts": len(attempts), "e_root": checks["e_root"].get("winerror"), "d_root": checks["d_root"].get("winerror"), "e_file": checks["e_file"].get("winerror"), "d_file": checks["d_file"].get("winerror"), "cred_targets": len(creds.get("relevant") or [])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
