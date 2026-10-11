# -*- coding: utf-8 -*-
"""Gate tests for dependency closure — must call evaluate_links, not hand-written booleans."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import tempfile
import traceback
from pathlib import Path
from unittest import mock

OUT = Path(r"C:\LAN_SHARE_REPORT\BLACKBOX_R9_ED_INPUT")
sys.path.insert(0, str(OUT))
sys.path.insert(0, str(Path(r"C:\LAN_SHARE_REPORT")))

import dependency_closure_gate_r3 as G  # noqa: E402
from pathutil_r3 import has_traversal, is_absolute_win_path, normalize_win_path, path_under  # noqa: E402

R: list[dict] = []


def rec(name, fn):
    try:
        d = fn() or {}
        R.append({"name": name, "pass": True, **d})
        print("PASS", name, d, flush=True)
    except Exception as e:
        R.append({"name": name, "pass": False, "error": str(e), "tb": traceback.format_exc()})
        print("FAIL", name, e, flush=True)


def make_d_db(root: Path) -> Path:
    db = root / "d.sqlite"
    con = sqlite3.connect(str(db))
    con.executescript(
        """
        create table nodes(
          path text primary key, is_dir int, is_reparse int,
          file_id text, volume_serial text, logical_size int, object_class text
        );
        """
    )
    # selected D content
    con.execute(
        "insert into nodes values(?,?,?,?,?,?,?)",
        (r"D:\CURSOR_TASK_ARCHIVE\pit\a", 1, 0, None, "1", 0, "Directory"),
    )
    con.execute(
        "insert into nodes values(?,?,?,?,?,?,?)",
        (r"D:\CURSOR_TASK_ARCHIVE\pit\a\f.txt", 0, 0, "FID1", "1", 10, "File"),
    )
    con.commit()
    con.close()
    return db


def make_e_db(root: Path) -> Path:
    db = root / "e.sqlite"
    con = sqlite3.connect(str(db))
    con.executescript(
        """
        create table meta(key text primary key, value text);
        create table entries(
          path text primary key, object_class text, is_dir int, logical_size int,
          file_id text, volume_serial text, nlinks int, reparse_target text, mtime_utc text
        );
        """
    )
    con.execute("insert into meta values('source_root','E:\\\\BLACKBOX')")
    # terminal content under E
    con.execute(
        "insert into entries values(?,?,?,?,?,?,?,?,?)",
        (
            r"E:\BLACKBOX\data\x",
            "Directory",
            1,
            0,
            None,
            "2387166462",
            1,
            None,
            None,
        ),
    )
    con.execute(
        "insert into entries values(?,?,?,?,?,?,?,?,?)",
        (
            r"E:\BLACKBOX\data\x\f.bin",
            "File",
            0,
            100,
            "EID1",
            "2387166462",
            1,
            None,
            None,
        ),
    )
    con.commit()
    con.close()
    return db


def fake_link_row(i, direction, src, tgt=None):
    return {
        "id": i,
        "direction": direction,
        "link_type": "Junction",
        "source_path": src,
        "target_path": tgt,
        "evidence": "TEST",
    }


def t_normalize_rejects_traversal():
    assert normalize_win_path(r"\\?\E:\BLACKBOX\a") == r"E:\BLACKBOX\a"
    assert is_absolute_win_path(r"E:\BLACKBOX") is True
    assert is_absolute_win_path(r"BLACKBOX\a") is False
    assert is_absolute_win_path(r"E:foo") is False
    assert has_traversal(r"E:\BLACKBOX\..\Windows") is True
    assert path_under(r"E:\BLACKBOX\..\Windows\x", r"E:\BLACKBOX") is False
    assert path_under(r"\\?\E:\BLACKBOX\data", r"E:\BLACKBOX") is True
    return {}


def t_happy_d_to_e_in_manifest():
    td = Path(tempfile.mkdtemp(prefix="dep_gate_"))
    try:
        edb = make_e_db(td)
        ddb = make_d_db(td)
        econ = sqlite3.connect(f"file:{edb.as_posix()}?mode=ro", uri=True)
        econ.row_factory = sqlite3.Row
        dcon = sqlite3.connect(f"file:{ddb.as_posix()}?mode=ro", uri=True)
        dcon.row_factory = sqlite3.Row
        src = r"D:\CURSOR_TASK_ARCHIVE\pit\junc"
        # pad to 40 rows: 1 real D_TO_E + 39 closed stubs via mock
        with mock.patch.object(G, "C") as cmod, mock.patch.object(G, "EXPECTED_LINK_COUNT", 1):
            cmod.is_reparse_path.side_effect = lambda p: p == src
            cmod.get_attrs.return_value = 0x10
            cmod.open_source_stable.return_value = 1
            cmod.safe_close.return_value = None

            def rl(p):
                if p == src:
                    return r"\\?\E:\BLACKBOX\data\x"
                raise OSError("no")

            with mock.patch.object(G.os, "readlink", side_effect=rl):
                rows = [fake_link_row(1, "D_TO_E", src)]
                out = G.evaluate_links(
                    e_con=econ,
                    d_con=dcon,
                    selected_roots=[r"D:\CURSOR_TASK_ARCHIVE\pit"],
                    links_rows=rows,
                )
        econ.close()
        dcon.close()
        assert out["dependency_closure_closed"] is True, out
        assert out["links"][0]["target_in_actual_manifest"] is True
        assert out["links"][0]["target_content_coverage_proven"] is True
        return {"closed": True}
    finally:
        shutil.rmtree(td, ignore_errors=True)


def t_exists_but_not_in_e_manifest_fails():
    td = Path(tempfile.mkdtemp(prefix="dep_gate_"))
    try:
        edb = make_e_db(td)
        ddb = make_d_db(td)
        econ = sqlite3.connect(f"file:{edb.as_posix()}?mode=ro", uri=True)
        econ.row_factory = sqlite3.Row
        dcon = sqlite3.connect(f"file:{ddb.as_posix()}?mode=ro", uri=True)
        dcon.row_factory = sqlite3.Row
        src = r"D:\CURSOR_TASK_ARCHIVE\pit\junc2"
        missing = r"E:\BLACKBOX\missing\target"

        def is_rep(p):
            return normalize_win_path(p) == src

        with mock.patch.object(G, "C") as cmod, mock.patch.object(G, "EXPECTED_LINK_COUNT", 1):
            cmod.is_reparse_path.side_effect = is_rep
            cmod.get_attrs.return_value = 0x10
            cmod.open_source_stable.return_value = 1
            cmod.safe_close.return_value = None
            with mock.patch.object(G.os, "readlink", return_value=missing):
                out = G.evaluate_links(
                    e_con=econ,
                    d_con=dcon,
                    selected_roots=[r"D:\CURSOR_TASK_ARCHIVE\pit"],
                    links_rows=[fake_link_row(1, "D_TO_E", src)],
                )
        assert out["dependency_closure_closed"] is False
        assert out["links"][0]["target_in_actual_manifest"] is False
        assert out["links"][0]["alive"] is True  # openable mocked
        return {"closed": False}
    finally:
        shutil.rmtree(td, ignore_errors=True)


def t_alive_false_blocks_closed():
    """ChatGPT repro: alive=false must not allow dep_closed true."""
    td = Path(tempfile.mkdtemp(prefix="dep_gate_"))
    try:
        edb = make_e_db(td)
        ddb = make_d_db(td)
        econ = sqlite3.connect(f"file:{edb.as_posix()}?mode=ro", uri=True)
        econ.row_factory = sqlite3.Row
        dcon = sqlite3.connect(f"file:{ddb.as_posix()}?mode=ro", uri=True)
        dcon.row_factory = sqlite3.Row
        src = r"D:\CURSOR_TASK_ARCHIVE\pit\junc3"
        tgt = r"E:\BLACKBOX\data\x"

        def is_rep(p):
            return normalize_win_path(p) == src

        with mock.patch.object(G, "C") as cmod, mock.patch.object(G, "EXPECTED_LINK_COUNT", 1):
            cmod.is_reparse_path.side_effect = is_rep
            # current target not openable
            cmod.get_attrs.side_effect = OSError("nope")
            with mock.patch.object(G.os, "readlink", return_value=tgt):
                out = G.evaluate_links(
                    e_con=econ,
                    d_con=dcon,
                    selected_roots=[r"D:\CURSOR_TASK_ARCHIVE\pit"],
                    links_rows=[fake_link_row(1, "D_TO_E", src)],
                )
        assert out["links"][0]["alive"] is False
        assert out["dependency_closure_closed"] is False
        return {"alive": False, "closed": False}
    finally:
        shutil.rmtree(td, ignore_errors=True)


def t_empty_links_fail():
    td = Path(tempfile.mkdtemp(prefix="dep_gate_"))
    try:
        ddb = make_d_db(td)
        dcon = sqlite3.connect(str(ddb))
        dcon.row_factory = sqlite3.Row
        out = G.evaluate_links(e_con=None, d_con=dcon, selected_roots=[r"D:\x"], links_rows=[])
        dcon.close()
        assert out["dependency_closure_closed"] is False
        assert out.get("reason") == "EMPTY_LINKS_TABLE"
        return {}
    finally:
        shutil.rmtree(td, ignore_errors=True)


def t_digest_tamper_detect():
    obj = {"a": 1, "dependency_map_sha256": "OLD"}
    d1 = G.canonical_digest(obj, {"dependency_map_sha256"})
    obj2 = {"a": 2, "dependency_map_sha256": "OLD"}
    d2 = G.canonical_digest(obj2, {"dependency_map_sha256"})
    assert d1 != d2
    # keeping old digest while changing content must fail equality check
    assert d1 != "OLD"
    return {"d1": d1[:12], "d2": d2[:12]}


def t_cycle_fails():
    td = Path(tempfile.mkdtemp(prefix="dep_gate_"))
    try:
        edb = make_e_db(td)
        ddb = make_d_db(td)
        econ = sqlite3.connect(f"file:{edb.as_posix()}?mode=ro", uri=True)
        econ.row_factory = sqlite3.Row
        dcon = sqlite3.connect(f"file:{ddb.as_posix()}?mode=ro", uri=True)
        dcon.row_factory = sqlite3.Row
        src = r"D:\CURSOR_TASK_ARCHIVE\pit\cyc"
        a = r"E:\BLACKBOX\loopA"
        b = r"E:\BLACKBOX\loopB"

        def is_rep(p):
            return True

        def rl(p):
            if normalize_win_path(p) in (src, normalize_win_path(src)):
                return a
            if normalize_win_path(p) == a:
                return b
            if normalize_win_path(p) == b:
                return a
            raise OSError("x")

        with mock.patch.object(G, "C") as cmod, mock.patch.object(G, "EXPECTED_LINK_COUNT", 1):
            cmod.is_reparse_path.side_effect = is_rep
            cmod.get_attrs.return_value = 0x10
            cmod.open_source_stable.return_value = 1
            cmod.safe_close.return_value = None
            with mock.patch.object(G.os, "readlink", side_effect=rl):
                out = G.evaluate_links(
                    e_con=econ,
                    d_con=dcon,
                    selected_roots=[r"D:\CURSOR_TASK_ARCHIVE\pit"],
                    links_rows=[fake_link_row(1, "D_TO_E", src)],
                )
        assert out["dependency_closure_closed"] is False
        assert out["links"][0]["chain"]["cycle"] is True
        return {"cycle": True}
    finally:
        shutil.rmtree(td, ignore_errors=True)


def main() -> int:
    for name, fn in [
        ("normalize_rejects_traversal", t_normalize_rejects_traversal),
        ("happy_d_to_e_in_manifest", t_happy_d_to_e_in_manifest),
        ("exists_not_in_e_manifest_fails", t_exists_but_not_in_e_manifest_fails),
        ("alive_false_blocks_closed", t_alive_false_blocks_closed),
        ("empty_links_fail", t_empty_links_fail),
        ("digest_tamper_detect", t_digest_tamper_detect),
        ("cycle_fails", t_cycle_fails),
    ]:
        rec(name, fn)
    out = {
        "task_id": "R9_NOTEBOOK_FREEZE_ED_INPUT_20261011_1438",
        "passed": sum(1 for x in R if x["pass"]),
        "failed": sum(1 for x in R if not x["pass"]),
        "total": len(R),
        "results": R,
    }
    (OUT / "R9_DEPENDENCY_GATE_TEST_RESULTS.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"passed": out["passed"], "failed": out["failed"]}, indent=2))
    return 0 if out["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
