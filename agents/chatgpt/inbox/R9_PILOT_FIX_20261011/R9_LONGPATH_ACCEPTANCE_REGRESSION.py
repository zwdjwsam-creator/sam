# -*- coding: utf-8 -*-
"""
R9 long-path acceptance regression (C: only; does not touch E: pilot dest).

Exercises presence / open / hash / hardlink-identity / walk_extra paths used by
acceptance_script_r9_1g.py after the long-path fix. No mocked overall_pass.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import traceback
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT")
import r9_pilot_common_r9fix as C
from acceptance_script_r9_1g import walk_dest_extra

ROOT = Path(r"C:\LAN_SHARE_REPORT\R9_LONGPATH_REGRESSION_20261011_1301")
OUT = Path(r"C:\LAN_SHARE_REPORT\R9_LONGPATH_ACCEPTANCE_REGRESSION_RESULT.json")


def _long_seg(n: int, ch: str = "测") -> str:
    return (ch * n)[:240]


def _mk_tree(base: Path) -> dict:
    if base.exists():
        raise RuntimeError(f"REFUSING_REUSE_EXISTING:{base}")
    base.mkdir(parents=True)

    parts = [
        "数据",
        "清洗成品",
        _long_seg(80, "长"),
        _long_seg(80, "路"),
        _long_seg(60, "径"),
        "releases",
        "sample_group",
    ]
    d = base
    for p in parts:
        d = d / p
        os.makedirs(C.to_win_long_path(str(d)), exist_ok=True)

    content_a = b"R9-LONGPATH-A-" + os.urandom(64)
    content_b = b"R9-LONGPATH-B-" + os.urandom(64)
    sha_a = hashlib.sha256(content_a).hexdigest()
    sha_b = hashlib.sha256(content_b).hexdigest()

    name_a1 = _long_seg(100, "文") + "_a1.bin"
    name_a2 = _long_seg(100, "链") + "_a2.bin"
    name_b1 = _long_seg(100, "另") + "_b1.bin"
    p_a1, p_a2, p_b1 = d / name_a1, d / name_a2, d / name_b1

    def _write(path: Path, data: bytes) -> None:
        with open(C.to_win_long_path(str(path)), "wb") as f:
            f.write(data)

    _write(p_a1, content_a)
    if not C.CreateHardLinkW(C.to_win_long_path(str(p_a2)), C.to_win_long_path(str(p_a1)), None):
        raise RuntimeError(f"HARDLINK_FAIL winerror={__import__('ctypes').get_last_error()}")
    _write(p_b1, content_b)

    # ensure >300 chars via extra nest + hardlink
    extra = d / (_long_seg(80, "超") + "_nest")
    os.makedirs(C.to_win_long_path(str(extra)), exist_ok=True)
    p_a3 = extra / (_long_seg(90, "超") + "_a3.bin")
    if not C.CreateHardLinkW(C.to_win_long_path(str(p_a3)), C.to_win_long_path(str(p_a1)), None):
        raise RuntimeError(f"HARDLINK_FAIL_A3 winerror={__import__('ctypes').get_last_error()}")

    def rel(p: Path) -> str:
        return C.relative_under_root(str(p), base)

    info = {
        "base": str(base),
        "paths": {"a1": str(p_a1), "a2": str(p_a2), "a3": str(p_a3), "b1": str(p_b1)},
        "rels": {"a1": rel(p_a1), "a2": rel(p_a2), "a3": rel(p_a3), "b1": rel(p_b1)},
        "sha_a": sha_a,
        "sha_b": sha_b,
        "content_a": content_a,
        "content_b": content_b,
        "len_a1": len(str(p_a1)),
        "len_a2": len(str(p_a2)),
        "len_a3": len(str(p_a3)),
    }
    if min(info["len_a1"], info["len_a3"]) < 260:
        raise RuntimeError(f"PATH_NOT_LONG_ENOUGH:{info}")
    return info


def _accept_entities(dest_root: Path, entities: list[dict], expected_rels: set[str]) -> dict:
    deficits: list[str] = []
    missing: list[str] = []
    path_attr_fail: list[dict] = []
    content_fail: list[dict] = []
    link_fail: list[dict] = []
    merge_fail: list[dict] = []
    eid_by_dest_key: dict[tuple[str, str], int] = {}
    entities_hashed = 0
    paths_checked = 0

    for ent in entities:
        eid = int(ent["entity_id"])
        expect = int(ent["unique_file_bytes"])
        expect_sha = ent["sha256"]
        dest_paths = [C.dest_under_root(dest_root, r) for r in ent["rels"]]
        try:
            presence0 = C.classify_path_presence(str(dest_paths[0]))
        except OSError as ex:
            path_attr_fail.append({"entity_id": eid, "error": str(ex)})
            continue
        if presence0 == "missing":
            missing.append(str(dest_paths[0]))
            continue
        h = None
        try:
            h = C.open_source_stable(str(dest_paths[0]))
            ident0 = C.handle_identity(h)
            if ident0["size"] != expect:
                content_fail.append({"entity_id": eid, "error": "size"})
            C.seek_begin(h)
            _n, digest = C.read_exact_hash(h, expect)
            entities_hashed += 1
            if digest != expect_sha:
                content_fail.append({"entity_id": eid, "error": "sha_mismatch"})
        except Exception as ex:
            content_fail.append({"entity_id": eid, "error": str(ex)})
            continue
        finally:
            C.safe_close(h)

        keys = set()
        for dp in dest_paths:
            try:
                presence = C.classify_path_presence(str(dp))
            except OSError as ex:
                path_attr_fail.append({"entity_id": eid, "path": str(dp), "error": str(ex)})
                continue
            if presence == "missing":
                missing.append(str(dp))
                continue
            h2 = None
            try:
                h2 = C.open_source_stable(str(dp))
                idn = C.handle_identity(h2)
                keys.add((idn["volume_serial"], idn["file_id"]))
                paths_checked += 1
            except Exception as ex:
                link_fail.append({"entity_id": eid, "path": str(dp), "error": str(ex)})
            finally:
                C.safe_close(h2)
        if len(keys) != 1:
            link_fail.append({"entity_id": eid, "error": "dest_hl_not_same_entity", "keys": list(keys)})
        else:
            dkey = next(iter(keys))
            if dkey in eid_by_dest_key and eid_by_dest_key[dkey] != eid:
                merge_fail.append({"a": eid_by_dest_key[dkey], "b": eid})
            else:
                eid_by_dest_key[dkey] = eid

    if missing:
        deficits.append("MISSING_DEST_PATHS")
    if path_attr_fail:
        deficits.append("PATH_ATTR_OR_ACCESS_FAIL")
    if content_fail:
        deficits.append("CONTENT_HASH_OR_SIZE_FAIL")
    if link_fail:
        deficits.append("LINK_ACCEPTANCE_FAIL")
    if merge_fail:
        deficits.append("CROSS_ENTITY_MERGE")

    extra = walk_dest_extra(dest_root, expected_rels)
    if extra["walk_errors"]:
        deficits.append("DEST_WALK_ENUM_ERROR")
    if extra["extra_files"]:
        deficits.append("EXTRA_FILES_OUTSIDE_MANIFEST")
    if extra["unexpected_reparse"]:
        deficits.append("UNEXPECTED_REPARSE_IN_DEST")

    return {
        "overall_pass": len(deficits) == 0,
        "deficits": deficits,
        "entities_hashed": entities_hashed,
        "paths_checked": paths_checked,
        "extra": {k: (v[:5] if isinstance(v, list) else v) for k, v in extra.items()},
        "missing_sample": missing[:5],
        "content_fail_sample": content_fail[:5],
        "link_fail_sample": link_fail[:5],
        "merge_fail_sample": merge_fail[:5],
    }


def _entities_from_info(info: dict) -> tuple[list[dict], set[str]]:
    rels_a = [info["rels"]["a1"], info["rels"]["a2"], info["rels"]["a3"]]
    ents = [
        {
            "entity_id": 1,
            "unique_file_bytes": len(info["content_a"]),
            "sha256": info["sha_a"],
            "rels": rels_a,
        },
        {
            "entity_id": 2,
            "unique_file_bytes": len(info["content_b"]),
            "sha256": info["sha_b"],
            "rels": [info["rels"]["b1"]],
        },
    ]
    expected: set[str] = set()
    for e in ents:
        expected.update(e["rels"])
    return ents, expected


def _restore_baseline(info: dict) -> None:
    """Restore hardlinks and file contents to known-good baseline."""
    for key in ("a2", "a3", "b1"):
        p = info["paths"][key]
        if C.classify_path_presence(p) == "present":
            os.remove(C.to_win_long_path(p))
    if not C.CreateHardLinkW(
        C.to_win_long_path(info["paths"]["a2"]), C.to_win_long_path(info["paths"]["a1"]), None
    ):
        raise RuntimeError("restore a2 hardlink failed")
    if not C.CreateHardLinkW(
        C.to_win_long_path(info["paths"]["a3"]), C.to_win_long_path(info["paths"]["a1"]), None
    ):
        raise RuntimeError("restore a3 hardlink failed")
    with open(C.to_win_long_path(info["paths"]["b1"]), "wb") as f:
        f.write(info["content_b"])
    # remove extras
    for root, dirs, files in os.walk(C.to_win_long_path(str(ROOT))):
        for fn in files:
            if "_EXTRA.bin" in fn:
                os.remove(root.rstrip("\\") + "\\" + fn)


def run() -> dict:
    results = []
    info = _mk_tree(ROOT)
    ents, expected = _entities_from_info(info)

    def run_case(name: str, expect_pass: bool, prepare, wrap_accept=None) -> None:
        _restore_baseline(info)
        local_ents = json.loads(json.dumps(ents))
        local_expected = set(expected)
        prepare(local_ents, local_expected, info)
        if wrap_accept:
            got = wrap_accept(lambda: _accept_entities(ROOT, local_ents, local_expected))
        else:
            got = _accept_entities(ROOT, local_ents, local_expected)
        ok = (got["overall_pass"] is True) if expect_pass else (got["overall_pass"] is False)
        results.append(
            {
                "case": name,
                "expect_pass": expect_pass,
                "got_pass": got["overall_pass"],
                "ok": ok,
                "deficits": got["deficits"],
                "detail": {
                    "entities_hashed": got["entities_hashed"],
                    "paths_checked": got["paths_checked"],
                    "extra": got["extra"],
                    "missing_sample": got["missing_sample"],
                    "content_fail_sample": got["content_fail_sample"],
                    "link_fail_sample": got["link_fail_sample"],
                    "merge_fail_sample": got["merge_fail_sample"],
                },
            }
        )

    run_case("LONGPATH_PRESENT_CONTENT_LINK_PASS", True, lambda e, x, i: None)

    def prep_missing(e, x, i):
        os.remove(C.to_win_long_path(i["paths"]["a2"]))

    run_case("DELETE_ONE_PATH_FAIL", False, prep_missing)

    def prep_corrupt(e, x, i):
        with open(C.to_win_long_path(i["paths"]["b1"]), "r+b") as f:
            f.write(b"X" * 16)

    run_case("CORRUPT_CONTENT_FAIL", False, prep_corrupt)

    def prep_noop(e, x, i):
        return None

    def wrap_walk_err(fn):
        real_walk = os.walk

        def broken(root, topdown=True, onerror=None, followlinks=False):
            if onerror is not None:
                onerror(OSError(5, "injected walk enumeration error"))
            yield from real_walk(root, topdown=topdown, onerror=onerror, followlinks=followlinks)

        os.walk = broken  # type: ignore[assignment]
        try:
            return fn()
        finally:
            os.walk = real_walk  # type: ignore[assignment]

    run_case("INJECT_WALK_ENUM_ERROR_FAIL", False, prep_noop, wrap_walk_err)

    def prep_extra(e, x, i):
        extra = Path(i["paths"]["a1"]).parent / (_long_seg(50, "外") + "_EXTRA.bin")
        with open(C.to_win_long_path(str(extra)), "wb") as f:
            f.write(b"EXTRA")

    run_case("EXTRA_LONGPATH_FILE_FAIL", False, prep_extra)

    def prep_split(e, x, i):
        os.remove(C.to_win_long_path(i["paths"]["a2"]))
        with open(C.to_win_long_path(i["paths"]["a1"]), "rb") as src, open(
            C.to_win_long_path(i["paths"]["a2"]), "wb"
        ) as dst:
            dst.write(src.read())

    run_case("HARDLINK_SPLIT_FAIL", False, prep_split)

    def prep_merge(e, x, i):
        os.remove(C.to_win_long_path(i["paths"]["b1"]))
        if not C.CreateHardLinkW(
            C.to_win_long_path(i["paths"]["b1"]), C.to_win_long_path(i["paths"]["a1"]), None
        ):
            raise RuntimeError("merge hardlink failed")
        for ent in e:
            if ent["entity_id"] == 2:
                ent["unique_file_bytes"] = len(i["content_a"])
                ent["sha256"] = i["sha_a"]

    run_case("CROSS_GROUP_MERGE_FAIL", False, prep_merge)

    pe = Path(info["paths"]["a3"]).exists()
    cw = C.path_exists_win(info["paths"]["a3"])
    results.append(
        {
            "case": "PATH_EXISTS_VS_LONGPATH_HELPER",
            "expect_pass": True,
            "got_pass": bool(cw),
            "ok": cw is True,
            "deficits": [],
            "detail": {"Path.exists": pe, "path_exists_win": cw, "path_len": info["len_a3"]},
        }
    )

    summary = {
        "root": str(ROOT),
        "path_lengths": {k: info[k] for k in ("len_a1", "len_a2", "len_a3")},
        "cases": results,
        "all_ok": all(r["ok"] for r in results),
        "note": "C: only; E: pilot dest untouched",
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"all_ok": summary["all_ok"], "log": str(OUT)}, ensure_ascii=False))
    return summary


if __name__ == "__main__":
    try:
        s = run()
        sys.exit(0 if s["all_ok"] else 2)
    except Exception:
        err = {"exception": traceback.format_exc()}
        OUT.write_text(json.dumps(err, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"all_ok": False, **err}, ensure_ascii=False))
        sys.exit(2)
