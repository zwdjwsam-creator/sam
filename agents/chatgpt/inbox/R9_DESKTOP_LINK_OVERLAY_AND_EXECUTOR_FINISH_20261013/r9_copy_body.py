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


def _under(path: str, root: str) -> bool:
    child = PureWindowsPath(path)
    base = PureWindowsPath(root)
    if child == base:
        return True
    return base == child or base in child.parents


def assert_dest_allowed(dest: str, roots: tuple[str, ...]) -> None:
    text = str(dest)
    if ".." in PureWindowsPath(text).parts:
        raise LinkRejected("ESCAPE")
    if text.startswith("\\\\"):
        raise LinkRejected("UNC_DEST")
    if not any(_under(text, root) for root in roots):
        raise LinkRejected("OUTSIDE_ROOT")


def write_entity_bytes(read_source, identity_now, dest: str, expected_size: int, expected_identity, roots, write_temp, commit):
    """Copy one entity through injected IO. Does not open a real disk by itself."""
    assert_dest_allowed(dest, roots)
    before = identity_now()
    if before != expected_identity:
        raise SourceChanged("IDENTITY_BEFORE")
    data = read_source()
    if len(data) != expected_size:
        raise SourceChanged("SIZE")
    if identity_now() != expected_identity:
        raise SourceChanged("IDENTITY_DURING")
    temp = dest + ".partial"
    write_temp(temp, data)
    if identity_now() != expected_identity:
        raise SourceChanged("IDENTITY_AFTER")
    commit(temp, dest)
    return {"bytes": len(data), "identity": expected_identity}


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


def accept_on_disk(planned: dict, observed: dict) -> dict:
    """Compare one planned record with an observed record. No disk access."""
    reasons = []
    if observed.get("sha256") != planned.get("sha256"):
        reasons.append("CONTENT_SHA")
    if observed.get("file_id") != planned.get("file_id"):
        reasons.append("FILE_ID")
    if observed.get("volume_serial") != planned.get("volume_serial"):
        reasons.append("VOLUME")
    if int(observed.get("logical_size", -1)) != int(planned.get("logical_size", -2)):
        reasons.append("SIZE")
    if observed.get("link_target") != planned.get("link_target"):
        reasons.append("LINK_TARGET")
    if int(observed.get("alloc_size", -1)) != int(planned.get("alloc_size", -2)):
        reasons.append("ALLOCATION_SIZE")
    return {"ok": not reasons, "reasons": reasons}
