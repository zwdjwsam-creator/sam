# -*- coding: utf-8 -*-
"""Verify R9LP_RO and read the four previously failing files. No writes."""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
from r9_pilot_common_r9fix import open_source_stable, handle_identity, CloseHandle, read_exact_hash, to_win_long_path

OUT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_LONGPATH_ACCESS_AND_RESUME_PREP_20261019")
PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\FINAL_CANDIDATE.sqlite")
facts = json.loads((OUT / "DEEP_SHARE_FACTS.json").read_text(encoding="utf-8"))
local = json.loads((OUT / "LOCAL_FILE_844424930324643.json").read_text(encoding="utf-8"))
ANCHOR = facts["path"]
UNC = r"\\192.168.100.2\R9LP_RO"
EXPECTED = {
    "844424930324628": 1166,
    "844424930324634": 9095,
    "844424930324640": 558,
    "844424930324643": 816,
}


def open_ident(path):
    handle = open_source_stable(path)
    try:
        return handle, handle_identity(handle)
    except Exception:
        CloseHandle(handle)
        raise


root_handle, root_ident = open_ident(UNC)
CloseHandle(root_handle)
root = {
    "volume": root_ident["volume_serial"],
    "file_id": root_ident["file_id"],
    "size": root_ident["size"],
    "volume_match": root_ident["volume_serial"] == str(facts["root_identity"]["volume_serial"]),
    "file_id_match": root_ident["file_id"] == str(facts["root_identity"]["file_id"]),
}
if not (root["volume_match"] and root["file_id_match"]):
    report = {"anchor_ok": False, "root": root}
    (OUT / "DEEP_SHARE_READ_PROOF.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ANCHOR_MISMATCH")
    raise SystemExit(0)

plan = sqlite3.connect(f"file:{PLAN.resolve().as_posix()}?mode=ro", uri=True)
results = []
for file_id, size in EXPECTED.items():
    row = plan.execute(
        "SELECT path, logical_size, volume_serial FROM paths WHERE volume_serial=? AND file_id=? AND is_dir=0 AND is_reparse=0",
        ("2387166462", file_id),
    ).fetchone()
    item = {"file_id": file_id, "plan_size": size}
    if row is None or int(row[1]) != size:
        item["ok"] = False
        item["stage"] = "plan_lookup"
        results.append(item)
        continue
    inventory = row[0]
    if not inventory.startswith(ANCHOR + "\\"):
        item["ok"] = False
        item["stage"] = "anchor_prefix"
        results.append(item)
        continue
    tail = inventory[len(ANCHOR) + 1:]
    if tail.startswith("\\") or ".." in tail.split("\\") or ":" in tail:
        item["ok"] = False
        item["stage"] = "tail_rejected"
        results.append(item)
        continue
    access = UNC + "\\" + tail
    item["access_api_chars"] = len(to_win_long_path(access))
    item["saved_vs_old_unc"] = None
    try:
        handle, before = open_ident(access)
    except OSError as exc:
        item["ok"] = False
        item["stage"] = "open"
        item["errno"] = exc.errno
        item["message_has_206"] = "winerror=206" in str(exc)
        results.append(item)
        continue
    try:
        _unused, digest = read_exact_hash(handle, size)
        after = handle_identity(handle)
    finally:
        CloseHandle(handle)
    item.update({
        "ok": True,
        "volume": before["volume_serial"],
        "file_id_observed": before["file_id"],
        "size": before["size"],
        "sha256": digest,
        "identity_stable": before["file_id"] == after["file_id"] and before["size"] == after["size"],
        "matches_plan": before["volume_serial"] == "2387166462" and before["file_id"] == file_id and before["size"] == size,
    })
    if file_id == "844424930324643":
        item["matches_sam_sha"] = digest == local["sha256"]
    results.append(item)
    print(file_id, item["ok"], item.get("matches_plan"), item.get("matches_sam_sha"), item.get("access_api_chars"), item.get("sha256"))
plan.close()
report = {"anchor_ok": True, "root": root, "files": results, "all_ok": all(x.get("ok") and x.get("matches_plan") for x in results)}
(OUT / "DEEP_SHARE_READ_PROOF.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("ALL", report["all_ok"])
