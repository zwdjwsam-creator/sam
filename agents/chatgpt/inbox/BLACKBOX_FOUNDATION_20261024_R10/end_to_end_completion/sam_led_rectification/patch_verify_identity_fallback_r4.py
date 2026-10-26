# -*- coding: utf-8 -*-
"""R4: fix the field-source chain in verify()'s disk scan (false-negative killer).

Measured: on both SAM and the desktop, disk_equivalent_dirs reported 0 while the append-only
log reported 1 (SAM) and the desktop's four RELEASE.json files were provably identical on
asof / source_cleaning_release / parent_release_id.

Cause: `verify()` fed `scan_equivalent_dirs()` from `commit["identity"]` only. A legacy
`CC_COMMIT_R1` COMMIT.json has NO `identity` key and no top-level
`source_cleaning_release` / `parent_release_id` — those live in
`versions/<commit_id[:16]>/CHECKPOINT.json` under `identity`. With None on the probe side,
`str(x) == str(None)` never matches a real value, so the scan could only ever return 0.

Fix: resolve each field from, in order,
  commit.identity -> commit.<top-level> -> checkpoint.identity
and record which source was used (`identity_source`) so a future reader can tell whether the
comparison was anchored on committed data or on a legacy record.

Also: cross-host scans must not be run with a local `release_root` string. If the resolved
parent directory does not live on the local machine, the scan now reports
`HOST_SCOPE_MISMATCH` instead of silently scanning a same-named local tree — that is exactly
how the first desktop test produced a bogus total of 2 dirs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

STAMP = "20261026"

# 1) make the helper aware of host scope
SCAN_ANCHOR = '''    out = {"release_dirs_total": 0, "reference_root": str(reference_root),
           "identity_equivalent_dirs": [], "identity_equivalent_count": 0,
           "precision": "IDENTITY_LEVEL_NOT_CONTENT_PROVEN"}
    try:
        parent = Path(str(reference_root)).parent
        if not parent.is_dir():
            return {**out, "error": "REFERENCE_PARENT_MISSING"}
'''

SCAN_NEW = '''    out = {"release_dirs_total": 0, "reference_root": str(reference_root),
           "identity_equivalent_dirs": [], "identity_equivalent_count": 0,
           "precision": "IDENTITY_LEVEL_NOT_CONTENT_PROVEN"}
    try:
        ref_str = str(reference_root)
        # A local drive path cannot describe a remote tree: refuse instead of silently
        # scanning a same-named local directory (this produced a bogus count of 2 once).
        if ref_str[:1].isalpha() and ref_str[1:3] == ":\\\\":
            drive = ref_str[:2].upper()
            if not os.path.exists(drive + "\\\\"):
                return {**out, "error": "HOST_SCOPE_MISMATCH", "drive": drive}
        parent = Path(ref_str).parent
        if not parent.is_dir():
            return {**out, "error": "REFERENCE_PARENT_MISSING"}
'''

# 2) resolve the comparison fields from commit -> checkpoint fallback
VERIFY_ANCHOR = '''        "disk_equivalent_dirs": scan_equivalent_dirs(
            commit.get("release_root"),
            asof=commit.get("asof"),
            source_cleaning_release=(commit.get("identity") or {}).get("source_cleaning_release")
            or commit.get("source_cleaning_release"),
            parent_release_id=(commit.get("identity") or {}).get("parent_release_id")
            or commit.get("parent_release_id"),
        ),
'''

VERIFY_NEW = '''        "disk_equivalent_dirs": scan_equivalent_dirs(
            commit.get("release_root"),
            asof=commit.get("asof"),
            source_cleaning_release=_resolved_identity.get("source_cleaning_release"),
            parent_release_id=_resolved_identity.get("parent_release_id"),
        ),
        "identity_source": _resolved_identity.get("_source"),
'''

# 3) build the resolved identity before the return dict
RESOLVE_ANCHOR = '''    # ---- additive: full-content fingerprint comparison (never weakens the 3-product check)
'''

RESOLVE_NEW = '''    # ---- resolve the identity fields used by the disk scan -------------------------
    # Legacy CC_COMMIT_R1 COMMIT.json carries no `identity` and no top-level
    # source_cleaning_release / parent_release_id; they live in CHECKPOINT.json. Without this
    # fallback the scan compared every dir against None and always returned 0.
    _ck_ident = {}
    try:
        _ck_path = Path(str(commit.get("checkpoint_path") or ""))
        if _ck_path.is_file():
            _ck_ident = (json.loads(_ck_path.read_text(encoding="utf-8")).get("identity") or {})
    except Exception:  # noqa: BLE001
        _ck_ident = {}
    _c_ident = commit.get("identity") or {}

    def _pick(field):
        for src_name, src in (("commit.identity", _c_ident),
                              ("commit", commit),
                              ("checkpoint.identity", _ck_ident)):
            v = src.get(field)
            if v not in (None, "", "None"):
                return v, src_name
        return None, "MISSING"

    _scr, _scr_src = _pick("source_cleaning_release")
    _prid, _prid_src = _pick("parent_release_id")
    _resolved_identity = {
        "source_cleaning_release": _scr,
        "parent_release_id": _prid,
        "_source": {"source_cleaning_release": _scr_src, "parent_release_id": _prid_src},
    }

    # ---- additive: full-content fingerprint comparison (never weakens the 3-product check)
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

    if "_resolved_identity" in text:
        print(json.dumps({"file": str(p), "status": "ALREADY_PATCHED"}))
        return 0
    if "scan_equivalent_dirs" not in text:
        print("PREREQ_MISSING: apply patch_verify_disk_scan_r3.py first")
        return 5

    applied = []
    for name, anchor, new in (
        ("host_scope_guard", SCAN_ANCHOR, SCAN_NEW),
        ("resolve_identity", RESOLVE_ANCHOR, RESOLVE_NEW),
        ("verify_use_resolved", VERIFY_ANCHOR, VERIFY_NEW),
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
    bak = p.with_name(p.name + f".bak_sam_led_{STAMP}_r4")
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
