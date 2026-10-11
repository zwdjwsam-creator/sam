# -*- coding: utf-8 -*-
"""Repair selected manifest from existing DB copy — no full rescan unless audit requires it."""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(r"C:\LAN_SHARE_REPORT")
OUT = ROOT / "BLACKBOX_R9_SELECTED_MANIFEST"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(OUT))

import selected_manifest_enumerator_r2 as E  # noqa: E402

ORIG = OUT / "SELECTED_D_MANIFEST.sqlite"
REPAIRED = OUT / "SELECTED_D_MANIFEST_REPAIRED.sqlite"
ORIG_SHA_EXPECT = "787b14d267b3b167b37695adbdffaba96c719ed50bf64659ba4ba3828f630d39"


def file_sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def audit(con: sqlite3.Connection) -> dict:
    q = {
        s: con.execute("select count(*) from queue where status=?", (s,)).fetchone()[0]
        for s in ("pending", "in_progress", "done", "error")
    }
    d = {
        s: con.execute("select count(*) from dir_enum where status=?", (s,)).fetchone()[0]
        for s in ("ENUM_DONE", "ERROR", "PENDING_CHANGED")
    }
    return {
        "queue": q,
        "dir_enum": d,
        "files_bad": con.execute(
            "select count(*) from nodes where is_dir=0 and is_reparse=0 and (file_id is null or identity_err is not null or access_err is not null)"
        ).fetchone()[0],
        "nodes": con.execute("select count(*) from nodes").fetchone()[0],
        "needs_targeted_reenum": (
            q["in_progress"] > 0
            or q["pending"] > 0
            or q["error"] > 0
            or d["ERROR"] > 0
            or d["PENDING_CHANGED"] > 0
        ),
    }


def main() -> int:
    if not ORIG.exists():
        print(json.dumps({"ok": False, "error": "ORIG_MISSING"}))
        return 2
    orig_sha = file_sha(ORIG)
    if orig_sha != ORIG_SHA_EXPECT:
        print(json.dumps({"ok": False, "error": "ORIG_SHA_MISMATCH", "got": orig_sha, "expect": ORIG_SHA_EXPECT}))
        return 2

    if REPAIRED.exists():
        REPAIRED.unlink()
    shutil.copy2(ORIG, REPAIRED)

    con = E.connect(REPAIRED, rw=True)
    E.init_db(con)
    # recover any stuck in_progress
    con.execute("update queue set status='pending' where status='in_progress'")
    con.commit()
    aud = audit(con)
    content = E.compute_content_stats(con)

    # load/create r2 config (export may refresh later)
    cfg_path = OUT / "R9_SAM_SELECTED_SCOPE_CONFIG_R2.json"
    if not cfg_path.exists():
        old = json.loads((OUT / "R9_SAM_SELECTED_SCOPE_CONFIG.json").read_text(encoding="utf-8"))
        cfg = {
            "task_id": "R9_NOTEBOOK_MANIFEST_REPAIR_20261011_1415",
            "synthetic": False,
            "required_hostname": None,
            "source_root": "D:\\",
            "budget_sec": 1800,
            "checkpoint_every_sec": 300,
            "enum_roots": old["enum_roots"],
            "dependency_closure_closed": False,
            "runtime_dependency_blockers": [],
            "rules": old.get("rules", []),
        }
        cfg["config_sha256"] = E.canonical_config_sha(cfg)
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        E.verify_config(cfg)

    # bind volume from meta if present; do not force live D probe if already bound
    prev_vol = E.meta_get(con, "source_volume_serial")
    if not prev_vol:
        # read-only bind from first root
        try:
            vol = E.bind_volume_for_roots([r["path"] for r in cfg["enum_roots"]], allow_unknown=False)
            E.meta_set(con, "source_volume_serial", vol)
        except Exception as e:
            print(json.dumps({"ok": False, "error": f"VOLUME_BIND:{e}"}))
            con.close()
            return 2
        prev_vol = vol
    E.meta_set(con, "config_sha256", cfg["config_sha256"])
    con.commit()

    # targeted reenum only if audit requires
    elapsed = 0.0
    if aud["needs_targeted_reenum"]:
        con.close()
        summary_run = E.run_batch(cfg_path, REPAIRED, budget_sec=min(1800, int(cfg.get("budget_sec", 1800))))
        stop_reason = summary_run.get("stop_reason")
        elapsed = summary_run.get("elapsed_sec", 0)
        con = E.connect(REPAIRED, rw=True)
        aud = audit(con)
        content = E.compute_content_stats(con)
    else:
        # reuse complete enumeration; stop_reason must be QUEUE_EMPTY for proven fields
        stop_reason = "QUEUE_EMPTY"

    snap = OUT / "SELECTED_D_MANIFEST_REPAIRED.snapshot.sqlite"
    con.close()
    snap_sha = E.snapshot_db_sha(REPAIRED, snap)
    con = E.connect(REPAIRED, rw=True)
    # refresh cfg after possible export later — use current
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    # temporary dep fields until export updates
    summary = E.build_summary(con, cfg, cfg["config_sha256"], REPAIRED, snap_sha, stop_reason, elapsed)
    summary["original_db"] = str(ORIG)
    summary["original_db_sha256"] = orig_sha
    summary["repaired_db"] = str(REPAIRED)
    summary["repaired_db_bytes"] = REPAIRED.stat().st_size
    summary["audit_before_finalize"] = aud
    summary["content_stats"] = content
    # legacy aliases for readers
    summary["unique_file_entities"] = content["unique_file_entities"]
    summary["unique_content_bytes"] = content["unique_content_bytes"]
    summary["unique_entities_LEGACY_WRONG_INCLUDES_DIRS"] = None
    summary["unique_bytes_LEGACY_WRONG_INCLUDES_DIRS"] = None
    E.meta_set(con, "last_summary_json", json.dumps(summary, ensure_ascii=False))
    con.commit()
    con.close()

    (OUT / "R9_SAM_MANIFEST_REPAIR_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # resume slim
    resume = {
        "generated_at": summary["generated_at"],
        "task_id": summary["task_id"],
        "config_sha256": summary["config_sha256"],
        "source_volume_serial": prev_vol,
        "queue": summary["queue"],
        "dir_enum": summary["dir_enum"],
        "enumeration_complete": summary["enumeration_complete"],
        "identity_complete": summary["identity_complete"],
        "content_stats": content,
        "manifest_db": str(REPAIRED),
        "manifest_snapshot_sha256": snap_sha,
        "original_db_sha256": orig_sha,
        "stop_reason": stop_reason,
    }
    (OUT / "R9_SAM_MANIFEST_REPAIR_RESUME_STATE.json").write_text(
        json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "ok": True,
                "needs_targeted_reenum": aud["needs_targeted_reenum"],
                "unique_file_entities": content["unique_file_entities"],
                "unique_content_bytes": content["unique_content_bytes"],
                "snap_sha": snap_sha,
                "enumeration_complete": summary["enumeration_complete"],
                "identity_complete": summary["identity_complete"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
