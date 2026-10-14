# -*- coding: utf-8 -*-
"""Build a C-only candidate plan. The frozen plan is opened read-only and copied first."""
import hashlib
import json
import shutil
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_CORRECT_FULL_LINK_RESOLUTION_READONLY_20261014")
import r9_plan_reader as reader
import r9_source_contract as source_contract
from link_resolve import Graph

PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite")
ROOT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_DESTINATION_LINK_REPAIR_PLAN_20261014")
JSONL = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_CORRECT_FULL_LINK_RESOLUTION_READONLY_20261014\LINK_RESOLUTION.jsonl")
CANDIDATE = ROOT / "CANDIDATE_PLAN.sqlite"
EXPECTED_PLAN = "94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba"
EXPECTED_JSONL = "03318d69ce1db041b34c314e3c2b8244df6fa92efe8341916e7162386c45ef82"
BROKEN = r"E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_ADJFACTOR_PIT_CLEAN_ASOF_20260814_20260816_044000\CURRENT_POINTER_COPY.json"
GOOD = r"E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_ADJFACTOR_PIT_ASOF_20260814_20260816_034243\CURRENT_POINTER_COPY.json"
DYNAMIC_NAMES = {"CURRENT", "LATEST", "HEAD", "ACTIVE", "LIVE", "TIP"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(8 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def role(link_path: str, chain_length: int) -> tuple[str, str]:
    name = str(link_path).rsplit("\\", 1)[-1].upper()
    if name in DYNAMIC_NAMES or name.startswith("CURRENT_") or name.startswith("LATEST_"):
        return "DYNAMIC_KEEP", "link name is a publish head; keep the indirect edge"
    if chain_length <= 1:
        return "ALREADY_DIRECT", "target is already the ordinary directory"
    upper = link_path.upper()
    if "ASOF" in upper or "RELEASE" in upper or "PIT_" in upper:
        return "HISTORICAL_SHORTEN", "dated or release-internal directory link; point at the resolved directory"
    return "UNKNOWN_DYNAMIC_KEEP", "role is not clearly historical; keep the original edge"


def main():
    jsonl_sha = sha256_file(JSONL)
    plan_before = sha256_file(PLAN)
    code_before = source_contract.code_digest()
    if jsonl_sha != EXPECTED_JSONL or plan_before != EXPECTED_PLAN:
        raise SystemExit("INPUT_SHA")
    overlay = []
    kept = []
    for line in JSONL.open(encoding="utf-8"):
        row = json.loads(line)
        if row["class"] != "CLOSED_DIRECTORY":
            continue
        action, basis = role(row["link_path"], int(row["chain_length"]))
        item = {
            "dest_link": row["link_path"],
            "original_target": row["target"],
            "terminal": row["terminal"],
            "chain_length": row["chain_length"],
            "action": action,
            "basis": basis,
        }
        if action == "HISTORICAL_SHORTEN":
            overlay.append(item)
        else:
            kept.append(item)
    (ROOT / "DEST_DIRECTORY_LINK_OVERLAY.json").write_text(
        json.dumps(overlay, ensure_ascii=False), encoding="utf-8"
    )
    (ROOT / "KEPT_DIRECTORY_LINKS.json").write_text(
        json.dumps({"count": len(kept), "dynamic": sum(1 for item in kept if item["action"] == "DYNAMIC_KEEP"), "unknown": [item for item in kept if item["action"] == "UNKNOWN_DYNAMIC_KEEP"], "already_direct": sum(1 for item in kept if item["action"] == "ALREADY_DIRECT")}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if any(item["action"] == "UNKNOWN_DYNAMIC_KEEP" for item in kept):
        raise SystemExit("UNKNOWN_DYNAMIC")
    src = sqlite3.connect(f"file:{PLAN.resolve().as_posix()}?mode=ro", uri=True)
    good = src.execute(
        "SELECT is_dir, is_reparse, logical_size, volume_serial, file_id, nlinks, alloc_size, source FROM paths WHERE path=?",
        (GOOD,),
    ).fetchone()
    broken_path = src.execute(
        "SELECT is_dir, is_reparse FROM paths WHERE path=?",
        (BROKEN,),
    ).fetchone()
    broken_link = src.execute("SELECT path, target FROM links WHERE path=?", (BROKEN,)).fetchone()
    if not good or int(good[0]) != 0 or int(good[1]) != 0 or not broken_link:
        src.close()
        raise SystemExit("JSON_POINTER_NOT_READY")
    entity = src.execute(
        "SELECT path_count, min_size, max_size FROM entities WHERE volume_serial=? AND file_id=?",
        (good[3], good[4]),
    ).fetchone()
    src.close()
    if CANDIDATE.exists():
        CANDIDATE.unlink()
    shutil.copy2(PLAN, CANDIDATE)
    if sha256_file(PLAN) != plan_before:
        raise SystemExit("ORIGINAL_PLAN_CHANGED")
    dst = sqlite3.connect(CANDIDATE)
    changed = 0
    for item in overlay:
        cur = dst.execute(
            "UPDATE links SET migrated_target=?, mapped_dest=? WHERE COALESCE(migrated_link_path, path)=?",
            (item["terminal"], item["terminal"], item["dest_link"]),
        )
        changed += cur.rowcount
    dst.execute("DELETE FROM links WHERE path=?", (BROKEN,))
    if broken_path is None:
        dst.execute(
            """
            INSERT INTO paths(path, is_dir, is_reparse, logical_size, alloc_size, volume_serial, file_id, nlinks, reparse_target, source)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (BROKEN, 0, 0, good[2], good[6], good[3], good[4], good[5], None, "dest_repair_alias"),
        )
    else:
        dst.execute(
            """
            UPDATE paths SET is_dir=0, is_reparse=0, logical_size=?, alloc_size=?, volume_serial=?, file_id=?, nlinks=?, reparse_target=NULL, source='dest_repair_alias'
            WHERE path=?
            """,
            (good[2], good[6], good[3], good[4], good[5], BROKEN),
        )
    dst.execute(
        "UPDATE entities SET path_count=path_count+1 WHERE volume_serial=? AND file_id=?",
        (good[3], good[4]),
    )
    dst.commit()
    dst.close()
    for extra in (Path(str(CANDIDATE) + "-wal"), Path(str(CANDIDATE) + "-journal")):
        if extra.exists() and extra.stat().st_size:
            raise SystemExit("CANDIDATE_NOT_FROZEN")
    manifest = {
        "good_path": GOOD,
        "broken_link": BROKEN,
        "volume_serial": good[3],
        "file_id": good[4],
        "logical_size": good[2],
        "original_path_count": entity[0],
        "overlay_applied": changed,
        "winerror": 267,
        "conversion": "destination hardlink alias of the existing file entity; source reparse metadata stays in the frozen plan and this manifest",
    }
    (ROOT / "JSON_POINTER_REPAIR.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("overlay", len(overlay), "applied", changed, "candidate", sha256_file(CANDIDATE))


if __name__ == "__main__":
    main()
