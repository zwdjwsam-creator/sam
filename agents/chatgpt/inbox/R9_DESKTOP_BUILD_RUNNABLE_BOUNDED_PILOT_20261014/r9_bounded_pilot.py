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


def entities_for_run(sample: dict, mtimes: dict) -> list[dict]:
    built = []
    for entity in sample["entities"]:
        paths = entity["paths"]
        mtime = mtimes[entity["entity_key"]]
        built.append({
            "entity_key": entity["entity_key"],
            "volume_serial": entity["volume_serial"],
            "file_id": entity["file_id"],
            "logical_size": entity["logical_size"],
            "mtime": mtime,
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


def execute(sample_path: Path, contract_path: Path) -> int:
    sample = json.loads(sample_path.read_bytes().decode("utf-8"))
    contract = json.loads(contract_path.read_bytes().decode("utf-8"))
    validate_sample(sample)
    from r9_winio import Win32Syscalls
    before = Win32Syscalls.write_calls
    if not pilot_authorized(contract, sample_path):
        print("PILOT_WRITE_REFUSED")
        print(f"win32_write_calls={Win32Syscalls.write_calls - before}")
        return 3
    print("PILOT_EXECUTE_NOT_RELEASED")
    return 3


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
