# -*- coding: utf-8 -*-
"""Formal R9 executor. This round is validate / plan / preflight only.

copy is implemented as a refusal while COPY_AUTHORIZED is false.
It does not remove the 1GiB cap from r9_pilot_common_r9fix.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import r9_formal_chain as formal_chain

HISTORICAL_DEST_SERIAL = "806508DF"
ORIGINAL_D_SHA_NOT_REPAIRED = "787b14d267b3b167b37695adbdffaba96c719ed50bf64659ba4ba3828f630d39"
EXPECTED_E_SNAPSHOT_SHA = "a5590154ed4da7b45c1ad19dfe82989cd2bb058702aad9b6ea58c2868d0a5572"
EXPECTED_DELTA_SHA = "9f1a37f945e80682a93190565e553bdef61bf8451b96216c2686c1d3e8887ad6"
WIN32_MASK = 0xFFFFFFFF
INVALID_ID_TEXT = {"", "none", "null", "0"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_int_id(value) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in INVALID_ID_TEXT:
        return None
    try:
        n = int(text, 10)
    except ValueError:
        return None
    if n <= 0:
        return None
    return n


def win32_volume_serial(value) -> int | None:
    n = parse_int_id(value)
    if n is None:
        return None
    if n <= WIN32_MASK:
        return n
    return n & WIN32_MASK


def identity_comparable(left_vol, left_fid, right_vol, right_fid) -> bool:
    """Same entity only when both sides already use the same raw identity form.

    A low-32 collapse of Python st_dev onto a Win32 serial is recorded as a
    candidate, not as permission to merge entities.
    """
    lv, rv = parse_int_id(left_vol), parse_int_id(right_vol)
    lf, rf = parse_int_id(left_fid), parse_int_id(right_fid)
    if None in (lv, rv, lf, rf):
        return False
    return lv == rv and lf == rf


def post_format_copy_allowed(observed_serial: str, copy_authorized: bool) -> bool:
    """Historical E: serial is not a license to copy after a future format."""
    if not copy_authorized:
        return False
    if str(observed_serial).upper() == HISTORICAL_DEST_SERIAL:
        return False
    return False


def connect_ro(path: Path) -> sqlite3.Connection:
    uri = path.resolve().as_posix()
    return sqlite3.connect(f"file:{uri}?mode=ro", uri=True)


def validate_sha(path: Path, expected: str, role: str) -> dict:
    actual = sha256_file(path)
    ok = actual.lower() == expected.lower()
    reason = "OK" if ok else "SHA_MISMATCH"
    if role == "d_repaired" and actual.lower() == ORIGINAL_D_SHA_NOT_REPAIRED:
        ok = False
        reason = "REJECT_ORIGINAL_D_SHA_FOR_REPAIRED_DB"
    if role == "d_repaired" and expected.lower() == ORIGINAL_D_SHA_NOT_REPAIRED:
        ok = False
        reason = "CONTRACT_BINDS_REPAIRED_DB_TO_ORIGINAL_SHA"
    return {"role": role, "path": str(path), "expected": expected, "actual": actual, "ok": ok, "reason": reason}


def refuse_copy(copy_authorized: bool) -> int:
    if not copy_authorized:
        print("COPY_REFUSED COPY_AUTHORIZED=false")
        return 3
    print("COPY_REFUSED post-format preflight and a new user authorization are required")
    return 3


def _init_plan(out: Path) -> sqlite3.Connection:
    if out.exists():
        out.unlink()
    conn = sqlite3.connect(out)
    conn.executescript(
        """
        create table meta(key text primary key, value text);
        create table deficits(id integer primary key, code text, detail text);
        create table overlay(
          path text primary key,
          in_base integer,
          in_delta integer,
          delta_wins integer
        );
        create table stats(key text primary key, value integer);
        """
    )
    return conn


def plan_from_inputs(e_base: Path | None, e_delta: Path | None, d_repaired: Path | None, out: Path) -> dict:
    conn = _init_plan(out)
    deficits = []
    if e_base is None or not e_base.exists():
        deficits.append(("E_BASE_MISSING", "bound snapshot not available on this host"))
    if e_delta is None or not e_delta.exists():
        deficits.append(("E_DELTA_MISSING", "delta sqlite missing"))
    if d_repaired is None or not d_repaired.exists():
        deficits.append(("D_REPAIRED_MISSING", "SELECTED_D_MANIFEST_REPAIRED.sqlite is not on ZHANGWEI and the notebook share is not readable"))
    for code, detail in deficits:
        conn.execute("insert into deficits(code, detail) values(?,?)", (code, detail))

    file_paths = dir_paths = content_bytes = alloc_bytes = reparses = 0
    overlay_hits = 0
    if e_base and e_base.exists():
        base = connect_ro(e_base)
        file_paths = base.execute("select count(*) from entries where is_dir=0").fetchone()[0]
        dir_paths = base.execute("select count(*) from entries where is_dir=1").fetchone()[0]
        content_bytes = base.execute("select coalesce(sum(logical_size),0) from entries where is_dir=0").fetchone()[0]
        alloc_bytes = base.execute("select coalesce(sum(alloc_size),0) from entries where is_dir=0").fetchone()[0]
        reparses = base.execute(
            "select count(*) from entries where reparse_tag is not null and reparse_tag != 0"
        ).fetchone()[0]
        vols = base.execute("select volume_serial, count(*) from entries group by volume_serial").fetchall()
        conn.execute("insert into meta(key,value) values('e_base_volume_groups',?)", (json.dumps(vols),))
        if e_delta and e_delta.exists():
            delta = connect_ro(e_delta)
            for (path,) in delta.execute("select path from files"):
                hit = base.execute("select 1 from entries where path=?", (path,)).fetchone()
                conn.execute(
                    "insert into overlay(path, in_base, in_delta, delta_wins) values(?,?,1,1)",
                    (path, 1 if hit else 0),
                )
                if hit:
                    overlay_hits += 1
            # identity form check: do not merge entities across encodings
            mismatch = 0
            delta_rows = list(delta.execute("select volume_serial, file_id from files"))
            delta_vols = list(delta.execute("select distinct volume_serial from files"))
            delta.close()
            for vol, fid in delta_rows:
                if parse_int_id(vol) is None or parse_int_id(fid) is None:
                    mismatch += 1
                    continue
                # base files use the 32-bit serial; delta files use the wide st_dev form
                base_same = base.execute(
                    "select 1 from entries where is_dir=0 and volume_serial=? and file_id=? limit 1",
                    (str(vol), str(fid)),
                ).fetchone()
                if not base_same:
                    mismatch += 1
            conn.execute("insert into stats(key,value) values('delta_identity_not_raw_equal_to_base_files',?)", (mismatch,))
            low32_ok = True
            base_serial = base.execute("select value from meta where key='source_volume_serial'").fetchone()
            base_serial_n = parse_int_id(base_serial[0]) if base_serial else None
            for (vol,) in delta_vols:
                if win32_volume_serial(vol) != base_serial_n:
                    low32_ok = False
            conn.execute(
                "insert into meta(key,value) values('delta_low32_matches_base_win32_serial',?)",
                ("true" if low32_ok else "false",),
            )
            if low32_ok:
                deficits.append((
                    "IDENTITY_FORM_DIFFERS",
                    "delta file volume_serial low-32 matches E base Win32 serial, but raw file_id/volume text differs; entities are not merged",
                ))
                conn.execute(
                    "insert into deficits(code, detail) values('IDENTITY_FORM_DIFFERS',?)",
                    ("raw delta identity is not equal to base file identity; no cross-form merge",),
                )
        base.close()

    stats = {
        "e_file_paths": file_paths,
        "e_dir_paths": dir_paths,
        "e_content_bytes": int(content_bytes or 0),
        "e_alloc_bytes": int(alloc_bytes or 0),
        "e_reparses": reparses,
        "delta_paths_already_in_base": overlay_hits,
    }
    for k, v in stats.items():
        conn.execute("insert into stats(key,value) values(?,?)", (k, int(v)))
    ready = not any(code in {"E_BASE_MISSING", "E_DELTA_MISSING", "D_REPAIRED_MISSING", "IDENTITY_FORM_DIFFERS"} for code, _ in deficits)
    # D missing or identity form difference => not ready for copy
    ready = False if deficits else ready
    status = "PARTIAL" if deficits else "PLAN_COMPLETE"
    conn.execute("insert into meta(key,value) values('status',?)", (status,))
    conn.execute("insert into meta(key,value) values('copy_ready',?)", ("false",))
    conn.commit()
    conn.close()
    return {"status": status, "copy_ready": False, "stats": stats, "deficits": deficits}


def formal_write_gate(contract: dict, backend) -> bool:
    """Legal formal/bench copy gate. A false contract still refuses before any write."""
    return formal_chain.formal_write_gate(contract, backend)


def main(argv: list[str] | None = None, backend=None, probe=None) -> int:
    import r9_adapter as adapter

    parser = argparse.ArgumentParser(prog="r9_formal_executor")
    sub = parser.add_subparsers(dest="mode", required=True)
    p_val = sub.add_parser("validate-input")
    p_val.add_argument("--e-base", required=True)
    p_val.add_argument("--e-delta", required=True)
    p_val.add_argument("--d-repaired", required=True)
    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--e-base", required=True)
    p_plan.add_argument("--e-delta", required=True)
    p_plan.add_argument("--d-repaired", required=True)
    p_plan.add_argument("--out", required=True)
    p_pre = sub.add_parser("preflight-readonly")
    p_pre.add_argument("--e-base", required=True)
    p_pre.add_argument("--e-delta", required=True)
    p_pre.add_argument("--d-repaired", required=True)
    p_copy = sub.add_parser("copy")
    p_copy.add_argument("--copy-authorized", action="store_true")
    p_copy.add_argument("--format-done", action="store_true")
    sub.add_parser("accept-simulated")
    p_dry = sub.add_parser("dry-run")
    p_dry.add_argument("--contract", required=True)
    p_exec = sub.add_parser("execute")
    p_exec.add_argument("--contract", required=True)
    p_subset = sub.add_parser("build-subset")
    p_subset.add_argument("--plan", required=True)
    p_subset.add_argument("--out-dir", required=True)
    p_verify = sub.add_parser("verify-existing")
    p_verify.add_argument("--contract", required=True)
    p_pilot = sub.add_parser("bounded-pilot")
    p_pilot.add_argument("pilot_mode", choices=["dry-run", "execute"])
    p_pilot.add_argument("--sample", required=True)
    p_pilot.add_argument("--contract", required=True)
    args = parser.parse_args(argv)
    if args.mode in ("dry-run", "execute"):
        payload = json.loads(Path(args.contract).read_text(encoding="utf-8"))
        result = formal_chain.execute_contract(payload, args.mode, backend=backend, probe=probe)
        formal_chain.last_result = result
        print(json.dumps(result, ensure_ascii=False, default=str))
        return formal_chain.exit_code(result, args.mode)
    if args.mode == "build-subset":
        result = formal_chain.build_subset(Path(args.plan), Path(args.out_dir))
        formal_chain.last_result = result
        print(json.dumps({"ok": True, "subset": result.get("subset"), "unique_bytes": result.get("unique_bytes")}, ensure_ascii=False))
        return 0
    if args.mode == "verify-existing":
        payload = json.loads(Path(args.contract).read_text(encoding="utf-8"))
        result = formal_chain.readonly_reverify(payload, backend=backend)
        formal_chain.last_result = result
        print(json.dumps(result, ensure_ascii=False, default=str))
        return 0 if result.get("bench_verified") else 4
    if args.mode == "bounded-pilot":
        from r9_bounded_pilot import main as pilot_main
        return pilot_main([args.pilot_mode, "--sample", args.sample, "--contract", args.contract])
    if args.mode == "accept-simulated":
        print("ACCEPTANCE_REAL_IO=NOT_RUN")
        print("simulated acceptance runs inside production_run when phase=SIMULATED_CHAIN")
        return 3
    if args.mode == "copy":
        from r9_scheduler import FakeBackend, PreparationGate, run_batch
        result = run_batch(iter(()), FakeBackend(), PreparationGate(), {"phase": "PREPARATION_ONLY", "copy_authorized": bool(args.copy_authorized), "format_done": bool(args.format_done)})
        if result["backend_calls"] != 0:
            print("COPY_GATE_FAILED")
            return 4
        return adapter.copy_entry_refused(bool(args.copy_authorized), bool(args.format_done))
    if args.mode == "validate-input":
        code, rows = adapter.validate_inputs(Path(args.e_base), Path(args.e_delta), Path(args.d_repaired))
        print(json.dumps({"ok": code == 0, "bindings": rows}, ensure_ascii=False))
        return code
    if args.mode == "preflight-readonly":
        report = adapter.preflight(Path(args.e_base), Path(args.e_delta), Path(args.d_repaired))
        print(json.dumps(report, ensure_ascii=False))
        if report["overall_copy_ready"]:
            return 2
        if not report["INPUT_VALID"] or not report["hostname_ok"] or not report["SOURCE_ACCESS_VALID"]:
            return 2
        return 2
    if args.mode == "plan":
        code, result = adapter.build_plan(
            Path(args.e_base), Path(args.e_delta), Path(args.d_repaired), Path(args.out)
        )
        print(json.dumps(result, ensure_ascii=False))
        return code
    return 2


if __name__ == "__main__":
    sys.exit(main())
