# -*- coding: utf-8 -*-
"""Map only the verified anchor onto the fixed R9LP_RO share."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

FACTS_PATH = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_LONGPATH_ACCESS_AND_RESUME_PREP_20261019\DEEP_SHARE_FACTS.json")
ALIAS_UNC = "\\\\192.168.100.2\\R9LP_RO"
EXPECTED_VOLUME = "2387166462"
EXPECTED_FILE_ID = "1688849860437540"
FACTS_CONTENT_SHA256 = "58c8c4f088f41b4d020d1fd73edf0494558212d207f8e14a9496626d9e62f5b7"
FILE_ATTRIBUTE_DIRECTORY = 0x10


def load_facts() -> dict:
    raw = FACTS_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != FACTS_CONTENT_SHA256:
        raise RuntimeError("ACCESS_ALIAS_FACTS_HASH")
    facts = json.loads(raw.decode("utf-8"))
    if facts.get("unc_root") != ALIAS_UNC:
        raise RuntimeError("ACCESS_ALIAS_UNC_MISMATCH")
    if str(facts["root_identity"]["volume_serial"]) != EXPECTED_VOLUME:
        raise RuntimeError("ACCESS_ALIAS_VOLUME_MISMATCH")
    if str(facts["root_identity"]["file_id"]) != EXPECTED_FILE_ID:
        raise RuntimeError("ACCESS_ALIAS_FILE_ID_MISMATCH")
    if facts.get("root_identity", {}).get("reparse") is not False:
        raise RuntimeError("ACCESS_ALIAS_REPARSE")
    path = facts.get("path")
    if not isinstance(path, str) or not path:
        raise RuntimeError("ACCESS_ALIAS_ANCHOR")
    return facts


def load_anchor() -> str:
    return load_facts()["path"]


def tail_after_anchor(inventory: str, anchor: str) -> str | None:
    text = str(inventory).replace("/", "\\")
    if text == anchor:
        return ""
    prefix = anchor + "\\"
    if not text.startswith(prefix):
        return None
    tail = text[len(prefix):]
    parts = tail.split("\\")
    if any(part in ("", ".", "..") or ":" in part or part.startswith("\\\\") for part in parts):
        raise ValueError("ACCESS_TAIL_REJECTED")
    return tail


def verify_anchor(contract: dict | None = None) -> bool:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from r9_pilot_common_r9fix import open_source_stable, handle_identity, CloseHandle
    try:
        facts = load_facts()
    except (OSError, RuntimeError, json.JSONDecodeError, KeyError, TypeError):
        return False
    anchor = facts["path"]
    if contract is not None:
        if contract.get("access_unc") != ALIAS_UNC:
            return False
        if contract.get("facts_content_sha256") != FACTS_CONTENT_SHA256:
            return False
        if contract.get("inventory_anchor") != anchor:
            return False
        if str(contract.get("anchor_file_id")) != EXPECTED_FILE_ID:
            return False
        if str(contract.get("source_volume_serial")) != EXPECTED_VOLUME:
            return False
    try:
        handle = open_source_stable(ALIAS_UNC)
    except (OSError, RuntimeError):
        return False
    try:
        try:
            ident = handle_identity(handle)
        except (OSError, RuntimeError):
            return False
    finally:
        CloseHandle(handle)
    directory = bool(int(ident.get("attrs") or 0) & FILE_ATTRIBUTE_DIRECTORY)
    return (
        ident.get("volume_serial") == EXPECTED_VOLUME
        and ident.get("file_id") == EXPECTED_FILE_ID
        and int(ident.get("size") or 0) == 0
        and directory
        and ident.get("is_reparse") is not True
    )


def access_path(inventory: str, canonical_source: str, anchor: str | None = None) -> str:
    root = load_anchor() if anchor is None else anchor
    tail = tail_after_anchor(inventory, root)
    if tail is None:
        return canonical_source
    if tail == "":
        return ALIAS_UNC
    return ALIAS_UNC + "\\" + tail
