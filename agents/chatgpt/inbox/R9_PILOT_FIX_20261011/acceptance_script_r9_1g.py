# -*- coding: utf-8 -*-
"""
BLACKBOX R9 — 1GiB pilot acceptance (post ChatGPT review fix).

- No overall PASS on empty/partial/missing/errors.
- --limit-entities => partial check only; cannot yield overall PASS.
- Hash once per unique entity; identity-check all dest paths.
- Bind manifest SHA + copy record; measure true allocation via FILE_STANDARD_INFO.
Old version: acceptance_script_r9_1g_PRE_REVIEW_FIX.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import r9_pilot_common_r9fix as C

LOG_DIR = Path(r"C:\LAN_SHARE_REPORT")
DEFAULT_MANIFEST = Path(r"C:\LAN_SHARE_REPORT\BLACKBOX_R9_MANIFEST\PILOT_1G_MANIFEST.sqlite")


def walk_dest_extra(dest_root: Path, expected_rels: set[str]) -> dict:
    extras = []
    reparses = []
    walk_errors: list[str] = []

    def _onerror(err: BaseException) -> None:
        # Directory enumeration failure is an acceptance deficit (not silent skip).
        walk_errors.append(f"WALK_ONERROR:{type(err).__name__}:{err}")

    for root, dirs, files in os.walk(str(dest_root), onerror=_onerror):
        # detect reparse dirs without following
        keep = []
        for d in dirs:
            p = str(Path(root) / d)
            try:
                if C.is_reparse_path(p):
                    reparses.append(p)
                    continue  # do not descend
            except OSError as e:
                reparses.append(f"ATTR_FAIL:{p}:{e}")
                walk_errors.append(f"DIR_ATTR_FAIL:{p}:{e}")
                continue
            keep.append(d)
        dirs[:] = keep
        for fn in files:
            fp = Path(root) / fn
            try:
                if C.is_reparse_path(str(fp)):
                    reparses.append(str(fp))
            except OSError as e:
                reparses.append(f"ATTR_FAIL:{fp}:{e}")
                walk_errors.append(f"FILE_ATTR_FAIL:{fp}:{e}")
            rel = str(fp.relative_to(dest_root)).replace("/", "\\")
            if rel not in expected_rels:
                extras.append(rel)
    return {
        "extra_files": extras,
        "unexpected_reparse": reparses,
        "walk_errors": walk_errors,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--dest", type=Path, default=C.ALLOWED_DEST)
    ap.add_argument("--copy-record", type=Path, required=False, default=None)
    ap.add_argument("--dry-structure-only", action="store_true")
    ap.add_argument("--limit-entities", type=int, default=0)
    ap.add_argument("--source-root", type=str, default=C.DESKTOP_UNC_SOURCE_ROOT)
    ap.add_argument("--log", type=Path, default=None)
    args = ap.parse_args(argv)

    stamp = C.now_iso().replace(":", "").replace("+", "")
    log_path = args.log or (LOG_DIR / f"ACCEPTANCE_R9FIX_{stamp}.json")
    report: dict = {
        "generated_at": C.now_iso(),
        "dest": str(args.dest),
        "dry_structure_only": args.dry_structure_only,
        "partial": bool(args.limit_entities and args.limit_entities > 0),
        "deficits": [],
        "overall_pass": False,
        "content_link_pass": False,
        "occupancy_pass": False,
    }

    def finish(verdict: str, code: int) -> int:
        report["verdict"] = verdict
        report["finished_at"] = C.now_iso()
        # hard rule: partial / structure-only / any deficit => no overall PASS
        if report["deficits"] or report["partial"] or args.dry_structure_only:
            report["overall_pass"] = False
        log_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {
                    "verdict": verdict,
                    "overall_pass": report["overall_pass"],
                    "deficits": report["deficits"],
                    "log": str(log_path),
                },
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )
        return code

    try:
        if str(args.dest).rstrip("\\").lower() != str(C.ALLOWED_DEST).rstrip("\\").lower():
            report["deficits"].append(f"DEST_NOT_ALLOWED:{args.dest}")
            return finish("FAIL_DEST", 2)

        con, minfo = C.bind_manifest(args.manifest)
        report["manifest"] = minfo

        ents = list(con.execute("select * from entities order by entity_id"))
        if args.limit_entities > 0:
            ents = ents[: args.limit_entities]
            report["deficits"].append("PARTIAL_LIMIT_ENTITIES")

        if not ents:
            report["deficits"].append("EMPTY_ENTITY_SET")
            con.close()
            return finish("FAIL_EMPTY", 2)

        expected_rels: set[str] = set()
        logical_bytes = 0
        unique_bytes = 0
        for e in ents:
            rows = list(
                con.execute(
                    "select source_relative_path from hardlink_paths where entity_id=?",
                    (e["entity_id"],),
                )
            )
            if not rows:
                report["deficits"].append(f"ENTITY_NO_PATHS:{e['entity_id']}")
                continue
            unique_bytes += int(e["unique_file_bytes"])
            logical_bytes += int(e["unique_file_bytes"]) * len(rows)
            for r in rows:
                expected_rels.add(C.validate_relative_path(r["source_relative_path"]))

        report["bytes"] = {
            "manifest_unique_content_bytes": unique_bytes,
            "dest_unique_content_bytes": None,  # sum of EndOfFile / size over distinct dest entities
            "dest_unique_allocated_bytes": None,  # AllocationSize — NOT file length
            "logical_path_bytes": logical_bytes,
            "volume_free_before": None,
            "volume_free_after": None,
            "volume_free_delta": None,
            "compressed_or_sparse_seen": False,
        }

        if args.dry_structure_only:
            for rel in list(expected_rels)[:20]:
                C.join_unc_source(rel, args.source_root)
                C.dest_under_root(args.dest, rel)
            con.close()
            if report["partial"]:
                return finish("PARTIAL", 0)
            return finish("STRUCTURE_DRY_OK_NO_COPY_ACCEPTANCE", 0)

        if not args.dest.exists():
            report["deficits"].append("DEST_MISSING")
            con.close()
            return finish("FAIL_DEST_MISSING", 2)

        try:
            C.ensure_no_reparse_ancestors(args.dest, stop_at=Path(str(args.dest.anchor) or "E:\\"))
        except Exception as e:
            report["deficits"].append(f"DEST_REPARSE_OR_ATTR:{e}")
            con.close()
            return finish("FAIL_DEST_REPARSE", 2)

        if not args.copy_record or not Path(args.copy_record).exists():
            report["deficits"].append("COPY_RECORD_REQUIRED")
            con.close()
            return finish("FAIL_NO_COPY_RECORD", 2)

        crec = json.loads(Path(args.copy_record).read_text(encoding="utf-8"))
        report["binding"] = {
            "run_id": crec.get("run_id"),
            "manifest_sha256": crec.get("manifest_sha256"),
            "dest": crec.get("dest"),
            "dest_volume_record": crec.get("dest_volume"),
        }
        if crec.get("manifest_sha256") != C.EXPECTED_MANIFEST_SHA256:
            report["deficits"].append("COPY_RECORD_MANIFEST_SHA_MISMATCH")
        if crec.get("manifest_sha256") != minfo["sha256"]:
            report["deficits"].append("COPY_RECORD_VS_LIVE_MANIFEST_SHA_MISMATCH")
        if str(crec.get("dest", "")).rstrip("\\").lower() != str(args.dest).rstrip("\\").lower():
            report["deficits"].append("COPY_RECORD_DEST_MISMATCH")

        expected_eids = {int(e["entity_id"]) for e in ents}
        # Full pilot ⇒ exact entity set + space/run_id/sha integrity (no soft skip).
        rec_deficits = C.validate_copy_record_integrity(
            crec,
            expected_eids,
            require_full_pilot_counts=not report["partial"],
        )
        report["deficits"].extend(rec_deficits)
        if len(ents) != C.EXPECTED_ENTITY_COUNT and not report["partial"]:
            report["deficits"].append("ACCEPTANCE_ENTITY_SET_INCOMPLETE")

        try:
            live_vol = C.get_volume_identity("E:\\")
            report["binding"]["dest_volume_live"] = live_vol
            rec_vol = crec.get("dest_volume") or {}
            if rec_vol.get("VolumeSerialNumber_dword") != live_vol.get("VolumeSerialNumber_dword"):
                report["deficits"].append("DEST_VOLUME_DRIFT_VS_COPY_RECORD")
            if live_vol.get("VolumeSerialNumber_dword") != C.EXPECTED_DEST_VOLUME["VolumeSerialNumber_dword"]:
                report["deficits"].append("DEST_VOLUME_NOT_EXPECTED_DESKTOP_E")
        except OSError as e:
            report["deficits"].append(f"DEST_VOLUME_QUERY_FAIL:{e}")

        report["bytes"]["volume_free_before"] = crec.get("volume_free_before")
        report["bytes"]["volume_free_after_record"] = crec.get("volume_free_after")
        try:
            free_now = C.volume_free_bytes("E:\\")
            report["bytes"]["volume_free_after"] = free_now
            if crec.get("volume_free_before") is not None:
                report["bytes"]["volume_free_delta"] = crec["volume_free_before"] - free_now
        except OSError as e:
            report["deficits"].append(f"FREE_SPACE_MEASURE_FAIL:{e}")

        sha_by_eid: dict[int, str] = {}
        for x in crec.get("entities") or []:
            if isinstance(x, dict) and "entity_id" in x:
                sha_by_eid[int(x["entity_id"])] = x.get("sha256")  # type: ignore[assignment]
        eid_by_dest_key: dict[tuple[str, str], int] = {}
        allocated_by_key: dict[tuple[str, str], int] = {}
        content_by_key: dict[tuple[str, str], int] = {}
        missing = []
        content_fail = []
        link_fail = []
        merge_fail = []
        paths_checked = 0
        entities_hashed = 0

        for e in ents:
            eid = int(e["entity_id"])
            expect = int(e["unique_file_bytes"])
            rows = list(
                con.execute(
                    "select source_relative_path from hardlink_paths where entity_id=? order by source_relative_path",
                    (eid,),
                )
            )
            dest_paths = [C.dest_under_root(args.dest, r["source_relative_path"]) for r in rows]

            if not dest_paths[0].exists():
                missing.append(str(dest_paths[0]))
                continue
            h = None
            try:
                h = C.open_source_stable(str(dest_paths[0]))
                ident0 = C.handle_identity(h)
                if ident0.get("is_compressed") or ident0.get("is_sparse"):
                    report["bytes"]["compressed_or_sparse_seen"] = True
                if ident0["size"] != expect:
                    content_fail.append({"entity_id": eid, "error": "size", "got": ident0["size"]})
                C.seek_begin(h)
                _e, digest = C.read_exact_hash(h, expect)
                entities_hashed += 1
                expected_sha = sha_by_eid.get(eid)
                if expected_sha and digest != expected_sha:
                    content_fail.append({"entity_id": eid, "error": "sha_mismatch_vs_record", "got": digest})
                key0 = (ident0["volume_serial"], ident0["file_id"])
                content_by_key[key0] = ident0["size"]
                if ident0.get("allocation_size") is None:
                    raise RuntimeError("ALLOCATION_SIZE_MISSING")
                allocated_by_key[key0] = int(ident0["allocation_size"])
            except Exception as ex:
                content_fail.append({"entity_id": eid, "error": str(ex)})
                continue
            finally:
                C.safe_close(h)

            keys = set()
            for dp in dest_paths:
                if not dp.exists():
                    missing.append(str(dp))
                    continue
                h2 = None
                try:
                    h2 = C.open_source_stable(str(dp))
                    idn = C.handle_identity(h2)
                    key = (idn["volume_serial"], idn["file_id"])
                    keys.add(key)
                    allocated_by_key[key] = int(idn["allocation_size"])
                    content_by_key[key] = idn["size"]
                    paths_checked += 1
                    if idn.get("is_compressed") or idn.get("is_sparse"):
                        report["bytes"]["compressed_or_sparse_seen"] = True
                except Exception as ex:
                    link_fail.append({"entity_id": eid, "path": str(dp), "error": str(ex)})
                finally:
                    C.safe_close(h2)
            if len(keys) != 1:
                link_fail.append({"entity_id": eid, "error": "dest_hl_not_same_entity", "keys": list(keys)})
            else:
                dkey = next(iter(keys))
                if dkey in eid_by_dest_key and eid_by_dest_key[dkey] != eid:
                    merge_fail.append({"dest_key": list(dkey), "a": eid_by_dest_key[dkey], "b": eid})
                else:
                    eid_by_dest_key[dkey] = eid

        report["checks_done"] = {
            "entities_hashed": entities_hashed,
            "paths_identity_checked": paths_checked,
            "expected_entities": C.EXPECTED_ENTITY_COUNT if not report["partial"] else len(ents),
            "expected_paths": C.EXPECTED_PATH_COUNT if not report["partial"] else len(expected_rels),
        }
        if not report["partial"]:
            if entities_hashed != C.EXPECTED_ENTITY_COUNT:
                report["deficits"].append(f"HASH_COVERAGE={entities_hashed}")
            if paths_checked != C.EXPECTED_PATH_COUNT:
                report["deficits"].append(f"PATH_IDENTITY_COVERAGE={paths_checked}")

        if missing:
            report["deficits"].append("MISSING_DEST_PATHS")
            report["missing_sample"] = missing[:20]
        if content_fail:
            report["deficits"].append("CONTENT_HASH_OR_SIZE_FAIL")
            report["content_fail_sample"] = content_fail[:10]
        if link_fail:
            report["deficits"].append("LINK_ACCEPTANCE_FAIL")
            report["link_fail_sample"] = link_fail[:10]
        if merge_fail:
            report["deficits"].append("CROSS_ENTITY_MERGE")
            report["merge_fail_sample"] = merge_fail[:10]

        extra = walk_dest_extra(args.dest, expected_rels)
        if extra["walk_errors"]:
            report["deficits"].append("DEST_WALK_ENUM_ERROR")
            report["walk_error_sample"] = extra["walk_errors"][:20]
        if extra["extra_files"]:
            report["deficits"].append("EXTRA_FILES_OUTSIDE_MANIFEST")
            report["extra_sample"] = extra["extra_files"][:20]
        if extra["unexpected_reparse"]:
            report["deficits"].append("UNEXPECTED_REPARSE_IN_DEST")
            report["reparse_sample"] = extra["unexpected_reparse"][:20]

        report["bytes"]["dest_unique_content_bytes"] = sum(content_by_key.values()) if content_by_key else None
        alloc_sum = sum(allocated_by_key.values()) if allocated_by_key else None
        report["bytes"]["dest_unique_allocated_bytes"] = alloc_sum
        report["bytes"]["note"] = (
            "dest_unique_allocated_bytes = sum FILE_STANDARD_INFO.AllocationSize over distinct "
            "(dest_volume_serial, file_id). Never use file length as allocated. "
            "If compressed/sparse seen, AllocationSize is the authoritative on-disk measure; "
            "free-space delta also reflects metadata/cluster rounding."
        )

        hard_fail_tokens = {
            "MISSING_DEST_PATHS",
            "CONTENT_HASH_OR_SIZE_FAIL",
            "LINK_ACCEPTANCE_FAIL",
            "CROSS_ENTITY_MERGE",
            "EXTRA_FILES_OUTSIDE_MANIFEST",
            "UNEXPECTED_REPARSE_IN_DEST",
            "DEST_WALK_ENUM_ERROR",
            "COPY_RECORD_REQUIRED",
            "COPY_RECORD_MANIFEST_SHA_MISMATCH",
            "COPY_RECORD_VS_LIVE_MANIFEST_SHA_MISMATCH",
            "COPY_RECORD_DEST_MISMATCH",
            "COPY_RECORD_RUN_ID_MISSING",
            "COPY_RECORD_ENTITIES_MISSING",
            "COPY_RECORD_ENTITY_ID_DUPLICATE",
            "DEST_VOLUME_DRIFT_VS_COPY_RECORD",
            "DEST_VOLUME_NOT_EXPECTED_DESKTOP_E",
            "DEST_MISSING",
            "EMPTY_ENTITY_SET",
            "ACCEPTANCE_ENTITY_SET_INCOMPLETE",
            "ALLOC_MEASURE_FAIL",
        }

        def _is_hard_deficit(d: str) -> bool:
            if d in hard_fail_tokens:
                return True
            return any(
                d.startswith(p)
                for p in (
                    "HASH_COVERAGE",
                    "PATH_IDENTITY_COVERAGE",
                    "COPY_RECORD_",
                    "DEST_VOLUME_",
                    "DEST_REPARSE",
                    "FREE_SPACE_",
                )
            )

        content_link_ok = not any(_is_hard_deficit(d) for d in report["deficits"])
        report["content_link_pass"] = content_link_ok and not report["partial"]

        space_ok = (
            crec.get("volume_free_before") is not None
            and crec.get("volume_free_after") is not None
            and "FREE_SPACE_MEASURE_FAIL" not in report["deficits"]
            and not any(str(d).startswith("COPY_RECORD_SPACE_EVIDENCE") for d in report["deficits"])
        )
        if alloc_sum is None or report["bytes"]["dest_unique_content_bytes"] is None:
            report["deficits"].append("ALLOC_MEASURE_FAIL")
            report["occupancy_pass"] = False
        elif not space_ok:
            report["occupancy_pass"] = False
            if "COPY_RECORD_SPACE_EVIDENCE_MISSING:volume_free_before" not in report["deficits"] and crec.get(
                "volume_free_before"
            ) is None:
                report["deficits"].append("COPY_RECORD_SPACE_EVIDENCE_MISSING:volume_free_before")
            if "COPY_RECORD_SPACE_EVIDENCE_MISSING:volume_free_after" not in report["deficits"] and crec.get(
                "volume_free_after"
            ) is None:
                report["deficits"].append("COPY_RECORD_SPACE_EVIDENCE_MISSING:volume_free_after")
        else:
            report["occupancy_pass"] = True
            delta = report["bytes"].get("volume_free_delta")
            if delta is not None and delta < 0:
                report["deficits"].append("FREE_SPACE_INCREASED_UNEXPECTED")
                report["occupancy_pass"] = False

        # Any necessary evidence deficit ⇒ overall_pass cannot be TRUE
        report["overall_pass"] = bool(
            report["content_link_pass"]
            and report["occupancy_pass"]
            and not report["deficits"]
            and not report["partial"]
            and not any(_is_hard_deficit(d) for d in report["deficits"])
        )
        con.close()
        if report["partial"]:
            return finish("PARTIAL", 2)
        return finish("PASS" if report["overall_pass"] else "FAIL_DEFICITS_PRESENT", 0 if report["overall_pass"] else 2)
    except Exception as ex:
        report["deficits"].append(f"EXCEPTION:{type(ex).__name__}:{ex}")
        return finish("FAIL_EXCEPTION", 2)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
