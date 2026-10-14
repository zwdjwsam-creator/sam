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
    for extra in (PARENT, root):
        if extra not in found:
            found.append(extra)
    found.sort(key=lambda item: (len(PureWindowsPath(item).parts), item.casefold()))
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
    directories = contract.get("allow_dirs") or []
    files = contract.get("allow_files") or []
    links = contract.get("links") or []
    if len(links) != 2 or not directories or not files:
        return False
    root = root_for(scenario).casefold()
    try:
        ordered = [canonical if False else str(item) for item in directories]
    except Exception:
        return False
    previous = -1
    for item in ordered:
        text = str(item)
        if not text.casefold().startswith(root) and text.casefold() != PARENT.casefold():
            return False
        depth = len(PureWindowsPath(text).parts)
        if depth < previous:
            return False
        previous = depth
    for item in files:
        if not str(item).casefold().startswith(root + "\\"):
            return False
    for link in links:
        target = str(link.get("target") or "")
        if target.upper().startswith("\\\\") or not target.casefold().startswith(root + "\\"):
            return False
        if int(link.get("reparse_tag") or 0) != TAG:
            return False
    from r9_winio import Win32Syscalls
    return isinstance(getattr(backend, "sc", None), Win32Syscalls)


def _probe(os_api, scenario: str, sample: dict) -> dict:
    """Same volume, disk and scenario-path walk for the real OS and an injected OS."""
    from r9_bounded_pilot import RealLiveOs
    api = os_api or RealLiveOs()
    volume = api.volume_information("E:\\")
    if not isinstance(volume, dict) or "serial" not in volume or "filesystem" not in volume:
        return {"ok": False, "reason": "TARGET_QUERY_FAILED"}
    try:
        serial = int(volume["serial"])
    except (TypeError, ValueError):
        return {"ok": False, "reason": "TARGET_QUERY_FAILED"}
    if serial != VOLUME_DWORD or str(volume["filesystem"]).upper() != "NTFS":
        return {"ok": False, "reason": "TARGET_VOLUME_MISMATCH"}
    disk = api.disk_unique_id("E")
    if disk is None or str(disk).strip() == "":
        return {"ok": False, "reason": "DISK_QUERY_UNKNOWN"}
    if str(disk) != DISK_ID:
        return {"ok": False, "reason": "DISK_MISMATCH"}
    plan = scenario_plan(sample, scenario)
    links = {link["link_path"].casefold(): link for link in plan["links"]}
    checked = []
    for path in [PARENT, plan["dest_root"], *plan["directories"]]:
        for item in [path, *_ancestors(path)]:
            if item not in checked and len(item) > 3:
                checked.append(item)
    for entity in plan["entities"]:
        for path in [entity["dest_path"], *entity["extra_dest_paths"]]:
            for item in _ancestors(path):
                if item not in checked and len(item) > 3:
                    checked.append(item)
    for link in plan["links"]:
        if link["link_path"] not in checked:
            checked.append(link["link_path"])
    for path in checked:
        seen = api.observe_nofollow(path)
        if not isinstance(seen, dict):
            return {"ok": False, "reason": "REPARSE_QUERY_UNKNOWN"}
        status = seen.get("status")
        link = links.get(path.casefold())
        if link is not None:
            if status == "MISSING":
                continue
            if status != "PRESENT":
                return {"ok": False, "reason": "REPARSE_QUERY_UNKNOWN"}
            if int(seen.get("reparse_tag") or 0) != TAG or seen.get("reparse_target") != link["target"]:
                return {"ok": False, "reason": "LINK_TARGET"}
            continue
        if status == "MISSING":
            continue
        if status != "PRESENT":
            return {"ok": False, "reason": "REPARSE_QUERY_UNKNOWN"}
        if seen.get("object_type") in ("junction", "symlink") or seen.get("reparse_target") or seen.get("reparse_tag"):
            return {"ok": False, "reason": "REPARSE_ANCESTOR"}
    return {
        "ok": True,
        "serial_dword": VOLUME_DWORD,
        "disk_unique_id": DISK_ID,
        "filesystem": "NTFS",
        "reparse_clear": True,
        "checked_paths": len(checked),
    }


def _reasons(items: list[str]) -> list[str]:
    found = []
    for item in items:
        if item not in found:
            found.append(item)
    return found


def accept_capability(sample: dict, backend, state_path, run: dict, scenario: str) -> dict:
    """Independent check of bytes, identities, directories and the two junction opens."""
    reasons = []
    plan = scenario_plan(sample, scenario)
    state = sqlite3.connect(state_path)
    digests = {}
    try:
        row = state.execute(
            "SELECT run_id, plan_digest, inputs_digest, code_digest, dest_volume, dest_root FROM run_bind"
        ).fetchone()
        expected = (
            run["run_id"], run["plan_digest"], run["inputs_digest"], run["code_digest"],
            run["dest_volume"], run["dest_root"],
        )
        if row is None or tuple(row) != expected:
            reasons.append("RUN_BINDING_MISMATCH")
        before = int(getattr(backend.sc, "hash_calls", 0))
        identities = []
        for entity in plan["entities"]:
            stage = state.execute(
                "SELECT phase, sha256, file_id, volume_serial, logical_size FROM stage WHERE item_key=?",
                ("entity:" + entity["entity_key"],),
            ).fetchone()
            if stage is None or stage[0] != "DONE" or not stage[1]:
                reasons.append("MISSING_ENTITY")
                continue
            digest = backend.content_sha(entity["dest_path"])
            digests[entity["dest_path"]] = digest
            observed = backend.observe_destination(entity["dest_path"])
            if digest != stage[1]:
                reasons.append("CONTENT_HASH")
            if int(observed.get("logical_size") or -1) != int(entity["logical_size"]) or int(stage[4] or -1) != int(entity["logical_size"]):
                reasons.append("SIZE_MISMATCH")
            if str(observed.get("file_id") or "") != str(stage[2] or "") or str(observed.get("volume_serial") or "") != str(VOLUME_DWORD):
                reasons.append("IDENTITY_MISMATCH")
            if observed.get("allocation_size") is None or observed.get("object_type") != "file":
                reasons.append("MISSING_FIELD")
            for alias in entity["extra_dest_paths"]:
                seen = backend.observe_destination(alias)
                if (
                    seen.get("status") != "PRESENT"
                    or seen.get("file_id") != observed.get("file_id")
                    or seen.get("volume_serial") != observed.get("volume_serial")
                    or seen.get("logical_size") != observed.get("logical_size")
                    or seen.get("allocation_size") != observed.get("allocation_size")
                ):
                    reasons.append("ALIAS_SPLIT")
            identities.append(str(observed.get("file_id")))
        if len(identities) != 3 or len(set(identities)) != 3:
            reasons.append("ENTITY_MERGE")
        for directory in plan["directories"]:
            seen = backend.observe_destination(directory)
            if seen.get("status") != "PRESENT" or seen.get("object_type") != "directory":
                reasons.append("MISSING_DIRECTORY")
        follows = (
            (plan["links"][0], "PRODUCT_MANIFESTS.json", plan["entities"][0]["dest_path"]),
            (plan["links"][1], "part_000.parquet", plan["entities"][1]["dest_path"]),
        )
        for link, child, representative in follows:
            seen = backend.observe_destination(link["link_path"])
            if int(seen.get("reparse_tag") or 0) != TAG:
                reasons.append("LINK_TAG")
            if seen.get("reparse_target") != link["target"]:
                reasons.append("LINK_TARGET")
            try:
                followed = backend.sc.follow_identity(link["link_path"] + "\\" + child)
            except (OSError, RuntimeError):
                reasons.append("LINK_FOLLOW")
                continue
            rep = backend.observe_destination(representative)
            if str(followed.get("file_id")) != str(rep.get("file_id")) or followed.get("sha256") != digests.get(representative):
                reasons.append("LINK_FOLLOW")
        if int(getattr(backend.sc, "hash_calls", 0)) - before != 3:
            reasons.append("CONTENT_HASH_FANOUT")
    finally:
        state.close()
    unique = _reasons(reasons)
    return {"full_acceptance": not unique, "reasons": unique}


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
            "allow_dirs": plan["directories"],
            "allow_files": [entity["dest_path"] for entity in plan["entities"]] + [
                path for entity in plan["entities"] for path in entity["extra_dest_paths"]
            ],
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
    acceptance = accept_capability(sample, backend, state_path, run, scenario)
    print(json.dumps({
        "scenario": scenario,
        "copied_count": result["copied_count"],
        "linked_count": result["linked_count"],
        "reparse_count": result["reparse_count"],
        "resumed_entities": result["resumed_entities"],
        "resumed_links": result["resumed_links"],
        "acceptance": acceptance["full_acceptance"],
        "reasons": acceptance["reasons"],
    }, ensure_ascii=False))
    return 0 if acceptance["full_acceptance"] else 4


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


def main(argv: list[str] | None = None, backend=None, os_api=None, state_path: Path | None = None) -> int:
    parser = argparse.ArgumentParser(prog="r9_capability_pilot")
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("dry-run", "execute", "build-sample"):
        cmd = sub.add_parser(name)
        if name != "build-sample":
            cmd.add_argument("--scenario", required=True, choices=SCENARIOS)
            cmd.add_argument("--sample", required=True)
            cmd.add_argument("--contract", required=True)
            if name == "execute":
                cmd.add_argument("--fault", choices=["A", "B", "C"])
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
    if args.fault and args.fault != args.scenario:
        print("FAULT_SCENARIO_MISMATCH")
        return 3
    return execute(Path(args.sample), Path(args.contract), args.scenario, backend=backend, os_api=os_api, state_path=state_path, fault=args.fault)


if __name__ == "__main__":
    sys.exit(main())
