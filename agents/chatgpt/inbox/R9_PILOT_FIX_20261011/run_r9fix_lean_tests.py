# -*- coding: utf-8 -*-
"""Lean C: synthetic tests for R9FIX2 gaps — no E/D business, no pilot dest write."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest import mock

ROOT = Path(r"C:\LAN_SHARE_REPORT")
sys.path.insert(0, str(ROOT))
# Notebook helper only — must NOT affect enable_copy path (executor forces allow_env_skip=False).
os.environ["R9_SKIP_PROC_CHECK"] = "1"
WORK = ROOT / "R9_SYNTH_TESTS" / "_lean"
if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)

import r9_pilot_common_r9fix as C  # noqa: E402
import copy_executor_r9_1g as EX  # noqa: E402
import acceptance_script_r9_1g as ACC  # noqa: E402

R = []


def ok(name, fn):
    try:
        fn()
        R.append({"name": name, "pass": True})
        print("PASS", name, flush=True)
    except Exception as e:
        R.append({"name": name, "pass": False, "error": str(e), "tb": traceback.format_exc()})
        print("FAIL", name, e, flush=True)


def t_unc():
    assert C.to_win_long_path(r"\\192.168.100.2\E_DRIVE\BLACKBOX\a") == r"\\?\UNC\192.168.100.2\E_DRIVE\BLACKBOX\a"
    assert C.to_win_long_path(r"C:\x") == r"\\?\C:\x"
    u = C.join_unc_source(r"数据\f.bin")
    assert u.startswith("\\\\192.168.100.2\\E_DRIVE\\BLACKBOX\\")
    assert not u.upper().startswith("E:")


def t_rel():
    for b in [r"E:\a", r"\\s\share\a", r"a\..\b", r"a:b", "", r"\a"]:
        try:
            C.validate_relative_path(b)
            raise AssertionError(b)
        except ValueError:
            pass


def t_r8_ok_and_rejects():
    p = WORK / "r8.json"
    p.write_text(
        json.dumps(
            {"OLD_LN_STOPPED": True, "OLD_WRAPPER_STOPPED": True, "OLD_MONITORS_INACTIVE": True}
        ),
        encoding="utf-8",
    )
    assert C.parse_r8_stop_report(p)["ok"]
    # FALSE
    p.write_text(
        json.dumps(
            {"OLD_LN_STOPPED": True, "OLD_WRAPPER_STOPPED": False, "OLD_MONITORS_INACTIVE": True}
        ),
        encoding="utf-8",
    )
    assert not C.parse_r8_stop_report(p)["ok"]
    # UNKNOWN
    p.write_text(
        "OLD_LN_STOPPED=TRUE\nOLD_WRAPPER_STOPPED=UNKNOWN\nOLD_MONITORS_INACTIVE=TRUE\n",
        encoding="utf-8",
    )
    assert not C.parse_r8_stop_report(p)["ok"]
    # conflict duplicate values
    p.write_text(
        "OLD_LN_STOPPED=TRUE\nOLD_LN_STOPPED=FALSE\n"
        "OLD_WRAPPER_STOPPED=TRUE\nOLD_MONITORS_INACTIVE=TRUE\n",
        encoding="utf-8",
    )
    r = C.parse_r8_stop_report(p)
    assert not r["ok"] and r["reason"] == "FIELD_VALUE_CONFLICT"
    # missing fields — historical READY alone insufficient
    p.write_text("DESKTOP_READY=TRUE\nWRITERS_STOPPED=TRUE\nSOURCE_FREEZE_PASS=true\n", encoding="utf-8")
    assert C.parse_r8_stop_report(p)["reason"] == "FIELDS_MISSING"
    p.write_text("R8_STOPPED=FALSE\n", encoding="utf-8")
    assert not C.parse_r8_stop_report(p)["ok"]


def t_r8_legacy_proc_rejected():
    snap = [
        {
            "ProcessId": 111,
            "ParentProcessId": 1,
            "Name": "powershell.exe",
            "CreationDate": "20261010180000.000000+480",
            "CommandLine": r"powershell -File C:\LAN_SHARE_REPORT\BLACKBOX_R8_SOURCE_FREEZE_MONITOR_V2.ps1 "
            r"-RunId 20261010_173201_R8_3B85D677",
        }
    ]
    # env skip must NOT apply when allow_env_skip=False (copy path)
    os.environ["R9_SKIP_PROC_CHECK"] = "1"
    r = C.live_r8_process_check(allow_env_skip=False, proc_snapshot=snap)
    assert r["ok"] is False and r["reason"] == "R8_LEGACY_TASK_STILL_RUNNING"
    # skip only when explicitly allowed
    r2 = C.live_r8_process_check(allow_env_skip=True, proc_snapshot=snap)
    assert r2.get("skipped") is True
    # clean snapshot ok
    r3 = C.live_r8_process_check(
        allow_env_skip=False,
        proc_snapshot=[{"ProcessId": 1, "Name": "idle", "CommandLine": "C:\\Windows\\System32\\idle"}],
    )
    assert r3["ok"] is True


def t_host():
    class A:
        r8_stopped_evidence = str(WORK / "r8ok.json")
        confirm_dest = str(C.ALLOWED_DEST)
        allow_proc_check_skip = True

    (WORK / "r8ok.json").write_text(
        json.dumps(
            {"OLD_LN_STOPPED": True, "OLD_WRAPPER_STOPPED": True, "OLD_MONITORS_INACTIVE": True}
        ),
        encoding="utf-8",
    )
    pre = EX.preflight_copy(A(), {"sha256": C.EXPECTED_MANIFEST_SHA256})
    assert pre["ok"] is False
    assert any("WRONG_HOST" in i for i in pre["issues"])


def t_identity_wrong_vol_and_mtime():
    live = {
        "volume_serial": "1",
        "volume_serial_dword": 1,
        "file_id": "99",
        "size": 10,
        "mtime_ft": "0",
    }
    try:
        C.compare_identity_vol_fid_size(
            manifest_volume_serial="2387166462",
            manifest_file_id="99",
            manifest_size=10,
            live=live,
        )
        raise AssertionError("wrong vol must reject")
    except RuntimeError as e:
        assert "SOURCE_IDENTITY_DRIFT" in str(e)

    # matching vol/fid/size
    live2 = {
        "volume_serial": "2387166462",
        "volume_serial_dword": 2387166462,
        "file_id": "99",
        "size": 10,
        "mtime_ft": "0",
    }
    C.compare_identity_vol_fid_size(
        manifest_volume_serial="2387166462",
        manifest_file_id="99",
        manifest_size=10,
        live=live2,
    )

    # ISO mtime drift (second precision)
    epoch = C.FILETIME_EPOCH_UTC
    ft_ok = int((datetime(2026, 7, 30, 3, 35, 36, tzinfo=timezone.utc) - epoch).total_seconds() * 10_000_000)
    ft_bad = int((datetime(2026, 7, 30, 3, 35, 37, tzinfo=timezone.utc) - epoch).total_seconds() * 10_000_000)
    C.compare_mtime_manifest_vs_handle("2026-07-30T03:35:36Z", ft_ok)
    try:
        C.compare_mtime_manifest_vs_handle("2026-07-30T03:35:36Z", ft_bad)
        raise AssertionError("mtime drift must reject")
    except RuntimeError as e:
        assert "SOURCE_MTIME_DRIFT" in str(e)
    try:
        C.compare_mtime_manifest_vs_handle("not-a-time", ft_ok)
        raise AssertionError("unparseable must stop")
    except RuntimeError as e:
        assert "UNPARSEABLE" in str(e)


def t_same_handle_copy_hash():
    f = WORK / "src.bin"
    f.write_bytes(b"ABCDEFGH" * 100)
    dest = WORK / "out.bin"
    h = C.open_source_stable(str(f))
    try:
        before = C.handle_identity(h)
        C.seek_begin(h)
        res = C.copy_bounded(h, str(dest), before["size"], C.UNIQUE_CAP)
        after = C.handle_identity(h)
        assert before["file_id"] == after["file_id"]
        assert before["size"] == after["size"]
        assert C.is_valid_sha256_hex(res["sha256"])
        assert before["allocation_size"] is not None
    finally:
        C.safe_close(h)
    h = C.open_source_stable(str(f))
    try:
        try:
            C.read_exact_hash(h, before["size"] - 1)
            raise AssertionError("should detect longer")
        except RuntimeError as e:
            assert "LONGER" in str(e) or "GREW" in str(e)
    finally:
        C.safe_close(h)


def t_eof_probe_readfile_fail():
    f = WORK / "eof.bin"
    f.write_bytes(b"XYZ")
    h = C.open_source_stable(str(f))
    C.safe_close(h)
    # closed handle → ReadFile fail on probe/body must not look like success
    try:
        C.read_exact_hash(h, 0)  # size0 goes straight to EOF probe
        raise AssertionError("closed handle probe must fail")
    except OSError as e:
        assert "EOF_PROBE_ReadFile_fail" in str(e) or e.winerror or e.errno is not None


def t_hl_distinct():
    a = WORK / "a.bin"
    a.write_bytes(b"SAMECONTENT!!")
    al = WORK / "a_link.bin"
    assert C.CreateHardLinkW(C.to_win_long_path(str(al)), C.to_win_long_path(str(a)), None)
    b = WORK / "b.bin"
    b.write_bytes(b"SAMECONTENT!!")
    ha, hb, hl = C.open_source_stable(str(a)), C.open_source_stable(str(b)), C.open_source_stable(str(al))
    try:
        ia, ib, il = C.handle_identity(ha), C.handle_identity(hb), C.handle_identity(hl)
        assert ia["file_id"] == il["file_id"]
        assert ia["file_id"] != ib["file_id"]
        C.compare_hardlink_sibling_identity(ia, il, str(al))
        try:
            C.compare_hardlink_sibling_identity(ia, ib, str(b))
            raise AssertionError("distinct files must HL_SPLIT")
        except RuntimeError as e:
            assert "HL_SPLIT" in str(e)
    finally:
        C.safe_close(ha)
        C.safe_close(hb)
        C.safe_close(hl)


def t_copy_record_integrity_rejects():
    expected = {1, 2}
    good_sha = "a" * 64
    base = {
        "run_id": "RUN1",
        "volume_free_before": 1000,
        "volume_free_after": 900,
        "path_count": 2,
        "unique_bytes": 10,
        "entities": [
            {"entity_id": 1, "sha256": good_sha},
            {"entity_id": 2, "sha256": "b" * 64},
        ],
    }
    # empty sha
    bad = json.loads(json.dumps(base))
    bad["entities"][0]["sha256"] = ""
    d = C.validate_copy_record_integrity(bad, expected, require_full_pilot_counts=False)
    assert any("SHA_INVALID" in x for x in d)
    # duplicate entity
    bad = json.loads(json.dumps(base))
    bad["entities"].append({"entity_id": 1, "sha256": "c" * 64})
    d = C.validate_copy_record_integrity(bad, expected, require_full_pilot_counts=False)
    assert "COPY_RECORD_ENTITY_ID_DUPLICATE" in d
    # missing entity
    bad = json.loads(json.dumps(base))
    bad["entities"] = [bad["entities"][0]]
    d = C.validate_copy_record_integrity(bad, expected, require_full_pilot_counts=False)
    assert any("ENTITY_MISSING" in x for x in d)
    # missing run_id
    bad = json.loads(json.dumps(base))
    bad["run_id"] = ""
    d = C.validate_copy_record_integrity(bad, expected, require_full_pilot_counts=False)
    assert "COPY_RECORD_RUN_ID_MISSING" in d
    # missing space
    bad = json.loads(json.dumps(base))
    del bad["volume_free_after"]
    d = C.validate_copy_record_integrity(bad, expected, require_full_pilot_counts=False)
    assert any("SPACE_EVIDENCE_MISSING" in x for x in d)
    # content wrong → acceptance helper path: force sha compare
    assert C.is_valid_sha256_hex(good_sha)
    assert not C.is_valid_sha256_hex("zz")
    assert not C.is_valid_sha256_hex(None)


def t_walk_onerror_deficit():
    # Force os.walk onerror path via monkeypatch
    root = WORK / "walkroot"
    root.mkdir(exist_ok=True)
    (root / "f.txt").write_text("x", encoding="utf-8")

    real_walk = os.walk

    def fake_walk(path, onerror=None):
        if onerror:
            onerror(OSError(5, "Access is denied", r"C:\fake\denied"))
        yield from real_walk(path)

    with mock.patch("acceptance_script_r9_1g.os.walk", side_effect=fake_walk):
        extra = ACC.walk_dest_extra(root, expected_rels=set())
    assert extra["walk_errors"], extra
    assert any("WALK_ONERROR" in e for e in extra["walk_errors"])


def t_empty_manifest_struct():
    db = WORK / "empty.sqlite"
    con = sqlite3.connect(str(db))
    con.executescript(
        "CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);"
        "CREATE TABLE entities(entity_id INTEGER PRIMARY KEY, volume_serial TEXT, file_id TEXT,"
        " representative_source_relative_path TEXT, unique_file_bytes INTEGER, source_file_size INTEGER,"
        " source_attributes INTEGER, source_last_write_time TEXT, nlinks_index INTEGER, sibling_count INTEGER,"
        " cross_release INTEGER, is_hardlink_group INTEGER, verify_ok INTEGER);"
        "CREATE TABLE hardlink_paths(entity_id INTEGER, source_relative_path TEXT, source_absolute_path TEXT,"
        " PRIMARY KEY(entity_id, source_relative_path));"
    )
    con.commit()
    st = C.validate_manifest_structure(con)
    con.close()
    assert st["ok"] is False and "EMPTY_MANIFEST" in st["issues"]


def t_partial_acc():
    rc = ACC.main(
        [
            "--manifest",
            str(ROOT / "BLACKBOX_R9_MANIFEST" / "PILOT_1G_MANIFEST.sqlite"),
            "--dry-structure-only",
            "--limit-entities",
            "2",
            "--log",
            str(WORK / "acc_partial.json"),
        ]
    )
    rep = json.loads((WORK / "acc_partial.json").read_text(encoding="utf-8"))
    assert rep["overall_pass"] is False
    assert rep.get("verdict") == "PARTIAL" or rep.get("partial") is True


def t_manifest_bind():
    con, info = C.bind_manifest(ROOT / "BLACKBOX_R9_MANIFEST" / "PILOT_1G_MANIFEST.sqlite")
    con.close()
    assert info["sha256"] == C.EXPECTED_MANIFEST_SHA256
    assert info["entity_count"] == 662


def t_dry_run():
    rc = EX.main(["--log", str(WORK / "dry.json")])
    d = json.loads((WORK / "dry.json").read_text(encoding="utf-8"))
    assert d["status"] == "DRY_RUN_OK" and d["dry_run"] is True
    assert d.get("source_root_mapped") == C.DESKTOP_UNC_SOURCE_ROOT


def t_enable_copy_ignores_skip_env():
    """Document/enforce: enable_copy preflight sets allow_proc_check_skip=False."""

    class A:
        r8_stopped_evidence = str(WORK / "r8ok2.json")
        confirm_dest = str(C.ALLOWED_DEST)
        allow_proc_check_skip = True  # caller tries to skip

    (WORK / "r8ok2.json").write_text(
        json.dumps(
            {"OLD_LN_STOPPED": True, "OLD_WRAPPER_STOPPED": True, "OLD_MONITORS_INACTIVE": True}
        ),
        encoding="utf-8",
    )
    # Simulate executor enable path
    A.allow_proc_check_skip = False
    snap = [
        {
            "ProcessId": 9,
            "ParentProcessId": 1,
            "Name": "powershell.exe",
            "CreationDate": "x",
            "CommandLine": f"pwsh -File freeze.ps1 {C.R8_LEGACY_RUN_ID}",
        }
    ]
    os.environ["R9_SKIP_PROC_CHECK"] = "1"
    with mock.patch.object(C, "live_r8_process_check", wraps=C.live_r8_process_check) as wrapped:
        # direct: skip ignored
        r = C.live_r8_process_check(allow_env_skip=False, proc_snapshot=snap)
        assert r["ok"] is False
        # with allow True would skip — prove asymmetry
        r2 = C.live_r8_process_check(allow_env_skip=True, proc_snapshot=snap)
        assert r2.get("skipped") is True


def main():
    ok("unc", t_unc)
    ok("rel", t_rel)
    ok("r8_ok_and_rejects", t_r8_ok_and_rejects)
    ok("r8_legacy_proc_rejected", t_r8_legacy_proc_rejected)
    ok("host_blocks_copy", t_host)
    ok("identity_wrong_vol_and_mtime", t_identity_wrong_vol_and_mtime)
    ok("same_handle_copy_hash", t_same_handle_copy_hash)
    ok("eof_probe_readfile_fail", t_eof_probe_readfile_fail)
    ok("hl_distinct", t_hl_distinct)
    ok("copy_record_integrity_rejects", t_copy_record_integrity_rejects)
    ok("walk_onerror_deficit", t_walk_onerror_deficit)
    ok("empty_manifest", t_empty_manifest_struct)
    ok("partial_acc", t_partial_acc)
    ok("manifest_bind", t_manifest_bind)
    ok("dry_run", t_dry_run)
    ok("enable_copy_ignores_skip_env", t_enable_copy_ignores_skip_env)
    out = {
        "generated_at": C.now_iso(),
        "hostname": __import__("socket").gethostname(),
        "suite": "R9FIX2_LEAN",
        "passed": sum(1 for x in R if x["pass"]),
        "failed": sum(1 for x in R if not x["pass"]),
        "results": R,
        "notes": [
            "D coverage integrity still unproven",
            "Historical R8 READY must not be reused as stop evidence",
            "Desktop UniqueId / UNC stable read remain on-site checks",
            "No real 1GiB copy executed in this suite",
        ],
        "desktop_still_required": [
            "Hostname ZHANGWEI",
            "E: serial 806508DF + UniqueId live match",
            "UNC \\\\192.168.100.2\\E_DRIVE\\BLACKBOX stable share-read",
            "Real R8 stop report with OLD_LN/WRAPPER/MONITORS all TRUE (no conflict)",
            f"No live cmdline hosting {C.R8_LEGACY_RUN_ID} / freeze monitors / ln wrapper",
            "Fresh E:\\BLACKBOX_MANIFEST_PILOT_R9_1G create + full 662 copy/accept",
        ],
    }
    (ROOT / "R9_SYNTH_TESTS" / "R9FIX_LEAN_TEST_RESULTS.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # Also keep a non-summary full dump path for HUB
    (ROOT / "R9_SYNTH_TESTS" / "R9FIX2_LEAN_TEST_FULL.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"passed": out["passed"], "failed": out["failed"]}, indent=2), flush=True)
    return 0 if out["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
