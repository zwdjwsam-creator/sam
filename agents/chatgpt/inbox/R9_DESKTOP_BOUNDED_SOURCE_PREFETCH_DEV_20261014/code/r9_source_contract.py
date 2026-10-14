# -*- coding: utf-8 -*-
"""Bound source facts. Does not modify the fact files or the frozen input databases."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

MOUNT_POINT_TAG = 0xA0000003
D_VOLUME = 3187598165
E_UNC_ROOT = "\\\\192.168.100.2\\E_DRIVE\\BLACKBOX"
D_UNC_ROOT = "\\\\192.168.100.2\\D_DRIVE"
CODE_FILES = (
    "r9_acceptance.py",
    "r9_adapter.py",
    "r9_bounded_pilot.py",
    "r9_capability_pilot.py",
    "r9_copy_body.py",
    "r9_formal_chain.py",
    "r9_formal_executor.py",
    "r9_pilot_common_r9fix.py",
    "r9_plan_reader.py",
    "r9_runner.py",
    "r9_scheduler.py",
    "r9_source_contract.py",
    "r9_source_prefetch.py",
    "r9_state.py",
    "r9_winio.py",
)


def code_digest(root: Path | None = None) -> str:
    base = root or Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for name in CODE_FILES:
        path = base / name
        if not path.is_file():
            raise RuntimeError(f"CODE_MODULE_MISSING:{name}")
        data = path.read_bytes()
        digest.update(name.encode("utf-8"))
        digest.update(len(data).to_bytes(8, "little"))
        digest.update(data)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_bytes().decode("utf-8"))


def share_contract(facts: dict) -> dict:
    shares = {item["Name"]: item["Path"] for item in facts.get("shares_relevant", [])}
    if shares.get("E_DRIVE") != "E:\\":
        raise RuntimeError("E_DRIVE_ROOT_MISMATCH")
    if "D_DRIVE" not in shares:
        raise RuntimeError("D_DRIVE_NOT_PRESENT")
    if shares.get("D_DRIVE") != "D:\\":
        raise RuntimeError("D_DRIVE_ROOT_MISMATCH")
    chosen = "D_DRIVE"
    return {
        "e_unc_root": E_UNC_ROOT,
        "d_unc_root": D_UNC_ROOT,
        "e_share": "E_DRIVE",
        "d_share": chosen,
        "e_drive_field_is_blackbox_name": facts.get("E_DRIVE_share", {}).get("Name") == "BLACKBOX",
        "desktop_smb_access_verified": False,
    }


def _norm(path: str) -> str:
    return str(path).replace("/", "\\").rstrip("\\").casefold()


def validate_overlay(payload: dict) -> list[dict]:
    records = payload.get("records") or []
    if len(records) != 16:
        raise RuntimeError("OVERLAY_COUNT")
    if payload.get("stats", {}).get("errors") not in (0, None) and payload["stats"].get("errors") != 0:
        raise RuntimeError("OVERLAY_ERRORS")
    if payload.get("stats", {}).get("ok") != 16:
        raise RuntimeError("OVERLAY_NOT_OK")
    seen = set()
    rows = []
    for record in records:
        map_id = int(record["map_id"])
        if map_id in seen or not 25 <= map_id <= 40:
            raise RuntimeError("OVERLAY_MAP_CONFLICT")
        seen.add(map_id)
        if int(record["reparse_tag"]) != MOUNT_POINT_TAG:
            raise RuntimeError("OVERLAY_TAG")
        if record.get("status") != "OK" or record.get("errors"):
            raise RuntimeError("OVERLAY_STATUS")
        if int(record["source_volume_serial"]) != D_VOLUME:
            raise RuntimeError("OVERLAY_VOLUME")
        if record.get("matches_map") is not True:
            raise RuntimeError("OVERLAY_MAP_MISMATCH")
        target = str(record.get("expected_target") or "")
        resolved = str(record.get("final_resolved_target_map") or record.get("normalized_target") or "")
        if _norm(target) != _norm(resolved):
            raise RuntimeError("OVERLAY_TARGET_CONFLICT")
        if not _norm(target).startswith("e:\\blackbox"):
            raise RuntimeError("OVERLAY_TARGET_SCOPE")
        source = str(record["source_path"])
        if not source.upper().startswith("D:\\"):
            raise RuntimeError("OVERLAY_SOURCE_SCOPE")
        rows.append({
            "map_id": map_id,
            "source_path": source,
            "target": target,
            "reparse_tag": MOUNT_POINT_TAG,
            "kind": "junction",
        })
    if seen != set(range(25, 41)):
        raise RuntimeError("OVERLAY_MAP_MISSING")
    return rows
