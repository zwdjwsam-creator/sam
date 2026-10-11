# -*- coding: utf-8 -*-
"""
BLACKBOX R9 — 1GiB pilot copy executor (post ChatGPT review fix).

- Default: dry-run (notebook OK). Actual copy ONLY on ZHANGWEI with volume+R8 gates.
- Source bytes always from UNC \\\\192.168.100.2\\E_DRIVE\\BLACKBOX + validated relative path.
- Manifest SHA pinned; bounded copy; exclusive CREATE_NEW; no dest reuse.
Old version retained as copy_executor_r9_1g_PRE_REVIEW_FIX.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import r9_pilot_common_r9fix as C

LOG_DIR = Path(r"C:\LAN_SHARE_REPORT")
DEFAULT_MANIFEST = Path(r"C:\LAN_SHARE_REPORT\BLACKBOX_R9_MANIFEST\PILOT_1G_MANIFEST.sqlite")
DEFAULT_VOLUME_REPORT = Path(
    r"C:\LAN_SHARE_REPORT\BLACKBOX_R8_DESKTOP_READY.md"
)  # identity constants also embedded; live GetVolumeInformation required


def check_dest_volume_live() -> dict:
    live = C.get_volume_identity("E:\\")
    exp = C.EXPECTED_DEST_VOLUME
    issues = []
    if live["FileSystem"].upper() != exp["FileSystem"].upper():
        issues.append(f"FS={live['FileSystem']}")
    if live["VolumeSerialNumber_dword"] != exp["VolumeSerialNumber_dword"]:
        issues.append(
            f"SERIAL live={live['VolumeSerialNumber_hex']} expected={exp['VolumeSerialNumber_hex']}"
        )
    # label soft-check (encoding may vary); serial+FS are hard
    return {"ok": len(issues) == 0, "live": live, "expected": exp, "issues": issues}


def preflight_copy(args, manifest_info: dict) -> dict:
    issues = []
    host_ok, host = C.hostname_ok()
    if not host_ok:
        issues.append(f"WRONG_HOST:{host}")
    vol = {"ok": False, "issues": ["SKIPPED_WRONG_HOST"], "live": None, "expected": C.EXPECTED_DEST_VOLUME}
    # Actual copy preflight must never honor R9_SKIP_PROC_CHECK.
    allow_proc_skip = bool(getattr(args, "allow_proc_check_skip", False))
    proc = {"ok": True, "suspicious": [], "skipped": True}
    if host_ok:
        vol = check_dest_volume_live()
        if not vol["ok"]:
            issues.append("DEST_VOLUME_MISMATCH:" + ",".join(vol["issues"]))
        proc = C.live_r8_process_check(allow_env_skip=allow_proc_skip)
        if not proc.get("ok"):
            issues.append(f"R8_LIVE_PROC:{proc.get('reason')}")
    r8 = C.parse_r8_stop_report(Path(args.r8_stopped_evidence)) if args.r8_stopped_evidence else {
        "ok": False,
        "reason": "R8_PATH_REQUIRED",
    }
    if not r8.get("ok"):
        issues.append(
            f"R8_STOP_FAIL:{r8.get('reason')}:{r8.get('falsy') or r8.get('missing') or r8.get('conflicts')}"
        )
    if str(args.confirm_dest).rstrip("\\").lower() != str(C.ALLOWED_DEST).rstrip("\\").lower():
        issues.append(f"CONFIRM_DEST_MISMATCH:{args.confirm_dest}")
    # dest must NOT exist
    if C.ALLOWED_DEST.exists():
        issues.append("DEST_ALREADY_EXISTS")
    else:
        # parent E:\ must exist and not be reparse
        try:
            C.ensure_no_reparse_ancestors(Path("E:\\"), stop_at=Path("E:\\"))
        except Exception as e:
            issues.append(f"E_ROOT_REPARSE_OR_ATTR:{e}")
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "hostname": host,
        "volume": vol,
        "r8": r8,
        "r8_process": proc,
        "manifest_sha256": manifest_info["sha256"],
        "note": "Notebook dry-run must not be treated as desktop copy preflight PASS.",
    }


def plan_and_optionally_copy(args) -> int:
    stamp = C.now_iso().replace(":", "").replace("+", "")
    log_path = args.log or (LOG_DIR / f"COPY_EXECUTOR_R9FIX_{stamp}.json")
    enable = bool(args.enable_copy and args.i_accept_pilot_copy)
    dry_run = not enable
    log: dict = {
        "generated_at": C.now_iso(),
        "dry_run": dry_run,
        "enable_copy": args.enable_copy,
        "source_root_mapped": C.DESKTOP_UNC_SOURCE_ROOT,
        "dest": str(C.ALLOWED_DEST),
        "manifest_sha_pinned": C.EXPECTED_MANIFEST_SHA256,
        "events": [],
        "status": "INIT",
    }

    def stop(code: str, detail: str = "") -> int:
        log["status"] = code
        log["detail"] = detail
        log["finished_at"] = C.now_iso()
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": code, "detail": detail, "log": str(log_path)}, ensure_ascii=False), flush=True)
        return 0 if code in ("DRY_RUN_OK", "COPY_OK", "PREFLIGHT_PASS") else 2

    try:
        if str(args.dest).rstrip("\\").lower() != str(C.ALLOWED_DEST).rstrip("\\").lower():
            return stop("DEST_REFUSED", str(args.dest))

        con, minfo = C.bind_manifest(args.manifest)
        log["manifest"] = minfo

        if args.limit_entities and args.limit_entities > 0:
            if enable:
                return stop("LIMIT_ENTITIES_FORBIDDEN_FOR_COPY", str(args.limit_entities))
            log["partial_check"] = True
            log["limit_entities"] = args.limit_entities

        pre = None
        if enable or args.preflight_only:
            # enable_copy ⇒ proc check skip forbidden even if env set
            args.allow_proc_check_skip = False if enable else bool(getattr(args, "allow_proc_check_skip", False))
            pre = preflight_copy(args, minfo)
            log["desktop_preflight"] = pre
            if args.preflight_only:
                return stop("PREFLIGHT_PASS" if pre["ok"] else "PREFLIGHT_FAIL", ",".join(pre["issues"]))
            if not pre["ok"]:
                return stop("COPY_BLOCKED_PREFLIGHT", ",".join(pre["issues"]))

        if dry_run and not args.probe_sources:
            # structure + path mapping only (no UNC open) — notebook-safe
            n = 0
            for row in con.execute("select entity_id, source_relative_path from hardlink_paths order by entity_id, source_relative_path"):
                rel = row["source_relative_path"]
                unc = C.join_unc_source(rel)
                dest = C.dest_under_root(C.ALLOWED_DEST, rel)
                n += 1
                if args.limit_entities and n > args.limit_entities * 50:
                    break
            log["mapped_path_samples"] = n
            log["note"] = "DRY_RUN_NO_SOURCE_PROBE; desktop must probe UNC + volume + R8"
            con.close()
            return stop("DRY_RUN_OK", f"mapped_checks≈{n}")

        # probe / copy path
        free_before = None
        if enable:
            free_before = C.volume_free_bytes("E:\\")
            log["volume_free_before"] = free_before
            C.ALLOWED_DEST.mkdir(parents=False, exist_ok=False)
            try:
                C.ensure_no_reparse_ancestors(C.ALLOWED_DEST, stop_at=Path("E:\\"))
            except Exception as e:
                return stop("DEST_ROOT_REPARSE", str(e))

        entity_ids = [r[0] for r in con.execute("select entity_id from entities order by entity_id")]
        if args.limit_entities and args.limit_entities > 0:
            entity_ids = entity_ids[: args.limit_entities]

        budget = C.UNIQUE_CAP
        planned_bytes = 0
        copy_record = {"entities": [], "unique_bytes": 0, "path_count": 0}

        for eid in entity_ids:
            e = con.execute("select * from entities where entity_id=?", (eid,)).fetchone()
            paths = list(
                con.execute(
                    "select source_relative_path from hardlink_paths where entity_id=? order by source_relative_path",
                    (eid,),
                )
            )
            if not paths:
                return stop("ENTITY_NO_PATHS", str(eid))
            expect = int(e["unique_file_bytes"])
            if expect != int(e["source_file_size"]) or expect < 0:
                return stop("SIZE_FIELD_BAD", str(eid))

            unc_paths = []
            for pr in paths:
                rel = pr["source_relative_path"]
                unc = C.join_unc_source(rel)
                # source reparse check via attrs before open
                if args.probe_sources or enable:
                    try:
                        if C.is_reparse_path(unc):
                            return stop("SOURCE_REPARSE", unc)
                    except OSError as ex:
                        return stop("SOURCE_ATTR_FAIL", f"{unc}:{ex}")
                unc_paths.append((rel, unc))

            primary_rel, primary_unc = unc_paths[0]
            dest_primary = C.dest_under_root(C.ALLOWED_DEST, primary_rel)

            if not (args.probe_sources or enable):
                continue

            # ONE stable source handle: identity → (optional sibling checks) →
            # bounded read/hash/write → post identity. Never close then shutil/reopen for content.
            h = None
            try:
                try:
                    h = C.open_source_stable(primary_unc)
                except RuntimeError as ex:
                    if "SMB_STABLE_READ_UNAVAILABLE" in str(ex):
                        return stop("SMB_STABLE_READ_UNAVAILABLE", str(ex))
                    raise
                ident = C.handle_identity(h)
                try:
                    C.compare_identity_vol_fid_size(
                        manifest_volume_serial=e["volume_serial"],
                        manifest_file_id=e["file_id"],
                        manifest_size=expect,
                        live=ident,
                        label=f"entity={eid}",
                    )
                    C.compare_mtime_manifest_vs_handle(e["source_last_write_time"], ident["mtime_ft"])
                except RuntimeError as ex:
                    return stop(str(ex).split(":", 1)[0], str(ex))

                for rel, unc in unc_paths[1:]:
                    h2 = None
                    try:
                        h2 = C.open_source_stable(unc)
                        id2 = C.handle_identity(h2)
                        try:
                            C.compare_hardlink_sibling_identity(ident, id2, unc)
                            if int(id2["size"]) != expect:
                                return stop("HL_SIZE_DRIFT", f"entity={eid} path={unc}")
                        except RuntimeError as ex:
                            return stop("HL_SPLIT", f"entity={eid}:{ex}")
                    finally:
                        C.safe_close(h2)

                C.seek_begin(h)
                if dry_run:
                    _empty, digest = C.read_exact_hash(h, expect)
                    after = C.handle_identity(h)
                    if after["file_id"] != ident["file_id"] or after["size"] != expect:
                        return stop("SOURCE_CHANGED_DURING_PROBE", str(eid))
                    log["events"].append(
                        {
                            "entity_id": eid,
                            "action": "PROBE_HASH",
                            "sha256": digest,
                            "bytes": expect,
                            "unc": primary_unc,
                            "same_handle": True,
                        }
                    )
                    planned_bytes += expect
                    budget -= expect
                    continue

                dest_primary.parent.mkdir(parents=True, exist_ok=True)
                C.ensure_no_reparse_ancestors(dest_primary.parent, stop_at=C.ALLOWED_DEST)
                # same handle: identity already taken; seek begin; copy+hash without reopen
                C.seek_begin(h)
                result = C.copy_bounded(h, str(dest_primary), expect, budget)
                after = C.handle_identity(h)
                if (
                    after["file_id"] != ident["file_id"]
                    or after["size"] != expect
                    or after["mtime_ft"] != ident["mtime_ft"]
                ):
                    return stop("SOURCE_CHANGED_DURING_COPY", str(eid))
                budget -= result["bytes"]
                planned_bytes += result["bytes"]

                for rel, unc in unc_paths[1:]:
                    dp = C.dest_under_root(C.ALLOWED_DEST, rel)
                    dp.parent.mkdir(parents=True, exist_ok=True)
                    C.ensure_no_reparse_ancestors(dp.parent, stop_at=C.ALLOWED_DEST)
                    if dp.exists():
                        return stop("DEST_LINK_EXISTS", str(dp))
                    ok = C.CreateHardLinkW(
                        C.to_win_long_path(str(dp)), C.to_win_long_path(str(dest_primary)), None
                    )
                    if not ok:
                        err = __import__("ctypes").get_last_error()
                        return stop("HARDLINK_FAIL", f"{dp}:winerror={err}")

                ent_rec = {
                    "entity_id": eid,
                    "file_id": e["file_id"],
                    "volume_serial": e["volume_serial"],
                    "unique_file_bytes": expect,
                    "sha256": result["sha256"],
                    "primary_dest": str(dest_primary),
                    "path_count": len(unc_paths),
                    "same_handle_copy": True,
                    "source_attrs": {
                        "is_compressed": ident.get("is_compressed"),
                        "is_sparse": ident.get("is_sparse"),
                    },
                    "ident_before": {
                        k: ident[k]
                        for k in ("file_id", "size", "mtime_ft", "volume_serial", "allocation_size")
                    },
                    "ident_after": {
                        k: after[k]
                        for k in ("file_id", "size", "mtime_ft", "volume_serial", "allocation_size")
                    },
                }
                copy_record["entities"].append(ent_rec)
                copy_record["unique_bytes"] += expect
                copy_record["path_count"] += len(unc_paths)
                log["events"].append(
                    {
                        "entity_id": eid,
                        "action": "COPIED",
                        "sha256": result["sha256"],
                        "bytes": expect,
                        "same_handle": True,
                    }
                )
            finally:
                C.safe_close(h)

        con.close()
        if enable:
            free_after = C.volume_free_bytes("E:\\")
            log["volume_free_after"] = free_after
            log["volume_free_delta"] = free_before - free_after if free_before is not None else None
            rec_path = LOG_DIR / f"PILOT_COPY_RECORD_{stamp}.json"
            vol_live = C.get_volume_identity("E:\\")
            copy_record["run_id"] = stamp
            copy_record["manifest_sha256"] = minfo["sha256"]
            copy_record["dest"] = str(C.ALLOWED_DEST)
            copy_record["dest_volume"] = vol_live
            copy_record["expected_dest_volume"] = C.EXPECTED_DEST_VOLUME
            copy_record["hostname"] = __import__("socket").gethostname()
            copy_record["source_root_mapped"] = C.DESKTOP_UNC_SOURCE_ROOT
            copy_record["volume_free_before"] = free_before
            copy_record["volume_free_after"] = free_after
            copy_record["generated_at"] = C.now_iso()
            # Self-check record integrity before persist (same rules acceptance will enforce)
            expected_ids = set(int(x) for x in entity_ids)
            rec_deficits = C.validate_copy_record_integrity(
                copy_record, expected_ids, require_full_pilot_counts=True
            )
            if rec_deficits:
                log["copy_record_deficits"] = rec_deficits
                return stop("COPY_RECORD_INCOMPLETE", ",".join(rec_deficits))
            for ent in copy_record["entities"]:
                if not C.is_valid_sha256_hex(ent.get("sha256")):
                    return stop("COPY_SHA_INVALID", str(ent.get("entity_id")))
            rec_path.write_text(json.dumps(copy_record, ensure_ascii=False, indent=2), encoding="utf-8")
            log["copy_record"] = str(rec_path)
            return stop("COPY_OK", f"entities={len(copy_record['entities'])} unique={copy_record['unique_bytes']}")
        return stop("DRY_RUN_OK", f"probed_entities={len(entity_ids)} planned_bytes={planned_bytes}")
    except Exception as ex:
        return stop("STOPPED_ON_ERROR", f"{type(ex).__name__}:{ex}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--dest", type=Path, default=C.ALLOWED_DEST)
    ap.add_argument("--confirm-dest", type=str, default="")
    ap.add_argument("--enable-copy", action="store_true")
    ap.add_argument("--i-accept-pilot-copy", action="store_true")
    ap.add_argument("--r8-stopped-evidence", type=str, default="")
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--probe-sources", action="store_true", help="Dry-run: open UNC sources (desktop/network)")
    ap.add_argument("--limit-entities", type=int, default=0, help="Dry-run / partial only; forbidden with copy")
    ap.add_argument("--log", type=Path, default=None)
    args = ap.parse_args(argv)
    return plan_and_optionally_copy(args)


if __name__ == "__main__":
    # ensure import path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
