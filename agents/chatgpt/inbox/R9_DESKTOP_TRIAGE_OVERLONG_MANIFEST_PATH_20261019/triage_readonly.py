# -*- coding: utf-8 -*-
"""Readonly triage for the 2026-10-19 WinError 206 stop. Does not write the plan or state."""
import hashlib
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

DEV = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
sys.path.insert(0, str(DEV))
from r9_pilot_common_r9fix import open_source_stable, handle_identity, CloseHandle, to_win_long_path
from r9_plan_reader import E_ROOT, E_UNC, map_inventory_path
from r9_source_contract import code_digest

OUT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_TRIAGE_OVERLONG_MANIFEST_PATH_20261019")
PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\FINAL_CANDIDATE.sqlite")
STATE = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_MISSING_DEST_ROOT_20261015\state\full_1400.sqlite")
FAILED = (OUT / "failed_source_path.txt").read_text(encoding="utf-8")
LIMIT = 32767
NOW = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def api_len(path: str) -> int:
    return len(to_win_long_path(path))


def parts_of(path: str):
    return [part for part in path.split("\\") if part]


def measure(path: str) -> dict:
    parts = parts_of(path)
    return {
        "python_chars": len(path),
        "utf16_code_units": len(path.encode("utf-16-le")) // 2,
        "api_chars": api_len(path),
        "components": len(parts),
        "max_component": max((len(part) for part in parts), default=0),
    }


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bounded(path: str) -> dict:
    text = str(path)
    return {
        "sha256": sha(text),
        "python_chars": len(text),
        "head": text[:160],
        "tail": text[-160:],
    }


def main() -> None:
    started = time.perf_counter()
    if not FAILED.startswith("\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\"):
        raise SystemExit("FAIL unexpected failed path prefix")
    rel = FAILED[len(E_UNC):].lstrip("\\")
    inventory = E_ROOT if not rel else E_ROOT + "\\" + rel
    mapped = map_inventory_path(inventory)
    if mapped["source_path"] != FAILED:
        raise SystemExit("FAIL mapped source does not equal the logged path")

    plan = sqlite3.connect(f"file:{PLAN.resolve().as_posix()}?mode=ro", uri=True)
    plan.row_factory = sqlite3.Row
    row = plan.execute(
        "SELECT path, is_dir, is_reparse, logical_size, volume_serial, file_id, nlinks, reparse_target, source FROM paths WHERE path=?",
        (inventory,),
    ).fetchone()
    if row is None:
        raise SystemExit("FAIL inventory path not in candidate")
    volume = row["volume_serial"]
    file_id = row["file_id"]
    siblings = plan.execute(
        "SELECT path, is_dir, is_reparse, logical_size, nlinks, reparse_target FROM paths WHERE volume_serial=? AND file_id=? ORDER BY path",
        (volume, file_id),
    ).fetchall()
    path_rows = []
    for item in siblings:
        one = map_inventory_path(item["path"])
        path_rows.append({
            "inventory": measure(item["path"]),
            "source": measure(one["source_path"]),
            "dest": measure(one["dest_path"]),
            "source_share": one["source_share"],
            "is_dir": item["is_dir"],
            "is_reparse": item["is_reparse"],
            "logical_size": item["logical_size"],
            "nlinks": item["nlinks"],
            "reparse_target_chars": len(item["reparse_target"] or ""),
            "sample": bounded(item["path"]),
            "sorts_first": item["path"] == inventory,
        })
    path_rows.sort(key=lambda item: item["source"]["api_chars"])
    short = next((item for item in path_rows if item["source"]["api_chars"] <= LIMIT and item["is_reparse"] == 0 and item["is_dir"] == 0), None)

    # Key ancestors only: file parent, first nested backup directory, and the directory one repeat deeper.
    marker = "\\manifest_backup\\"
    first = inventory.find(marker)
    ancestors = []
    if first >= 0:
        ancestors.append(inventory[:first])
        ancestors.append(inventory[: first + len(marker) - 1])
        second = inventory.find(marker, first + len(marker))
        if second >= 0:
            ancestors.append(inventory[:second])
            ancestors.append(inventory[: second + len(marker) - 1])
    ancestors.append(inventory.rsplit("\\", 1)[0])
    ancestor_facts = []
    seen = set()
    for ancestor in ancestors:
        if ancestor in seen:
            continue
        seen.add(ancestor)
        found = plan.execute(
            "SELECT path, is_dir, is_reparse, logical_size, reparse_target FROM paths WHERE path=?",
            (ancestor,),
        ).fetchone()
        ancestor_facts.append({
            "sample": bounded(ancestor),
            "in_plan": found is not None,
            "is_dir": None if found is None else found["is_dir"],
            "is_reparse": None if found is None else found["is_reparse"],
            "reparse_target_chars": 0 if found is None or not found["reparse_target"] else len(found["reparse_target"]),
            "reparse_target_sample": None if found is None or not found["reparse_target"] else bounded(found["reparse_target"]),
            "measures": measure(ancestor),
        })

    link = plan.execute(
        "SELECT path, target, status, reparse_tag, mapped_dest FROM links WHERE path=?",
        (inventory,),
    ).fetchone()

    # One streaming pass. No DDL.
    scope_started = time.perf_counter()
    file_entities = {}
    dir_over = 0
    dir_component_over = 0
    dir_seen = 0
    file_rows = 0
    samples = []
    for path, is_dir, is_reparse, logical_size, vol, fid in plan.execute(
        "SELECT path, is_dir, is_reparse, logical_size, volume_serial, file_id FROM paths"
    ):
        try:
            one = map_inventory_path(path)
        except ValueError:
            continue
        source_api = api_len(one["source_path"])
        dest_api = api_len(one["dest_path"])
        source_max_component = max((len(part) for part in parts_of(one["source_path"])), default=0)
        over_source = source_api > LIMIT
        over_dest = dest_api > LIMIT
        over_component = source_max_component > 255
        if is_dir:
            dir_seen += 1
            if over_source or over_dest:
                dir_over += 1
            if over_component:
                dir_component_over += 1
            continue
        if is_reparse:
            continue
        file_rows += 1
        key = (vol, fid)
        slot = file_entities.get(key)
        if slot is None:
            slot = {
                "min_source": source_api,
                "max_source": source_api,
                "min_dest": dest_api,
                "max_dest": dest_api,
                "paths": 1,
                "size": logical_size or 0,
            }
            file_entities[key] = slot
        else:
            slot["min_source"] = min(slot["min_source"], source_api)
            slot["max_source"] = max(slot["max_source"], source_api)
            slot["min_dest"] = min(slot["min_dest"], dest_api)
            slot["max_dest"] = max(slot["max_dest"], dest_api)
            slot["paths"] += 1
        if (over_source or over_dest or over_component) and len(samples) < 10:
            samples.append({
                "sample": bounded(path),
                "source_api": source_api,
                "dest_api": dest_api,
                "max_component": source_max_component,
                "logical_size": logical_size,
            })
    over_entities = 0
    over_bytes = 0
    short_alias_entities = 0
    source_only = 0
    dest_only = 0
    both = 0
    no_short_source = 0
    for slot in file_entities.values():
        source_over = slot["max_source"] > LIMIT
        dest_over = slot["max_dest"] > LIMIT
        if not source_over and not dest_over:
            continue
        over_entities += 1
        over_bytes += slot["size"]
        if source_over and dest_over:
            both += 1
        elif source_over:
            source_only += 1
        else:
            dest_only += 1
        if slot["min_source"] <= LIMIT:
            short_alias_entities += 1
        else:
            no_short_source += 1
    scope_seconds = round(time.perf_counter() - scope_started, 3)
    plan.close()

    state = sqlite3.connect(f"file:{STATE.resolve().as_posix()}?mode=ro", uri=True)
    state.row_factory = sqlite3.Row
    phases = [
        {"kind": kind, "phase": phase, "count": count}
        for kind, phase, count in state.execute("SELECT kind, phase, COUNT(*) FROM stage GROUP BY kind, phase ORDER BY kind, phase")
    ]
    entity_bytes = state.execute("SELECT COALESCE(SUM(logical_size),0) FROM stage WHERE kind='entity' AND phase='DONE'").fetchone()[0]
    entity_done = state.execute("SELECT COUNT(*) FROM stage WHERE kind='entity' AND phase='DONE'").fetchone()[0]
    intent = state.execute("SELECT COUNT(*) FROM stage WHERE phase!='DONE'").fetchone()[0]
    bind = dict(state.execute("SELECT run_id, plan_digest, inputs_digest, code_digest, dest_volume, dest_root FROM run_bind").fetchone())
    stage_hits = [
        {
            "kind": item["kind"],
            "phase": item["phase"],
            "logical_size": item["logical_size"],
            "dest": bounded(item["dest_path"] or ""),
        }
        for item in state.execute(
            "SELECT kind, phase, logical_size, dest_path FROM stage WHERE volume_serial=? AND file_id=?",
            (volume, file_id),
        )
    ]
    state.close()

    opened = {"attempted": False, "same_entity": False}
    if short is not None:
        short_source = None
        for item in siblings:
            one = map_inventory_path(item["path"])
            if api_len(one["source_path"]) == short["source"]["api_chars"] and item["is_reparse"] == 0 and item["is_dir"] == 0:
                short_source = one["source_path"]
                break
        opened["attempted"] = short_source is not None
        opened["source_api_chars"] = None if short_source is None else api_len(short_source)
        if short_source is not None:
            try:
                handle = open_source_stable(short_source)
            except OSError as exc:
                opened["open_winerror"] = exc.winerror
                opened["same_entity"] = False
            else:
                try:
                    identity = handle_identity(handle)
                finally:
                    CloseHandle(handle)
                opened["volume_match"] = str(identity.get("volume_serial")) == str(volume)
                opened["file_id_match"] = str(identity.get("file_id")) == str(file_id)
                opened["size_match"] = int(identity.get("size")) == int(row["logical_size"])
                opened["same_entity"] = opened["volume_match"] and opened["file_id_match"] and opened["size_match"]
                opened["observed_size"] = int(identity.get("size"))

    digest = code_digest(DEV)
    facts = {
        "queried_at": NOW,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "measurement": {
            "logged_source_path": measure(FAILED),
            "api_path_after_to_win_long_path": measure(to_win_long_path(FAILED))["api_chars"],
            "manifest_backup_count": FAILED.count("manifest_backup"),
            "threshold_utf16": LIMIT,
            "why_33770": "33770 was the character count after the GBK result log was decoded as UTF-8 with replacement. It is not the source path length. The same log decoded as GBK gives 32759.",
            "why_336": "Count of the substring manifest_backup inside the GBK-decoded source_path argument.",
            "json_file_bytes": 75321,
            "json_encoding": "gbk",
            "json_is_not_the_path_length": True,
            "path_sha256": sha(FAILED),
            "prefix": FAILED[:120],
            "suffix": FAILED[-180:],
            "call": "open_source_stable(source_path) -> CreateFileW(to_win_long_path(source_path)). The exception text uses the pre-extension path.",
            "not_alias_create": True,
            "not_readback_temp": True,
            "not_hash_call": True,
        },
        "entity": {
            "entity_key": f"{volume}|{file_id}",
            "volume_serial": volume,
            "file_id": file_id,
            "logical_size": row["logical_size"],
            "nlinks": row["nlinks"],
            "is_dir": row["is_dir"],
            "is_reparse": row["is_reparse"],
            "path_count_in_plan_row": len(siblings),
            "representative_is_logged_path": siblings[0]["path"] == inventory,
            "representative_rule": "ORDER BY path, first inventory path, then map_inventory_path",
            "paths": path_rows,
        },
        "link_row": None if link is None else {
            "status": link["status"],
            "reparse_tag": link["reparse_tag"],
            "target": bounded(link["target"] or ""),
            "mapped_dest": bounded(link["mapped_dest"] or ""),
        },
        "ancestors": ancestor_facts,
        "stage_rows_for_entity": stage_hits,
        "short_open": opened,
        "code_digest": digest,
        "expected_digest": "62aff763e4c12d782039e067ea12985e36d2164af41564453249774c89d84ae3",
        "digest_matches_resume": digest == "62aff763e4c12d782039e067ea12985e36d2164af41564453249774c89d84ae3",
    }
    scope = {
        "queried_at": NOW,
        "scope_seconds": scope_seconds,
        "threshold": "CreateFileW/CreateDirectoryW extended path fails when the UTF-16 API string length exceeds 32767. Component limit checked separately at 255. A \\\\?\\ prefix cannot repair either overflow.",
        "directory_rows_seen": dir_seen,
        "directory_rows_over_api_limit": dir_over,
        "directory_rows_component_over_255": dir_component_over,
        "file_rows_seen": file_rows,
        "file_entities": len(file_entities),
        "file_entities_over_api_limit": over_entities,
        "unique_bytes_of_over_entities": over_bytes,
        "entities_with_a_source_alias_within_limit": short_alias_entities,
        "entities_with_no_source_alias_within_limit": no_short_source,
        "source_over_only": source_only,
        "dest_over_only": dest_only,
        "source_and_dest_over": both,
        "samples": samples,
    }
    state_summary = {
        "queried_at": NOW,
        "run_bind": bind,
        "phases": phases,
        "entity_done": entity_done,
        "entity_done_logical_bytes": entity_bytes,
        "planned_entities": 1223767,
        "remaining_entities": 1223767 - entity_done,
        "non_done_stage_rows": intent,
        "stream_write_bytes_from_result_json": 348928107919,
        "note": "entity_done_logical_bytes is the sum of DONE entity logical_size in state. stream_write_bytes includes bytes written during copy and is not the same figure.",
    }
    (OUT / "FAILED_ENTITY_FACTS.json").write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "OVERLONG_SCOPE_SUMMARY.json").write_text(json.dumps(scope, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "STATE_PRESERVATION_SUMMARY.json").write_text(json.dumps(state_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", facts["elapsed_seconds"], "over_entities", over_entities, "digest_ok", facts["digest_matches_resume"])


if __name__ == "__main__":
    main()
