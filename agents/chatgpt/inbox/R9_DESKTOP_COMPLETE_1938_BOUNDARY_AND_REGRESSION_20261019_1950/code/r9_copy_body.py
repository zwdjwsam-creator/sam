# -*- coding: utf-8 -*-
"""Copy and acceptance body. Not authorized to touch E: in this phase.

The CLI must refuse before calling these functions. Tests pass fakes.
"""
from __future__ import annotations

from pathlib import PureWindowsPath


class CopyRefusal(Exception):
    pass


class SourceChanged(Exception):
    pass


class LinkRejected(Exception):
    pass


_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def _under(path: str, root: str) -> bool:
    child = str(path).replace("/", "\\").rstrip("\\").casefold()
    base = str(root).replace("/", "\\").rstrip("\\").casefold()
    return child == base or child.startswith(base + "\\")


def assert_dest_allowed(dest: str, roots: tuple[str, ...], reparse_ancestors: tuple[str, ...] = ()) -> None:
    text = str(dest).replace("/", "\\")
    if text.startswith("\\\\?\\") or text.startswith("\\\\.\\") or text.startswith("\\\\"):
        raise LinkRejected("DEVICE_OR_UNC")
    if len(text) < 3 or text[1] != ":" or text[2] != "\\":
        raise LinkRejected("NOT_ABSOLUTE")
    if ":" in text[2:]:
        raise LinkRejected("ADS")
    parts = text.split("\\")
    for part in parts[1:]:
        if part in ("", ".", ".."):
            raise LinkRejected("ESCAPE")
        if part.endswith(" ") or part.endswith("."):
            raise LinkRejected("TRAILING_DOT_OR_SPACE")
        if part.split(".")[0].upper() in _RESERVED:
            raise LinkRejected("DEVICE_NAME")
    if not any(_under(text, root) for root in roots):
        raise LinkRejected("OUTSIDE_ROOT")
    for ancestor in reparse_ancestors:
        if _under(text, ancestor) and text.rstrip("\\").casefold() != str(ancestor).rstrip("\\").casefold():
            raise LinkRejected("REPARSE_ANCESTOR")


def write_entity_bytes(read_chunk, identity_now, dest: str, expected_size: int, expected_identity, expected_sha256: str, roots, write_chunk, commit):
    """Stream one entity. read_chunk returns b'' at EOF and must not be asked for the whole file."""
    import hashlib
    assert_dest_allowed(dest, roots)
    if not expected_sha256 or not expected_identity:
        raise SourceChanged("MISSING_EXPECTED_EVIDENCE")
    before = identity_now()
    if before != expected_identity:
        raise SourceChanged("IDENTITY_BEFORE")
    hasher = hashlib.sha256()
    total = 0
    while True:
        chunk = read_chunk()
        if chunk is None:
            raise SourceChanged("EOF_READ_FAILED")
        if chunk == b"":
            break
        if not isinstance(chunk, (bytes, bytearray)):
            raise SourceChanged("BAD_CHUNK")
        total += len(chunk)
        if total > expected_size:
            raise SourceChanged("SHORT_WRITE_OR_LONG_READ")
        hasher.update(chunk)
        written = write_chunk(bytes(chunk))
        if written != len(chunk):
            raise SourceChanged("SHORT_WRITE")
        if identity_now() != expected_identity:
            raise SourceChanged("IDENTITY_DURING")
    if total != expected_size:
        raise SourceChanged("SIZE")
    digest = hasher.hexdigest()
    if digest != expected_sha256:
        raise SourceChanged("HASH")
    if identity_now() != expected_identity:
        raise SourceChanged("IDENTITY_AFTER")
    from r9_temp_name import temp_path
    temp = temp_path(dest)
    if commit(temp, dest) is not True:
        raise SourceChanged("COMMIT_FAILED")
    return {"bytes": total, "identity": expected_identity, "sha256": digest, "dest": dest}


def create_local_hardlink(link_fn, source: str, dest: str, source_volume, dest_volume, roots):
    assert_dest_allowed(dest, roots)
    assert_dest_allowed(source, roots)
    if source_volume != dest_volume:
        raise LinkRejected("CROSS_VOLUME")
    link_fn(source, dest)
    return {"source": source, "dest": dest, "volume": source_volume}


def rebuild_reparse(create_fn, link_path: str, target: str, roots):
    assert_dest_allowed(link_path, roots)
    if str(target).startswith("\\\\") or str(target).upper().startswith("D:\\"):
        raise LinkRejected("TARGET_STILL_ON_SOURCE")
    if ".." in PureWindowsPath(str(target)).parts:
        raise LinkRejected("ESCAPE")
    assert_dest_allowed(target, roots)
    create_fn(link_path, target)
    return {"link_path": link_path, "target": target}


_REQUIRED = ("sha256", "file_id", "volume_serial", "logical_size", "alloc_size", "object_type")


def _missing(record: dict) -> list[str]:
    missing = []
    for key in _REQUIRED:
        value = record.get(key, None)
        if value is None or value == "":
            missing.append(key)
    return missing


def accept_on_disk(planned: dict, observed: dict) -> dict:
    """Compare records. Missing evidence is a failure; None must not match None."""
    reasons = []
    for side, record in (("PLANNED", planned), ("OBSERVED", observed)):
        for key in _missing(record):
            reasons.append(f"MISSING_{side}_{key}")
    if reasons:
        return {"ok": False, "reasons": reasons}
    if observed.get("sha256") != planned.get("sha256"):
        reasons.append("CONTENT_SHA")
    if str(observed.get("object_type")) != str(planned.get("object_type")):
        reasons.append("OBJECT_TYPE")
    if int(observed.get("logical_size")) != int(planned.get("logical_size")):
        reasons.append("SIZE")
    if planned.get("compare_source_identity"):
        if observed.get("file_id") != planned.get("file_id") or observed.get("volume_serial") != planned.get("volume_serial"):
            reasons.append("SOURCE_IDENTITY")
    else:
        if not observed.get("dest_file_id") or not observed.get("dest_volume_serial"):
            reasons.append("MISSING_OBSERVED_dest_file_id")
    if planned.get("link_target") is not None and observed.get("link_target") != planned.get("link_target"):
        reasons.append("LINK_TARGET")
    for key in ("dest_file_id", "dest_volume_serial"):
        if planned.get(key) not in (None, "") and observed.get(key) != planned.get(key):
            reasons.append("DEST_" + key.upper())
    return {"ok": not reasons, "reasons": reasons}


def accept_batch(planned_rows, observe, expected_count: int | None = None) -> dict:
    rows = list(planned_rows)
    expected = len(rows) if expected_count is None else expected_count
    failures = []
    checked = 0
    for row in rows:
        checked += 1
        observed = observe(row)
        if not observed:
            failures.append({"path": row.get("path"), "reasons": ["MISSING_OBSERVED"]})
            continue
        result = accept_on_disk(row, observed)
        if not result["ok"]:
            failures.append({"path": row.get("path"), "reasons": result["reasons"]})
    complete = expected > 0 and checked == expected and not failures
    return {"checked": checked, "ok": complete, "overall_full_acceptance": complete, "failures": failures}


def hardlink_groups_ok(groups: list[list[dict]]) -> dict:
    """Each group is one source entity. Dest FileId+volume must agree inside a group and differ across groups."""
    seen = set()
    for group in groups:
        if not group:
            return {"ok": False, "reason": "EMPTY_GROUP"}
        key = (group[0].get("dest_volume_serial"), group[0].get("dest_file_id"))
        if not key[0] or not key[1]:
            return {"ok": False, "reason": "MISSING_DEST_ID"}
        if any((row.get("dest_volume_serial"), row.get("dest_file_id")) != key for row in group):
            return {"ok": False, "reason": "GROUP_SPLIT"}
        if key in seen:
            return {"ok": False, "reason": "ENTITIES_MERGED"}
        seen.add(key)
    return {"ok": True, "groups": len(seen)}
