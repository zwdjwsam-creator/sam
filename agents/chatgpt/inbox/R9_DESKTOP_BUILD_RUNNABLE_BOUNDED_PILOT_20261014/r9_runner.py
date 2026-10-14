# -*- coding: utf-8 -*-
"""Production runner. Preparation contracts never reach a write syscall."""
from __future__ import annotations

from pathlib import Path

from r9_plan_reader import order_links
from r9_state import bind_run, destination_matches, get_stage, open_state, put_stage
from r9_winio import WindowsBackend


def allows_write(contract: dict, backend=None) -> bool:
    if contract.get("phase") != "SIMULATED_CHAIN":
        return False
    binding = contract.get("dest_binding")
    if not isinstance(binding, dict) or not binding.get("volume_serial"):
        return False
    if backend is None:
        return False
    from r9_winio import VirtualSyscalls
    return isinstance(getattr(backend, "sc", None), VirtualSyscalls)


def _dest(item) -> str:
    if isinstance(item, dict):
        return item["dest_path"]
    return item


def _record_from_stage(stage: dict) -> dict:
    return {
        "dest_path": stage["dest_path"],
        "sha256": stage["sha256"],
        "dest_file_id": stage["file_id"],
        "dest_volume_serial": stage["volume_serial"],
        "bytes": stage["logical_size"],
    }


def _require_mtime(entity: dict) -> None:
    if entity.get("mtime") is None or entity.get("mtime_status") in ("ABSENT_IN_PLAN", "MTIME_DEFICIT"):
        raise RuntimeError("MTIME_DEFICIT")


def _finish_entity(db, key: str, entity: dict, observed: dict, sha: str, size: int) -> dict:
    put_stage(
        db,
        key,
        kind="entity",
        phase="DONE",
        dest_path=entity["dest_path"],
        sha256=sha,
        file_id=observed.get("file_id"),
        volume_serial=observed.get("volume_serial"),
        object_type="file",
        logical_size=size,
        parent_key=entity["entity_key"],
    )
    db.commit()
    return {
        "dest_path": entity["dest_path"],
        "sha256": sha,
        "dest_file_id": observed.get("file_id"),
        "dest_volume_serial": observed.get("volume_serial"),
        "bytes": size,
    }


def production_run(entities, backend: WindowsBackend, contract: dict, state_path: Path) -> dict:
    db = open_state(Path(state_path))
    counts = {
        "copied_count": 0,
        "linked_count": 0,
        "reparse_count": 0,
        "directory_count": 0,
        "skipped_entities": 0,
        "skipped_links": 0,
        "skipped_reparse": 0,
        "resumed_entities": 0,
        "resumed_links": 0,
        "resumed_reparse": 0,
    }
    try:
        if not allows_write(contract, backend):
            return {
                "refused_before_write": True,
                "write_calls": getattr(backend.sc, "write_calls", 0),
                "backend_calls": backend.calls,
                **counts,
            }
        bind_run(db, contract.get("run"))
        if contract.get("plan_path"):
            import r9_plan_reader as reader
            import r9_source_contract as source_contract
            check = reader.connect(Path(contract["plan_path"]))
            try:
                if contract.get("run", {}).get("plan_digest") != reader.plan_digest(check):
                    raise RuntimeError("PLAN_DIGEST_MISMATCH")
                if contract.get("run", {}).get("code_digest") != source_contract.code_digest():
                    raise RuntimeError("CODE_DIGEST_MISMATCH")
            finally:
                check.close()
        for directory in contract.get("directories") or ():
            path = _dest(directory)
            backend.ensure_directory(path)
            observed = backend.observe_destination(path)
            if observed.get("object_type") != "directory":
                raise RuntimeError("TYPE_CONFLICT")
            put_stage(db, "dir:" + path, kind="dir", phase="DONE", dest_path=path, object_type="directory", logical_size=0)
            db.commit()
            counts["directory_count"] += 1
        for entity in entities:
            if entity.get("orphan"):
                raise RuntimeError("PLAN_ORPHAN_ENTITY")
            _require_mtime(entity)
            backend.assert_no_reparse_ancestor(entity["dest_path"])
            key = "entity:" + entity["entity_key"]
            stage = get_stage(db, key)
            observed = backend.observe_destination(entity["dest_path"])
            if stage is None and observed.get("status") == "PRESENT":
                raise RuntimeError("UNKNOWN_TARGET_EXISTS")
            if stage and stage["phase"] == "DONE":
                if not destination_matches(observed, stage):
                    raise RuntimeError("RESUME_DEST_MISMATCH")
                record = _record_from_stage(stage)
                counts["skipped_entities"] += 1
            elif stage and stage["phase"] == "INTENT" and observed.get("status") == "PRESENT":
                if not destination_matches(observed, stage):
                    raise RuntimeError("RESUME_DEST_MISMATCH")
                record = _finish_entity(db, key, entity, observed, stage["sha256"], stage["logical_size"])
                counts["resumed_entities"] += 1
            else:
                def before_commit(info, entity=entity, key=key):
                    put_stage(
                        db,
                        key,
                        kind="entity",
                        phase="INTENT",
                        dest_path=entity["dest_path"],
                        sha256=info["sha256"],
                        object_type="file",
                        logical_size=info["bytes"],
                        parent_key=entity["entity_key"],
                    )
                    db.commit()

                copied = backend.copy_entity(entity, before_commit=before_commit)
                if contract.get("fault") == "A":
                    raise RuntimeError("INTERRUPT_A")
                observed = backend.observe_destination(entity["dest_path"])
                record = _finish_entity(db, key, entity, observed, copied["sha256"], copied["bytes"])
                counts["copied_count"] += 1
            aliases = list(entity.get("extra_dest_paths") or ())
            for index, alias in enumerate(aliases):
                _alias(db, backend, contract, entity, record, alias, index, aliases, counts)
        for link in order_links(contract.get("links") or ()):
            _reparse(db, backend, contract, link, counts)
        acceptance = None
        if contract.get("accept"):
            db.close()
            db = None
            from r9_acceptance import full_acceptance
            acceptance = full_acceptance(Path(contract["plan_path"]), Path(state_path), backend, contract.get("run"))
        return {"refused_before_write": False, "acceptance": acceptance, "backend_calls": backend.calls, **counts}
    finally:
        if db is not None:
            db.close()


def _alias(db, backend, contract, entity, record, alias, index, aliases, counts) -> None:
    key = "alias:" + alias
    stage = get_stage(db, key)
    seen = backend.observe_destination(alias)
    if stage and stage["phase"] == "DONE":
        if seen.get("file_id") != record["dest_file_id"] or seen.get("volume_serial") != record["dest_volume_serial"]:
            raise RuntimeError("RESUME_ALIAS_MISMATCH")
        counts["skipped_links"] += 1
        return
    if stage is None and seen.get("status") == "PRESENT":
        raise RuntimeError("UNKNOWN_TARGET_EXISTS")
    if stage and stage["phase"] == "INTENT" and seen.get("status") == "PRESENT":
        if seen.get("file_id") != record["dest_file_id"] or seen.get("volume_serial") != record["dest_volume_serial"]:
            raise RuntimeError("RESUME_ALIAS_MISMATCH")
        put_stage(
            db,
            key,
            kind="alias",
            phase="DONE",
            dest_path=alias,
            sha256=record["sha256"],
            file_id=seen.get("file_id"),
            volume_serial=seen.get("volume_serial"),
            object_type="file",
            logical_size=record["bytes"],
            parent_key=entity["entity_key"],
        )
        db.commit()
        counts["resumed_links"] += 1
        return
    if seen.get("status") == "PRESENT":
        raise RuntimeError("RESUME_ALIAS_MISMATCH")
    put_stage(
        db,
        key,
        kind="alias",
        phase="INTENT",
        dest_path=alias,
        sha256=record["sha256"],
        file_id=record["dest_file_id"],
        volume_serial=record["dest_volume_serial"],
        object_type="file",
        logical_size=record["bytes"],
        parent_key=entity["entity_key"],
    )
    db.commit()
    backend.hardlink(record["dest_path"], alias)
    if contract.get("fault") == "C":
        raise RuntimeError("INTERRUPT_C")
    final = backend.observe_destination(alias)
    put_stage(
        db,
        key,
        kind="alias",
        phase="DONE",
        dest_path=alias,
        sha256=record["sha256"],
        file_id=final.get("file_id"),
        volume_serial=final.get("volume_serial"),
        object_type="file",
        logical_size=record["bytes"],
        parent_key=entity["entity_key"],
    )
    db.commit()
    counts["linked_count"] += 1
    if contract.get("fault") == "B" and index < len(aliases) - 1:
        raise RuntimeError("INTERRUPT_B")


def _reparse(db, backend, contract, link, counts) -> None:
    path = link["link_path"]
    key = "reparse:" + path
    stage = get_stage(db, key)
    seen = backend.observe_destination(path)
    if stage and stage["phase"] == "DONE":
        if not destination_matches(seen, stage):
            raise RuntimeError("REPARSE_MISMATCH")
        counts["skipped_reparse"] += 1
        return
    if stage is None and seen.get("status") == "PRESENT":
        raise RuntimeError("UNKNOWN_TARGET_EXISTS")
    if stage and stage["phase"] == "INTENT" and seen.get("status") == "PRESENT":
        if seen.get("reparse_target") != link["target"] or seen.get("object_type") != link["kind"]:
            raise RuntimeError("REPARSE_MISMATCH")
        put_stage(
            db,
            key,
            kind="reparse",
            phase="DONE",
            dest_path=path,
            object_type=link["kind"],
            link_target=link["target"],
            file_id=seen.get("file_id"),
            volume_serial=seen.get("volume_serial"),
            logical_size=0,
        )
        db.commit()
        counts["resumed_reparse"] += 1
        return
    put_stage(
        db,
        key,
        kind="reparse",
        phase="INTENT",
        dest_path=path,
        object_type=link["kind"],
        link_target=link["target"],
        logical_size=0,
    )
    db.commit()
    backend.create_reparse(path, link["target"], link["kind"])
    if contract.get("fault") == "C_REPARSE":
        raise RuntimeError("INTERRUPT_C")
    final = backend.observe_destination(path)
    put_stage(
        db,
        key,
        kind="reparse",
        phase="DONE",
        dest_path=path,
        object_type=link["kind"],
        link_target=link["target"],
        file_id=final.get("file_id"),
        volume_serial=final.get("volume_serial"),
        logical_size=0,
    )
    db.commit()
    counts["reparse_count"] += 1
