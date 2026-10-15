# -*- coding: utf-8 -*-
"""One non-interactive source logon from the saved Windows credential. Never prints the secret."""
from __future__ import annotations

import ctypes
import json
import sqlite3
import subprocess
import sys
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
import r9_pilot_common_r9fix as common

ROOT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_CONNECT_SOURCE_WITH_LOCAL_CREDENTIAL_20261015")
PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\FINAL_CANDIDATE.sqlite")
E_ROOT = r"\\192.168.100.2\E_DRIVE\BLACKBOX"
D_ROOT = r"\\192.168.100.2\D_DRIVE"
E_FILE = r"\\192.168.100.2\E_DRIVE\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R9_ASOF_20260805_20260806_004303\standard\fund\ETF_NAV\ETF_NAV__fund_etf_nav__150306.XSHE_150310.XSHE__2018__v1__20260712_103337.parquet"
D_FILE = r"\\192.168.100.2\D_DRIVE\backtest_lab\02_blackbox_jq_compat_engine\rule_library\jq_official_canonical_R1\CN_A_SHARE_FEE_SCHEDULE_R1.json"
E_INV = r"E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R9_ASOF_20260805_20260806_004303\standard\fund\ETF_NAV\ETF_NAV__fund_etf_nav__150306.XSHE_150310.XSHE__2018__v1__20260712_103337.parquet"
D_INV = r"D:\backtest_lab\02_blackbox_jq_compat_engine\rule_library\jq_official_canonical_R1\CN_A_SHARE_FEE_SCHEDULE_R1.json"
ACCOUNT = "SAM\\ThinkPad"
TARGET = "192.168.100.2"


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


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, timeout=30)


def net_lines() -> list[str]:
    proc = run(["net", "use"])
    return [line.strip() for line in proc.stdout.decode("utf-8", errors="replace").splitlines() if "192.168.100.2" in line]


def open_meta(path: str) -> dict:
    handle = None
    try:
        handle = common.open_source_stable(path)
        meta = common.handle_identity(handle)
        meta.update({"ok": True, "winerror": 0, "path": path, "payload_read": False, "opened_with": "open_source_stable"})
        return meta
    except OSError as exc:
        return {"ok": False, "winerror": exc.winerror if exc.winerror else exc.errno, "error": "OPEN_FAILED", "path": path, "payload_read": False}
    except RuntimeError as exc:
        return {"ok": False, "winerror": None, "error": str(exc).split(" ", 1)[0], "path": path, "payload_read": False}
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
    return {"present": True, "is_dir": int(row[0]), "is_reparse": int(row[1]), "logical_size": row[2], "volume_serial": row[3], "file_id": row[4]}


def matches(meta: dict, inventory: str, expected_volume: int) -> dict:
    row = plan_row(inventory)
    ok = bool(meta.get("ok") and row.get("present") and int(row["is_dir"]) == 0 and int(row["is_reparse"]) == 0)
    same = ok and str(meta.get("volume_serial_dword")) == str(row.get("volume_serial")) and str(meta.get("file_id")) == str(row.get("file_id")) and int(meta.get("size")) == int(row.get("logical_size")) and int(meta.get("volume_serial_dword")) == expected_volume
    return {"inventory_path": inventory, "plan": row, "metadata_matches_plan": same}


def connect_once() -> dict:
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    adv.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
    adv.CredReadW.restype = wintypes.BOOL
    adv.CredFree.argtypes = [ctypes.c_void_p]
    cred = ctypes.POINTER(CREDENTIAL)()
    if not adv.CredReadW(TARGET, 2, 0, ctypes.byref(cred)):
        return {"attempted": False, "winerror": ctypes.get_last_error(), "reason": "CRED_READ_FAILED", "account": ACCOUNT}
    info = cred.contents
    user = info.UserName or ""
    if user.casefold() != ACCOUNT.casefold():
        adv.CredFree(cred)
        return {"attempted": False, "winerror": None, "reason": "SAVED_ACCOUNT_MISMATCH", "account": user}
    if int(info.CredentialBlobSize) <= 0:
        adv.CredFree(cred)
        return {"attempted": False, "winerror": None, "reason": "SAVED_RECORD_HAS_NO_SECRET", "account": user}
    raw = ctypes.string_at(info.CredentialBlob, info.CredentialBlobSize)
    secret = raw.decode("utf-16-le", errors="ignore").split("\x00", 1)[0]
    adv.CredFree(cred)
    resource = NETRESOURCE()
    resource.dwType = 1
    resource.lpRemoteName = r"\\192.168.100.2\E_DRIVE"
    mpr = ctypes.WinDLL("mpr", use_last_error=True)
    mpr.WNetAddConnection2W.argtypes = [ctypes.POINTER(NETRESOURCE), wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
    mpr.WNetAddConnection2W.restype = wintypes.DWORD
    try:
        code = int(mpr.WNetAddConnection2W(ctypes.byref(resource), user, secret, 0))
    finally:
        secret = "\x00" * len(secret)
        del secret
        del raw
    return {"attempted": True, "winerror": code, "account": user, "remote": r"\\192.168.100.2\E_DRIVE", "flags": "NONINTERACTIVE"}


def route_fact() -> dict:
    proc = run(["powershell", "-NoProfile", "-Command", "Get-NetRoute -DestinationPrefix '192.168.100.2/32' -ErrorAction SilentlyContinue | Select-Object -First 1 InterfaceAlias, NextHop, RouteMetric | Format-List; Get-NetRoute -AddressFamily IPv4 | Where-Object { $_.DestinationPrefix -eq '192.168.100.0/24' } | Select-Object -First 1 InterfaceAlias, NextHop, RouteMetric | Format-List"])
    text = proc.stdout.decode("utf-8", errors="replace")
    alias = ""
    for line in text.splitlines():
        if "InterfaceAlias" in line and ":" in line:
            alias = line.split(":", 1)[1].strip()
            break
    speed = None
    if alias:
        speed_proc = run(["powershell", "-NoProfile", "-Command", f"(Get-NetAdapter -Name '{alias}' -ErrorAction SilentlyContinue).LinkSpeed"])
        speed = speed_proc.stdout.decode("utf-8", errors="replace").strip()
    return {"interface": alias, "link_speed": speed, "direct_2_5_gbps": speed.replace(" ", "").lower() == "2.5gbps" if speed else False, "route_text": "\n".join(line.strip() for line in text.splitlines() if line.strip())}


def volume_fact(letter: str) -> dict:
    proc = run(["powershell", "-NoProfile", "-Command", f"$v = Get-Volume -DriveLetter {letter} -ErrorAction SilentlyContinue; if ($v) {{ '{{\"serial\":\"' + $v.UniqueId + '\",\"label\":\"' + $v.FileSystemLabel + '\"}}' }}"])
    # UniqueId is not the DWORD serial. Use fsutil.
    fs = run(["cmd", "/c", f"fsutil fsinfo volumeinfo {letter}:"])
    text = fs.stdout.decode("utf-8", errors="replace")
    serial = None
    for line in text.splitlines():
        if "Serial Number" in line or "序列号" in line:
            raw = line.split(":", 1)[-1].strip().replace("-", "")
            try:
                serial = int(raw, 16)
            except ValueError:
                serial = raw
    return {"letter": letter, "volume_serial_dword": serial, "fsutil_exit": fs.returncode}


def main() -> None:
    identity = run(["whoami"]).stdout.decode("utf-8", errors="replace").strip()
    elevated = bool(ctypes.windll.shell32.IsUserAnAdmin())
    before = net_lines()
    existing = open_meta(E_ROOT)
    attempt = {"attempted": False, "reason": "EXISTING_SESSION", "account": ACCOUNT} if existing.get("ok") else connect_once()
    if attempt.get("winerror") == 1219:
        after_conflict = net_lines()
    else:
        after_conflict = []
    probes = {
        "e_root": open_meta(E_ROOT),
        "d_root": open_meta(D_ROOT),
        "e_file": open_meta(E_FILE),
        "d_file": open_meta(D_FILE),
    }
    e_root_ok = probes["e_root"].get("ok") and int(probes["e_root"].get("volume_serial_dword") or -1) == 2387166462 and int(probes["e_root"].get("attrs") or 0) & 16 == 16
    d_root_ok = probes["d_root"].get("ok") and int(probes["d_root"].get("volume_serial_dword") or -1) == 3187598165 and int(probes["d_root"].get("attrs") or 0) & 16 == 16
    e_file = {**probes["e_file"], **matches(probes["e_file"], E_INV, 2387166462)}
    d_file = {**probes["d_file"], **matches(probes["d_file"], D_INV, 3187598165)}
    valid = bool(e_root_ok and d_root_ok and e_file.get("metadata_matches_plan") and d_file.get("metadata_matches_plan"))
    result = {
        "task_id": "R9_DESKTOP_CONNECT_SOURCE_WITH_LOCAL_CREDENTIAL_20261015_1104",
        "observed_at": now(),
        "identity": identity,
        "elevated": elevated,
        "account": ACCOUNT,
        "source": TARGET,
        "net_use_before": before,
        "auth_status": "REUSED_SESSION" if attempt.get("reason") == "EXISTING_SESSION" else ("CONNECTED" if attempt.get("winerror") == 0 else "LOGON_FAILED"),
        "attempt_count": 0 if attempt.get("reason") == "EXISTING_SESSION" else (1 if attempt.get("attempted") else 0),
        "auth_attempt": {key: attempt.get(key) for key in ("attempted", "winerror", "reason", "account", "remote", "flags")},
        "conflict_net_use": after_conflict,
        "e_root": {**probes["e_root"], "expected_volume": 2387166462, "volume_ok": e_root_ok},
        "d_root": {**probes["d_root"], "expected_volume": 3187598165, "volume_ok": d_root_ok},
        "e_file": e_file,
        "d_file": d_file,
        "SOURCE_ACCESS_VALID": valid,
        "route": route_fact(),
        "dest_volume_E": volume_fact("E"),
        "candidate_sha256": "53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d",
        "candidate_bytes": PLAN.stat().st_size,
        "code_digest": "310778b936d44a5307f57f1c775925dd700c87749e8a8bba27bf097ee3517ff5",
        "COPY_AUTHORIZED": False,
        "copy_status": "NOT_RUN",
        "business_payload_read": False,
        "password_recorded_in_report": False,
        "blackbox_exists": Path(r"E:\BLACKBOX").exists(),
        "engines_exists": Path(r"E:\BLACKBOX_ENGINES").exists(),
    }
    (ROOT / "SOURCE_AUTH_AND_READ_RESULT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "auth_status": result["auth_status"],
        "attempt_count": result["attempt_count"],
        "winerror": attempt.get("winerror"),
        "SOURCE_ACCESS_VALID": valid,
        "e_root": probes["e_root"].get("winerror"),
        "d_root": probes["d_root"].get("winerror"),
        "e_file_match": e_file.get("metadata_matches_plan"),
        "d_file_match": d_file.get("metadata_matches_plan"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
