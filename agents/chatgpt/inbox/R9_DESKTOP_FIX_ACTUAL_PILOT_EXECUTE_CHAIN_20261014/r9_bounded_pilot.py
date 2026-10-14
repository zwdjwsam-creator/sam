# -*- coding: utf-8 -*-
"""Bounded pilot entry. Full-plan copy stays refused. This round does not write E:."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

DEST_ROOT = "E:\\R9_POSTFORMAT_PILOT_20261014"
DISK_ID = "eui.E8238FA6BF530001001B448B42E694AE"
VOLUME_HEX = "D86AEE82"
PLAN_SHA = "94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba"
MAX_ENTITIES = 2
MAX_FILE_PATHS = 40
MAX_DIRS = 3
MAX_UNIQUE_BYTES = 9312
E_PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite")
E_FILE = r"E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R9_ASOF_20260805_20260806_004303\standard\fund\ETF_NAV\ETF_NAV__fund_etf_nav__150306.XSHE_150310.XSHE__2018__v1__20260712_103337.parquet"
D_FILE = r"D:\backtest_lab\02_blackbox_jq_compat_engine\rule_library\jq_official_canonical_R1\CN_A_SHARE_FEE_SCHEDULE_R1.json"
SOURCE_MTIME = {
    "e": "134298545883539099",
    "d": "134315573127171246",
}


def sample_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unc(inventory: str) -> str:
    if inventory.upper().startswith("E:\\BLACKBOX\\"):
        return "\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\" + inventory[len("E:\\BLACKBOX\\"):]
    if inventory.upper().startswith("D:\\"):
        return "\\\\192.168.100.2\\D_DRIVE\\" + inventory[3:]
    raise ValueError("UNMAPPED_SAMPLE_PATH")


def build_sample(plan: Path = E_PLAN) -> dict:
    conn = sqlite3.connect(f"file:{plan.resolve().as_posix()}?mode=ro", uri=True)
    try:
        entities = []
        for kind, inventory, folder in (("e", E_FILE, "e"), ("d", D_FILE, "d")):
            row = conn.execute(
                "SELECT volume_serial, file_id, logical_size FROM paths WHERE path=?",
                (inventory,),
            ).fetchone()
            if not row:
                raise RuntimeError("SAMPLE_PATH_MISSING")
            paths = [
                item[0]
                for item in conn.execute(
                    "SELECT path FROM paths WHERE is_dir=0 AND is_reparse=0 AND volume_serial=? AND file_id=? ORDER BY path",
                    (row[0], row[1]),
                )
            ]
            mapped = []
            for index, path in enumerate(paths):
                mapped.append({
                    "inventory_path": path,
                    "source_unc": _unc(path),
                    "dest_path": f"{DEST_ROOT}\\{folder}\\p{index:02d}",
                })
            entities.append({
                "kind": kind,
                "entity_key": f"{row[0]}|{row[1]}",
                "volume_serial": str(row[0]),
                "file_id": str(row[1]),
                "logical_size": int(row[2]),
                "mtime": SOURCE_MTIME[kind],
                "mtime_status": "FROM_SOURCE_HANDLE",
                "paths": mapped,
            })
    finally:
        conn.close()
    return {
        "plan_sha256": PLAN_SHA,
        "dest_root": DEST_ROOT,
        "directories": [DEST_ROOT, DEST_ROOT + "\\e", DEST_ROOT + "\\d"],
        "entities": entities,
        "junctions_included": 0,
    }


def validate_sample(sample: dict) -> None:
    entities = sample.get("entities") or []
    if len(entities) != MAX_ENTITIES:
        raise RuntimeError("PILOT_ENTITY_LIMIT")
    paths = [item for entity in entities for item in entity["paths"]]
    if len(paths) != MAX_FILE_PATHS:
        raise RuntimeError("PILOT_PATH_LIMIT")
    if len(sample.get("directories") or []) != MAX_DIRS:
        raise RuntimeError("PILOT_DIR_LIMIT")
    if sum(int(entity["logical_size"]) for entity in entities) != MAX_UNIQUE_BYTES:
        raise RuntimeError("PILOT_BYTE_LIMIT")
    if sample.get("junctions_included") not in (0, None):
        raise RuntimeError("PILOT_JUNCTION_EXCLUDED")
    dests = [item["dest_path"] for item in paths]
    if len(dests) != len(set(dests)):
        raise RuntimeError("PILOT_DEST_COLLISION")
    root = DEST_ROOT.upper() + "\\"
    if any(not item["dest_path"].upper().startswith(root) for item in paths):
        raise RuntimeError("PILOT_DEST_ROOT")
    if sample.get("plan_sha256") != PLAN_SHA:
        raise RuntimeError("PILOT_PLAN_SHA")


def entities_for_run(sample: dict) -> list[dict]:
    built = []
    for entity in sample["entities"]:
        paths = entity["paths"]
        if not entity.get("mtime"):
            raise RuntimeError("MTIME_DEFICIT")
        built.append({
            "entity_key": entity["entity_key"],
            "volume_serial": entity["volume_serial"],
            "file_id": entity["file_id"],
            "logical_size": entity["logical_size"],
            "mtime": entity["mtime"],
            "mtime_status": "FROM_SOURCE_HANDLE",
            "source_path": paths[0]["source_unc"],
            "dest_path": paths[0]["dest_path"],
            "extra_dest_paths": [item["dest_path"] for item in paths[1:]],
        })
    return built


def pilot_authorized(contract: dict, sample_path: Path) -> bool:
    if contract.get("pilot_write_authorized") is not True:
        return False
    if contract.get("copy_authorized") is not False or contract.get("full_migration") is not False:
        return False
    if contract.get("disk_unique_id") != DISK_ID or contract.get("volume_serial_hex") != VOLUME_HEX:
        return False
    if contract.get("dest_root") != DEST_ROOT:
        return False
    if contract.get("sample_sha256") != sample_sha256(sample_path):
        return False
    if contract.get("plan_sha256") != PLAN_SHA:
        return False
    import r9_source_contract as source_contract
    if contract.get("code_digest") != source_contract.code_digest():
        return False
    return True


def dry_run(sample_path: Path, contract_path: Path) -> int:
    sample = json.loads(sample_path.read_bytes().decode("utf-8"))
    contract = json.loads(contract_path.read_bytes().decode("utf-8"))
    validate_sample(sample)
    from r9_winio import Win32Syscalls
    before = Win32Syscalls.write_calls
    print(json.dumps({
        "mode": "dry-run",
        "refused_before_write": True,
        "pilot_write_authorized": pilot_authorized(contract, sample_path),
        "entities": len(sample["entities"]),
        "file_paths": sum(len(item["paths"]) for item in sample["entities"]),
        "win32_write_calls": Win32Syscalls.write_calls - before,
    }, ensure_ascii=False))
    return 0


def live_target_probe() -> dict:
    """Read-only disk and volume check. Does not create the pilot directory."""
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    get_vol = kernel.GetVolumeInformationW
    get_vol.argtypes = [
        wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR, wintypes.DWORD,
    ]
    get_vol.restype = wintypes.BOOL
    serial = wintypes.DWORD()
    name = ctypes.create_unicode_buffer(64)
    fs = ctypes.create_unicode_buffer(32)
    maxcomp = wintypes.DWORD()
    flags = wintypes.DWORD()
    if not get_vol("E:\\", name, 64, ctypes.byref(serial), ctypes.byref(maxcomp), ctypes.byref(flags), fs, 32):
        return {"ok": False, "reason": "TARGET_QUERY_FAILED", "winerror": ctypes.get_last_error()}
    if f"{int(serial.value):08X}" != VOLUME_HEX or fs.value.upper() != "NTFS":
        return {"ok": False, "reason": "TARGET_VOLUME_MISMATCH", "serial_hex": f"{int(serial.value):08X}"}
    return {"ok": True, "serial_hex": VOLUME_HEX, "filesystem": "NTFS"}


def accept_pilot(sample: dict, backend, expected_volume: str) -> dict:
    reasons = []
    seen = {}
    for entity in sample["entities"]:
        ids = set()
        volumes = set()
        for index, item in enumerate(entity["paths"]):
            observed = backend.observe_destination(item["dest_path"])
            if observed.get("status") != "PRESENT" or observed.get("object_type") != "file":
                reasons.append("MISSING_OBJECT")
                continue
            if not observed.get("file_id") or not observed.get("volume_serial") or observed.get("sha256") in (None, ""):
                reasons.append("MISSING_FIELD")
            if observed.get("allocation_size") is None:
                reasons.append("MISSING_FIELD")
            ids.add(observed.get("file_id"))
            volumes.add(str(observed.get("volume_serial")))
            if index == 0:
                seen[entity["entity_key"]] = observed
        if len(ids) != 1 or len(volumes) != 1:
            reasons.append("ALIAS_SPLIT")
        if volumes and expected_volume not in volumes:
            reasons.append("DEST_VOLUME")
    if len(seen) != 2:
        reasons.append("ENTITY_COUNT")
    unique = []
    for reason in reasons:
        if reason not in unique:
            unique.append(reason)
    return {"full_acceptance": not unique, "reasons": unique, "checked_entities": len(seen)}


def execute(sample_path: Path, contract_path: Path, backend=None, live_probe=None, state_path: Path | None = None) -> int:
    sample = json.loads(sample_path.read_bytes().decode("utf-8"))
    contract = json.loads(contract_path.read_bytes().decode("utf-8"))
    validate_sample(sample)
    from r9_winio import Win32Syscalls
    before = Win32Syscalls.write_calls
    if not pilot_authorized(contract, sample_path):
        print("PILOT_WRITE_REFUSED")
        print(f"win32_write_calls={Win32Syscalls.write_calls - before}")
        return 3
    probe = live_probe() if live_probe else live_target_probe()
    if not probe.get("ok"):
        print(probe.get("reason") or "TARGET_BINDING_MISMATCH")
        print(f"win32_write_calls={Win32Syscalls.write_calls - before}")
        return 3
    if backend is None:
        from r9_winio import WindowsBackend
        backend = WindowsBackend()
    import r9_runner as runner
    entities = entities_for_run(sample)
    run_contract = {
        "phase": "PILOT_REAL_IO",
        "pilot_write_authorized": True,
        "scope": "BOUNDED_PILOT_ONLY",
        "dest_root": DEST_ROOT,
        "volume_serial_hex": VOLUME_HEX,
        "dest_binding": {"volume_serial": VOLUME_HEX},
        "directories": sample["directories"],
        "links": [],
        "run": contract.get("run"),
    }
    if state_path is None:
        state_path = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\state\pilot.sqlite")
    result = runner.production_run(iter(entities), backend, run_contract, state_path)
    if result.get("refused_before_write"):
        print("PILOT_REAL_IO_NOT_RUN")
        print(f"win32_write_calls={Win32Syscalls.write_calls - before}")
        return 3
    acceptance = accept_pilot(sample, backend, backend.sc.dest_volume)
    print(json.dumps({"copied_count": result["copied_count"], "linked_count": result["linked_count"], "acceptance": acceptance["full_acceptance"]}, ensure_ascii=False))
    return 0 if acceptance["full_acceptance"] else 4


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="r9_bounded_pilot")
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("dry-run", "execute"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--sample", required=True)
        cmd.add_argument("--contract", required=True)
    args = parser.parse_args(argv)
    if args.mode == "dry-run":
        return dry_run(Path(args.sample), Path(args.contract))
    return execute(Path(args.sample), Path(args.contract))


if __name__ == "__main__":
    sys.exit(main())
