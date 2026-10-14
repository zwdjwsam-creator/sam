# -*- coding: utf-8 -*-
"""Capability pilot planner. This round does not create directories on E:."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path, PureWindowsPath

PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite")
PLAN_SHA = "94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba"
DISK_ID = "eui.E8238FA6BF530001001B448B42E694AE"
VOLUME_HEX = "D86AEE82"
VOLUME_DWORD = 3630886530
PARENT = "E:\\R9_CAPABILITY_PILOT_20261014"
SCENARIOS = ("NORMAL", "A", "B", "C")
TAG = 2684354563
MAX_DIRS = 24
MAX_ENTITIES = 4
MAX_BYTES = 1024 * 1024
E_LINK = r"E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_R23_TRADEABILITY_ASOF_20260812_20260813_004505\_manifest"
E_TARGET = r"E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_ASOF_20260812_20260813_000640\_manifest"
E_FILE = E_TARGET + r"\PRODUCT_MANIFESTS.json"
D_LINK = r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_20260903_SUCCESSOR_BUILD_AND_ATOMIC_PUBLISH_R1\pit_products\INDEX_WEIGHT_PIT_R1_ASOF_20260903_EFF_20260831_20260904_042231\year=2014"
D_TARGET = r"E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260903_20260903_180234\INDEX_WEIGHT_PIT_R1\year=2014"
D_FILE = D_TARGET + r"\part_000.parquet"
LONG_FILE = (
    r"E:\BLACKBOX\数据\原始只读\JQData_reference_dictionary\31_jq_pre_download_experiment_cleanup_dryrun"
    r"\manifest_backup\数据\原始只读\JQData_reference_dictionary\31_jq_pre_download_experiment_cleanup_dryrun"
    r"\manifest_backup\数据\原始只读\JQData_reference_dictionary\30_jq_pre_download_experiment_cleanup_contract"
    r"\jq_pre_download_experiment_cleanup_r0_manifest.json"
)


def root_for(scenario: str) -> str:
    if scenario not in SCENARIOS:
        raise RuntimeError("SCENARIO")
    return PARENT + "\\" + scenario


def remap(path: str, root: str) -> str:
    if path.upper().startswith("E:\\BLACKBOX\\"):
        return root + "\\e\\" + path[len("E:\\BLACKBOX\\"):]
    if path.upper().startswith("D:\\"):
        return root + "\\d\\" + path[3:]
    raise RuntimeError("UNMAPPED_CAPABILITY_PATH")


def _ancestors(path: str) -> list[str]:
    current = PureWindowsPath(path)
    found = []
    parent = current.parent
    while str(parent) != str(current):
        found.append(str(parent))
        if len(str(parent)) <= 3:
            break
        current = parent
        parent = current.parent
    return found


def _unc(path: str) -> str:
    if path.upper().startswith("E:\\BLACKBOX\\"):
        return "\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\" + path[len("E:\\BLACKBOX\\"):]
    raise RuntimeError("UNMAPPED_CAPABILITY_PATH")


def _plan_file(conn, path: str) -> dict:
    row = conn.execute(
        "SELECT volume_serial, file_id, logical_size, is_dir, is_reparse FROM paths WHERE path=?",
        (path,),
    ).fetchone()
    if not row or row[3] or row[4]:
        raise RuntimeError("CAPABILITY_FILE_MISSING")
    return {"path": path, "volume_serial": str(row[0]), "file_id": str(row[1]), "logical_size": int(row[2])}


def _plan_link(conn, path: str, target: str, map_id) -> dict:
    row = conn.execute(
        "SELECT target, reparse_tag, map_id FROM links WHERE path=?",
        (path,),
    ).fetchone()
    if not row or int(row[1]) != TAG or row[0] != target:
        raise RuntimeError("CAPABILITY_LINK_MISSING")
    if map_id is not None and row[2] != map_id:
        raise RuntimeError("CAPABILITY_LINK_MAP")
    return {"path": path, "target": target, "reparse_tag": TAG, "map_id": row[2]}


def build_sample(plan: Path = PLAN) -> dict:
    conn = sqlite3.connect(f"file:{plan.resolve().as_posix()}?mode=ro", uri=True)
    try:
        e_file = _plan_file(conn, E_FILE)
        d_file = _plan_file(conn, D_FILE)
        long_file = _plan_file(conn, LONG_FILE)
        long_count = conn.execute(
            "SELECT COUNT(*) FROM paths WHERE is_dir=0 AND is_reparse=0 AND volume_serial=? AND file_id=?",
            (long_file["volume_serial"], long_file["file_id"]),
        ).fetchone()[0]
        e_link = _plan_link(conn, E_LINK, E_TARGET, None)
        d_link = _plan_link(conn, D_LINK, D_TARGET, 29)
    finally:
        conn.close()
    if len(LONG_FILE) <= 260 or long_file["logical_size"] > MAX_BYTES:
        raise RuntimeError("CAPABILITY_LONG_PATH")
    files = [
        {**e_file, "role": "e_junction_child"},
        {**d_file, "role": "d_junction_child"},
        {**long_file, "role": "long_path", "plan_path_count": int(long_count)},
    ]
    if sum(item["logical_size"] for item in files) > MAX_BYTES or len(files) > MAX_ENTITIES:
        raise RuntimeError("CAPABILITY_BUDGET")
    sample = {
        "plan_sha256": PLAN_SHA,
        "parent_root": PARENT,
        "scenarios": list(SCENARIOS),
        "selection": {
            "e_junction": e_link,
            "d_junction": d_link,
            "long_path_chars": len(LONG_FILE),
            "long_plan_paths": int(long_count),
            "long_alias_note": "reachable plan paths over 260 chars in the searched raw tree have one path; dest adds two long hardlink aliases for the B/C exercise",
        },
        "files": files,
        "junctions_included": 2,
    }
    dirs = _directories(sample, "NORMAL")
    if len(dirs) > MAX_DIRS:
        raise RuntimeError(f"CAPABILITY_DIR_LIMIT:{len(dirs)}")
    return sample


def _directories(sample: dict, scenario: str) -> list[str]:
    root = root_for(scenario)
    paths = []
    for item in sample["files"]:
        paths.append(remap(item["path"], root))
        if item["role"] == "long_path":
            dest = remap(item["path"], root)
            parent = str(PureWindowsPath(dest).parent)
            name = PureWindowsPath(dest).name
            paths.append(parent + "\\alias1_" + name)
            paths.append(parent + "\\alias2_" + name)
    paths.append(root + "\\e_manifest")
    paths.append(root + "\\d_year2014")
    paths.append(remap(E_TARGET, root))
    paths.append(remap(D_TARGET, root))
    found = []
    for path in paths:
        for ancestor in _ancestors(path):
            if ancestor not in found and len(ancestor) > 3:
                found.append(ancestor)
    return found


def scenario_plan(sample: dict, scenario: str) -> dict:
    root = root_for(scenario)
    entities = []
    for item in sample["files"]:
        dest = remap(item["path"], root)
        extra = []
        if item["role"] == "long_path":
            parent = str(PureWindowsPath(dest).parent)
            name = PureWindowsPath(dest).name
            extra = [parent + "\\alias1_" + name, parent + "\\alias2_" + name]
        entities.append({
            "entity_key": item["volume_serial"] + "|" + item["file_id"],
            "volume_serial": item["volume_serial"],
            "file_id": item["file_id"],
            "logical_size": item["logical_size"],
            "mtime": item.get("mtime"),
            "mtime_prior": item.get("mtime"),
            "mtime_status": "PRIOR_OBSERVATION",
            "source_path": _unc(item["path"]),
            "dest_path": dest,
            "extra_dest_paths": extra,
            "role": item["role"],
        })
    links = [
        {
            "link_path": root + "\\e_manifest",
            "target": remap(E_TARGET, root),
            "kind": "junction",
            "blocked": False,
            "reparse_tag": TAG,
            "source_path": E_LINK,
        },
        {
            "link_path": root + "\\d_year2014",
            "target": remap(D_TARGET, root),
            "kind": "junction",
            "blocked": False,
            "reparse_tag": TAG,
            "source_path": D_LINK,
            "map_id": 29,
        },
    ]
    directories = _directories(sample, scenario)
    return {"dest_root": root, "directories": directories, "entities": entities, "links": links}


def validate_sample(sample: dict) -> None:
    if sample.get("plan_sha256") != PLAN_SHA or sample.get("junctions_included") != 2:
        raise RuntimeError("CAPABILITY_SAMPLE")
    if len(sample.get("files") or []) > MAX_ENTITIES:
        raise RuntimeError("CAPABILITY_ENTITY_LIMIT")
    if sum(int(item["logical_size"]) for item in sample["files"]) > MAX_BYTES:
        raise RuntimeError("CAPABILITY_BYTE_LIMIT")
    if len(LONG_FILE) <= 260:
        raise RuntimeError("CAPABILITY_LONG_PATH")
    for scenario in SCENARIOS:
        plan = scenario_plan(sample, scenario)
        if len(plan["directories"]) > MAX_DIRS:
            raise RuntimeError("CAPABILITY_DIR_LIMIT")
        for link in plan["links"]:
            target = link["target"].upper()
            if target.startswith("\\\\") or "R9_POSTFORMAT_PILOT" in target or not target.startswith(root_for(scenario).upper()):
                raise RuntimeError("CAPABILITY_LINK_TARGET")
        long_dest = [item["dest_path"] for item in plan["entities"] if item["role"] == "long_path"][0]
        if len(long_dest) <= 260 or any(len(path) <= 260 for path in plan["entities"][-1]["extra_dest_paths"]):
            raise RuntimeError("CAPABILITY_DEST_LONG_PATH")


def sample_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capability_write_gate(contract: dict, backend) -> bool:
    if contract.get("phase") != "CAPABILITY_PILOT":
        return False
    if contract.get("pilot_write_authorized") is not True:
        return False
    if contract.get("copy_authorized") is not False or contract.get("full_migration") is not False:
        return False
    if contract.get("scope") != "CAPABILITY_PILOT_ONLY":
        return False
    scenario = contract.get("scenario")
    if scenario not in SCENARIOS or contract.get("dest_root") != root_for(scenario):
        return False
    if contract.get("disk_unique_id") != DISK_ID or contract.get("volume_serial_hex") != VOLUME_HEX:
        return False
    import r9_source_contract as source_contract
    if contract.get("code_digest") != source_contract.code_digest():
        return False
    run = contract.get("run")
    if not isinstance(run, dict) or run.get("run_id") != contract.get("run_id"):
        return False
    if run.get("dest_root") != root_for(scenario) or run.get("code_digest") != contract.get("code_digest"):
        return False
    verified = contract.get("target_verified")
    if not isinstance(verified, dict) or verified.get("ok") is not True or verified.get("reparse_clear") is not True:
        return False
    if verified.get("serial_dword") != VOLUME_DWORD or verified.get("disk_unique_id") != DISK_ID:
        return False
    if not str(contract.get("state_path") or "").upper().startswith("C:\\"):
        return False
    from r9_winio import VirtualSyscalls, Win32Syscalls
    return isinstance(getattr(backend, "sc", None), (VirtualSyscalls, Win32Syscalls))


def _probe(os_api, scenario: str, sample: dict) -> dict:
    if os_api is None:
        from r9_bounded_pilot import live_target_probe
        base = live_target_probe()
    else:
        base = {
            "ok": True,
            "serial_dword": getattr(os_api, "serial", VOLUME_DWORD),
            "disk_unique_id": getattr(os_api, "disk", DISK_ID),
            "filesystem": getattr(os_api, "filesystem", "NTFS"),
            "reparse_clear": True,
        }
        if base["serial_dword"] != VOLUME_DWORD:
            return {"ok": False, "reason": "TARGET_VOLUME_MISMATCH"}
        if not base["disk_unique_id"]:
            return {"ok": False, "reason": "DISK_QUERY_UNKNOWN"}
        if base["disk_unique_id"] != DISK_ID:
            return {"ok": False, "reason": "DISK_MISMATCH"}
    if not base.get("ok"):
        return base
    plan = scenario_plan(sample, scenario)
    observe = getattr(os_api, "observe_nofollow", None)
    if observe is None:
        return base
    for directory in plan["directories"]:
        seen = observe(directory)
        status = seen.get("status") if isinstance(seen, dict) else None
        if status in (None, "ERROR"):
            return {"ok": False, "reason": "REPARSE_QUERY_UNKNOWN"}
        if status == "PRESENT" and (seen.get("object_type") in ("junction", "symlink") or seen.get("reparse_target")):
            return {"ok": False, "reason": "REPARSE_ANCESTOR"}
    return base


def _authorized(contract: dict, sample_path: Path, scenario: str) -> bool:
    if contract.get("pilot_write_authorized") is not True:
        return False
    if contract.get("copy_authorized") is not False or contract.get("full_migration") is not False:
        return False
    if contract.get("sample_sha256") != sample_sha256(sample_path):
        return False
    import r9_source_contract as source_contract
    if contract.get("code_digest") != source_contract.code_digest():
        return False
    return contract.get("scenarios", {}).get(scenario, {}).get("dest_root") == root_for(scenario)


def execute(sample_path: Path, contract_path: Path, scenario: str, backend=None, os_api=None, state_path: Path | None = None, fault: str | None = None) -> int:
    sample = json.loads(sample_path.read_bytes().decode("utf-8"))
    contract = json.loads(contract_path.read_bytes().decode("utf-8"))
    validate_sample(sample)
    from r9_winio import Win32Syscalls
    before = Win32Syscalls.write_calls

    def refused(text: str) -> int:
        print(text)
        print(f"win32_write_calls={Win32Syscalls.write_calls - before}")
        return 3

    if scenario not in SCENARIOS or not _authorized(contract, sample_path, scenario):
        return refused("CAPABILITY_WRITE_REFUSED")
    probe = _probe(os_api, scenario, sample)
    if not probe.get("ok"):
        return refused(probe.get("reason") or "TARGET_BINDING_MISMATCH")
    plan = scenario_plan(sample, scenario)
    if state_path is None:
        state_path = Path(contract["scenarios"][scenario]["state_path"])
    import r9_source_contract as source_contract
    run = {
        "run_id": contract["scenarios"][scenario]["run_id"],
        "plan_digest": PLAN_SHA,
        "inputs_digest": sample_sha256(sample_path),
        "code_digest": source_contract.code_digest(),
        "dest_volume": str(VOLUME_DWORD),
        "dest_root": plan["dest_root"],
    }
    if backend is None:
        from r9_winio import WindowsBackend
        backend = WindowsBackend()
    try:
        from r9_bounded_pilot import observe_sources
        observe_sources(backend, plan["entities"])
        import r9_runner as runner
        result = runner.production_run(iter(plan["entities"]), backend, {
            "phase": "CAPABILITY_PILOT",
            "pilot_write_authorized": True,
            "copy_authorized": False,
            "full_migration": False,
            "scope": "CAPABILITY_PILOT_ONLY",
            "scenario": scenario,
            "dest_root": plan["dest_root"],
            "disk_unique_id": DISK_ID,
            "volume_serial_hex": VOLUME_HEX,
            "code_digest": run["code_digest"],
            "directories": plan["directories"],
            "links": plan["links"],
            "run": run,
            "run_id": run["run_id"],
            "state_path": str(state_path),
            "fault": fault,
            "target_verified": {
                "ok": True,
                "serial_dword": probe.get("serial_dword", VOLUME_DWORD),
                "disk_unique_id": probe.get("disk_unique_id", DISK_ID),
                "filesystem": probe.get("filesystem", "NTFS"),
                "reparse_clear": True,
            },
        }, state_path)
    except RuntimeError as exc:
        print(str(exc))
        print(f"win32_write_calls={Win32Syscalls.write_calls - before}")
        return 3
    if result.get("refused_before_write"):
        return refused("CAPABILITY_NOT_RUN")
    print(json.dumps({
        "scenario": scenario,
        "copied_count": result["copied_count"],
        "linked_count": result["linked_count"],
        "reparse_count": result["reparse_count"],
        "resumed_entities": result["resumed_entities"],
        "resumed_links": result["resumed_links"],
    }, ensure_ascii=False))
    return 0


def dry_run(sample_path: Path, contract_path: Path, scenario: str) -> int:
    sample = json.loads(sample_path.read_bytes().decode("utf-8"))
    contract = json.loads(contract_path.read_bytes().decode("utf-8"))
    validate_sample(sample)
    from r9_winio import Win32Syscalls
    before = Win32Syscalls.write_calls
    plan = scenario_plan(sample, scenario)
    print(json.dumps({
        "mode": "dry-run",
        "scenario": scenario,
        "authorized": _authorized(contract, sample_path, scenario),
        "entities": len(plan["entities"]),
        "directories": len(plan["directories"]),
        "junctions": len(plan["links"]),
        "long_dest_chars": len([item for item in plan["entities"] if item["role"] == "long_path"][0]["dest_path"]),
        "win32_write_calls": Win32Syscalls.write_calls - before,
        "e_root_created": Path(root_for(scenario)).exists(),
    }, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="r9_capability_pilot")
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("dry-run", "execute", "build-sample"):
        cmd = sub.add_parser(name)
        if name != "build-sample":
            cmd.add_argument("--scenario", required=True)
            cmd.add_argument("--sample", required=True)
            cmd.add_argument("--contract", required=True)
        else:
            cmd.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.mode == "build-sample":
        payload = build_sample()
        Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(sample_sha256(Path(args.out)))
        return 0
    if args.mode == "dry-run":
        return dry_run(Path(args.sample), Path(args.contract), args.scenario)
    return execute(Path(args.sample), Path(args.contract), args.scenario)


if __name__ == "__main__":
    sys.exit(main())
