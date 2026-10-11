# -*- coding: utf-8 -*-
"""R9FIX2b patch tests — walk_errors deficit + fail-closed proc check + mini acceptance PASS."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import traceback
from pathlib import Path
from unittest import mock

ROOT = Path(r"C:\LAN_SHARE_REPORT")
sys.path.insert(0, str(ROOT))
os.environ.pop("R9_SKIP_PROC_CHECK", None)

WORK = ROOT / "R9_SYNTH_TESTS" / "_fix2b"
if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)

import r9_pilot_common_r9fix as C  # noqa: E402
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


def t_proc_empty_list_fails():
    r = C.live_r8_process_check(allow_env_skip=False, proc_snapshot=[])
    assert r["ok"] is False and r["reason"] == "PROC_CHECK_EMPTY_OR_NOT_LIST"


def t_proc_not_list_fails():
    r = C.live_r8_process_check(allow_env_skip=False, proc_snapshot={"ProcessId": 1})  # type: ignore[arg-type]
    assert r["ok"] is False


def t_proc_malformed_fails():
    r = C.live_r8_process_check(allow_env_skip=False, proc_snapshot=["bad"])  # type: ignore[list-item]
    assert r["ok"] is False and r["reason"] == "PROC_CHECK_MALFORMED_ROW"


def t_proc_unreadable_cmdline_fails():
    snap = [
        {
            "ProcessId": 1,
            "ParentProcessId": 0,
            "Name": "powershell.exe",
            "CreationDate": "x",
            "CommandLine": None,
        }
    ]
    r = C.live_r8_process_check(allow_env_skip=False, proc_snapshot=snap)
    assert r["ok"] is False
    assert r["reason"] == "PROC_CMDLINE_UNREADABLE"
    assert r.get("status") == "UNKNOWN"


def t_proc_query_fail():
    import subprocess

    with mock.patch("subprocess.check_output", side_effect=RuntimeError("cim boom")):
        r = C.live_r8_process_check(allow_env_skip=False, proc_snapshot=None)
    assert r["ok"] is False and "PROC_CHECK_FAIL" in r["reason"]


def t_proc_empty_output():
    with mock.patch("subprocess.check_output", return_value="   \n"):
        r = C.live_r8_process_check(allow_env_skip=False, proc_snapshot=None)
    assert r["ok"] is False and r["reason"] == "PROC_CHECK_EMPTY_OUTPUT"


def t_proc_skip_cannot_pass():
    os.environ["R9_SKIP_PROC_CHECK"] = "1"
    try:
        r = C.live_r8_process_check(allow_env_skip=True, proc_snapshot=[{"ProcessId": 1, "Name": "x", "CommandLine": "y"}])
        assert r["ok"] is False and r["reason"] == "PROC_CHECK_SKIP_NOT_ALLOWED"
        r2 = C.live_r8_process_check(
            allow_env_skip=False,
            proc_snapshot=[
                {
                    "ProcessId": 9,
                    "ParentProcessId": 1,
                    "Name": "powershell.exe",
                    "CreationDate": "x",
                    "CommandLine": f"pwsh -File freeze.ps1 {C.R8_LEGACY_RUN_ID}",
                }
            ],
        )
        assert r2["ok"] is False and r2["reason"] == "R8_LEGACY_TASK_STILL_RUNNING"
    finally:
        os.environ.pop("R9_SKIP_PROC_CHECK", None)


def t_proc_clean_nonempty_passes():
    snap = [
        {
            "ProcessId": 4,
            "ParentProcessId": 0,
            "Name": "System",
            "CreationDate": "x",
            "CommandLine": "System",
        },
        {
            "ProcessId": 100,
            "ParentProcessId": 4,
            "Name": "notepad.exe",
            "CreationDate": "x",
            "CommandLine": "C:\\Windows\\notepad.exe",
        },
    ]
    r = C.live_r8_process_check(allow_env_skip=False, proc_snapshot=snap)
    assert r["ok"] is True


def _build_mini_manifest(db: Path, dest_file: Path, content: bytes) -> tuple[str, dict]:
    h = C.open_source_stable(str(dest_file))
    try:
        ident = C.handle_identity(h)
    finally:
        C.safe_close(h)
    sha = hashlib.sha256(content).hexdigest()
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
    # ISO mtime from live FILETIME
    m_dt = C.filetime_to_utc_datetime(ident["mtime_ft"])
    mtime_iso = m_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    con.execute(
        "INSERT INTO entities VALUES (1,?,?,?,?,?,?,?,1,1,0,0,1)",
        (
            ident["volume_serial"],
            ident["file_id"],
            r"mini\a.bin",
            len(content),
            len(content),
            0,
            mtime_iso,
        ),
    )
    con.execute(
        "INSERT INTO hardlink_paths VALUES (1,?,?)",
        (r"mini\a.bin", str(dest_file)),
    )
    con.commit()
    con.close()
    digest = C.sha256_file_path(db)
    return digest, {
        "vol": ident["volume_serial"],
        "fid": ident["file_id"],
        "size": len(content),
        "sha": sha,
        "mtime": mtime_iso,
    }


def _run_mini_acceptance(*, inject_walk_error: bool) -> dict:
    dest_root = WORK / ("acc_pass" if not inject_walk_error else "acc_walk_fail")
    if dest_root.exists():
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True)
    rel_dir = dest_root / "mini"
    rel_dir.mkdir()
    content = b"MINI-ACCEPT-OK-CONTENT-001"
    dest_file = rel_dir / "a.bin"
    dest_file.write_bytes(content)

    db = WORK / ("mini_pass.sqlite" if not inject_walk_error else "mini_fail.sqlite")
    digest, meta = _build_mini_manifest(db, dest_file, content)

    crec = {
        "run_id": "MINI_RUN_1",
        "manifest_sha256": digest,
        "dest": str(dest_root),
        "dest_volume": {
            "VolumeSerialNumber_dword": C.EXPECTED_DEST_VOLUME["VolumeSerialNumber_dword"],
            "VolumeSerialNumber_hex": C.EXPECTED_DEST_VOLUME["VolumeSerialNumber_hex"],
        },
        "volume_free_before": 10_000_000_000,
        "volume_free_after": 9_999_000_000,
        "path_count": 1,
        "unique_bytes": meta["size"],
        "entities": [{"entity_id": 1, "sha256": meta["sha"]}],
    }
    crec_path = WORK / ("crec_pass.json" if not inject_walk_error else "crec_fail.json")
    crec_path.write_text(json.dumps(crec), encoding="utf-8")
    log_path = WORK / ("acc_pass.json" if not inject_walk_error else "acc_fail.json")

    real_walk = ACC.walk_dest_extra

    def walk_wrap(dest_root_p, expected_rels):
        extra = real_walk(dest_root_p, expected_rels)
        if inject_walk_error:
            extra = dict(extra)
            extra["walk_errors"] = list(extra.get("walk_errors") or []) + [
                "WALK_ONERROR:OSError:Access is denied:C:\\fake\\denied"
            ]
        return extra

    patches = [
        mock.patch.object(C, "ALLOWED_DEST", dest_root),
        mock.patch.object(ACC.C, "ALLOWED_DEST", dest_root),
        mock.patch.object(C, "EXPECTED_MANIFEST_SHA256", digest),
        mock.patch.object(ACC.C, "EXPECTED_MANIFEST_SHA256", digest),
        mock.patch.object(C, "EXPECTED_ENTITY_COUNT", 1),
        mock.patch.object(ACC.C, "EXPECTED_ENTITY_COUNT", 1),
        mock.patch.object(C, "EXPECTED_PATH_COUNT", 1),
        mock.patch.object(ACC.C, "EXPECTED_PATH_COUNT", 1),
        mock.patch.object(C, "EXPECTED_UNIQUE_BYTES", meta["size"]),
        mock.patch.object(ACC.C, "EXPECTED_UNIQUE_BYTES", meta["size"]),
        mock.patch.object(
            C,
            "get_volume_identity",
            return_value={
                "root": "E:\\",
                "VolumeSerialNumber_dword": C.EXPECTED_DEST_VOLUME["VolumeSerialNumber_dword"],
                "VolumeSerialNumber_hex": C.EXPECTED_DEST_VOLUME["VolumeSerialNumber_hex"],
                "FileSystem": "NTFS",
                "VolumeName": "MarketData",
            },
        ),
        mock.patch.object(ACC.C, "get_volume_identity", return_value={
            "root": "E:\\",
            "VolumeSerialNumber_dword": C.EXPECTED_DEST_VOLUME["VolumeSerialNumber_dword"],
            "VolumeSerialNumber_hex": C.EXPECTED_DEST_VOLUME["VolumeSerialNumber_hex"],
            "FileSystem": "NTFS",
            "VolumeName": "MarketData",
        }),
        mock.patch.object(C, "volume_free_bytes", return_value=9_999_000_000),
        mock.patch.object(ACC.C, "volume_free_bytes", return_value=9_999_000_000),
        mock.patch.object(C, "ensure_no_reparse_ancestors", return_value=None),
        mock.patch.object(ACC.C, "ensure_no_reparse_ancestors", return_value=None),
        mock.patch.object(ACC, "walk_dest_extra", side_effect=walk_wrap),
    ]
    for p in patches:
        p.start()
    try:
        # validate_manifest_structure uses EXPECTED_* — already patched
        rc = ACC.main(
            [
                "--manifest",
                str(db),
                "--dest",
                str(dest_root),
                "--copy-record",
                str(crec_path),
                "--log",
                str(log_path),
            ]
        )
    finally:
        for p in patches:
            p.stop()

    rep = json.loads(log_path.read_text(encoding="utf-8"))
    rep["_rc"] = rc
    return rep


def t_acceptance_full_can_pass():
    rep = _run_mini_acceptance(inject_walk_error=False)
    assert rep["overall_pass"] is True, rep.get("deficits")
    assert rep["content_link_pass"] is True
    assert "DEST_WALK_ENUM_ERROR" not in rep.get("deficits", [])


def t_acceptance_walk_error_fails():
    rep = _run_mini_acceptance(inject_walk_error=True)
    assert "DEST_WALK_ENUM_ERROR" in rep.get("deficits", []), rep
    assert rep["content_link_pass"] is False
    assert rep["overall_pass"] is False


def main():
    ok("proc_empty_list_fails", t_proc_empty_list_fails)
    ok("proc_not_list_fails", t_proc_not_list_fails)
    ok("proc_malformed_fails", t_proc_malformed_fails)
    ok("proc_unreadable_cmdline_fails", t_proc_unreadable_cmdline_fails)
    ok("proc_query_fail", t_proc_query_fail)
    ok("proc_empty_output", t_proc_empty_output)
    ok("proc_skip_cannot_pass", t_proc_skip_cannot_pass)
    ok("proc_clean_nonempty_passes", t_proc_clean_nonempty_passes)
    ok("acceptance_full_can_pass", t_acceptance_full_can_pass)
    ok("acceptance_walk_error_fails", t_acceptance_walk_error_fails)

    out = {
        "generated_at": C.now_iso(),
        "hostname": __import__("socket").gethostname(),
        "suite": "R9FIX2B_PATCH",
        "passed": sum(1 for x in R if x["pass"]),
        "failed": sum(1 for x in R if not x["pass"]),
        "results": R,
        "desktop_gate": {
            "required_hostname": C.REQUIRED_HOSTNAME,
            "this_host": __import__("socket").gethostname(),
            "desktop_steps_blocked": __import__("socket").gethostname().upper()
            != C.REQUIRED_HOSTNAME.upper(),
            "reason": "Field preflight/copy/accept only on ZHANGWEI; this host is not ZHANGWEI.",
        },
    }
    (ROOT / "R9_SYNTH_TESTS" / "R9FIX2B_PATCH_TEST_FULL.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"passed": out["passed"], "failed": out["failed"], "desktop_blocked": out["desktop_gate"]["desktop_steps_blocked"]}, indent=2), flush=True)
    return 0 if out["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
