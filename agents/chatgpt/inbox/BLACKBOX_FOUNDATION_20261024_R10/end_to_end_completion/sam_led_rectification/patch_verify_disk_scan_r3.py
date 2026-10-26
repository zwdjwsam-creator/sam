# -*- coding: utf-8 -*-
"""R3: verify() must scan the DISK for equivalent release dirs, not just trust the log.

Gap found in R2's own test: `equivalent_duplicates` counted only roots that had gone through
commit(). On the desktop, 4 equivalent dirs exist but only the rounds that actually called
commit() are logged — dirs produced by an aborted/failed run, or by a run whose commit never
reached the NOOP branch, are invisible.

Fix: `scan_equivalent_dirs()` lists every sibling release dir under the reference's parent and
compares the identity-determining metadata (`asof`, `source_cleaning_release`,
`parent_release_id` — exactly the non-product part of CC_COMMIT_IDENTITY_V2) plus
`SEAL.all_pass`. That is fast (small JSON reads only) and is reported with an explicit
precision label `IDENTITY_LEVEL_NOT_CONTENT_PROVEN`, because it does NOT hash products.
`release_content_id` remains the only whole-content proof.

Reading order in verify():
  equivalent_duplicates        -> what commit() actually observed (append-only log)
  disk_equivalent_dirs         -> what is on disk right now (identity-level screen)
Both are reported; neither changes `consistent`, because an equivalent duplicate is not a
corruption — it is untracked accumulation that the reference intentionally ignores.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

STAMP = "20261026"

HELPER_ANCHOR = '''def read_duplicate_roots(commit_id: str = None) -> list:
'''

HELPER_NEW = '''def scan_equivalent_dirs(reference_root: str, asof=None, source_cleaning_release=None,
                         parent_release_id=None) -> Dict[str, Any]:
    """Screen sibling release dirs for identity-equivalent content (fast, metadata only).

    Compares the three non-product fields that feed CC_COMMIT_IDENTITY_V2 plus SEAL.all_pass.
    Deliberately does NOT hash products, so the result is labelled
    IDENTITY_LEVEL_NOT_CONTENT_PROVEN: a match here means "almost certainly the same payload",
    not "proven byte-equal". release_content_id is the content-level proof.
    """
    out = {"release_dirs_total": 0, "reference_root": str(reference_root),
           "identity_equivalent_dirs": [], "identity_equivalent_count": 0,
           "precision": "IDENTITY_LEVEL_NOT_CONTENT_PROVEN"}
    try:
        parent = Path(str(reference_root)).parent
        if not parent.is_dir():
            return {**out, "error": "REFERENCE_PARENT_MISSING"}
        ref_norm = os.path.normcase(os.path.normpath(str(reference_root)))
        dirs = sorted([p for p in parent.iterdir() if p.is_dir()], key=lambda p: p.name)
        out["release_dirs_total"] = len(dirs)
        for d in dirs:
            if os.path.normcase(os.path.normpath(str(d))) == ref_norm:
                continue
            rj = d / "RELEASE.json"
            if not rj.is_file():
                continue
            try:
                j = json.loads(rj.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            same = (
                str(j.get("asof")) == str(asof)
                and str(j.get("source_cleaning_release")) == str(source_cleaning_release)
                and str(j.get("parent_release_id")) == str(parent_release_id)
            )
            if not same:
                continue
            all_pass = None
            sj = d / "SEAL.json"
            if sj.is_file():
                try:
                    all_pass = json.loads(sj.read_text(encoding="utf-8")).get("all_pass")
                except Exception:  # noqa: BLE001
                    all_pass = None
            out["identity_equivalent_dirs"].append({
                "root": str(d),
                "release_id": j.get("cache_release_id"),
                "all_pass": all_pass,
            })
        out["identity_equivalent_count"] = len(out["identity_equivalent_dirs"])
    except OSError as e:
        out["error"] = f"{type(e).__name__}: {e}"
    return out


def read_duplicate_roots(commit_id: str = None) -> list:
'''

VERIFY_ANCHOR = '''        "reference_root_present": Path(str(commit.get("release_root"))).exists(),
        "equivalent_duplicates": len(read_duplicate_roots(commit.get("commit_id"))),
        "equivalent_duplicate_roots": [r.get("duplicate_root")
                                       for r in read_duplicate_roots(commit.get("commit_id"))],
'''

VERIFY_NEW = '''        "reference_root_present": Path(str(commit.get("release_root"))).exists(),
        "equivalent_duplicates": len(read_duplicate_roots(commit.get("commit_id"))),
        "equivalent_duplicate_roots": [r.get("duplicate_root")
                                       for r in read_duplicate_roots(commit.get("commit_id"))],
        "disk_equivalent_dirs": scan_equivalent_dirs(
            commit.get("release_root"),
            asof=commit.get("asof"),
            source_cleaning_release=(commit.get("identity") or {}).get("source_cleaning_release")
            or commit.get("source_cleaning_release"),
            parent_release_id=(commit.get("identity") or {}).get("parent_release_id")
            or commit.get("parent_release_id"),
        ),
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    args = ap.parse_args()
    p = Path(args.file)
    if not p.is_file():
        print("MISSING", p)
        return 2
    raw = p.read_bytes()
    before = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8")
    crlf = "\r\n" in text
    eol = "\r\n" if crlf else "\n"

    def A(s: str) -> str:
        return s.replace("\n", eol) if crlf else s

    if "scan_equivalent_dirs" in text:
        print(json.dumps({"file": str(p), "status": "ALREADY_PATCHED"}))
        return 0
    if "DUPLICATE_ROOTS.jsonl" not in text:
        print("PREREQ_MISSING: apply patch_duplicate_roots_r2.py first")
        return 5

    applied = []
    for name, anchor, new in (
        ("scan_helper", HELPER_ANCHOR, HELPER_NEW),
        ("verify_report_disk", VERIFY_ANCHOR, VERIFY_NEW),
    ):
        if A(anchor) not in text:
            print(f"ANCHOR_FAIL {name} (crlf={crlf})")
            return 3
        text = text.replace(A(anchor), A(new), 1)
        applied.append(name)

    nb = text.encode("utf-8")
    try:
        compile(nb, str(p), "exec")
    except SyntaxError as e:
        print("SYNTAX_ERROR_ABORT", e)
        return 4
    bak = p.with_name(p.name + f".bak_sam_led_{STAMP}_scan")
    if not bak.exists():
        shutil.copy2(p, bak)
    p.write_bytes(nb)
    print(json.dumps({"file": str(p), "crlf": crlf, "applied": applied, "backup": str(bak),
                      "sha256_before": before,
                      "sha256_after": hashlib.sha256(p.read_bytes()).hexdigest(),
                      "bytes_before": len(raw), "bytes_after": len(nb)},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
