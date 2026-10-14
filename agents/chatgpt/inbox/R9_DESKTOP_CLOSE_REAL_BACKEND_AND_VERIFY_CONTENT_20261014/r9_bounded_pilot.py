# -*- coding: utf-8 -*-
"""Bounded pilot entry. Full-plan copy stays refused. This round does not write E:."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path, PureWindowsPath

DEST_ROOT = "E:\\R9_POSTFORMAT_PILOT_20261014"
DISK_ID = "eui.E8238FA6BF530001001B448B42E694AE"
VOLUME_HEX = "D86AEE82"
VOLUME_DWORD = 3630886530
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
                "mtime_status": "PRIOR_OBSERVATION",
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


def canonical_path(path: str) -> str:
    if not isinstance(path, str) or "\x00" in path or path == "":
        raise RuntimeError("PATH_REJECTED")
    text = path.replace("/", "\\")
    if text.startswith("\\\\?\\"):
        text = text[4:]
    if len(text) < 2 or text[1] != ":":
        raise RuntimeError("PATH_REJECTED")
    if ":" in text[2:]:
        raise RuntimeError("PATH_ADS")
    stripped = text.rstrip("\\")
    if len(stripped) == 2:
        return stripped + "\\"
    parts = stripped.split("\\")
    if any(part in ("", ".", "..") for part in parts[1:]):
        raise RuntimeError("PATH_REJECTED")
    return "\\".join(parts)


def allow_directories() -> list[str]:
    return [DEST_ROOT, DEST_ROOT + "\\e", DEST_ROOT + "\\d"]


def allow_files() -> list[str]:
    files = [f"{DEST_ROOT}\\e\\p{index:02d}" for index in range(39)]
    files.append(DEST_ROOT + "\\d\\p00")
    return files


def _same_paths(left, right) -> bool:
    return sorted(canonical_path(item).casefold() for item in left) == sorted(canonical_path(item).casefold() for item in right)


def normalize_volume(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    if text.upper() == VOLUME_HEX:
        return str(VOLUME_DWORD)
    try:
        number = int(text, 10)
    except ValueError:
        return None
    if number == VOLUME_DWORD:
        return str(VOLUME_DWORD)
    return None


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
    if not _same_paths(dests, allow_files()):
        raise RuntimeError("PILOT_DEST_ALLOWLIST")
    if not _same_paths(sample.get("directories") or [], allow_directories()):
        raise RuntimeError("PILOT_DIR_ALLOWLIST")


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
            "mtime_prior": entity.get("mtime"),
            "mtime_status": "PRIOR_OBSERVATION",
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


def pilot_write_gate(contract: dict, backend) -> bool:
    """Allow a bounded pilot write only after run, sample, code, disk, volume and allowlist all match."""
    if contract.get("phase") != "PILOT_REAL_IO":
        return False
    if contract.get("pilot_write_authorized") is not True:
        return False
    if contract.get("copy_authorized") is not False or contract.get("full_migration") is not False:
        return False
    if contract.get("scope") != "BOUNDED_PILOT_ONLY":
        return False
    if contract.get("dest_root") != DEST_ROOT or contract.get("volume_serial_hex") != VOLUME_HEX:
        return False
    if contract.get("disk_unique_id") != DISK_ID:
        return False
    sample_sha = str(contract.get("sample_sha256") or "")
    if len(sample_sha) != 64:
        return False
    import r9_source_contract as source_contract
    code = source_contract.code_digest()
    if contract.get("code_digest") != code:
        return False
    run = contract.get("run")
    if not isinstance(run, dict) or not str(run.get("run_id") or "").strip():
        return False
    if run.get("plan_digest") != PLAN_SHA or run.get("inputs_digest") != sample_sha or run.get("code_digest") != code:
        return False
    if normalize_volume(run.get("dest_volume")) != str(VOLUME_DWORD) or run.get("dest_root") != DEST_ROOT:
        return False
    try:
        if contract.get("links") != []:
            return False
        if not _same_paths(contract.get("directories") or [], allow_directories()):
            return False
        if not _same_paths(contract.get("allow_files") or [], allow_files()):
            return False
    except RuntimeError:
        return False
    verified = contract.get("target_verified")
    if not isinstance(verified, dict) or verified.get("ok") is not True or verified.get("reparse_clear") is not True:
        return False
    if verified.get("serial_dword") != VOLUME_DWORD or verified.get("disk_unique_id") != DISK_ID:
        return False
    if str(verified.get("filesystem") or "").upper() != "NTFS":
        return False
    if not str(contract.get("state_path") or "").upper().startswith("C:\\"):
        return False
    from r9_winio import VirtualSyscalls, Win32Syscalls
    return isinstance(getattr(backend, "sc", None), (VirtualSyscalls, Win32Syscalls))


class RealLiveOs:
    """Read-only volume, disk and no-follow queries. Does not create the pilot directory."""

    def volume_information(self, root: str):
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
        if not get_vol(root, name, 64, ctypes.byref(serial), ctypes.byref(maxcomp), ctypes.byref(flags), fs, 32):
            return None
        return {"serial": int(serial.value), "filesystem": fs.value}

    def disk_unique_id(self, letter: str):
        import subprocess
        script = (
            "$p = Get-Partition -DriveLetter '%s' -ErrorAction Stop; "
            "$d = Get-Disk -Number $p.DiskNumber -ErrorAction Stop; "
            "Write-Output $d.UniqueId"
        ) % letter
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True, text=True, timeout=60, check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if out.returncode != 0:
            return None
        lines = [line.strip() for line in (out.stdout or "").splitlines() if line.strip()]
        return lines[-1] if lines else None

    def observe_nofollow(self, path: str):
        from r9_winio import Win32Syscalls
        return Win32Syscalls().observe(path)


def _chain(path: str) -> list[str]:
    current = canonical_path(path)
    found = []
    while True:
        found.append(current)
        if len(current) <= 3:
            break
        parent = str(PureWindowsPath(current).parent)
        if parent == current:
            break
        current = canonical_path(parent)
    return found


def _reparse_reason(observed) -> str | None:
    if not isinstance(observed, dict):
        return "REPARSE_QUERY_UNKNOWN"
    status = observed.get("status")
    if status == "MISSING":
        return None
    if status != "PRESENT":
        return "REPARSE_QUERY_UNKNOWN"
    if observed.get("object_type") in ("junction", "symlink") or observed.get("reparse_target"):
        return "REPARSE_ANCESTOR"
    if observed.get("object_type") not in ("directory", "file"):
        return "REPARSE_QUERY_UNKNOWN"
    return None


def live_target_probe(os_api=None) -> dict:
    """Query E: volume, the partition's physical disk, and no-follow ancestors."""
    api = os_api or RealLiveOs()
    volume = api.volume_information("E:\\")
    if not isinstance(volume, dict) or "serial" not in volume or "filesystem" not in volume:
        return {"ok": False, "reason": "TARGET_QUERY_FAILED"}
    try:
        serial = int(volume["serial"])
    except (TypeError, ValueError):
        return {"ok": False, "reason": "TARGET_QUERY_FAILED"}
    if serial != VOLUME_DWORD or str(volume["filesystem"]).upper() != "NTFS":
        return {"ok": False, "reason": "TARGET_VOLUME_MISMATCH", "serial_hex": f"{serial & 0xFFFFFFFF:08X}"}
    disk = api.disk_unique_id("E")
    if disk is None or str(disk).strip() == "":
        return {"ok": False, "reason": "DISK_QUERY_UNKNOWN"}
    if str(disk) != DISK_ID:
        return {"ok": False, "reason": "DISK_MISMATCH"}
    seen = set()
    for path in allow_directories() + allow_files():
        for item in _chain(path):
            key = item.casefold()
            if key in seen:
                continue
            seen.add(key)
            reason = _reparse_reason(api.observe_nofollow(item))
            if reason:
                return {"ok": False, "reason": reason}
    return {
        "ok": True,
        "serial_hex": VOLUME_HEX,
        "serial_dword": VOLUME_DWORD,
        "disk_unique_id": DISK_ID,
        "filesystem": "NTFS",
        "reparse_clear": True,
    }


def bound_run(contract: dict, sample_path: Path) -> dict:
    run = contract.get("run")
    if not isinstance(run, dict) or not str(run.get("run_id") or "").strip():
        raise RuntimeError("RUN_BINDING_MISSING")
    import r9_source_contract as source_contract
    expected = {
        "run_id": str(run["run_id"]),
        "plan_digest": PLAN_SHA,
        "inputs_digest": sample_sha256(sample_path),
        "code_digest": source_contract.code_digest(),
        "dest_volume": str(VOLUME_DWORD),
        "dest_root": DEST_ROOT,
    }
    for key, value in expected.items():
        if key == "dest_volume":
            if normalize_volume(run.get(key)) != value:
                raise RuntimeError("RUN_BINDING_MISSING")
            continue
        if str(run.get(key)) != str(value):
            raise RuntimeError("RUN_BINDING_MISSING")
    return expected


def observe_sources(backend, entities: list[dict]) -> None:
    """Read each source handle once and replace the prior mtime with this observation."""
    for entity in entities:
        handle = backend.sc.open_source(entity["source_path"])
        try:
            ident = backend.sc.identity(handle)
        finally:
            backend.sc.close(handle)
        if str(ident.get("file_id")) != str(entity["file_id"]) or str(ident.get("volume_serial")) != str(entity["volume_serial"]):
            raise RuntimeError("SOURCE_IDENTITY")
        if int(ident.get("size")) != int(entity["logical_size"]):
            raise RuntimeError("SOURCE_SIZE")
        if ident.get("mtime_ft") not in (None, ""):
            token = str(ident["mtime_ft"])
        elif ident.get("mtime") not in (None, ""):
            token = str(ident["mtime"])
        else:
            raise RuntimeError("MTIME_DEFICIT")
        entity["mtime_prior"] = entity.get("mtime_prior", entity.get("mtime"))
        entity["mtime"] = token
        entity["mtime_status"] = "FROM_SOURCE_HANDLE"


def _unique(reasons: list[str]) -> list[str]:
    found = []
    for reason in reasons:
        if reason not in found:
            found.append(reason)
    return found


def accept_pilot(sample: dict, backend, state_path, run) -> dict:
    """Compare copied bytes with the persistent stage. One content read per entity."""
    reasons = []
    expected_volume = normalize_volume(run.get("dest_volume")) if isinstance(run, dict) else None
    needed = ("run_id", "plan_digest", "inputs_digest", "code_digest", "dest_volume", "dest_root")
    if expected_volume is None or not isinstance(run, dict) or any(run.get(key) in (None, "") for key in needed):
        reasons.append("RUN_BINDING_MISSING")
    state = sqlite3.connect(state_path)
    hash_calls = 0
    checked = 0
    try:
        row = state.execute(
            "SELECT run_id, plan_digest, inputs_digest, code_digest, dest_volume, dest_root FROM run_bind"
        ).fetchone()
        if "RUN_BINDING_MISSING" not in reasons:
            stored = (
                run["run_id"], run["plan_digest"], run["inputs_digest"], run["code_digest"],
                expected_volume, run["dest_root"],
            )
            if row is None or tuple(row) != stored:
                reasons.append("RUN_BINDING_MISMATCH")
        for directory in allow_directories():
            observed = backend.observe_destination(directory)
            if observed.get("status") != "PRESENT" or observed.get("object_type") != "directory":
                reasons.append("MISSING_DIRECTORY")
            elif observed.get("allocation_size") is None:
                reasons.append("MISSING_FIELD")
        before = int(getattr(backend.sc, "hash_calls", 0))
        identities = []
        for entity in sample["entities"]:
            stage = state.execute(
                "SELECT phase, sha256, file_id, volume_serial, logical_size FROM stage WHERE item_key=?",
                ("entity:" + entity["entity_key"],),
            ).fetchone()
            representative = entity["paths"][0]["dest_path"]
            if stage is None or stage[0] != "DONE" or stage[1] in (None, ""):
                reasons.append("MISSING_ENTITY")
                continue
            try:
                digest = backend.content_sha(representative)
            except (OSError, RuntimeError, FileNotFoundError):
                reasons.append("CONTENT_HASH")
                continue
            observed = backend.observe_destination(representative)
            checked += 1
            if observed.get("status") != "PRESENT" or observed.get("object_type") != "file":
                reasons.append("MISSING_OBJECT")
                continue
            if any(observed.get(key) in (None, "") for key in ("file_id", "volume_serial")) or observed.get("logical_size") is None or observed.get("allocation_size") is None:
                reasons.append("MISSING_FIELD")
            if digest != stage[1]:
                reasons.append("CONTENT_HASH")
            if int(observed.get("logical_size") or -1) != int(entity["logical_size"]) or int(stage[4] or -1) != int(entity["logical_size"]):
                reasons.append("SIZE_MISMATCH")
            if normalize_volume(observed.get("volume_serial")) != expected_volume or normalize_volume(stage[3]) != expected_volume:
                reasons.append("DEST_VOLUME")
            if str(observed.get("file_id")) != str(stage[2]):
                reasons.append("IDENTITY_MISMATCH")
            ids = {str(observed.get("file_id"))}
            volumes = {normalize_volume(observed.get("volume_serial"))}
            sizes = {int(observed.get("logical_size") or -1)}
            allocs = {observed.get("allocation_size")}
            for item in entity["paths"][1:]:
                alias = backend.observe_destination(item["dest_path"])
                if alias.get("status") != "PRESENT" or alias.get("object_type") != "file":
                    reasons.append("MISSING_OBJECT")
                    continue
                ids.add(str(alias.get("file_id")))
                volumes.add(normalize_volume(alias.get("volume_serial")))
                sizes.add(int(alias.get("logical_size") or -1))
                allocs.add(alias.get("allocation_size"))
            if len(ids) != 1 or len(volumes) != 1 or len(sizes) != 1 or len(allocs) != 1 or None in allocs:
                reasons.append("ALIAS_SPLIT")
            identities.append(str(observed.get("file_id")))
        if len(identities) != 2 or len(set(identities)) != 2:
            reasons.append("ENTITY_MERGE")
        root_names = {PureWindowsPath(item["path"]).name.casefold() for item in backend.list_nofollow(DEST_ROOT)}
        e_names = {PureWindowsPath(item["path"]).name.casefold() for item in backend.list_nofollow(DEST_ROOT + "\\e")}
        d_names = {PureWindowsPath(item["path"]).name.casefold() for item in backend.list_nofollow(DEST_ROOT + "\\d")}
        if root_names != {"e", "d"} or e_names != {f"p{index:02d}" for index in range(39)} or d_names != {"p00"}:
            reasons.append("PATH_COVERAGE")
        hash_calls = int(getattr(backend.sc, "hash_calls", 0)) - before
        if hash_calls != len(sample["entities"]):
            reasons.append("CONTENT_HASH_FANOUT")
    finally:
        state.close()
    return {
        "full_acceptance": not _unique(reasons),
        "reasons": _unique(reasons),
        "checked_entities": checked,
        "content_hash_calls": hash_calls,
    }


def execute(sample_path: Path, contract_path: Path, backend=None, os_api=None, state_path: Path | None = None) -> int:
    sample = json.loads(sample_path.read_bytes().decode("utf-8"))
    contract = json.loads(contract_path.read_bytes().decode("utf-8"))
    validate_sample(sample)
    from r9_winio import Win32Syscalls
    before = Win32Syscalls.write_calls

    def refused(text: str) -> int:
        print(text)
        print(f"win32_write_calls={Win32Syscalls.write_calls - before}")
        return 3

    if not pilot_authorized(contract, sample_path):
        return refused("PILOT_WRITE_REFUSED")
    probe = live_target_probe(os_api)
    if not probe.get("ok"):
        return refused(probe.get("reason") or "TARGET_BINDING_MISMATCH")
    try:
        run_record = bound_run(contract, sample_path)
    except RuntimeError as exc:
        return refused(str(exc))
    if state_path is None:
        state_path = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_CLOSE_REAL_BACKEND_AND_VERIFY_CONTENT_20261014\state\pilot.sqlite")
    if backend is None:
        from r9_winio import WindowsBackend
        backend = WindowsBackend()
    try:
        entities = entities_for_run(sample)
        if any(item.get("mtime_status") == "FROM_SOURCE_HANDLE" for item in entities):
            raise RuntimeError("MTIME_NOT_LIVE")
        observe_sources(backend, entities)
        import r9_runner as runner
        run_contract = {
            "phase": "PILOT_REAL_IO",
            "pilot_write_authorized": True,
            "copy_authorized": False,
            "full_migration": False,
            "scope": "BOUNDED_PILOT_ONLY",
            "dest_root": DEST_ROOT,
            "volume_serial_hex": VOLUME_HEX,
            "disk_unique_id": DISK_ID,
            "sample_sha256": sample_sha256(sample_path),
            "plan_sha256": PLAN_SHA,
            "code_digest": run_record["code_digest"],
            "directories": allow_directories(),
            "allow_files": allow_files(),
            "links": [],
            "run": run_record,
            "state_path": str(state_path),
            "target_verified": {
                "ok": True,
                "serial_dword": probe["serial_dword"],
                "disk_unique_id": probe["disk_unique_id"],
                "filesystem": probe["filesystem"],
                "reparse_clear": True,
            },
        }
        result = runner.production_run(iter(entities), backend, run_contract, state_path)
    except RuntimeError as exc:
        return refused(str(exc))
    if result.get("refused_before_write"):
        return refused("PILOT_REAL_IO_NOT_RUN")
    acceptance = accept_pilot(sample, backend, state_path, run_record)
    print(json.dumps({
        "copied_count": result["copied_count"],
        "linked_count": result["linked_count"],
        "acceptance": acceptance["full_acceptance"],
        "reasons": acceptance["reasons"],
        "content_hash_calls": acceptance["content_hash_calls"],
    }, ensure_ascii=False))
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
