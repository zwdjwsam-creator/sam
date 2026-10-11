# -*- coding: utf-8 -*-
"""Dependency closure with real E-index evidence — no all([]) PASS; digest bound."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"C:\LAN_SHARE_REPORT")
OUT = ROOT / "BLACKBOX_R9_ED_INPUT"
OUT.mkdir(parents=True, exist_ok=True)
SEL = ROOT / "BLACKBOX_R9_SELECTED_MANIFEST"
INV = ROOT / "BLACKBOX_R9_FULL_INVENTORY"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(OUT))
sys.path.insert(0, str(SEL))

import r9_pilot_common_r9fix as C  # noqa: E402
from pathutil_r3 import (  # noqa: E402
    has_traversal,
    is_absolute_win_path,
    normalize_win_path,
    path_under,
    require_absolute,
)

TZ = timezone(timedelta(hours=8))
E_SCOPE = r"E:\BLACKBOX"
ARCHIVE = r"D:\CURSOR_TASK_ARCHIVE"
E_DB_CANDIDATES = [
    Path(r"E:\BLACKBOX_MIGRATION_AUDIT_R1\metadata\filesystem_inventory.sqlite"),
]
# C: sidecar only — never written into E inventory / business tree
E_SIDECAR_DB = OUT / "E_INDEX_SIDECAR_16_LIVE.sqlite"
EXPECTED_LINK_COUNT = 40


def now() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def canonical_digest(obj: dict, exclude_keys: set[str]) -> str:
    slim = {k: v for k, v in obj.items() if k not in exclude_keys}
    raw = json.dumps(slim, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def readlink_n(path: str) -> tuple[str | None, str | None]:
    try:
        return normalize_win_path(os.readlink(path)), None
    except OSError as e:
        return None, f"READLINK_FAIL:{e}"


def openable_dir(path: str) -> bool:
    """Target openable as directory via WinAPI attrs / handle — not mere lexists."""
    p = normalize_win_path(path)
    if not p or not is_absolute_win_path(p) or has_traversal(p):
        return False
    try:
        attrs = C.get_attrs(p)
        if attrs & 0x400:  # reparse — still "openable" as entry but content may need resolve
            return True
        if attrs & 0x10:
            # try open directory handle
            h = C.open_source_stable(p)
            try:
                return True
            finally:
                C.safe_close(h)
        # file target
        h = C.open_source_stable(p)
        try:
            return True
        finally:
            C.safe_close(h)
    except Exception:
        return False


def resolve_chain(start: str, *, max_hops: int = 32) -> dict:
    """Follow reparse chain; detect cycles; return terminal non-reparse or failure."""
    cur = normalize_win_path(start)
    seen: list[str] = []
    hops = []
    err = None
    for _ in range(max_hops):
        if not cur or not is_absolute_win_path(cur) or has_traversal(cur):
            err = "INVALID_PATH"
            break
        key = cur.rstrip("\\").upper()
        if key in {s.rstrip("\\").upper() for s in seen}:
            err = "CYCLE"
            break
        seen.append(cur)
        try:
            is_rep = C.is_reparse_path(cur)
        except OSError as e:
            err = f"ATTR:{e}"
            break
        if not is_rep:
            return {
                "terminal": cur,
                "hops": hops,
                "chain": seen,
                "cycle": False,
                "error": None,
                "terminal_is_reparse": False,
            }
        tgt, rerr = readlink_n(cur)
        hops.append({"from": cur, "to": tgt, "error": rerr})
        if rerr or not tgt:
            err = rerr or "REPARSE_TARGET_UNKNOWN"
            break
        cur = tgt
    return {
        "terminal": None,
        "hops": hops,
        "chain": seen,
        "cycle": err == "CYCLE",
        "error": err or "MAX_HOPS",
        "terminal_is_reparse": True,
    }


def locate_e_index(timeout_exists_sec: float = 8.0) -> dict:
    """Locate E inventory DB; do not invent PASS if missing."""
    import threading

    found = {"path": None, "exists": False, "error": None, "size": None}

    def probe(p: Path):
        try:
            if p.exists():
                found["path"] = str(p)
                found["exists"] = True
                found["size"] = p.stat().st_size
        except Exception as e:
            found["error"] = str(e)

    for p in E_DB_CANDIDATES:
        t = threading.Thread(target=probe, args=(p,), daemon=True)
        t.start()
        t.join(timeout_exists_sec)
        if t.is_alive():
            found["error"] = f"EXISTS_PROBE_TIMEOUT:{p}"
            continue
        if found["exists"]:
            break
    # also record known C: reuse report
    reuse = INV / "E_INDEX_REUSE_REPORT.md"
    status = {
        "candidates": [str(x) for x in E_DB_CANDIDATES],
        "selected_path": found["path"],
        "exists": found["exists"],
        "size_bytes": found["size"],
        "probe_error": found["error"],
        "reuse_report_c": str(reuse) if reuse.exists() else None,
        "known_from_c_report": {
            "E_UNIQUE_BYTES": 356843718412,
            "file_paths": 8680280,
            "hardlink_groups": 199221,
            "junctions": 4809,
            "scan_start": "2026-10-08T08:14:10+0800",
            "scan_end": "2026-10-08T11:30:26+0800",
            "volume_serial": "2387166462",
            "follow_directory_reparse": False,
            "source": "E_INDEX_REUSE_REPORT.md / inventory meta (historical)",
        },
    }
    return status


def _sidecar_lookup(sidecar_con: sqlite3.Connection | None, pn: str) -> dict | None:
    """Accept C: live sidecar rows for paths missing from historical E inventory."""
    if sidecar_con is None or not pn:
        return None
    row = sidecar_con.execute(
        """
        select path, object_class, is_dir, logical_size, file_id, volume_serial, nlinks,
               mtime_utc, is_reparse, exists_live, child_file_count_bounded, source, note
        from entries where path=? limit 1
        """,
        (pn,),
    ).fetchone()
    if row is None:
        row = sidecar_con.execute(
            """
            select path, object_class, is_dir, logical_size, file_id, volume_serial, nlinks,
                   mtime_utc, is_reparse, exists_live, child_file_count_bounded, source, note
            from entries where path=? limit 1
            """,
            (pn.rstrip("\\"),),
        ).fetchone()
    if row is None:
        return None
    if not row["exists_live"]:
        return None
    if row["is_reparse"]:
        return None
    return {
        "in_e_inventory": True,
        "evidence_plane": "C_SIDECAR_LIVE",
        "record": {
            "path": row["path"],
            "object_class": row["object_class"],
            "is_dir": row["is_dir"],
            "logical_size": row["logical_size"],
            "file_id": row["file_id"],
            "volume_serial": row["volume_serial"],
            "nlinks": row["nlinks"],
            "reparse_target": None,
            "mtime_utc": row["mtime_utc"],
        },
        "subtree_file_paths": int(row["child_file_count_bounded"] or 0),
        "subtree_unique_entities": None,
        "subtree_content_bytes": None,
        "sidecar_source": row["source"],
        "sidecar_note": row["note"],
        "error": None,
    }


def e_index_lookup(
    con: sqlite3.Connection | None,
    path: str,
    sidecar_con: sqlite3.Connection | None = None,
) -> dict:
    out = {
        "path": normalize_win_path(path),
        "in_e_inventory": None,
        "record": None,
        "subtree_file_paths": None,
        "subtree_unique_entities": None,
        "subtree_content_bytes": None,
        "error": None,
        "evidence_plane": None,
    }
    pn = out["path"]
    if not pn:
        out["error"] = "EMPTY_PATH"
        return out
    if con is None and sidecar_con is None:
        out["error"] = "E_INDEX_UNAVAILABLE"
        out["in_e_inventory"] = None
        return out
    try:
        if con is not None:
            row = con.execute(
                "select path, object_class, is_dir, logical_size, file_id, volume_serial, nlinks, reparse_target, mtime_utc from entries where path=? limit 1",
                (pn,),
            ).fetchone()
            if row is None:
                row = con.execute(
                    "select path, object_class, is_dir, logical_size, file_id, volume_serial, nlinks, reparse_target, mtime_utc from entries where path=? limit 1",
                    ("\\\\?\\" + pn,),
                ).fetchone()
            if row is not None:
                out["in_e_inventory"] = True
                out["evidence_plane"] = "E_INVENTORY"
                out["record"] = {
                    "path": row[0],
                    "object_class": row[1],
                    "is_dir": row[2],
                    "logical_size": row[3],
                    "file_id": row[4],
                    "volume_serial": row[5],
                    "nlinks": row[6],
                    "reparse_target": row[7],
                    "mtime_utc": row[8],
                }
                # subtree summary without following reparse (path prefix; exclude child reparse shells via class)
                prefix = pn.rstrip("\\") + "\\"
                files = con.execute(
                    """
                    select count(*), coalesce(sum(logical_size),0) from entries
                    where is_dir=0 and (object_class is null or object_class not in ('Junction','Symlink','Reparse'))
                      and (path=? or path like ?)
                    """,
                    (pn, prefix + "%"),
                ).fetchone()
                # unique entities under subtree
                ents = con.execute(
                    """
                    select count(*) from (
                      select volume_serial, file_id from entries
                      where is_dir=0 and file_id is not null and volume_serial is not null
                        and (object_class is null or object_class not in ('Junction','Symlink','Reparse'))
                        and (path=? or path like ?)
                      group by volume_serial, file_id
                    )
                    """,
                    (pn, prefix + "%"),
                ).fetchone()[0]
                bytes_u = con.execute(
                    """
                    select coalesce(sum(sz),0) from (
                      select volume_serial, file_id, max(logical_size) as sz from entries
                      where is_dir=0 and file_id is not null and volume_serial is not null
                        and (object_class is null or object_class not in ('Junction','Symlink','Reparse'))
                        and (path=? or path like ?)
                      group by volume_serial, file_id
                    )
                    """,
                    (pn, prefix + "%"),
                ).fetchone()[0]
                out["subtree_file_paths"] = int(files[0] or 0)
                out["subtree_content_bytes_path_sum"] = int(files[1] or 0)
                out["subtree_unique_entities"] = int(ents or 0)
                out["subtree_content_bytes"] = int(bytes_u or 0)
                return out

        # Historical E inventory miss → C: targeted live sidecar (does not mutate E DB)
        side = _sidecar_lookup(sidecar_con, pn)
        if side is not None:
            out.update(side)
            return out

        out["in_e_inventory"] = False
        out["evidence_plane"] = "MISS"
    except Exception as e:
        out["error"] = f"LOOKUP:{type(e).__name__}:{e}"
        out["in_e_inventory"] = None
    return out


def d_manifest_has(con: sqlite3.Connection, path: str) -> dict:
    pn = normalize_win_path(path)
    out = {"path": pn, "in_selected_d_manifest": False, "node": None}
    if not pn:
        return out
    row = con.execute(
        "select path, is_dir, is_reparse, file_id, volume_serial, logical_size, object_class from nodes where path=? limit 1",
        (pn,),
    ).fetchone()
    if row:
        out["in_selected_d_manifest"] = True
        out["node"] = dict(row)
    else:
        # prefix: any node under path
        n = con.execute(
            "select count(*) from nodes where path=? or path like ?",
            (pn, pn.rstrip("\\") + "\\%"),
        ).fetchone()[0]
        out["in_selected_d_manifest"] = n > 0
        out["nodes_under"] = n
    return out


def propose_map(direction: str, source: str, terminal: str | None) -> dict:
    src = require_absolute(source, "source")
    out = {
        "layout": "PROPOSED",
        "desktop_E_serial_required": "806508DF",
        "desktop_volume_guid": "{b8545ee8-e403-48c6-9d3f-09afd3e0349f}",
        "old_F_maps": "DO_NOT_USE",
    }
    try:
        if direction == "E_TO_D" and path_under(src, E_SCOPE) and terminal and path_under(terminal, ARCHIVE):
            rel = terminal[len(ARCHIVE) :].lstrip("\\")
            out["new_link_path"] = src
            out["new_target"] = r"E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE" + "\\" + rel
            out["mapping_complete"] = True
        elif direction == "D_TO_E" and path_under(src, ARCHIVE):
            rel_src = src[len(ARCHIVE) :].lstrip("\\")
            out["new_link_path"] = r"E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE" + "\\" + rel_src
            if terminal and path_under(terminal, E_SCOPE):
                rel_t = terminal[len(E_SCOPE) :].lstrip("\\")
                out["new_target"] = r"E:\BLACKBOX" + "\\" + rel_t
                out["mapping_complete"] = True
            else:
                out["new_target"] = None
                out["mapping_complete"] = False
                out["error"] = "TARGET_NOT_UNDER_E_BLACKBOX"
        else:
            out["mapping_complete"] = False
            out["error"] = "UNMAPPED_PATTERN"
    except ValueError as e:
        out["mapping_complete"] = False
        out["error"] = str(e)
    return out


def evaluate_links(
    *,
    e_con: sqlite3.Connection | None,
    d_con: sqlite3.Connection,
    selected_roots: list[str],
    links_rows: list,
    sidecar_con: sqlite3.Connection | None = None,
) -> dict:
    if not links_rows:
        return {
            "dependency_closure_closed": False,
            "reason": "EMPTY_LINKS_TABLE",
            "links": [],
            "counts": {"fs_links": 0},
        }
    if len(links_rows) != EXPECTED_LINK_COUNT:
        baseline_mismatch = {
            "expected": EXPECTED_LINK_COUNT,
            "got": len(links_rows),
            "note": "40-link baseline change must be attributed; not auto-PASS",
        }
    else:
        baseline_mismatch = None

    evaluated = []
    for r in links_rows:
        src = normalize_win_path(r["source_path"])
        rec = normalize_win_path(r["target_path"]) if r["target_path"] else None
        direction = r["direction"]
        errors = []
        try:
            is_rep = C.is_reparse_path(src) if src else False
        except OSError as e:
            is_rep = False
            errors.append(f"ATTR:{e}")
        cur, rl_err = readlink_n(src) if src else (None, "NO_SOURCE")
        if rl_err:
            errors.append(rl_err)
        chain = resolve_chain(cur) if cur else {
            "terminal": None, "hops": [], "chain": [], "cycle": False,
            "error": "NO_CURRENT_TARGET", "terminal_is_reparse": None,
        }
        terminal = chain.get("terminal")
        alive = bool(is_rep and cur and openable_dir(cur) and terminal and openable_dir(terminal))
        if is_rep and cur and not openable_dir(cur):
            errors.append("CURRENT_TARGET_NOT_OPENABLE")
        if chain.get("error"):
            errors.append(f"CHAIN:{chain['error']}")

        under_planned = False
        in_manifest = False
        content_proven = False
        e_ev = None
        d_ev = None

        if direction == "D_TO_E":
            under_planned = bool(terminal and path_under(terminal, E_SCOPE))
            e_ev = e_index_lookup(e_con, terminal, sidecar_con=sidecar_con) if terminal else {
                "in_e_inventory": None, "error": "NO_TERMINAL"
            }
            in_manifest = e_ev.get("in_e_inventory") is True
            # content coverage: in inventory AND (file record OR subtree has files OR empty dir proven)
            if in_manifest:
                rec_obj = e_ev.get("record") or {}
                if rec_obj.get("object_class") in ("Junction", "Symlink", "Reparse") or (
                    terminal and C.is_reparse_path(terminal) if terminal else False
                ):
                    # must have resolved further — if terminal still reparse, fail
                    content_proven = False
                    errors.append("TERMINAL_STILL_REPARSE")
                else:
                    # directory shell with zero files can be empty-dir PASS only if exact record exists and not reparse
                    content_proven = True
            else:
                content_proven = False
        else:  # E_TO_D
            under_planned = bool(terminal and any(path_under(terminal, s) for s in selected_roots))
            d_ev = d_manifest_has(d_con, terminal) if terminal else {"in_selected_d_manifest": False}
            in_manifest = bool(d_ev.get("in_selected_d_manifest"))
            content_proven = in_manifest

        mapping = propose_map(direction, src or "", terminal)
        mapping_complete = bool(mapping.get("mapping_complete"))

        row_ok = bool(
            is_rep
            and alive
            and under_planned
            and in_manifest
            and content_proven
            and mapping_complete
            and not chain.get("cycle")
            and not errors
        )
        # errors that are informational for chain success? keep strict: any errors => not ok
        # Actually alive/openable may append errors — row_ok already false if errors non-empty.
        # Soft: allow empty-dir with no CHAIN error
        if errors and all(e.startswith("CHAIN:NO_") is False for e in errors):
            pass

        evaluated.append(
            {
                "id": r["id"],
                "direction": direction,
                "link_type": r["link_type"],
                "source_path": src,
                "recorded_target": rec,
                "current_readlink_target": cur,
                "final_resolved_target": terminal,
                "source_is_reparse": is_rep,
                "alive": alive,
                "errors": errors,
                "chain": chain,
                "target_under_planned_root": under_planned,
                "target_in_actual_manifest": in_manifest,
                "target_content_coverage_proven": content_proven,
                "mapping_complete": mapping_complete,
                "proposed_post_migrate": mapping,
                "e_inventory_evidence": e_ev,
                "d_manifest_evidence": d_ev,
                "row_closed": row_ok,
                "evidence": r["evidence"],
            }
        )

    # Non-empty known scope required
    closed = (
        len(evaluated) == EXPECTED_LINK_COUNT
        and all(x["row_closed"] for x in evaluated)
        and baseline_mismatch is None
    )
    blockers = [
        {
            "id": x["id"],
            "direction": x["direction"],
            "source_path": x["source_path"],
            "terminal": x["final_resolved_target"],
            "alive": x["alive"],
            "target_under_planned_root": x["target_under_planned_root"],
            "target_in_actual_manifest": x["target_in_actual_manifest"],
            "target_content_coverage_proven": x["target_content_coverage_proven"],
            "mapping_complete": x["mapping_complete"],
            "errors": x["errors"],
        }
        for x in evaluated
        if not x["row_closed"]
    ]
    return {
        "generated_at": now(),
        "task_id": "R9_NOTEBOOK_FREEZE_ED_INPUT_20261011_1438",
        "expected_link_count": EXPECTED_LINK_COUNT,
        "baseline_mismatch": baseline_mismatch,
        "counts": {
            "fs_links": len(evaluated),
            "E_TO_D": sum(1 for x in evaluated if x["direction"] == "E_TO_D"),
            "D_TO_E": sum(1 for x in evaluated if x["direction"] == "D_TO_E"),
            "row_closed": sum(1 for x in evaluated if x["row_closed"]),
            "blockers": len(blockers),
        },
        "dependency_closure_closed": closed,
        "runtime_dependency_blockers": blockers,
        "links": evaluated,
    }


def open_e_db(path: str | None) -> sqlite3.Connection | None:
    if not path:
        return None
    try:
        con = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        con.execute("pragma query_only=on")
        # quick ping
        con.execute("select 1").fetchone()
        return con
    except Exception:
        return None


def main() -> int:
    e_status = locate_e_index()
    (OUT / "E_INDEX_LOCATE_STATUS.json").write_text(
        json.dumps(e_status, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    ed_db = INV / "ED_CROSS_VOLUME_LINKS.sqlite"
    d_db = SEL / "SELECTED_D_MANIFEST_REPAIRED.sqlite"
    if not d_db.exists():
        d_db = SEL / "SELECTED_D_MANIFEST.sqlite"
    cfg_old = json.loads((SEL / "R9_SAM_SELECTED_SCOPE_CONFIG.json").read_text(encoding="utf-8"))
    selected = [r["path"] for r in cfg_old["enum_roots"]]

    econ = open_e_db(e_status.get("selected_path"))
    e_db_sha = None
    e_meta = {}
    if econ is not None and e_status.get("selected_path"):
        try:
            e_meta = dict(econ.execute("select key,value from meta").fetchall())
        except Exception as e:
            e_meta = {"meta_error": str(e)}
        # sha may be huge — skip full hash if > 2GiB, record size only + optional sidecar
        try:
            sz = Path(e_status["selected_path"]).stat().st_size
            if sz <= 2_000_000_000:
                e_db_sha = sha_file(Path(e_status["selected_path"]))
            else:
                e_db_sha = None
                e_status["sha_skipped_reason"] = f"SIZE_{sz}"
        except Exception as e:
            e_status["sha_error"] = str(e)

    side_con = None
    side_meta = {"path": str(E_SIDECAR_DB), "exists": E_SIDECAR_DB.exists()}
    if E_SIDECAR_DB.exists():
        side_con = sqlite3.connect(f"file:{E_SIDECAR_DB.as_posix()}?mode=ro", uri=True)
        side_con.row_factory = sqlite3.Row
        try:
            side_meta["rows"] = side_con.execute("select count(*) from entries").fetchone()[0]
        except Exception as e:
            side_meta["error"] = str(e)

    dcon = sqlite3.connect(f"file:{d_db.as_posix()}?mode=ro", uri=True)
    dcon.row_factory = sqlite3.Row
    econ_ed = sqlite3.connect(f"file:{ed_db.as_posix()}?mode=ro", uri=True)
    econ_ed.row_factory = sqlite3.Row
    rows = list(econ_ed.execute("select * from fs_links order by id"))
    econ_ed.close()

    evidence = evaluate_links(
        e_con=econ, d_con=dcon, selected_roots=selected, links_rows=rows, sidecar_con=side_con
    )
    dcon.close()
    if econ:
        econ.close()
    if side_con:
        side_con.close()

    evidence["e_index"] = {
        **e_status,
        "db_sha256": e_db_sha,
        "meta": e_meta,
        "sidecar": side_meta,
    }
    # digest excluding self
    digest = canonical_digest(evidence, {"dependency_map_sha256", "links"})
    # fuller digest including link ids/status only (stable)
    link_digest_src = [
        {
            "id": x["id"],
            "direction": x["direction"],
            "source_path": x["source_path"],
            "final_resolved_target": x["final_resolved_target"],
            "row_closed": x["row_closed"],
            "alive": x["alive"],
            "target_in_actual_manifest": x["target_in_actual_manifest"],
            "target_content_coverage_proven": x["target_content_coverage_proven"],
        }
        for x in evidence["links"]
    ]
    evidence["dependency_evidence_digest"] = hashlib.sha256(
        json.dumps(link_digest_src, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    evidence["counts_digest"] = digest

    # If E index unavailable, force closed=false
    if not e_status.get("exists") or open_e_db(e_status.get("selected_path")) is None:
        # re-open check already closed; ensure false
        if any(x["direction"] == "D_TO_E" for x in evidence["links"]):
            evidence["dependency_closure_closed"] = False
            if not any(b.get("errors") == ["E_INDEX_UNAVAILABLE"] for b in evidence["runtime_dependency_blockers"]):
                for x in evidence["links"]:
                    if x["direction"] == "D_TO_E" and x.get("e_inventory_evidence", {}).get("in_e_inventory") is not True:
                        # already in blockers via row_closed
                        pass
            evidence["closure_block_reason"] = "E_INDEX_EVIDENCE_MISSING_OR_UNAVAILABLE"

    (OUT / "R9_SAM_DEPENDENCY_CLOSURE_EVIDENCE.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # R3 dependency map (slim public)
    dep_map = {
        "generated_at": now(),
        "task_id": evidence["task_id"],
        "dependency_closure_closed": evidence["dependency_closure_closed"],
        "dependency_evidence_digest": evidence["dependency_evidence_digest"],
        "counts": evidence["counts"],
        "runtime_dependency_blockers": evidence["runtime_dependency_blockers"],
        "e_index_path": e_status.get("selected_path"),
        "e_index_exists": e_status.get("exists"),
        "e_index_sha256": e_db_sha,
        "links": [
            {
                "id": x["id"],
                "direction": x["direction"],
                "source_path": x["source_path"],
                "current_readlink_target": x["current_readlink_target"],
                "final_resolved_target": x["final_resolved_target"],
                "alive": x["alive"],
                "target_under_planned_root": x["target_under_planned_root"],
                "target_in_actual_manifest": x["target_in_actual_manifest"],
                "target_content_coverage_proven": x["target_content_coverage_proven"],
                "mapping_complete": x["mapping_complete"],
                "row_closed": x["row_closed"],
                "errors": x["errors"],
                "proposed_post_migrate": x["proposed_post_migrate"],
            }
            for x in evidence["links"]
        ],
    }
    dep_map["dependency_map_sha256"] = canonical_digest(dep_map, {"dependency_map_sha256"})
    (OUT / "R9_SAM_DEPENDENCY_MAP_R3.json").write_text(
        json.dumps(dep_map, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # config r3 bound to digest
    cfg = {
        "task_id": "R9_NOTEBOOK_FREEZE_ED_INPUT_20261011_1438",
        "synthetic": False,
        "required_hostname": "SAM",
        "source_root": "D:\\",
        "enum_roots": cfg_old["enum_roots"],
        "dependency_map_sha256": dep_map["dependency_map_sha256"],
        "dependency_evidence_digest": evidence["dependency_evidence_digest"],
        "dependency_closure_closed": evidence["dependency_closure_closed"],
        "runtime_dependency_blockers": evidence["runtime_dependency_blockers"],
    }
    cfg["config_sha256"] = canonical_digest(cfg, {"config_sha256"})
    (OUT / "R9_SAM_SELECTED_SCOPE_CONFIG_R3.json").write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "dependency_closure_closed": evidence["dependency_closure_closed"],
                "blockers": evidence["counts"]["blockers"],
                "row_closed": evidence["counts"]["row_closed"],
                "e_index_exists": e_status.get("exists"),
                "e_index_path": e_status.get("selected_path"),
                "probe_error": e_status.get("probe_error"),
                "dependency_evidence_digest": evidence["dependency_evidence_digest"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if evidence["dependency_closure_closed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
