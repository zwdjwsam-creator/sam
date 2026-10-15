# -*- coding: utf-8 -*-
"""One formal copy chain for a full plan and a bounded bench subset.

Dry-run never creates a destination. Execute reaches production_run.
COPY_AUTHORIZED false refuses inside that chain before the first write.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PureWindowsPath

import r9_plan_reader as reader
import r9_source_contract as source_contract

FULL_PLAN_SHA = "94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba"
FULL_PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite")
CANDIDATE_PLAN_SHA = "53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d"
CANDIDATE_PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\FINAL_CANDIDATE.sqlite")
BUDGET = 1073741824
EXPECTED_VOLUME = "3630886530"
EXPECTED_DISK = "eui.E8238FA6BF530001001B448B42E694AE"
HOST = "ZHANGWEI"
BENCH_PARENT = r"E:\R9_FORMAL_PILOT_1G_20261014"
BENCH_E = BENCH_PARENT + r"\BLACKBOX"
BENCH_D = BENCH_PARENT + r"\BLACKBOX_ENGINES"
RECHECK_PARENT = r"E:\R9_FORMAL_BENCH_RECHECK_20261014"
RECHECK_E = RECHECK_PARENT + r"\BLACKBOX"
RECHECK_D = RECHECK_PARENT + r"\BLACKBOX_ENGINES"
PREFETCH_PARENT = r"E:\R9_FORMAL_PREFETCH_BENCH_20261014"
PREFETCH_E = PREFETCH_PARENT + r"\BLACKBOX"
PREFETCH_D = PREFETCH_PARENT + r"\BLACKBOX_ENGINES"
BENCH_LAYOUTS = (
    (BENCH_PARENT, BENCH_E, BENCH_D),
    (RECHECK_PARENT, RECHECK_E, RECHECK_D),
    (PREFETCH_PARENT, PREFETCH_E, PREFETCH_D),
)
TIMING_NOTE = (
    "workers=1: copy_seconds includes source open and both identity calls inside the copy. "
    "workers=4: copy_seconds starts after the prefetched handle is ready. It does not include "
    "prefetch open, the first identity, or take wait. "
    "source_prefetch_worker_seconds_sum adds overlapping worker time and is not wall-clock time. "
    "source_prefetch_wait_seconds is only the time blocked while taking a prepared handle. "
    "Do not add those figures to copy_seconds or to each other. "
    "entity_phase_wall_seconds runs from before entity consumption through prefetch cleanup, "
    "and is the wall clock for that phase. "
    "Do not treat a workers=4 copy_seconds value as the same measure as the old 954.274084 copy_seconds."
)
FORMAL_E = r"E:\BLACKBOX"
FORMAL_D = r"E:\BLACKBOX_ENGINES"
FILL_CAP = 8000
CLOSURE_CAP = 16
last_result = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            block = handle.read(8 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _under(path: str, roots) -> bool:
    text = str(path).replace("/", "\\").rstrip("\\").casefold()
    for root in roots:
        base = str(root).replace("/", "\\").rstrip("\\").casefold()
        if text == base or text.startswith(base + "\\"):
            return True
    return False


def bench_layout(roots):
    """Return the one exact bench triple declared by dest_roots. Unknown roots are not a bench."""
    wanted = tuple(roots or ())
    for parent, blackbox, engines in BENCH_LAYOUTS:
        if wanted == (blackbox, engines):
            return parent, blackbox, engines
    return None


def _stop_for(path: str) -> str:
    text = str(path).casefold()
    for parent, _blackbox, _engines in BENCH_LAYOUTS:
        base = parent.casefold()
        if text == base or text.startswith(base + "\\"):
            return parent
    return BENCH_PARENT


def _backend_timing(backend) -> dict:
    return {
        "phase_stats": getattr(backend, "phase_stats", "NOT_RUN"),
        "state_commit_calls": getattr(backend, "_state_commit_calls", "NOT_RUN"),
        "state_commit_seconds": getattr(backend, "_state_commit_seconds", "NOT_RUN"),
        "entity_phase_wall_seconds": getattr(backend, "_entity_phase_wall_seconds", "NOT_RUN"),
        "timing_note": TIMING_NOTE,
    }


def _writes(backend) -> int:
    sc = getattr(backend, "sc", None)
    return int(getattr(sc, "write_calls", 0) or 0) + int(getattr(sc, "recorded_writes", 0) or 0)


def _refused(reason: str, **extra) -> dict:
    payload = {"refused_before_write": True, "reason": reason, "write_calls": 0, "dry_run": False}
    payload.update(extra)
    return payload


def bound_plan_sha(path: Path) -> str | None:
    """Exact path-to-SHA binding. Any other plan file is refused."""
    resolved = str(Path(path).resolve()).casefold()
    if resolved == str(FULL_PLAN.resolve()).casefold():
        return FULL_PLAN_SHA
    if resolved == str(CANDIDATE_PLAN.resolve()).casefold():
        return CANDIDATE_PLAN_SHA
    return None


def assert_plan_stable(path: Path, snapshot) -> None:
    now = Path(path).stat()
    if now.st_size != snapshot.st_size or now.st_mtime_ns != snapshot.st_mtime_ns:
        raise RuntimeError("PLAN_CHANGED")


def formal_write_gate(contract: dict, backend) -> bool:
    if not isinstance(contract, dict) or contract.get("phase") != "FORMAL_COPY":
        return False
    if contract.get("copy_authorized") is not True or contract.get("full_migration") is True and contract.get("scope") == "BENCH":
        return False
    scope = contract.get("scope")
    if scope not in ("BENCH", "FULL"):
        return False
    if scope == "FULL" and contract.get("full_migration") is not True:
        return False
    isolated = contract.get("isolated_chain") is True
    if scope == "FULL" and not isolated and contract.get("plan_sha") != CANDIDATE_PLAN_SHA:
        return False
    if scope == "FULL" and contract.get("version_choice") != "AS_IS_MIGRATE_MARKED":
        return False
    if scope == "FULL" and full_share_binding(contract) is None:
        return False
    if scope == "BENCH" and contract.get("full_migration") is True:
        return False
    roots = tuple(contract.get("dest_roots") or ())
    if scope == "BENCH" and bench_layout(roots) is None:
        return False
    prefetch_workers = contract.get("source_prefetch_workers", 1)
    if prefetch_workers not in (1, 4):
        return False
    if scope == "FULL" and roots != (FORMAL_E, FORMAL_D):
        return False
    audit = contract.get("plan_audit")
    if not isinstance(audit, dict) or audit.get("ok") is not True:
        return False
    probe = contract.get("dest_probe")
    if not isinstance(probe, dict) or probe.get("ok") is not True:
        return False
    if str(probe.get("volume_serial")) != str(contract.get("expected_volume_serial")):
        return False
    if str(probe.get("unique_id")) != str(contract.get("expected_unique_id")):
        return False
    isolated = contract.get("isolated_chain") is True
    if isolated:
        if str(contract.get("expected_unique_id")) == EXPECTED_DISK:
            return False
    else:
        if str(contract.get("expected_volume_serial")) != EXPECTED_VOLUME:
            return False
        if str(contract.get("expected_unique_id")) != EXPECTED_DISK:
            return False
        if str(probe.get("filesystem") or "").upper() != "NTFS":
            return False
    run = contract.get("run") if isinstance(contract.get("run"), dict) else {}
    if str(run.get("dest_volume")) != str(contract.get("expected_volume_serial")):
        return False
    if str(run.get("dest_root")) != roots[0]:
        return False
    if scope == "BENCH" and contract.get("source_plan_sha") != FULL_PLAN_SHA:
        return False
    if scope == "FULL" and not isolated and contract.get("source_plan_sha") != CANDIDATE_PLAN_SHA:
        return False
    if not contract.get("plan_sha") or contract.get("plan_sha") != run.get("plan_digest"):
        return False
    if run.get("inputs_digest") != run.get("plan_digest") or not run.get("code_digest"):
        return False
    try:
        cap = int(contract.get("max_unique_bytes"))
        declared = int(contract.get("subset_unique_bytes"))
    except (TypeError, ValueError):
        return False
    if cap <= 0 or cap != declared:
        return False
    if scope == "BENCH" and cap > BUDGET:
        return False
    state = contract.get("state_path")
    if not isinstance(state, str) or not state:
        return False
    try:
        if Path(state).drive.upper() != "C:":
            return False
    except (TypeError, ValueError):
        return False
    from r9_winio import VirtualSyscalls, Win32Syscalls
    sc = getattr(backend, "sc", None)
    if isinstance(sc, VirtualSyscalls):
        if not isolated:
            return False
    elif not isinstance(sc, Win32Syscalls):
        return False
    return True


def live_probe() -> dict:
    from r9_bounded_pilot import RealLiveOs
    api = RealLiveOs()
    volume = api.volume_information("E:\\")
    disk = api.disk_unique_id("E")
    if not isinstance(volume, dict) or "serial" not in volume:
        return {"ok": False, "reason": "TARGET_QUERY_FAILED", "volume_serial": None, "unique_id": None}
    serial = str(volume.get("serial"))
    filesystem = str(volume.get("filesystem") or "")
    unique = None if disk is None else str(disk)
    ok = serial == EXPECTED_VOLUME and filesystem.upper() == "NTFS" and unique == EXPECTED_DISK
    return {
        "ok": ok,
        "reason": None if ok else "TARGET_MISMATCH",
        "volume_serial": serial,
        "filesystem": filesystem,
        "unique_id": unique,
    }


def local_link_status() -> dict:
    """Read the local route toward the source host. Does not change adapters or sessions."""
    script = (
        "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false; "
        "$ErrorActionPreference='Stop'; "
        "$route = Find-NetRoute -RemoteIPAddress '192.168.100.2' | Select-Object -First 1; "
        "$adapter = Get-NetAdapter -InterfaceIndex $route.InterfaceIndex; "
        "[pscustomobject]@{ interface=[string]$adapter.Name; status=[string]$adapter.Status; "
        "linkSpeed=[string]$adapter.LinkSpeed; ifIndex=[int]$adapter.ifIndex; nextHop=[string]$route.NextHop; "
        "destination='192.168.100.2' } | ConvertTo-Json -Compress"
    )
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, timeout=40, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"queried": False, "error": type(exc).__name__}
    stdout = (out.stdout or b"").decode("utf-8", "replace")
    stderr = (out.stderr or b"").decode("utf-8", "replace")
    if out.returncode != 0 or not stdout.strip():
        return {"queried": False, "error": stderr[-300:]}
    try:
        payload = json.loads(stdout.strip().splitlines()[-1])
    except json.JSONDecodeError:
        return {"queried": False, "error": "LINK_STATUS_UNPARSEABLE"}
    payload["queried"] = True
    payload["speed_note"] = "LinkSpeed is the negotiated link rate. 2.5 Gbps is not 2.5 GB/s. It is not a migration ETA."
    payload["bench_measured"] = False
    return payload


def _scope_violation(conn: sqlite3.Connection, scope: str, roots=()) -> int:
    if scope == "BENCH":
        layout = bench_layout(roots)
        if layout is None:
            return 1
        parent, blackbox, engines = layout
        file_bad = conn.execute(
            """
            SELECT COUNT(*) FROM paths
            WHERE is_dir=0 AND NOT (
              path=? OR path LIKE ? OR path=? OR path LIKE ?
            )
            """,
            (blackbox, blackbox + "\\%", engines, engines + "\\%"),
        ).fetchone()[0]
        dir_bad = conn.execute(
            """
            SELECT COUNT(*) FROM paths
            WHERE is_dir=1 AND NOT (path=? OR path LIKE ?)
            """,
            (parent, parent + "\\%"),
        ).fetchone()[0]
        return int(file_bad or 0) + int(dir_bad or 0)
    if scope == "FULL":
        bad = conn.execute(
            """
            SELECT COUNT(*) FROM paths WHERE NOT (
              path='E:\\BLACKBOX' OR path LIKE 'E:\\BLACKBOX\\%'
              OR path='E:\\BLACKBOX_ENGINES' OR path LIKE 'E:\\BLACKBOX_ENGINES\\%'
              OR (path>='D:\\' AND path<'E:\\')
            )
            """
        ).fetchone()[0]
        return int(bad or 0)
    return 1


def directory_chain(path: str, include_self: bool, stop: str = BENCH_PARENT) -> list[str]:
    """Parents up to the bench root. include_self is only for a real directory, never a link path."""
    found = [str(path)] if include_self else []
    current = str(path)
    while True:
        parent = str(PureWindowsPath(current).parent)
        if parent == current or len(parent) <= 3:
            break
        found.append(parent)
        if parent.casefold() == str(stop).casefold():
            break
        current = parent
    return found


def _target_kind(conn: sqlite3.Connection, inventory: str) -> tuple[str, str | None]:
    info = conn.execute(
        "SELECT is_dir, is_reparse, reparse_target FROM paths WHERE path=?",
        (inventory,),
    ).fetchone()
    link = conn.execute(
        "SELECT target, reparse_tag FROM links WHERE path=? OR migrated_link_path=? LIMIT 1",
        (inventory, inventory),
    ).fetchone()
    if info is None and link is None:
        return "unknown", None
    if (info and int(info[1] or 0) == 1) or link is not None:
        nxt = None
        if link and link[0]:
            nxt = str(link[0])
        elif info and info[2]:
            nxt = str(info[2])
        return "link", nxt
    if info and int(info[0] or 0) == 1:
        return "ordinary", inventory
    if info and int(info[0] or 0) == 0:
        return "file", inventory
    return "unknown", None


def _resolve_ordinary(conn: sqlite3.Connection, inventory: str, hops: int = 8):
    """Follow link targets to an ordinary directory. Does not read file bytes."""
    seen = set()
    current = inventory
    chain = []
    for _ in range(hops):
        if current in seen:
            return None, [], "TARGET_LINK_CYCLE"
        seen.add(current)
        kind, nxt = _target_kind(conn, current)
        if kind == "ordinary":
            return current, chain, None
        if kind == "file":
            return None, chain, "TARGET_IS_FILE"
        if kind != "link" or not nxt:
            return None, chain, "TARGET_TYPE_UNKNOWN"
        chain.append((current, nxt))
        current = nxt
    return None, chain, "TARGET_LINK_NOT_CLOSED"


def _file_groups(conn: sqlite3.Connection, inventory: str) -> tuple[dict, bool]:
    groups = {}
    seen_paths = 0
    raw_rows = 0
    for vol, fid, logical, _row_path, _alloc, is_dir, is_reparse in _range_files(conn, inventory):
        raw_rows += 1
        if raw_rows > 64 or seen_paths > CLOSURE_CAP:
            return groups, True
        if is_dir or is_reparse:
            continue
        seen_paths += 1
        groups.setdefault((str(vol), str(fid)), int(logical or 0))
    return groups, seen_paths > CLOSURE_CAP


def audit_bench_links(conn: sqlite3.Connection) -> dict:
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "links" not in tables:
        return {"ok": True, "links": 0, "missing_target": 0, "missing_ancestor": 0, "link_as_dir": 0}
    dir_rows = {
        str(path).casefold(): (int(is_dir or 0), int(is_reparse or 0))
        for path, is_dir, is_reparse in conn.execute("SELECT path, is_dir, is_reparse FROM paths")
    }
    link_rows = list(conn.execute("SELECT path, COALESCE(migrated_target, target) FROM links"))
    by_link = {str(path).casefold(): str(target) for path, target in link_rows}
    missing_target = 0
    missing_ancestor = 0
    link_as_dir = 0

    def closed(target: str) -> bool:
        seen = set()
        current = str(target)
        for _ in range(8):
            key = current.casefold()
            if key in seen:
                return False
            seen.add(key)
            if key in by_link:
                current = by_link[key]
                continue
            return dir_rows.get(key) == (1, 0)
        return False

    for link_path, target in link_rows:
        if dir_rows.get(str(link_path).casefold()) == (1, 0):
            link_as_dir += 1
        if not closed(str(target)):
            missing_target += 1
        for parent in directory_chain(str(link_path), False, _stop_for(str(link_path))):
            if parent.casefold() in by_link:
                continue
            if dir_rows.get(parent.casefold()) != (1, 0):
                missing_ancestor += 1
                break
    return {
        "ok": missing_target == 0 and missing_ancestor == 0 and link_as_dir == 0,
        "links": len(link_rows),
        "missing_target": missing_target,
        "missing_ancestor": missing_ancestor,
        "link_as_dir": link_as_dir,
    }


def _path_key(path: str) -> str:
    return str(path).replace("/", "\\").rstrip("\\").casefold()


def _dest_inventory_key(path: str) -> str:
    text = str(path).replace("/", "\\").rstrip("\\")
    if text.upper().startswith("D:\\"):
        return _path_key("E:\\BLACKBOX_ENGINES\\" + text[3:])
    return _path_key(text)


def _parent_missing(path: str, directories: set, known_roots: set) -> bool:
    parent = str(path).replace("/", "\\").rstrip("\\").rsplit("\\", 1)[0]
    parent_key = parent.casefold()
    return parent_key not in directories and parent_key not in known_roots and len(parent) > 3


def _under_reparse(path: str, reparses: set) -> bool:
    current = str(path).replace("/", "\\").rstrip("\\").rsplit("\\", 1)[0]
    while len(current) > 3:
        if current.casefold() in reparses:
            return True
        if "\\" not in current:
            break
        current = current.rsplit("\\", 1)[0]
    return False


def _occupied_dest(path: str, migrated: str | None = None) -> str:
    """Destination path the reader will create, then case-folded."""
    if migrated:
        text = str(migrated).replace("/", "\\").rstrip("\\")
        return _path_key(text)
    try:
        text = reader.map_inventory_path(path)["dest_path"]
    except ValueError:
        text = str(path).replace("/", "\\").rstrip("\\")
    return _path_key(text)


def _note_collision(samples: list, kind: str, path: str, dest: str) -> None:
    if len(samples) < 8:
        samples.append({"kind": kind, "path": path, "dest": dest})


def audit_full_plan(conn: sqlite3.Connection) -> dict:
    """FULL closure. Directory rows are kept; ordinary file rows are streamed."""
    directories = set()
    dest_directories = set()
    dest_reparses = set()
    collisions = 0
    collision_samples: list[dict] = []
    for path, is_dir, is_reparse in conn.execute("SELECT path, is_dir, is_reparse FROM paths"):
        if not int(is_reparse) and not int(is_dir):
            continue
        key = _path_key(path)
        dest = _occupied_dest(path)
        if int(is_reparse):
            if dest in dest_directories or dest in dest_reparses:
                collisions += 1
                _note_collision(collision_samples, "reparse_name", path, dest)
            dest_reparses.add(dest)
        elif int(is_dir):
            directories.add(key)
            if dest in dest_directories or dest in dest_reparses:
                collisions += 1
                _note_collision(collision_samples, "directory_name", path, dest)
            dest_directories.add(dest)
    known_roots = {_path_key(root) for root in ("E:\\BLACKBOX", "E:\\BLACKBOX_ENGINES", "D:")}
    missing_parent = 0
    under_reparse = 0
    for key in directories:
        if _parent_missing(key, directories, known_roots):
            missing_parent += 1
    for dest in dest_directories:
        if _under_reparse(dest, dest_reparses):
            under_reparse += 1
    missing_terminal = 0
    cycles = 0
    link_missing_parent = 0
    engines_mapped = 0
    junctions = {}
    link_rows = []
    link_keys = set()
    for path, target, migrated_link, migrated_target in conn.execute(
        "SELECT path, target, migrated_link_path, migrated_target FROM links"
    ):
        inventory = str(path).replace("/", "\\").rstrip("\\")
        link_path = str(migrated_link or path).replace("/", "\\").rstrip("\\")
        dest = str(migrated_target or target).replace("/", "\\").rstrip("\\")
        link_key = _occupied_dest(path, migrated_link)
        dest_key = _occupied_dest(target, migrated_target)
        link_rows.append((inventory, link_path, dest, link_key, dest_key))
        if link_key in link_keys:
            collisions += 1
            _note_collision(collision_samples, "link_name", link_path, link_key)
        link_keys.add(link_key)
        junctions[link_key] = dest
    for inventory_link, link_path, dest, link_key, dest_key in link_rows:
        if _parent_missing(inventory_link, directories, known_roots):
            link_missing_parent += 1
        dest_parent = link_path.rsplit("\\", 1)[0]
        if _path_key(dest_parent) not in dest_directories and _path_key(dest_parent) not in known_roots and len(dest_parent) > 3:
            link_missing_parent += 1
        if link_key in dest_directories:
            collisions += 1
            _note_collision(collision_samples, "link_directory", link_path, link_key)
            if dest_key == link_key:
                cycles += 1
            continue
        if dest_key in dest_directories:
            if dest.upper().startswith("E:\\BLACKBOX_ENGINES\\"):
                engines_mapped += 1
            continue
        seen = set()
        hop = dest
        cyclic = False
        resolved = False
        for _ in range(64):
            hop_key = hop.casefold()
            if hop_key in seen:
                cyclic = True
                break
            seen.add(hop_key)
            mapped = _occupied_dest(hop)
            if mapped in dest_directories and hop_key not in junctions and mapped not in junctions:
                resolved = True
                break
            nxt = junctions.get(hop_key) or junctions.get(mapped)
            if not nxt:
                break
            hop = nxt
        if cyclic:
            cycles += 1
        elif not resolved:
            missing_terminal += 1
    state_dir = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\state")
    state_dir.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="r9dest_", suffix=".sqlite", dir=state_dir)
    os.close(fd)
    store = sqlite3.connect(temp_name)
    try:
        store.execute("PRAGMA journal_mode=OFF")
        store.execute("PRAGMA synchronous=OFF")
        store.execute("CREATE TABLE audit_dest_file (dest_key TEXT, entity_key TEXT, path TEXT)")
        batch = []
        cur = conn.execute(
            "SELECT path, volume_serial, file_id FROM paths WHERE is_dir=0 AND is_reparse=0"
        )
        while True:
            rows = cur.fetchmany(20000)
            if not rows:
                break
            for path, volume, file_id in rows:
                if _parent_missing(path, directories, known_roots):
                    missing_parent += 1
                dest = _occupied_dest(path)
                if _under_reparse(dest, dest_reparses):
                    under_reparse += 1
                if dest in dest_directories or dest in dest_reparses or dest in link_keys:
                    collisions += 1
                    _note_collision(collision_samples, "file_name", path, dest)
                batch.append((dest, f"{volume}|{file_id}", str(path)))
                if len(batch) >= 20000:
                    store.executemany("INSERT INTO audit_dest_file VALUES (?,?,?)", batch)
                    batch.clear()
        if batch:
            store.executemany("INSERT INTO audit_dest_file VALUES (?,?,?)", batch)
        store.execute("CREATE INDEX audit_dest_file_key ON audit_dest_file(dest_key)")
        distinct_entity = store.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT dest_key FROM audit_dest_file
                GROUP BY dest_key
                HAVING COUNT(DISTINCT entity_key) > 1
            )
            """
        ).fetchone()[0]
        collisions += int(distinct_entity or 0)
        for dest_key, path in store.execute(
            """
            SELECT dest_key, MIN(path) FROM audit_dest_file
            GROUP BY dest_key
            HAVING COUNT(DISTINCT entity_key) > 1
            LIMIT 8
            """
        ):
            _note_collision(collision_samples, "file_entity", path, dest_key)
    finally:
        store.close()
        Path(temp_name).unlink(missing_ok=True)
    missing_parent += link_missing_parent
    error = None
    if missing_terminal or cycles or missing_parent or under_reparse or collisions:
        error = "LINK_CLOSURE"
    return {
        "ok": error is None,
        "error": error,
        "missing_terminal": missing_terminal,
        "cycles": cycles,
        "missing_parent": missing_parent,
        "under_reparse": under_reparse,
        "collisions": collisions,
        "collision_samples": collision_samples,
        "engines_mapped": engines_mapped,
        "directories": len(directories),
        "reparses": len(dest_reparses),
    }


def inspect_plan(plan_path: Path, contract: dict) -> dict:
    path = Path(plan_path)
    if not path.is_file():
        return {"ok": False, "error": "PLAN_MISSING"}
    freeze = reader.plan_freeze_status(path)
    if not freeze["frozen"]:
        return {"ok": False, "error": "PLAN_NOT_FROZEN", **freeze}
    conn = reader.connect(path)
    try:
        digest = reader.plan_digest(conn)
        count, total = conn.execute("SELECT COUNT(*), COALESCE(SUM(min_size),0) FROM entities").fetchone()
        count = int(count or 0)
        total = int(total or 0)
        mismatch = conn.execute(
            """
            SELECT COUNT(*) FROM entities e
            WHERE e.path_count != (
                SELECT COUNT(*) FROM paths p
                WHERE p.is_dir=0 AND p.is_reparse=0
                  AND p.volume_serial=e.volume_serial AND p.file_id=e.file_id
            )
            """
        ).fetchone()[0]
        outside = _scope_violation(conn, str(contract.get("scope")), tuple(contract.get("dest_roots") or ()))
        scope_name = str(contract.get("scope"))
        if scope_name == "BENCH":
            closure = audit_bench_links(conn)
        elif scope_name == "FULL":
            closure = audit_full_plan(conn)
        else:
            closure = {"ok": False, "error": "SCOPE"}
    finally:
        conn.close()
    run = contract.get("run") if isinstance(contract.get("run"), dict) else {}
    error = None
    if count <= 0 or total <= 0:
        error = "EMPTY_PLAN"
    elif int(mismatch or 0) != 0:
        error = "PATH_COUNT"
    elif outside:
        error = "SCOPE_ESCAPE"
    elif not closure["ok"]:
        error = "LINK_CLOSURE"
    elif digest != contract.get("plan_sha") or digest != run.get("plan_digest") or digest != run.get("inputs_digest"):
        error = "PLAN_DIGEST_MISMATCH"
    elif run.get("code_digest") != source_contract.code_digest():
        error = "CODE_DIGEST_MISMATCH"
    else:
        try:
            cap = int(contract.get("max_unique_bytes"))
            declared = int(contract.get("subset_unique_bytes"))
        except (TypeError, ValueError):
            cap = declared = -1
        if cap != total or declared != total:
            error = "BUDGET_BINDING"
        elif contract.get("scope") == "BENCH" and total > BUDGET:
            error = "BUDGET"
    return {
        "ok": error is None,
        "error": error,
        "plan_sha": digest,
        "entities": count,
        "unique_bytes": total,
        "path_count_mismatches": int(mismatch or 0),
        "outside_paths": int(outside or 0),
        "frozen": True,
        "closure": closure,
    }


def _directories(plan_path: Path, scope: str):
    conn = reader.connect(plan_path)
    try:
        if scope == "BENCH":
            cur = conn.execute(
                """
                SELECT path FROM paths
                WHERE is_dir=1 AND is_reparse=0
                ORDER BY (length(path) - length(replace(path, char(92), ''))) , path
                """
            )
            for (path,) in cur:
                yield {"dest_path": path}
            return
        rows = [item["dest_path"] for item in reader.iter_directories(conn)]
        rows.sort(key=lambda item: (item.count("\\"), item.casefold()))
        for path in rows:
            yield {"dest_path": path}
    finally:
        conn.close()


def _links(plan_path: Path) -> list[dict]:
    conn = reader.connect(plan_path)
    try:
        links = list(reader.iter_links(conn))
    finally:
        conn.close()
    for link in links:
        if link.get("blocked") or not link.get("kind"):
            raise RuntimeError(link.get("reason") or "BAD_LINK_TARGET")
        if "\\\\" in str(link.get("target")) or str(link.get("target")).upper().startswith("D:\\"):
            raise RuntimeError("BAD_LINK_TARGET")
    return links


def full_share_binding(contract: dict):
    """Exact E and D UNC roots. A local drive letter is not a source binding."""
    shares = contract.get("shares") if isinstance(contract, dict) else None
    if not isinstance(shares, dict):
        return None
    d_root = str(shares.get("d_unc_root") or "").replace("/", "\\").rstrip("\\")
    e_root = str(shares.get("e_unc_root") or "").replace("/", "\\").rstrip("\\")
    if d_root.casefold() != reader.D_UNC_ROOT.casefold():
        return None
    if e_root.casefold() != reader.E_UNC.casefold():
        return None
    return {"d_unc_root": reader.D_UNC_ROOT, "e_unc_root": reader.E_UNC}


def _entities(plan_path: Path, snapshot, shares=None):
    conn = reader.connect(plan_path)
    produced = 0
    try:
        for entity in reader.read_executable(conn, shares=shares):
            source = str(entity.get("source_path") or "")
            if source.upper().startswith("D:\\") or entity.get("source_share") == "D_SHARE_NOT_IN_CONTRACT":
                raise RuntimeError("SOURCE_SHARE_UNBOUND")
            produced += 1
            if produced % 200 == 0:
                assert_plan_stable(plan_path, snapshot)
            yield entity
    finally:
        conn.close()


def _backend_for(contract: dict):
    from r9_winio import Win32Syscalls, WindowsBackend
    return WindowsBackend(Win32Syscalls())


def classify_failure(message: str, writes: int) -> tuple[str, int]:
    code = str(message).split(":", 1)[0]
    phase_codes = {
        "SOURCE_CHANGED", "SOURCE_CHANGED_DURING_COPY", "SHORT_READ", "SOURCE_SIZE",
        "SOURCE_LONGER", "SHORT_WRITE", "DEST_SHORT", "DEST_HASH", "UNKNOWN_TARGET_EXISTS",
        "PLAN_CHANGED", "MTIME_DEFICIT", "PLAN_ORPHAN_ENTITY",
    }
    if code in phase_codes or code.startswith("SOURCE_MTIME"):
        return "PHASE_STOP", 4
    if writes == 0:
        return "REFUSED_BEFORE_WRITE", 3
    return "PHASE_STOP", 4


def _peak_working_set() -> int | None:
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]
    counters = Counters()
    counters.cb = ctypes.sizeof(Counters)
    try:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        ok = psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
    except OSError:
        return None
    if not ok:
        return None
    return int(counters.PeakWorkingSetSize)


def execute_contract(contract: dict, mode: str, backend=None, probe=None) -> dict:
    global last_result
    if mode not in ("dry-run", "execute"):
        return _refused("MODE")
    working = dict(contract)
    working["phase"] = "FORMAL_COPY"
    isolated = working.get("isolated_chain") is True
    if not isolated:
        if socket.gethostname().upper() != HOST:
            return _refused("HOST_MISMATCH")
        source = Path(working.get("source_plan_path") or FULL_PLAN)
        try:
            actual = sha256_file(source)
        except OSError:
            return _refused("SOURCE_PLAN_MISMATCH")
        expected = bound_plan_sha(source)
        if expected is None or actual != expected or actual != working.get("source_plan_sha"):
            return _refused("SOURCE_PLAN_MISMATCH", actual_source_sha=actual)
        probed = live_probe() if probe is None else probe
    else:
        if working.get("scope") == "FULL":
            if full_share_binding(working) is None:
                return _refused("SOURCE_SHARE_UNBOUND")
        elif working.get("source_plan_sha") != FULL_PLAN_SHA:
            return _refused("SOURCE_PLAN_MISMATCH")
        probed = probe if isinstance(probe, dict) else {"ok": False, "reason": "TARGET_QUERY_FAILED"}
    working["dest_probe"] = probed
    plan_path = Path(working.get("plan_path") or "")
    try:
        audit = inspect_plan(plan_path, working)
    except (OSError, RuntimeError, sqlite3.Error) as exc:
        return _refused("PLAN_UNREADABLE", error=str(exc).split(":", 1)[0])
    working["plan_audit"] = audit
    scope = working.get("scope")
    full_plan_acceptance = False
    if mode == "dry-run":
        link = {"queried": False, "bench_measured": False} if isolated else local_link_status()
        result = {
            "refused_before_write": True,
            "dry_run": True,
            "write_calls": 0,
            "reason": "DRY_RUN" if audit.get("ok") else audit.get("error"),
            "plan_audit": audit,
            "link": link,
            "scope": scope,
            "full_plan_acceptance": False,
            "bench_measured": False,
            "would_write": False,
            "gate_open": formal_write_gate(working, backend or _backend_for(working)),
        }
        last_result = result
        return result
    if backend is None:
        backend = _backend_for(working)
    from r9_runner import production_run
    state_path = Path(working.get("state_path") or "")
    snapshot = plan_path.stat() if plan_path.is_file() else None
    directories = ()
    links = ()
    entities = iter(())
    if audit.get("ok") and formal_write_gate(working, backend) and snapshot is not None:
        try:
            directories = list(_directories(plan_path, scope))
            links = _links(plan_path)
            entities = _entities(plan_path, snapshot, full_share_binding(working) if scope == "FULL" else None)
        except RuntimeError as exc:
            kind, _code = classify_failure(str(exc), 0)
            result = _refused(str(exc).split(":", 1)[0], exit_class=kind, plan_audit=audit, scope=scope)
            last_result = result
            return result
    run = dict(working.get("run") or {})
    layout = bench_layout(working.get("dest_roots"))
    if scope == "BENCH" and layout is not None:
        run["acceptance_roots"] = [layout[0]]
    elif scope == "BENCH":
        run["acceptance_roots"] = [BENCH_PARENT]
    elif scope == "FULL":
        run.setdefault("acceptance_roots", [FORMAL_E, FORMAL_D])
    working["run"] = run
    working["directories"] = directories
    working["links"] = links
    working["accept"] = True
    working["collect_timing"] = True
    working["plan_path"] = str(plan_path)
    try:
        result = production_run(entities, backend, working, state_path)
    except Exception as exc:
        writes = _writes(backend)
        kind, code = classify_failure(str(exc), writes)
        result = {
            "refused_before_write": kind == "REFUSED_BEFORE_WRITE",
            "phase_stop": kind == "PHASE_STOP",
            "exit_class": kind,
            "exit_code": code,
            "reason": str(exc).split(":", 1)[0],
            "error": f"{type(exc).__name__}: {exc}",
            "write_calls": writes,
            "plan_audit": audit,
            "scope": scope,
            "full_plan_acceptance": False,
            "bench_measured": False,
            **_backend_timing(backend),
        }
        last_result = result
        return result
    result["plan_audit"] = audit
    result["scope"] = scope
    result["write_calls"] = _writes(backend)
    result["bench_measured"] = False
    accepted = bool((result.get("acceptance") or {}).get("full_acceptance"))
    result["full_plan_acceptance"] = bool(accepted and scope == "FULL" and working.get("plan_sha") == CANDIDATE_PLAN_SHA and working.get("version_choice") == "AS_IS_MIGRATE_MARKED")
    full_plan_acceptance = result["full_plan_acceptance"]
    if audit.get("error"):
        result["reason"] = audit["error"]
    elif result.get("refused_before_write"):
        result["reason"] = "REFUSED_BEFORE_WRITE"
    elif not accepted:
        result["reason"] = "ACCEPTANCE_FAILED"
        result["exit_class"] = "PHASE_STOP"
    else:
        result["reason"] = "ACCEPTED_SUBSET" if scope == "BENCH" else "ACCEPTED_FULL"
    result["peak_working_set_bytes"] = _peak_working_set()
    result["full_plan_acceptance"] = full_plan_acceptance
    result["timing_note"] = TIMING_NOTE
    result["state_commit_seconds"] = result.get("state_commit_seconds", getattr(backend, "_state_commit_seconds", "NOT_RUN"))
    last_result = result
    return result


def exit_code(result: dict, mode: str) -> int:
    if mode == "dry-run":
        if result.get("reason") in ("HOST_MISMATCH", "SOURCE_PLAN_MISMATCH", "PLAN_UNREADABLE"):
            return 2
        return 0
    if result.get("exit_class") == "PHASE_STOP" or result.get("reason") == "ACCEPTANCE_FAILED":
        return 4
    if result.get("refused_before_write"):
        return 3
    if result.get("reason") in ("ACCEPTED_SUBSET", "ACCEPTED_FULL"):
        return 0
    return 4


def _to_bench(path: str) -> str:
    text = str(path).replace("/", "\\")
    upper = text.upper()
    if upper == BENCH_E or upper.startswith(BENCH_E + "\\") or upper == BENCH_D or upper.startswith(BENCH_D + "\\"):
        return text
    engines = "E:\\BLACKBOX_ENGINES"
    blackbox = "E:\\BLACKBOX"
    if upper == engines or upper.startswith(engines + "\\"):
        rel = text[len(engines):].lstrip("\\")
        return BENCH_D if not rel else BENCH_D + "\\" + rel
    if upper == blackbox or upper.startswith(blackbox + "\\"):
        rel = text[len(blackbox):].lstrip("\\")
        return BENCH_E if not rel else BENCH_E + "\\" + rel
    if upper.startswith("D:\\"):
        rel = text[3:].lstrip("\\")
        return BENCH_D if not rel else BENCH_D + "\\" + rel
    raise ValueError("UNMAPPED_PATH")


def _is_chinese_long(path: str) -> bool:
    return len(path) >= 240 and any(ord(ch) > 127 for ch in path)


def _add_choice(chosen: dict, remaining: list, volume, file_id, size, label: str, limit: int | None = None) -> bool:
    key = (str(volume), str(file_id))
    size = int(size or 0)
    if key in chosen or size <= 0 or size > remaining[0]:
        return False
    if limit is not None and size > limit:
        return False
    if len(chosen) >= FILL_CAP:
        return False
    chosen[key] = {"min_size": size, "class": label}
    remaining[0] -= size
    return True


def _range_files(conn, root: str):
    """Path-index range. Callers must stop after a few rows; do not filter is_dir in SQL."""
    prefix = str(root).replace("/", "\\").rstrip("\\")
    lo = prefix + "\\"
    hi = prefix + "\\\uffff"
    return conn.execute(
        """
        SELECT volume_serial, file_id, logical_size, path, alloc_size, is_dir, is_reparse
        FROM paths
        WHERE path >= ? AND path < ?
        """,
        (lo, hi),
    )


def build_subset(plan: Path, out_dir: Path) -> dict:
    """Deterministic <=1GiB subset. Does not create the E: bench directory."""
    plan = Path(plan)
    out_dir = Path(out_dir)
    if out_dir.drive.upper() != "C:":
        raise RuntimeError("SUBSET_DEST_NOT_C")
    if plan.resolve() == (out_dir / "BENCH_SUBSET.sqlite").resolve():
        raise RuntimeError("SUBSET_ALIASES_SOURCE_PLAN")
    out_dir.mkdir(parents=True, exist_ok=True)
    existed = Path(BENCH_PARENT).exists()
    print("subset hash source plan", file=sys.stderr)
    source_sha = sha256_file(plan)
    if source_sha != FULL_PLAN_SHA:
        raise RuntimeError("SOURCE_PLAN_MISMATCH")
    snapshot = plan.stat()
    src = reader.connect(plan)
    src.execute("PRAGMA query_only=ON")
    chosen = {}
    remaining = [BUDGET]
    classes = {"ordinary": 0, "small": 0, "multi_alias": 0, "long_zh": 0, "d_source": 0, "medium": 0, "fill": 0, "closure": 0}
    examples = {}
    try:
        for volume, file_id, size in src.execute(
            """
            SELECT volume_serial, file_id, min_size FROM entities
            WHERE volume_serial='2387166462' AND path_count=1 AND COALESCE(d_paths,0)=0
              AND min_size>=1 AND min_size<=65536
            ORDER BY file_id LIMIT 20
            """
        ):
            if _add_choice(chosen, remaining, volume, file_id, size, "ordinary", 65536):
                classes["ordinary"] += 1
                examples["ordinary"] = {"volume_serial": volume, "file_id": file_id, "min_size": int(size)}
                break
        small_bytes = 0
        for volume, file_id, size in src.execute(
            """
            SELECT volume_serial, file_id, min_size FROM entities
            WHERE volume_serial='2387166462' AND path_count=1 AND min_size>=1 AND min_size<=4096
            ORDER BY min_size, file_id LIMIT 400
            """
        ):
            if classes["small"] >= 200 or small_bytes >= 2 * 1024 * 1024:
                break
            if _add_choice(chosen, remaining, volume, file_id, size, "small", 4096):
                classes["small"] += 1
                small_bytes += int(size)
        for volume, file_id, size, paths in src.execute(
            """
            SELECT volume_serial, file_id, min_size, path_count FROM entities
            WHERE volume_serial='2387166462' AND path_count>=2 AND path_count<=8
              AND min_size>=1 AND min_size<=1048576
            ORDER BY path_count DESC, file_id LIMIT 30
            """
        ):
            if _add_choice(chosen, remaining, volume, file_id, size, "multi_alias", 1048576):
                classes["multi_alias"] += 1
                examples["multi_alias"] = {"volume_serial": volume, "file_id": file_id, "path_count": int(paths), "min_size": int(size)}
                break
        for volume, file_id, size in src.execute(
            """
            SELECT volume_serial, file_id, min_size FROM entities
            WHERE volume_serial='3187598165' AND min_size>=1 AND min_size<=1048576
            ORDER BY file_id LIMIT 30
            """
        ):
            if _add_choice(chosen, remaining, volume, file_id, size, "d_source", 1048576):
                classes["d_source"] += 1
                examples["d_source"] = {"volume_serial": volume, "file_id": file_id, "min_size": int(size)}
                break
        for volume, file_id, size in src.execute(
            """
            SELECT volume_serial, file_id, min_size FROM entities
            WHERE min_size>1048576 AND min_size<=8388608
            ORDER BY volume_serial, file_id LIMIT 20
            """
        ):
            if _add_choice(chosen, remaining, volume, file_id, size, "medium", 8 * 1024 * 1024):
                classes["medium"] += 1
                examples["medium"] = {"volume_serial": volume, "file_id": file_id, "min_size": int(size)}
                break
        print("subset scan long chinese path", file=sys.stderr)
        seen = 0
        cur = src.execute(
            "SELECT path, volume_serial, file_id, logical_size FROM paths WHERE is_dir=0 AND is_reparse=0"
        )
        while classes["long_zh"] < 1:
            rows = cur.fetchmany(20000)
            if not rows:
                break
            for path, volume, file_id, size in rows:
                seen += 1
                if seen % 500000 == 0:
                    print(f"subset long scan {seen}", file=sys.stderr)
                if not _is_chinese_long(path):
                    continue
                if _add_choice(chosen, remaining, volume, file_id, size, "long_zh", 8 * 1024 * 1024):
                    classes["long_zh"] += 1
                    examples["long_zh"] = {"path_chars": len(path), "volume_serial": volume, "file_id": file_id, "min_size": int(size or 0)}
                    break
        print("subset fill", file=sys.stderr)
        for volume, file_id, size in src.execute(
            """
            SELECT volume_serial, file_id, min_size FROM entities
            WHERE min_size>=65536 AND min_size<=1048576
            ORDER BY volume_serial, file_id
            """
        ):
            if remaining[0] < 65536 or len(chosen) >= FILL_CAP:
                break
            if _add_choice(chosen, remaining, volume, file_id, size, "fill", 1048576):
                classes["fill"] += 1
        link_stats = {
            "included": 0,
            "included_ordinary": 0,
            "included_link_chain": 0,
            "excluded_large": 0,
            "excluded_budget": 0,
            "excluded_unmapped": 0,
            "excluded_type": 0,
            "excluded_link_not_closed": 0,
        }
        included_links = []
        link_dirs = {BENCH_PARENT}
        seen_link_paths = set()
        print("subset links", file=sys.stderr)

        def add_link(src_path, target_path, tag_value, file_count):
            key = str(src_path).casefold()
            if key in seen_link_paths:
                return
            seen_link_paths.add(key)
            included_links.append((src_path, target_path, int(tag_value), int(file_count)))
            link_stats["included"] += 1
            for parent in directory_chain(src_path, False):
                link_dirs.add(parent)

        for path, target, original, migrated_link, _migrated_target, tag, _content_files in src.execute(
            """
            SELECT path, target, original_target, migrated_link_path, migrated_target, reparse_tag, content_files
            FROM links ORDER BY path
            """
        ):
            inventory = None
            for item in (original, target):
                if item and (str(item).upper().startswith("E:\\BLACKBOX") or str(item).upper().startswith("D:\\")):
                    inventory = str(item)
                    break
            link_src = None
            for item in (path, migrated_link):
                if not item:
                    continue
                try:
                    link_src = _to_bench(str(item))
                    break
                except ValueError:
                    continue
            if inventory is None or link_src is None or tag is None:
                link_stats["excluded_unmapped"] += 1
                continue
            kind, _nxt = _target_kind(src, inventory)
            if kind == "ordinary":
                groups, too_big = _file_groups(src, inventory)
                if too_big:
                    link_stats["excluded_large"] += 1
                    continue
                extra = sum(size for key, size in groups.items() if key not in chosen and size > 0)
                if extra > remaining[0]:
                    link_stats["excluded_budget"] += 1
                    continue
                closed = True
                for key, size in groups.items():
                    if key in chosen:
                        continue
                    if not _add_choice(chosen, remaining, key[0], key[1], size, "closure", 8 * 1024 * 1024):
                        closed = False
                        break
                    classes["closure"] += 1
                if not closed or any(key not in chosen for key in groups):
                    link_stats["excluded_budget"] += 1
                    continue
                try:
                    bench_target = _to_bench(inventory)
                except ValueError:
                    link_stats["excluded_unmapped"] += 1
                    continue
                add_link(link_src, bench_target, tag, len(groups))
                link_dirs.update(directory_chain(bench_target, True))
                link_stats["included_ordinary"] += 1
                continue
            if kind != "link":
                link_stats["excluded_type"] += 1
                continue
            ordinary, chain, _reason = _resolve_ordinary(src, inventory)
            if ordinary is None:
                link_stats["excluded_link_not_closed"] += 1
                continue
            groups, too_big = _file_groups(src, ordinary)
            if too_big or any(key not in chosen for key in groups):
                link_stats["excluded_link_not_closed"] += 1
                continue
            try:
                bench_direct = _to_bench(inventory)
                bench_final = _to_bench(ordinary)
                hop_rows = []
                for hop_src, hop_dst in chain:
                    hop = src.execute(
                        "SELECT reparse_tag FROM links WHERE path=? OR migrated_link_path=? LIMIT 1",
                        (hop_src, hop_src),
                    ).fetchone()
                    hop_tag = int(hop[0]) if hop and hop[0] else int(tag)
                    hop_rows.append((_to_bench(hop_src), _to_bench(hop_dst), hop_tag, 0))
            except ValueError:
                link_stats["excluded_unmapped"] += 1
                continue
            add_link(link_src, bench_direct, tag, 0)
            for hop_src, hop_dst, hop_tag, hop_files in hop_rows:
                add_link(hop_src, hop_dst, hop_tag, hop_files)
            link_dirs.update(directory_chain(bench_final, True))
            link_stats["included_link_chain"] += 1
        print(f"subset materialize entities={len(chosen)}", file=sys.stderr)
        out_db = out_dir / "BENCH_SUBSET.sqlite"
        if out_db.exists():
            out_db.unlink()
        for suffix in ("-wal", "-shm", "-journal"):
            side = Path(str(out_db) + suffix)
            if side.exists():
                side.unlink()
        dst = sqlite3.connect(out_db)
        dst.execute("PRAGMA journal_mode=DELETE")
        dst.executescript(
            """
            CREATE TABLE entities(
              volume_serial TEXT, file_id TEXT, path_count INTEGER, min_size INTEGER,
              max_size INTEGER, max_nlinks INTEGER, d_paths INTEGER, delta_paths INTEGER
            );
            CREATE TABLE paths(
              path TEXT PRIMARY KEY, is_dir INTEGER, is_reparse INTEGER, logical_size INTEGER,
              alloc_size INTEGER, volume_serial TEXT, file_id TEXT, nlinks INTEGER,
              reparse_target TEXT, source TEXT
            );
            CREATE TABLE links(
              path TEXT PRIMARY KEY, target TEXT, source TEXT, mapped_dest TEXT, status TEXT,
              map_id INTEGER, original_target TEXT, migrated_link_path TEXT, migrated_target TEXT,
              map_source TEXT, content_files INTEGER, delta_files INTEGER, reparse_tag INTEGER, tag_source TEXT
            );
            """
        )
        dirs = {BENCH_PARENT}
        dropped = 0
        for (volume, file_id), meta in chosen.items():
            rows = list(src.execute(
                """
                SELECT path, logical_size, alloc_size, nlinks FROM paths
                WHERE is_dir=0 AND is_reparse=0 AND volume_serial=? AND file_id=?
                ORDER BY path
                """,
                (volume, file_id),
            ))
            mapped = []
            try:
                for row_path, logical, alloc, nlinks in rows:
                    mapped.append((_to_bench(row_path), int(logical or 0), int(alloc or 0), nlinks))
            except ValueError:
                dropped += 1
                continue
            if not mapped:
                dropped += 1
                continue
            d_paths = 1 if str(volume) == "3187598165" else 0
            dst.execute(
                "INSERT INTO entities VALUES (?,?,?,?,?,?,?,0)",
                (volume, file_id, len(mapped), meta["min_size"], meta["min_size"], len(mapped), d_paths),
            )
            for bench_path, logical, alloc, nlinks in mapped:
                dst.execute(
                    "INSERT OR REPLACE INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (bench_path, 0, 0, logical, alloc, volume, file_id, nlinks, None, "subset"),
                )
                current = bench_path
                while True:
                    parent = str(PureWindowsPath(current).parent)
                    if parent == current or len(parent) <= 3:
                        break
                    dirs.add(parent)
                    if parent.casefold() == BENCH_PARENT.casefold():
                        break
                    current = parent
        dirs.update(link_dirs)
        link_names = {item[0].casefold() for item in included_links}
        source_link_names = set(link_names)
        for (source_link,) in src.execute("SELECT path FROM links"):
            try:
                source_link_names.add(_to_bench(str(source_link)).casefold())
            except ValueError:
                continue
        for link_path, link_target, tag, files in included_links:
            dst.execute(
                "INSERT OR REPLACE INTO links VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (link_path, link_target, "subset", link_target, "OK", None, link_target, link_path, link_target, "subset", files, 0, tag, "plan"),
            )
        for directory in sorted(dirs, key=lambda item: (item.count("\\"), item.casefold())):
            if directory.casefold() in source_link_names:
                continue
            dst.execute(
                "INSERT OR IGNORE INTO paths VALUES (?,?,?,?,?,?,?,?,?,?)",
                (directory, 1, 0, 0, 0, None, None, 1, None, "subset_parent"),
            )
        dst.execute("CREATE INDEX ix_entity ON paths(is_dir, is_reparse, volume_serial, file_id)")
        dst.commit()
        stats = {
            "entities": dst.execute("SELECT COUNT(*) FROM entities").fetchone()[0],
            "unique_bytes": dst.execute("SELECT COALESCE(SUM(min_size),0) FROM entities").fetchone()[0],
            "file_paths": dst.execute("SELECT COUNT(*) FROM paths WHERE is_dir=0 AND is_reparse=0").fetchone()[0],
            "directories": dst.execute("SELECT COUNT(*) FROM paths WHERE is_dir=1 AND is_reparse=0").fetchone()[0],
            "links": dst.execute("SELECT COUNT(*) FROM links").fetchone()[0],
            "logical_path_bytes": dst.execute(
                "SELECT COALESCE(SUM(logical_size),0) FROM paths WHERE is_dir=0 AND is_reparse=0"
            ).fetchone()[0],
            "allocation_bytes": dst.execute(
                """
                SELECT COALESCE(SUM(alloc),0) FROM (
                  SELECT MAX(alloc_size) AS alloc FROM paths
                  WHERE is_dir=0 AND is_reparse=0
                  GROUP BY volume_serial, file_id
                )
                """
            ).fetchone()[0],
            "e_entities": dst.execute("SELECT COUNT(*) FROM entities WHERE volume_serial='2387166462'").fetchone()[0],
            "d_entities": dst.execute("SELECT COUNT(*) FROM entities WHERE volume_serial='3187598165'").fetchone()[0],
        }
        dst.close()
        d_roots = {}
        for (path,) in src.execute(
            "SELECT path FROM paths WHERE is_dir=0 AND is_reparse=0 AND path>='D:\\' AND path<'E:\\'"
        ):
            name = path[3:].split("\\", 1)[0]
            d_roots[name] = d_roots.get(name, 0) + 1
        e_outside = src.execute(
            """
            SELECT COUNT(*) FROM paths
            WHERE NOT (
              path='E:\\BLACKBOX' OR path LIKE 'E:\\BLACKBOX\\%'
              OR path>='D:\\' AND path<'E:\\'
            )
            """
        ).fetchone()[0]
    finally:
        src.close()
    assert_plan_stable(plan, snapshot)
    if Path(BENCH_PARENT).exists() != existed:
        raise RuntimeError("BENCH_DIRECTORY_CREATED")
    digest = sha256_file(out_db)
    gaps = [
        "Plan entities have no mtime column and no content hash. Formal copy records the source-handle mtime and the stream SHA from this run; it does not invent a historical value.",
        "E scope in the frozen plan is E:\\BLACKBOX. Paths outside E:\\BLACKBOX and D:\\ are counted in e_outside.",
        "Selected D roots below are the D:\\ first folders present in the frozen plan. They are not proof that the whole D: disk is unchanged or complete.",
        "Files created, deleted, or rewritten on the source after the frozen plan are outside this subset. SOURCE_CHANGED, short read, unknown target, and acceptance failure stop at that phase.",
        "This round does not stop source processes and does not rescan either disk.",
        "Two copied samples do not stand in for the full plan. Full-plan acceptance stays false until a FULL contract is authorized and the run accepts the frozen plan.",
        "Junctions whose targets contain more than 16 files, or whose missing files do not fit the remaining byte budget, are excluded. A whole release is not copied just to close a link.",
    ]
    manifest = {
        "task_id": "R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014_1616",
        "source_plan": str(plan),
        "source_plan_sha": source_sha,
        "subset": str(out_db),
        "subset_sha": digest,
        "budget_bytes": BUDGET,
        "unique_bytes": int(stats["unique_bytes"]),
        "stopped_by": "BUDGET" if remaining[0] < 65536 else "ENTITY_CAP" if len(chosen) >= FILL_CAP else "SCAN_END",
        "classes": classes,
        "examples": examples,
        "links": link_stats,
        "stats": {key: int(value) for key, value in stats.items()},
        "dropped_entities": dropped,
        "d_roots": [{"name": name, "file_paths": count} for name, count in sorted(d_roots.items())],
        "e_scope": "E:\\BLACKBOX",
        "e_outside_paths": int(e_outside or 0),
        "dest_roots_not_created": [BENCH_E, BENCH_D],
        "dest_existed_before": existed,
        "selection_rules": [
            "One ordinary E file, path_count=1, size 1..65536, lowest file_id text.",
            "Up to 200 E files of 1..4096 bytes, or 2MiB, ordered by size then file_id.",
            "One E multi-alias entity with path_count 2..8 and size <=1MiB.",
            "One Chinese path of at least 240 characters whose entity is <=8MiB.",
            "One D-volume entity size <=1MiB, lowest file_id text.",
            "One medium entity of 1MiB..8MiB.",
            "Fill with entities of 64KiB..1MiB in (volume_serial, file_id) order until 1GiB or 8000 entities.",
            "A link whose source target is an ordinary directory is included only when that directory has at most 16 file paths and any missing bytes fit. The directory itself and its parents are written.",
            "A link whose source target is another link is included only when the chain reaches an ordinary directory without adding file bytes. Otherwise it is excluded. Unknown or file targets are excluded and are not invented as directories.",
            "Link paths are not also recorded as ordinary directories.",
            "Destinations are E:\\R9_FORMAL_PILOT_1G_20261014\\BLACKBOX and \\BLACKBOX_ENGINES. This builder does not create them.",
        ],
        "gaps": gaps,
        "bench_measured": False,
    }
    (out_dir / "SUBSET_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"subset sha {digest} bytes {stats['unique_bytes']}", file=sys.stderr)
    return manifest


class ReadOnlyGuard:
    """Blocks destination writes. Enumeration, observe and content hash stay available."""

    def __init__(self, inner):
        self.inner = inner
        self.sc = inner.sc
        self.write_attempts = 0

    def observe_destination(self, path):
        return self.inner.observe_destination(path)

    def list_nofollow(self, root):
        return self.inner.list_nofollow(root)

    def content_sha(self, path):
        return self.inner.content_sha(path)

    def _refuse(self, *_args, **_kwargs):
        self.write_attempts += 1
        raise RuntimeError("READONLY_WRITE_REFUSED")

    ensure_directory = _refuse
    copy_entity = _refuse
    hardlink = _refuse
    create_reparse = _refuse


def readonly_reverify(contract: dict, backend=None) -> dict:
    """Re-read an existing bench. Does not call production_run and does not write E:."""
    from r9_acceptance import full_acceptance
    from r9_winio import Win32Syscalls, WindowsBackend

    historical = dict(contract["run"])
    plan = Path(contract["plan_path"])
    state = Path(contract["state_path"])
    source = Path(contract["source_plan_path"])
    plan_sha = sha256_file(plan)
    if plan_sha != contract.get("plan_sha") or plan_sha != historical.get("plan_digest"):
        return {"bench_verified": False, "reason": "PLAN_DIGEST_MISMATCH", "write_attempts": 0}
    if sha256_file(source) != contract.get("source_plan_sha"):
        return {"bench_verified": False, "reason": "SOURCE_PLAN_MISMATCH", "write_attempts": 0}
    keys = ("run_id", "plan_digest", "inputs_digest", "code_digest", "dest_volume", "dest_root")
    ro = sqlite3.connect(f"file:{state.resolve().as_posix()}?mode=ro", uri=True)
    try:
        row = ro.execute(
            "SELECT run_id, plan_digest, inputs_digest, code_digest, dest_volume, dest_root FROM run_bind"
        ).fetchone()
    finally:
        ro.close()
    if row is None or tuple(row) != tuple(historical[key] for key in keys):
        return {"bench_verified": False, "reason": "RUN_BINDING_MISMATCH", "write_attempts": 0}
    check_run = dict(historical)
    check_run["readonly_reverify"] = True
    check_run["copy_code_digest"] = historical["code_digest"]
    inner = backend if backend is not None else WindowsBackend(Win32Syscalls())
    guard = ReadOnlyGuard(inner)
    started = time.perf_counter()
    acceptance = full_acceptance(plan, state, guard, check_run)
    elapsed = time.perf_counter() - started
    limits = contract.get("limits") or {}
    verified = acceptance.get("full_acceptance") is True and guard.write_attempts == 0 and acceptance.get("missing") == 0 and acceptance.get("extra") == 0
    if limits.get("entities"):
        verified = verified and acceptance.get("content_hash_calls") == int(limits["entities"]) and acceptance.get("content_bytes") == int(limits["unique_bytes"])
    return {
        "bench_verified": bool(verified),
        "full_plan_acceptance": False,
        "write_attempts": guard.write_attempts,
        "accept_seconds": elapsed,
        "acceptance": acceptance,
        "copy_code_digest": historical["code_digest"],
        "verifier_code_digest": source_contract.code_digest(),
        "program_bench_measured": False,
        "reason": "BENCH_VERIFIED" if verified else "REVERIFY_FAILED",
    }
