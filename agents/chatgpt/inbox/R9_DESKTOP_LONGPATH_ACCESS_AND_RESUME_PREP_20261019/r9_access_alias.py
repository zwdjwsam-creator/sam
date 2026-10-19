# -*- coding: utf-8 -*-
"""Map only the verified anchor onto the fixed R9LP_RO share."""
from __future__ import annotations

import json
from pathlib import Path

FACTS_PATH = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_LONGPATH_ACCESS_AND_RESUME_PREP_20261019\DEEP_SHARE_FACTS.json")
ALIAS_UNC = "\\\\192.168.100.2\\R9LP_RO"
EXPECTED_VOLUME = "2387166462"
EXPECTED_FILE_ID = "1688849860437540"


def load_anchor() -> str:
    facts = json.loads(FACTS_PATH.read_bytes().decode("utf-8"))
    if facts.get("unc_root") != ALIAS_UNC:
        raise RuntimeError("ACCESS_ALIAS_UNC_MISMATCH")
    if str(facts["root_identity"]["volume_serial"]) != EXPECTED_VOLUME:
        raise RuntimeError("ACCESS_ALIAS_VOLUME_MISMATCH")
    if str(facts["root_identity"]["file_id"]) != EXPECTED_FILE_ID:
        raise RuntimeError("ACCESS_ALIAS_FILE_ID_MISMATCH")
    if facts.get("root_identity", {}).get("reparse") is not False:
        raise RuntimeError("ACCESS_ALIAS_REPARSE")
    return facts["path"]


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


def verify_anchor() -> bool:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from r9_pilot_common_r9fix import open_source_stable, handle_identity, CloseHandle
    handle = open_source_stable(ALIAS_UNC)
    try:
        ident = handle_identity(handle)
    finally:
        CloseHandle(handle)
    return ident.get("volume_serial") == EXPECTED_VOLUME and ident.get("file_id") == EXPECTED_FILE_ID and int(ident.get("size") or 0) == 0


def access_path(inventory: str, canonical_source: str, anchor: str | None = None) -> str:
    root = load_anchor() if anchor is None else anchor
    tail = tail_after_anchor(inventory, root)
    if tail is None:
        return canonical_source
    if tail == "":
        return ALIAS_UNC
    return ALIAS_UNC + "\\" + tail
