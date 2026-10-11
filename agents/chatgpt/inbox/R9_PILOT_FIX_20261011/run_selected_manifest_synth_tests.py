# -*- coding: utf-8 -*-
"""C: synthetic tests for selected manifest enumerator — real FS, no mocks for PASS."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import traceback
from pathlib import Path

ROOT = Path(r"C:\LAN_SHARE_REPORT")
OUT = ROOT / "BLACKBOX_R9_SELECTED_MANIFEST"
WORK = OUT / "_synth"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(OUT))

import selected_manifest_enumerator as E  # noqa: E402

R = []


def ok(name, fn):
    try:
        fn()
        R.append({"name": name, "pass": True})
        print("PASS", name, flush=True)
    except Exception as e:
        R.append({"name": name, "pass": False, "error": str(e), "tb": traceback.format_exc()})
        print("FAIL", name, e, flush=True)


def build_tree():
    if WORK.exists():
        shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True)
    root = WORK / "root"
    root.mkdir()
    for i in range(45):
        (root / f"f_{i:02d}.txt").write_text(f"x{i}", encoding="utf-8")
    d = root / "d1" / "d2" / "d3"
    d.mkdir(parents=True)
    (d / "deep.bin").write_bytes(b"DEEP")
    (root / "empty").mkdir()
    target = WORK / "link_tgt"
    target.mkdir()
    (target / "only_in_tgt.txt").write_text("tgt", encoding="utf-8")
    link = root / "junc"
    os.system(f'cmd /c mklink /J "{link}" "{target}" >nul 2>nul')
    return root


def dump_cfg(path: Path, root_path: Path, budget: int, sha: str):
    path.write_text(
        json.dumps(
            {
                "task_id": "SYNTH",
                "budget_sec": budget,
                "checkpoint_every_sec": 1000,
                "enum_roots": [{"path": str(root_path), "role": "SYNTH"}],
                "config_sha256": sha,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def t_full_children_and_depth():
    root = build_tree()
    cfg = WORK / "cfg.json"
    db = WORK / "m1.sqlite"
    dump_cfg(cfg, root, 120, "SYNTH_FIXED_SHA_V0")
    summary = E.run_batch(cfg, db, budget_sec=120)
    con = sqlite3.connect(str(db))
    n_files = con.execute("select count(*) from nodes where is_dir=0 and is_reparse=0").fetchone()[0]
    deep = con.execute(
        "select count(*) from nodes where path like ?",
        (str(root / "d1" / "d2" / "d3") + "%",),
    ).fetchone()[0]
    empty = con.execute(
        "select status, child_count from dir_enum where path=?",
        (str(root / "empty"),),
    ).fetchone()
    junc = con.execute("select is_reparse from nodes where path=?", (str(root / "junc"),)).fetchone()
    leaked = con.execute(
        "select count(*) from nodes where path like ?",
        (str(root / "junc") + "\\%",),
    ).fetchone()[0]
    con.close()
    assert n_files >= 46, n_files
    assert deep >= 1
    assert empty is not None and empty[0] == "ENUM_DONE" and empty[1] == 0
    assert junc is not None and int(junc[0]) == 1
    assert leaked == 0
    assert summary["queue_pending"] == 0


def t_mid_stop_resume():
    root = build_tree()
    cfg = WORK / "cfg2.json"
    db = WORK / "m2.sqlite"
    dump_cfg(cfg, root, 1, "SYNTH_FIXED_SHA_V1")
    E.run_batch(cfg, db, budget_sec=1)
    con = sqlite3.connect(str(db))
    nodes1 = con.execute("select count(*) from nodes").fetchone()[0]
    con.close()
    dump_cfg(cfg, root, 120, "SYNTH_FIXED_SHA_V1")
    E.run_batch(cfg, db, budget_sec=120)
    con = sqlite3.connect(str(db))
    pending2 = con.execute("select count(*) from queue where status='pending'").fetchone()[0]
    nodes2 = con.execute("select count(*) from nodes").fetchone()[0]
    dup = con.execute("select path, count(*) c from nodes group by path having c>1").fetchall()
    con.close()
    assert pending2 == 0
    assert nodes2 >= nodes1
    assert not dup


def t_missing_after_reenum():
    root = build_tree()
    cfg = WORK / "cfg3.json"
    db = WORK / "m3.sqlite"
    dump_cfg(cfg, root, 120, "SYNTH_FIXED_SHA_V3")
    E.run_batch(cfg, db, budget_sec=120)
    victim = root / "f_00.txt"
    victim.unlink()
    con = sqlite3.connect(str(db))
    con.execute("update queue set status='pending' where path=?", (str(root),))
    con.execute("delete from nodes where path=?", (str(victim),))
    con.commit()
    con.close()
    E.run_batch(cfg, db, budget_sec=60)
    con = sqlite3.connect(str(db))
    still = con.execute("select 1 from nodes where path=?", (str(victim),)).fetchone()
    con.close()
    assert still is None


def t_parent_done_old_child_missing_diff():
    db = WORK / "m4.sqlite"
    if db.exists():
        db.unlink()
    parent = str(WORK / "p")
    child = str(WORK / "p" / "c.txt")
    Path(parent).mkdir(parents=True, exist_ok=True)
    con = E.connect(db, rw=True)
    E.init_db(con)
    con.execute(
        "insert into dir_enum(path,status,child_count,started_at,finished_at,before_mtime_ft,after_mtime_ft,error) values(?,?,?,?,?,?,?,?)",
        (parent, "ENUM_DONE", 0, "t", "t", None, None, None),
    )
    con.execute(
        "insert into nodes(path,parent,name,is_dir,is_reparse,attrs,logical_size,volume_serial,file_id,nlinks,mtime_ft,mtime_iso,identity_err,access_err,object_class,updated_at) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (parent, str(WORK), "p", 1, 0, 16, 0, "1", "1", 1, None, None, None, None, "Directory", "t"),
    )
    con.commit()
    old_idx = {
        child: {
            "path": child,
            "parent": parent,
            "name": "c.txt",
            "is_dir": 0,
            "attrs": 32,
            "logical_size": 1,
            "volume_serial": "1",
            "file_id": "9",
            "mtime_utc": None,
            "identity_err": None,
            "reparse_tag": None,
        }
    }
    E.compare_with_old(con, old_idx)
    con.commit()
    n = con.execute("select count(*) from diffs where kind='OLD_DB_NOT_IN_LIVE'").fetchone()[0]
    con.close()
    assert n >= 1


def main():
    ok("full_children_depth_junction_empty", t_full_children_and_depth)
    ok("mid_stop_resume", t_mid_stop_resume)
    ok("missing_after_reenum", t_missing_after_reenum)
    ok("parent_done_old_child_missing_diff", t_parent_done_old_child_missing_diff)
    out = {
        "generated_at": E.now(),
        "passed": sum(1 for x in R if x["pass"]),
        "failed": sum(1 for x in R if not x["pass"]),
        "results": R,
    }
    (OUT / "R9_SELECTED_MANIFEST_SYNTH_TEST_RESULTS.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"passed": out["passed"], "failed": out["failed"]}, indent=2))
    return 0 if out["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
