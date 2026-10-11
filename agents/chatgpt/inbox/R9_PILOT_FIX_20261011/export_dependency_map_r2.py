# -*- coding: utf-8 -*-
"""R2 dependency map: normalize \\?\\ paths, close D→E into E:\\BLACKBOX scope, propose E engines maps."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"C:\LAN_SHARE_REPORT")
INV = ROOT / "BLACKBOX_R9_FULL_INVENTORY"
OUT = ROOT / "BLACKBOX_R9_SELECTED_MANIFEST"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(OUT))
import r9_pilot_common_r9fix as C  # noqa: E402
from pathutil_r2 import normalize_win_path, path_under  # noqa: E402
from selected_manifest_enumerator_r2 import canonical_config_sha  # noqa: E402

TZ = timezone(timedelta(hours=8))
E_SCOPE = r"E:\BLACKBOX"
ARCHIVE_ROOT = r"D:\CURSOR_TASK_ARCHIVE"


def now() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def readlink_target(path: str) -> tuple[str | None, str | None]:
    try:
        return os.readlink(path), None
    except OSError as e:
        return None, f"READLINK_FAIL:{e}"


def target_openable(path: str) -> bool:
    p = normalize_win_path(path)
    if not p:
        return False
    try:
        # prefer exists (may follow) for openability of target content
        return os.path.exists(C.to_win_long_path(p))
    except OSError:
        return False


def propose_maps(direction: str, source: str, target: str | None) -> dict:
    src_n = normalize_win_path(source) or source
    tgt_n = normalize_win_path(target) if target else None
    out = {
        "layout": "PROPOSED",
        "desktop_E_serial_required": "806508DF",
        "old_F_maps": "DO_NOT_USE",
        "note": "Proposal only — do not create links this round",
    }
    if direction == "E_TO_D" and path_under(src_n, E_SCOPE) and tgt_n and path_under(tgt_n, ARCHIVE_ROOT):
        rel = tgt_n[len(ARCHIVE_ROOT) :].lstrip("\\")
        out["new_link_path"] = src_n
        out["new_target"] = r"E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE" + "\\" + rel
    elif direction == "D_TO_E" and path_under(src_n, ARCHIVE_ROOT):
        rel_src = src_n[len(ARCHIVE_ROOT) :].lstrip("\\")
        out["new_link_path"] = r"E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE" + "\\" + rel_src
        if tgt_n and path_under(tgt_n, E_SCOPE):
            rel_tgt = tgt_n[len(E_SCOPE) :].lstrip("\\")
            out["new_target"] = r"E:\BLACKBOX" + "\\" + rel_tgt
        else:
            out["new_target"] = None
            out["target_map_error"] = "TARGET_NOT_UNDER_E_BLACKBOX_OR_UNKNOWN"
    else:
        out["new_link_path"] = None
        out["new_target"] = None
        out["target_map_error"] = "UNMAPPED_PATTERN"
    return out


def e_inventory_has(path: str) -> dict:
    """Exact lookup in E inventory if present; else live exists only."""
    edb = INV / "E_VOLUME_FILESYSTEM_INVENTORY.sqlite"
    pn = normalize_win_path(path)
    out = {"path": pn, "in_e_inventory": None, "live_exists": target_openable(pn) if pn else False}
    if not edb.exists() or not pn:
        return out
    try:
        con = sqlite3.connect(f"file:{edb.as_posix()}?mode=ro", uri=True)
        # try common schemas
        tables = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
        found = None
        for t in tables:
            cols = [c[1] for c in con.execute(f"pragma table_info({t})")]
            if "path" in cols:
                r = con.execute(f"select * from {t} where path=? limit 1", (pn,)).fetchone()
                if r is None:
                    # also try \\?\ form
                    r = con.execute(f"select * from {t} where path=? limit 1", ("\\\\?\\" + pn,)).fetchone()
                if r is not None:
                    found = True
                    break
        con.close()
        out["in_e_inventory"] = found
    except Exception as e:
        out["in_e_inventory"] = None
        out["e_inventory_error"] = str(e)
    return out


def main() -> int:
    ed_db = INV / "ED_CROSS_VOLUME_LINKS.sqlite"
    sel_db = OUT / "SELECTED_D_MANIFEST_REPAIRED.sqlite"
    if not sel_db.exists():
        sel_db = OUT / "SELECTED_D_MANIFEST.sqlite"

    old_cfg_path = OUT / "R9_SAM_SELECTED_SCOPE_CONFIG.json"
    base = json.loads(old_cfg_path.read_text(encoding="utf-8")) if old_cfg_path.exists() else {}
    selected = [r["path"] for r in base.get("enum_roots", [])]

    con = sqlite3.connect(f"file:{ed_db.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = list(con.execute("select * from fs_links order by id"))
    con.close()

    links = []
    runtime_blockers = []
    for r in rows:
        src = r["source_path"]
        rec = r["target_path"]
        src_n = normalize_win_path(src)
        rec_n = normalize_win_path(rec) if rec else None
        cur_rl, rl_err = readlink_target(src)
        cur_n = normalize_win_path(cur_rl) if cur_rl else None
        # final = current readlink only when available; never promote recorded as verified
        final = cur_n
        errors = []
        if rl_err:
            errors.append(rl_err)

        try:
            is_repar = C.is_reparse_path(src)
        except OSError as e:
            is_repar = None
            errors.append(f"ATTR:{e}")

        alive = False
        if is_repar and cur_n:
            alive = target_openable(cur_n)
            if not alive:
                errors.append("CURRENT_TARGET_NOT_OPENABLE")
        elif is_repar and not cur_n:
            alive = False
            errors.append("REPARSE_BUT_TARGET_UNKNOWN")
        elif is_repar is False:
            errors.append("SOURCE_NOT_REPARSE")

        # scope after normalize
        if r["direction"] == "E_TO_D":
            scope_tgt = cur_n or rec_n
            in_scope = any(path_under(scope_tgt, s) for s in selected) if scope_tgt else False
        else:
            scope_tgt = cur_n or rec_n
            in_scope = path_under(scope_tgt, E_SCOPE) if scope_tgt else False

        escape = None
        if r["direction"] == "D_TO_E" and scope_tgt and not path_under(scope_tgt, E_SCOPE):
            escape = "OUTSIDE_E_BLACKBOX"
        if r["direction"] == "E_TO_D" and scope_tgt and not any(path_under(scope_tgt, s) for s in selected):
            # not automatic runtime blocker — content may still be optional
            escape = None

        e_ev = e_inventory_has(scope_tgt) if (r["direction"] == "D_TO_E" and scope_tgt) else None

        item = {
            "id": r["id"],
            "direction": r["direction"],
            "link_type": r["link_type"],
            "source_path": src_n,
            "recorded_target": rec_n,
            "current_readlink_target": cur_n,
            "final_resolved_target": final,
            "source_is_reparse": is_repar,
            "alive": alive,
            "errors": errors,
            "cycle_or_escape": escape,
            "target_in_migration_scope": in_scope,
            "content_included": in_scope,
            "e_inventory_evidence": e_ev,
            "proposed_post_migrate": propose_maps(r["direction"], src_n or src, scope_tgt),
            "evidence": r["evidence"],
        }
        links.append(item)

        # runtime blocker only with concrete citation of missing-in-scope required target
        if r["direction"] == "E_TO_D" and alive and not in_scope:
            runtime_blockers.append(
                {
                    "source_path": src_n,
                    "ref_type": "E_TO_D_JUNCTION",
                    "target_path": scope_tgt,
                    "evidence": "alive_link_target_not_in_selected_enum_roots",
                }
            )
        if r["direction"] == "D_TO_E" and alive and not in_scope:
            runtime_blockers.append(
                {
                    "source_path": src_n,
                    "ref_type": "D_TO_E_JUNCTION",
                    "target_path": scope_tgt,
                    "evidence": "alive_link_target_outside_E_BLACKBOX_after_normalize",
                }
            )

    # reparse nodes in selected manifest
    reparses = []
    if sel_db.exists():
        scon = sqlite3.connect(f"file:{sel_db.as_posix()}?mode=ro", uri=True)
        scon.row_factory = sqlite3.Row
        for n in scon.execute("select path from nodes where is_reparse=1 order by path"):
            p = n["path"]
            rl, err = readlink_target(p)
            rl_n = normalize_win_path(rl)
            match = next((x for x in links if x["source_path"] == p), None)
            direction = "D_TO_E" if path_under(p, "D:\\") else "E_TO_D"
            reparses.append(
                {
                    "path": p,
                    "readlink": rl_n,
                    "readlink_error": err,
                    "matched_fs_link_id": match["id"] if match else None,
                    "in_selected_manifest": True,
                    "proposed_post_migrate": propose_maps(direction, p, rl_n) if rl_n else None,
                }
            )
        scon.close()

    # old inventory junctions not in selected
    out_of_scope = []
    ddb = INV / "D_VOLUME_FILESYSTEM_INVENTORY.sqlite"
    if ddb.exists():
        dcon = sqlite3.connect(f"file:{ddb.as_posix()}?mode=ro", uri=True)
        try:
            for r in dcon.execute(
                "select path, reparse_target from entries where reparse_tag is not null or (reparse_target is not null and reparse_target!='') limit 500"
            ):
                p = r[0]
                if any(path_under(p, s) for s in selected):
                    continue
                out_of_scope.append({"path": p, "status": "OUT_OF_SCOPE", "recorded_target": r[1]})
        except sqlite3.Error:
            pass
        dcon.close()

    optional = [
        {"path": r"D:\MIN_sandbox", "class": "OPTIONAL_RESEARCH_ARCHIVE", "runtime_blocker": False},
        {
            "path": r"D:\CURSOR_TASK_ARCHIVE",
            "class": "OPTIONAL_RESEARCH_ARCHIVE_EXCEPT_EXPLICIT_PIT",
            "runtime_blocker": False,
        },
        {"path": r"D:\国金证券QMT交易端", "class": "OPTIONAL_INSTALL_TREE", "runtime_blocker": False},
    ]

    d_to_e = [x for x in links if x["direction"] == "D_TO_E"]
    e_to_d = [x for x in links if x["direction"] == "E_TO_D"]
    dep_closed = (
        all(x["target_in_migration_scope"] for x in d_to_e)
        and all(x["target_in_migration_scope"] for x in e_to_d)
        and len(runtime_blockers) == 0
        and all(x.get("proposed_post_migrate", {}).get("new_target") for x in d_to_e)
        and all(x.get("proposed_post_migrate", {}).get("new_target") for x in e_to_d)
    )

    dep = {
        "generated_at": now(),
        "task_id": "R9_NOTEBOOK_MANIFEST_REPAIR_20261011_1415",
        "counts": {
            "fs_links": len(links),
            "E_TO_D": len(e_to_d),
            "D_TO_E": len(d_to_e),
            "D_TO_E_in_E_BLACKBOX_scope": sum(1 for x in d_to_e if x["target_in_migration_scope"]),
            "E_TO_D_in_selected_roots": sum(1 for x in e_to_d if x["target_in_migration_scope"]),
            "selected_reparse_nodes": len(reparses),
            "inventory_junctions_out_of_scope_listed": len(out_of_scope),
            "runtime_dependency_blockers": len(runtime_blockers),
        },
        "links": links,
        "selected_manifest_reparse_nodes": reparses,
        "out_of_scope_inventory_junctions": out_of_scope[:50],
        "optional_research_candidates": optional,
        "runtime_dependency_blockers": runtime_blockers,
        "dependency_closure_closed": dep_closed,
        "note": "Unscanned optional trees are not automatic runtime blockers without concrete citations.",
    }
    raw = json.dumps(dep, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    digest = sha_bytes(raw)
    dep["dependency_map_sha256"] = digest
    (OUT / "R9_SAM_DEPENDENCY_MAP_R2.json").write_text(
        json.dumps(dep, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    cfg = {
        "task_id": "R9_NOTEBOOK_MANIFEST_REPAIR_20261011_1415",
        "synthetic": False,
        "required_hostname": None,
        "source_root": "D:\\",
        "budget_sec": 1800,
        "checkpoint_every_sec": 300,
        "enum_roots": base.get("enum_roots", []),
        "dependency_map_sha256": digest,
        "dependency_closure_closed": dep_closed,
        "runtime_dependency_blockers": runtime_blockers,
        "rules": base.get("rules", []),
    }
    cfg["config_sha256"] = canonical_config_sha(cfg)
    (OUT / "R9_SAM_SELECTED_SCOPE_CONFIG_R2.json").write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "dependency_closure_closed": dep_closed,
                "D_TO_E_in_scope": dep["counts"]["D_TO_E_in_E_BLACKBOX_scope"],
                "D_TO_E": dep["counts"]["D_TO_E"],
                "E_TO_D_in_scope": dep["counts"]["E_TO_D_in_selected_roots"],
                "reparse_nodes": len(reparses),
                "runtime_blockers": len(runtime_blockers),
                "config_sha256": cfg["config_sha256"],
                "dependency_map_sha256": digest,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if dep_closed else 3


if __name__ == "__main__":
    raise SystemExit(main())
