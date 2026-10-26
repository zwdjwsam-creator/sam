# -*- coding: utf-8 -*-
"""Additive identity: `release_content_id` + coverage report + dangling-junction gate.

Why additive, not a REQUIRED_PRODUCTS change
--------------------------------------------
`REQUIRED_PRODUCTS` hashes 3 products; the compiler's own `required` list (line 617 of
cache_compiler_tip_rebase_from_current_r1.py) gates `overall` on 10. Measured consequence:
INDEX_DAILY_R1 2026 went 273 -> 106,822 rows across releases with an IDENTICAL commit_id, so
"same commit_id" does NOT mean "same content" for 48 of 51 products.

Changing REQUIRED_PRODUCTS would invalidate every historical commit_id and every
`cc_commit/versions/*` receipt, so it needs owner authorisation and is NOT done here.

What is done here is additive and breaks nothing:
  * `release_content_id` — sha256 over EVERY present product dir (sorted name + digest), so a
    full-content fingerprint exists alongside the legacy 3-product `commit_id`;
  * `coverage` — explicit accounting: products_present / commit_id_covers / uncovered, plus
    COVERAGE_PARTIAL so the gap can never be mistaken for full coverage;
  * `junction_products` — each product that is an NTFS reparse point, with its resolved target,
    and a HARD FAIL if the target no longer exists. This is the "candidate silently dangles
    after production is archived" defect: without it, SEAL and verify() both stay green while
    four products point at bytes outside the release tree.

`verify()` gains a release_content_id comparison when both sides carry it; a COMMIT.json
written before this patch (no field) is reported as `release_content_id: LEGACY_ABSENT`, not a
failure, so existing state keeps verifying.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

STAMP = "20261026"

# ------------------------------------------------------------------ 1. new helpers
HELPER_ANCHOR = '''def product_digest(product_dir: Path) -> Dict[str, Any]:
'''

HELPER_NEW = '''def _is_reparse(p: Path) -> bool:
    try:
        import stat as _st
        return bool(os.stat(p, follow_symlinks=False).st_file_attributes
                    & getattr(_st, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    except OSError:
        return False


def _reparse_target(p: Path) -> str | None:
    try:
        return str(os.readlink(p))
    except OSError:
        return None


def present_products(release_dir: Path) -> list:
    """Every product directory in the release (excludes _qa and other metadata dirs)."""
    out = []
    for p in sorted(Path(release_dir).iterdir()):
        if not p.is_dir():
            continue
        if p.name.startswith("_"):
            continue
        out.append(p.name)
    return out


def release_content_digest(release_dir: Path) -> Dict[str, Any]:
    """Full-content fingerprint: every present product, sorted, name + digest.

    Independent of REQUIRED_PRODUCTS, so it changes whenever ANY product content changes.
    Additive: it never replaces commit_id, it sits beside it.
    """
    release_dir = Path(release_dir)
    prods = {}
    for name in present_products(release_dir):
        prods[name] = product_digest(release_dir / name)
    h = hashlib.sha256()
    for name in sorted(prods):
        rec = prods[name]
        h.update(name.encode("utf-8"))
        h.update(str(rec.get("sha256")).encode("utf-8"))
        h.update(str(rec.get("rows")).encode("utf-8"))
    return {"release_content_id": h.hexdigest(), "products_present": prods}


def junction_audit(release_dir: Path) -> Dict[str, Any]:
    """Record every product that is a reparse point and REFUSE dangling targets.

    Carried-forward products are junctions into earlier releases. If such a target is archived
    or removed the candidate still looks healthy to SEAL and verify(), but the bytes are gone.
    """
    release_dir = Path(release_dir)
    junctions, dangling = {}, []
    for name in present_products(release_dir):
        p = release_dir / name
        if not _is_reparse(p):
            continue
        target = _reparse_target(p)
        exists = None
        if target:
            t = Path(target)
            try:
                exists = t.exists()
            except OSError:
                exists = False
        junctions[name] = {"target": target, "target_exists": exists}
        if exists is False:
            dangling.append(name)
    return {"junction_products": junctions, "dangling": dangling}


def coverage_report(release_dir: Path, covered_by_commit: list,
                    compiler_required: list = None) -> Dict[str, Any]:
    """Explicit accounting so partial coverage can never read as full coverage."""
    present = present_products(release_dir)
    uncovered = [p for p in present if p not in set(covered_by_commit)]
    req = list(compiler_required or [])
    return {
        "products_present": len(present),
        "commit_id_covers": sorted(covered_by_commit),
        "commit_id_covers_count": len(covered_by_commit),
        "uncovered_by_commit_id": uncovered,
        "uncovered_count": len(uncovered),
        "compiler_required_given": req,
        "compiler_required_missing_from_commit": [p for p in req if p not in set(covered_by_commit)],
        "COVERAGE_PARTIAL": bool(uncovered),
        "note": "commit_id is the legacy 3-product data identity; release_content_id covers all "
                "present products. COVERAGE_PARTIAL=true means commit_id alone cannot prove "
                "whole-release content equality.",
    }


def product_digest(product_dir: Path) -> Dict[str, Any]:
'''

# ------------------------------------------------------------------ 2. extend identity
IDENT_ANCHOR = '''    identity["commit_id"] = sha256_obj(content)
    return identity
'''

IDENT_NEW = '''    identity["commit_id"] = sha256_obj(content)

    # ---- additive identity + coverage + junction audit (never alters commit_id) ----------
    try:
        rcd = release_content_digest(release_dir)
        identity["release_content_id"] = rcd["release_content_id"]
        identity["products_present"] = sorted(rcd["products_present"])
        identity["products_present_digests"] = rcd["products_present"]
        ident_js = Path(release_dir) / "SEAL.json"
        seal_for_cov = json.loads(ident_js.read_text(encoding="utf-8")) if ident_js.is_file() else {}
        compiler_req = (seal_for_cov.get("formal_required_missing") is not None and
                        [p for p in (seal_for_cov.get("price", {}).get("products") or {})])
        identity["coverage"] = coverage_report(
            release_dir, list(REQUIRED_PRODUCTS), compiler_required=list(compiler_req or []))
        ja = junction_audit(release_dir)
        identity["junction_products"] = ja["junction_products"]
        if ja["dangling"]:
            raise CommitError(
                "DANGLING_JUNCTION_PRODUCT: " + json.dumps(
                    {k: ja["junction_products"][k] for k in ja["dangling"]},
                    ensure_ascii=False)[:800])
    except CommitError:
        raise
    except Exception as e:  # noqa: BLE001
        identity["release_content_id"] = None
        identity["coverage"] = {"ERROR": f"{type(e).__name__}: {e}"}
    return identity
'''

# ------------------------------------------------------------------ 3. persist in COMMIT.json
COMMIT_ANCHOR = '''        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": cp_sha,
'''

COMMIT_NEW = '''        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": cp_sha,
        "release_content_id": identity.get("release_content_id"),
        "products_present": identity.get("products_present"),
        "coverage": identity.get("coverage"),
        "junction_products": identity.get("junction_products"),
'''

# ------------------------------------------------------------------ 4. verify() compares it
VERIFY_ANCHOR = '''    deep_ok = True
    deep_detail = {}
'''

VERIFY_NEW = '''    deep_ok = True
    deep_detail = {}
    content_id_check = {"status": "LEGACY_ABSENT"}
'''

VERIFY2_ANCHOR = '''    consistent = bool(cp_ok and identity_ok and deep_ok)
'''

VERIFY2_NEW = '''    # ---- additive: full-content fingerprint comparison (never weakens the 3-product check)
    stored_rcid = commit.get("release_content_id")
    if stored_rcid:
        try:
            now_rcid = release_content_digest(Path(commit["release_root"]))["release_content_id"]
            same = now_rcid == stored_rcid
            content_id_check = {"status": "MATCH" if same else "MISMATCH",
                                "stored": stored_rcid, "now": now_rcid}
            deep_ok = deep_ok and same
        except Exception as e:  # noqa: BLE001
            content_id_check = {"status": "ERROR", "error": f"{type(e).__name__}: {e}"}
            deep_ok = False

    consistent = bool(cp_ok and identity_ok and deep_ok)
'''

VERIFY3_ANCHOR = '''        "payload_matches": deep_ok,
        "payload_root_missing": payload_root_missing,
'''

VERIFY3_NEW = '''        "payload_matches": deep_ok,
        "payload_root_missing": payload_root_missing,
        "release_content_id_check": content_id_check,
        "commit_id_coverage": commit.get("coverage"),
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

    if "release_content_id" in text:
        print(json.dumps({"file": str(p), "status": "ALREADY_PATCHED"}))
        return 0

    applied = []
    if A("import os\n") not in text:
        text = text.replace(A("import json\n"), A("import json\nimport os\n"), 1)
        applied.append("import_os")

    for name, anchor, new in (
        ("helpers", HELPER_ANCHOR, HELPER_NEW),
        ("identity_additive", IDENT_ANCHOR, IDENT_NEW),
        ("commit_persist", COMMIT_ANCHOR, COMMIT_NEW),
        ("verify_content_id", VERIFY_ANCHOR, VERIFY_NEW),
        ("verify_compare", VERIFY2_ANCHOR, VERIFY2_NEW),
        ("verify_report", VERIFY3_ANCHOR, VERIFY3_NEW),
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
    bak = p.with_name(p.name + f".bak_sam_led_{STAMP}_rcid")
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
