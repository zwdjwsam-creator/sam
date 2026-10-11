# -*- coding: utf-8 -*-
"""Export per-link E/D dependency map + selected scope config (read-only on E/D)."""
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
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))
import r9_pilot_common_r9fix as C  # noqa: E402

TZ = timezone(timedelta(hours=8))
FIXED_ROOTS = [
    r"D:\backtest_lab",
    r"D:\backtest_lab_backups",
    r"D:\backtest_lab_candidate_releases",
    r"D:\backtest_lab_shadow_experiments",
    r"D:\blackbox_data",
    r"D:\JQ",
    r"D:\BLACKBOX_DESKTOP_INIT_R1",
    r"D:\BLACKBOX_REMOTE_LINK_R1",
]


def now() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def live_link_status(source: str, recorded_target: str) -> dict:
    info = {
        "source_exists": False,
        "source_is_reparse": None,
        "resolved_target": None,
        "recorded_target": recorded_target,
        "alive": False,
        "cycle_or_escape": None,
        "errors": [],
    }
    try:
        if not os.path.lexists(C.to_win_long_path(source)):
            info["errors"].append("SOURCE_MISSING")
            return info
        info["source_exists"] = True
        try:
            info["source_is_reparse"] = C.is_reparse_path(source)
        except OSError as e:
            info["errors"].append(f"ATTR:{e}")
        # Do not follow for enumeration; try readlink / GetFinalPathName-ish via os.readlink if available
        try:
            resolved = os.readlink(source)
            info["resolved_target"] = resolved
        except OSError:
            # fallback: if recorded target exists as path
            info["resolved_target"] = recorded_target
        tgt = info["resolved_target"] or recorded_target
        # normalize for existence check
        check = tgt
        if check.startswith("\\\\?\\"):
            check = check[4:]
        try:
            info["alive"] = os.path.lexists(C.to_win_long_path(check)) or os.path.lexists(
                C.to_win_long_path(recorded_target)
            )
        except OSError as e:
            info["errors"].append(f"TARGET_CHECK:{e}")
        # escape: target outside D/E known roots roughly
        if tgt:
            tnorm = tgt.replace("/", "\\")
            if not (
                tnorm.upper().startswith("D:\\")
                or tnorm.upper().startswith("E:\\")
                or "CURSOR_TASK_ARCHIVE" in tnorm
                or "backtest_lab" in tnorm.lower()
            ):
                info["cycle_or_escape"] = "POSSIBLE_ESCAPE_OR_OTHER_VOLUME"
    except Exception as e:
        info["errors"].append(f"EXC:{e}")
    return info


def main() -> int:
    ed_db = INV / "ED_CROSS_VOLUME_LINKS.sqlite"
    recheck_path = INV / "ED_LINKS_RECHECK.json"
    con = sqlite3.connect(f"file:{ed_db.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = list(con.execute("select * from fs_links order by id"))
    con.close()

    links = []
    e_to_d_targets: list[str] = []
    for r in rows:
        src = r["source_path"]
        tgt = r["target_path"]
        live = live_link_status(src, tgt)
        item = {
            "id": r["id"],
            "direction": r["direction"],
            "link_type": r["link_type"],
            "source_path": src,
            "recorded_target": tgt,
            "evidence": r["evidence"],
            "db_verified_alive": bool(r["verified_alive"]),
            "live": live,
            "target_in_migration_scope": None,
            "proposed_post_migrate": {
                "layout": "PROPOSED",
                "note": "Desktop E: MarketData 806508DF; do not use old F: maps in exec config",
                "source_compat_keep_d_abs": src if str(src).upper().startswith("D:") else None,
                "new_link_suggestion": None,
            },
        }
        if r["direction"] == "E_TO_D" and tgt:
            e_to_d_targets.append(tgt)
            # proposed: E stays under E:\BLACKBOX\...; D target content moves to E:\BLACKBOX_ENGINES\archive_pit\...
            rel = tgt
            if rel.upper().startswith("D:\\CURSOR_TASK_ARCHIVE\\"):
                item["proposed_post_migrate"]["new_link_suggestion"] = {
                    "link_path_on_E": src,
                    "new_target_on_E": "E:\\BLACKBOX_ENGINES\\CURSOR_TASK_ARCHIVE\\"
                    + rel[len("D:\\CURSOR_TASK_ARCHIVE\\") :],
                }
        links.append(item)

    # selected roots = fixed + unique E→D targets (exact, not wildcards)
    # collapse overlapping: if target under another selected root, keep more specific targets as explicit deps
    selected_roots = list(FIXED_ROOTS)
    explicit_deps = []
    for t in sorted(set(e_to_d_targets)):
        under_fixed = any(t.upper().startswith(r.upper().rstrip("\\") + "\\") or t.upper() == r.upper() for r in FIXED_ROOTS)
        if under_fixed:
            explicit_deps.append({"path": t, "reason": "E_TO_D_TARGET_UNDER_FIXED_ROOT", "enumerate_separately": False})
        else:
            # e.g. under CURSOR_TASK_ARCHIVE — add exact path as enum root (not whole archive)
            explicit_deps.append({"path": t, "reason": "E_TO_D_EXPLICIT_TARGET", "enumerate_separately": True})
            if t not in selected_roots:
                selected_roots.append(t)

    # mark target_in_migration_scope
    sel_norm = [s.rstrip("\\").upper() for s in selected_roots]
    for item in links:
        tgt = (item.get("recorded_target") or "").rstrip("\\").upper()
        item["target_in_migration_scope"] = any(
            tgt == s or tgt.startswith(s + "\\") for s in sel_norm
        ) if tgt else False
        item["content_included"] = item["target_in_migration_scope"]
        item["link_exists_vs_content_included"] = {
            "link_alive": item["live"].get("alive"),
            "content_in_selected_enum": item["content_included"],
            "note": "alive link ≠ content closed into selected manifest",
        }

    # unauthorized expansions
    unauthorized = [
        {
            "path": r"D:\MIN_sandbox",
            "status": "UNAUTHORIZED_FULL_TREE",
            "reason": "would require full-tree scan to close unknown deps; not authorized this round",
        },
        {
            "path": r"D:\CURSOR_TASK_ARCHIVE",
            "status": "UNAUTHORIZED_FULL_TREE",
            "reason": "only explicit E→D pit_products targets authorized, not whole archive",
        },
        {
            "path": r"D:\国金证券QMT交易端",
            "status": "UNRESOLVED_NOT_ENUMERATED",
            "reason": "no explicit link proof this round",
        },
    ]

    dep_map = {
        "generated_at": now(),
        "task_id": "R9_NOTEBOOK_SELECTED_MANIFEST_20261011_1354",
        "hostname": __import__("socket").gethostname(),
        "ed_db": str(ed_db),
        "ed_links_recheck_exists": recheck_path.exists(),
        "ed_links_recheck_path": str(recheck_path) if recheck_path.exists() else None,
        "counts": {
            "fs_links_total": len(links),
            "E_TO_D": sum(1 for x in links if x["direction"] == "E_TO_D"),
            "D_TO_E": sum(1 for x in links if x["direction"] == "D_TO_E"),
            "E_TO_D_live_alive": sum(
                1 for x in links if x["direction"] == "E_TO_D" and x["live"].get("alive")
            ),
            "D_TO_E_live_alive": sum(
                1 for x in links if x["direction"] == "D_TO_E" and x["live"].get("alive")
            ),
        },
        "links": links,
        "explicit_deps": explicit_deps,
        "unauthorized_or_unresolved_boundaries": unauthorized,
        "desktop_target_facts": {
            "hostname_required": "ZHANGWEI",
            "volume": "E:",
            "fs": "NTFS",
            "label": "MarketData",
            "serial": "806508DF",
            "unique_id": "\\\\?\\Volume{b8545ee8-e403-48c6-9d3f-09afd3e0349f}\\",
            "status": "FROM_PRIOR_DESKTOP_EVIDENCE_PROPOSED_ONLY",
        },
        "proposed_layout": {
            "status": "PROPOSED",
            "E_BLACKBOX": r"E:\BLACKBOX",
            "E_BLACKBOX_ENGINES": r"E:\BLACKBOX_ENGINES",
            "old_F_maps": "DO_NOT_USE_IN_EXEC_CONFIG",
        },
    }

    # also attach recheck file digest
    if recheck_path.exists():
        dep_map["ed_links_recheck_sha256"] = sha_bytes(recheck_path.read_bytes())

    raw = json.dumps(dep_map, ensure_ascii=False, indent=2).encode("utf-8")
    (OUT / "R9_SAM_DEPENDENCY_MAP.json").write_bytes(raw)

    enum_roots = []
    for p in selected_roots:
        enum_roots.append(
            {
                "path": p,
                "role": "FIXED_REQUIRED_FAMILY"
                if p in FIXED_ROOTS
                else "EXPLICIT_E_TO_D_TARGET",
                "shadow_not_runtime_claim": p.lower().endswith("backtest_lab_shadow_experiments"),
            }
        )

    config = {
        "generated_at": now(),
        "task_id": "R9_NOTEBOOK_SELECTED_MANIFEST_20261011_1354",
        "source_host": __import__("socket").gethostname(),
        "source_volume_root": "D:\\",
        "budget_sec": 30 * 60,
        "checkpoint_every_sec": 5 * 60,
        "enum_roots": enum_roots,
        "rules": [
            "enumerate all direct children of normal dirs; recurse all normal subdirs",
            "no 40-cap / depth-2 cap",
            "record reparse, do not follow",
            "long-path WinAPI for attrs/identity",
            "write only under C:\\LAN_SHARE_REPORT",
            "read-only on E/D",
        ],
        "dependency_map_sha256": sha_bytes(raw),
        "old_required_bytes_baseline_not_expectation": 8161681208,
    }
    cfg_raw = json.dumps(config, ensure_ascii=False, indent=2).encode("utf-8")
    config["config_sha256"] = sha_bytes(cfg_raw)
    # rewrite with sha inside
    cfg_raw = json.dumps(config, ensure_ascii=False, indent=2).encode("utf-8")
    config["config_sha256"] = sha_bytes(cfg_raw)
    cfg_raw = json.dumps(config, ensure_ascii=False, indent=2).encode("utf-8")
    (OUT / "R9_SAM_SELECTED_SCOPE_CONFIG.json").write_bytes(cfg_raw)

    # copy recheck into OUT for hub upload packaging
    if recheck_path.exists():
        (OUT / "ED_LINKS_RECHECK.json").write_bytes(recheck_path.read_bytes())

    print(
        json.dumps(
            {
                "dependency_map": str(OUT / "R9_SAM_DEPENDENCY_MAP.json"),
                "config": str(OUT / "R9_SAM_SELECTED_SCOPE_CONFIG.json"),
                "config_sha256": config["config_sha256"],
                "enum_roots": len(enum_roots),
                "E_TO_D": dep_map["counts"]["E_TO_D"],
                "D_TO_E": dep_map["counts"]["D_TO_E"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
