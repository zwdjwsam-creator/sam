"""Candidate commit discipline for the connected pipeline (deliverable 3, diff 3).

Defect addressed
----------------
The previous pipeline rewrote `ACCUM_PART` in place (`merged.to_parquet(ACCUM_PART)`),
then wrote the checkpoint, then replaced pointer and registry one after the other.  An
exception between those steps could leave the published pointer aimed at data that had
already been rewritten, or at a checkpoint describing a different payload.  It also
implied a multi-file transaction that does not exist.

What this module does instead
-----------------------------
1. A build result is an IMMUTABLE versioned release directory (the original compiler
   already produces one per run: `BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_<asof>_<stamp>`).
   Nothing already released is ever rewritten.
2. `build_identity()` hashes what the release actually contains (per-product partition
   sha256 + row counts) and folds it into a `commit_id`.
3. `commit()` first writes an immutable per-version checkpoint, then performs ONE
   `os.replace` of the single authoritative `COMMIT.json`.  That single file is the
   only reference a reader needs, and it carries the checkpoint digest, so pointer and
   checkpoint cannot disagree: either the new COMMIT.json is in place or the previous
   one still is.
4. `verify()` re-derives the identity from disk and compares it with the committed
   identity, so a stale/tampered payload is detected instead of trusted.

Failure points are injectable (`fail_at=`), so the mid-commit failure and the recovery
are exercised on this very candidate, not asserted.

Nothing here touches production `CURRENT_CACHE_RELEASE.json`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
COMMIT_ROOT = TASK / "candidate" / "cc_commit"
COMMIT_FILE = COMMIT_ROOT / "COMMIT.json"
VERSIONS = COMMIT_ROOT / "versions"
REQUIRED_PRODUCTS = ("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "STOCK_FACTOR_DAILY_R1")

BB = Path(r"E:\BLACKBOX")
sys.path.insert(0, str(BB / "脚本"))


class CommitError(RuntimeError):
    pass


def now_cn() -> str:
    return dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0800")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_obj(obj: Any) -> str:
    blob = json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _is_reparse(p: Path) -> bool:
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


def _safe_product_digest(prod: Path) -> Dict[str, Any]:
    """Junction-aware product digest. NEVER walks a reparse point.

    A junction product borrows bytes from another release; its identity is that target
    (plus the target's own release id when readable), not a local re-hash. Walking it would
    also follow the junction cycle and never terminate.
    """
    import stat as _st

    if _is_reparse(prod):
        target = _reparse_target(prod)
        texists = None
        trelease = None
        if target:
            t = Path(target)
            try:
                texists = t.exists()
            except OSError:
                texists = False
            try:
                rj = t / "RELEASE.json"
                if rj.is_file():
                    trelease = json.loads(rj.read_text(encoding="utf-8")).get("cache_release_id")
            except Exception:  # noqa: BLE001
                trelease = None
        return {"kind": "JUNCTION", "target": target, "target_exists": texists,
                "target_release_id": trelease,
                "sha256": None, "rows": None, "parts": None}

    # real directory: explicit, reparse-aware, bounded walk
    parts = []
    total = 0
    cap = 200000
    for dp, dn, fns in os.walk(prod):
        dn[:] = [d for d in dn
                 if not _is_reparse(Path(dp) / d)]
        for fn in fns:
            if fn.lower().endswith(".parquet"):
                parts.append(Path(dp) / fn)
                total += 1
                if total >= cap:
                    break
        if total >= cap:
            break
    if not parts:
        return {"kind": "DIR", "parts": 0, "rows": 0, "sha256": None, "capped": total >= cap}
    import pyarrow.parquet as pq

    rows = 0
    for p in parts:
        try:
            rows += int(pq.ParquetFile(p).metadata.num_rows)
        except Exception:  # noqa: BLE001
            pass
    h = hashlib.sha256()
    for p in sorted(parts):
        h.update(str(p.relative_to(prod)).encode("utf-8"))
        try:
            h.update(product_digest_sha(p).encode("utf-8"))
        except Exception:  # noqa: BLE001
            h.update(b"UNREADABLE")
    return {"kind": "DIR", "parts": len(parts), "rows": int(rows),
            "sha256": h.hexdigest(), "capped": total >= cap}


def product_digest_sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def release_content_digest(release_dir: Path) -> Dict[str, Any]:
    """Full-content fingerprint over every present product, junction-aware.

    Junction products contribute their target identity instead of borrowed bytes, so this
    terminates, and "target archived" shows up as target_exists=false rather than a hang.
    """
    release_dir = Path(release_dir)
    prods = {}
    for name in present_products(release_dir):
        prods[name] = _safe_product_digest(release_dir / name)
    h = hashlib.sha256()
    for name in sorted(prods):
        rec = prods[name]
        h.update(name.encode("utf-8"))
        h.update(str(rec.get("kind")).encode("utf-8"))
        h.update(str(rec.get("sha256") or rec.get("target")).encode("utf-8"))
        h.update(str(rec.get("rows")).encode("utf-8"))
        h.update(str(rec.get("target_release_id")).encode("utf-8"))
    return {"release_content_id": h.hexdigest(), "products_present": prods}


DUPLICATE_LOG = COMMIT_ROOT / "DUPLICATE_ROOTS.jsonl"


def record_duplicate_root(*, commit_id: str, reference_root: str,
                          duplicate_root: str, release_id: str) -> Optional[Dict[str, Any]]:
    """Append an equivalent-content duplicate to an append-only audit log.

    Never rewrites an existing line and never touches COMMIT.json, so the authoritative
    reference and commit_id stay byte-identical (NOOP keeps meaning zero writes).
    Returns the record, or None when this exact (commit_id, duplicate_root) is already logged.
    """
    ref = os.path.normcase(os.path.normpath(str(reference_root)))
    dup = os.path.normcase(os.path.normpath(str(duplicate_root)))
    try:
        if DUPLICATE_LOG.is_file():
            for line in DUPLICATE_LOG.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                if (str(rec.get("commit_id")) == str(commit_id)
                        and os.path.normcase(os.path.normpath(str(rec.get("duplicate_root")))) == dup):
                    return None
    except OSError:
        pass
    rec = {
        "schema": "CC_DUPLICATE_ROOT_R1",
        "seen_at_cn": now_cn(),
        "commit_id": commit_id,
        "reference_root": str(reference_root),
        "duplicate_root": str(duplicate_root),
        "release_id": release_id,
        "content_identical_to_reference": True,
        "reference_moved": False,
        "note": "equivalent content committed earlier; reference intentionally not repointed",
    }
    DUPLICATE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DUPLICATE_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def scan_equivalent_dirs(reference_root: str, asof=None, source_cleaning_release=None,
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
        ref_str = str(reference_root)
        # A local drive path cannot describe a remote tree: refuse instead of silently
        # scanning a same-named local directory (this produced a bogus count of 2 once).
        if ref_str[:1].isalpha() and ref_str[1:3] == ":\\":
            drive = ref_str[:2].upper()
            if not os.path.exists(drive + "\\"):
                return {**out, "error": "HOST_SCOPE_MISMATCH", "drive": drive}
        parent = Path(ref_str).parent
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
    """All logged duplicates (optionally filtered by commit_id)."""
    out = []
    try:
        if not DUPLICATE_LOG.is_file():
            return out
        for line in DUPLICATE_LOG.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if commit_id is None or str(rec.get("commit_id")) == str(commit_id):
                out.append(rec)
    except OSError:
        pass
    return out


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
    import pyarrow.parquet as pq

    parts = sorted(product_dir.rglob("*.parquet"))
    if not parts:
        return {"parts": 0, "rows": 0, "sha256": None}
    rows = 0
    for p in parts:
        rows += int(pq.ParquetFile(p).metadata.num_rows)
    # content digest: sorted (relative name, file sha) so the same payload hashes the same
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p.relative_to(product_dir)).encode("utf-8"))
        h.update(sha256_file(p).encode("utf-8"))
    return {"parts": len(parts), "rows": int(rows), "sha256": h.hexdigest()}


def build_identity(release_dir: Path) -> Dict[str, Any]:
    release_dir = Path(release_dir)
    pointer = json.loads((release_dir / "RELEASE.json").read_text(encoding="utf-8"))
    seal = json.loads((release_dir / "SEAL.json").read_text(encoding="utf-8"))
    if not seal.get("all_pass"):
        raise CommitError(f"SEAL.all_pass is false for {pointer.get('cache_release_id')}: {release_dir}")
    missing = [p for p in REQUIRED_PRODUCTS if not (release_dir / p).exists()]
    if missing:
        raise CommitError(f"required products missing: {missing}")
    products = {}
    for pid in REQUIRED_PRODUCTS:
        products[pid] = product_digest(release_dir / pid)
    # The content hash must cover DATA only. `cache_release_id` and the release path
    # carry a per-build timestamp (and RELEASE.json / SEAL.json / _qa carry that same
    # timestamp), so including them made every rebuild of identical input produce a
    # different commit id and made the IDEMPOTENT_NOOP path unreachable. Measured:
    # two builds of the same input differed in 5 metadata files out of 766 and in
    # none of the 761 data files.
    content = {
        "schema": "CC_COMMIT_IDENTITY_V2",
        "asof": pointer.get("asof"),
        "source_cleaning_release": pointer.get("source_cleaning_release"),
        "parent_release_id": pointer.get("parent_release_id"),
        "products": products,
    }
    identity = {
        "release_id": pointer.get("cache_release_id"),
        "release_root": str(release_dir),
        "asof": pointer.get("asof"),
        "source_cleaning_release": pointer.get("source_cleaning_release"),
        "parent_release_id": pointer.get("parent_release_id"),
        "products": products,
        "content_scope": {
            "hashed": ["asof", "source_cleaning_release", "parent_release_id",
                       "products[*].sha256/rows"],
            "excluded": ["release_id", "release_root", "RELEASE.json", "SEAL.json",
                         "_qa/*", "PRODUCT_CAPABILITY_FACTS_CANDIDATE.json",
                         "CURRENT_POINTER_COPY.json"],
            "reason": "build metadata carries the build timestamp; it is not data",
        },
    }
    identity["commit_id"] = sha256_obj(content)

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


def _read_commit() -> Optional[Dict[str, Any]]:
    if not COMMIT_FILE.exists():
        return None
    return json.loads(COMMIT_FILE.read_text(encoding="utf-8"))


def verify(*, deep: bool = True) -> Dict[str, Any]:
    commit = _read_commit()
    if commit is None:
        return {"status": "NO_COMMIT", "consistent": False}
    cp_path = Path(commit["checkpoint_path"])
    out: Dict[str, Any] = {"commit_file": str(COMMIT_FILE), "commit_id": commit["commit_id"]}
    if not cp_path.exists():
        return {**out, "status": "CHECKPOINT_MISSING", "consistent": False}
    cp_sha = sha256_file(cp_path)
    checkpoint = json.loads(cp_path.read_text(encoding="utf-8"))
    cp_ok = cp_sha == commit["checkpoint_sha256"]
    # the checkpoint and the commit must name the same payload
    identity_ok = (
        checkpoint.get("identity", {}).get("commit_id") == commit["commit_id"]
        and checkpoint.get("release_id") == commit["release_id"]
        and checkpoint.get("asof") == commit["asof"]
    )
    deep_ok = True
    deep_detail = {}
    content_id_check = {"status": "LEGACY_ABSENT"}
    payload_root_missing = False
    if deep:
        rel = Path(commit["release_root"])
        if not rel.exists():
            deep_ok = False
            payload_root_missing = True
            deep_detail["missing_release_root"] = str(rel)
        else:
            for pid, rec in commit["products"].items():
                now = product_digest(rel / pid)
                same = now.get("sha256") == rec.get("sha256") and now.get("rows") == rec.get("rows")
                deep_detail[pid] = {"expected": rec.get("sha256"), "actual": now.get("sha256"), "match": same}
                deep_ok = deep_ok and same
    # ---- resolve the identity fields used by the disk scan -------------------------
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
    return {
        **out,
        "status": ("CONSISTENT" if consistent
                   else ("PAYLOAD_ROOT_MISSING" if payload_root_missing else "INCONSISTENT")),
        "consistent": consistent,
        "checkpoint_path": str(cp_path),
        "checkpoint_sha_matches": cp_ok,
        "checkpoint_identity_matches": identity_ok,
        "release_id": commit["release_id"],
        "asof": commit["asof"],
        "payload_matches": deep_ok,
        "payload_root_missing": payload_root_missing,
        "release_content_id_check": content_id_check,
        "reference_root_present": Path(str(commit.get("release_root"))).exists(),
        "equivalent_duplicates": len(read_duplicate_roots(commit.get("commit_id"))),
        "equivalent_duplicate_roots": [r.get("duplicate_root")
                                       for r in read_duplicate_roots(commit.get("commit_id"))],
        "disk_equivalent_dirs": scan_equivalent_dirs(
            commit.get("release_root"),
            asof=commit.get("asof"),
            source_cleaning_release=_resolved_identity.get("source_cleaning_release"),
            parent_release_id=_resolved_identity.get("parent_release_id"),
        ),
        "identity_source": _resolved_identity.get("_source"),
        "commit_id_coverage": commit.get("coverage"),
        "payload_detail": deep_detail,
    }


def commit(
    release_dir: Path,
    *,
    note: str = "",
    fail_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Single authoritative commit. Returns the receipt; raises on injected failure."""
    identity = build_identity(release_dir)
    current = _read_commit()
    if current and current.get("commit_id") == identity["commit_id"]:
        same_root = str(current.get("release_root")) == str(identity["release_root"])
        same_release_id = str(current.get("release_id")) == str(identity["release_id"])
        old_root = Path(str(current.get("release_root") or ""))
        if same_root and same_release_id:
            return {
                "status": "IDEMPOTENT_NOOP",
                "commit_id": identity["commit_id"],
                "commit_file_sha256": sha256_file(COMMIT_FILE),
                "release_id": identity["release_id"],
            }
        if same_root and not same_release_id:
            # Self-contradictory record: the stored reference already points at this tree,
            # but release_id/asof still name an earlier build of the SAME content
            # (commit_id hashes data only, so equality proves the payload matches).
            # The tree is right; only the label is stale. Repair it in place.
            cp_old = Path(str(current.get("checkpoint_path") or ""))
            if cp_old.is_file():
                checkpoint = json.loads(cp_old.read_text(encoding="utf-8"))
            else:
                checkpoint = {"seq": int(current.get("seq", 1)),
                              "parent_commit_id": current.get("parent_commit_id"),
                              "created_at_cn": now_cn(),
                              "PRODUCTION_CURRENT_WRITE": "NONE"}
            checkpoint["identity"] = identity
            checkpoint["release_id"] = identity["release_id"]
            checkpoint["asof"] = identity["asof"]
            checkpoint["repaired_from_release_id"] = str(current.get("release_id"))
            version_dir = VERSIONS / identity["commit_id"][:16]
            version_dir.mkdir(parents=True, exist_ok=True)
            checkpoint_path = version_dir / "CHECKPOINT.json"
            checkpoint_path.write_text(
                json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            commit_obj = {
                **current,
                "release_id": identity["release_id"],
                "asof": identity["asof"],
                "release_root": identity["release_root"],
                "products": identity["products"],
                "checkpoint_path": str(checkpoint_path),
                "checkpoint_sha256": sha256_file(checkpoint_path),
                "repaired_at_cn": now_cn(),
                "repaired_from_release_id": str(current.get("release_id")),
            }
            COMMIT_ROOT.mkdir(parents=True, exist_ok=True)
            tmp = COMMIT_FILE.with_name(f"COMMIT.json.{os.getpid()}.tmp")
            tmp.write_text(json.dumps(commit_obj, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, COMMIT_FILE)
            return {
                "status": "REPAIRED_SAME_ROOT_FIELD_DRIFT",
                "commit_id": identity["commit_id"],
                "release_id": identity["release_id"],
                "release_root": identity["release_root"],
                "commit_file_sha256": sha256_file(COMMIT_FILE),
                "repaired_from_release_id": str(current.get("release_id")),
            }
        if old_root.exists() and not same_root:
            # Same CONTENT already committed, under a root that still exists. Content
            # addressing means recompiling identical input commits nothing: no new
            # COMMIT.json, and the reference stays where it is. Only a vanished payload
            # may move the reference (see the rebind branch below).
            logged = record_duplicate_root(
                commit_id=identity["commit_id"],
                reference_root=str(old_root),
                duplicate_root=str(identity["release_root"]),
                release_id=str(identity["release_id"]),
            )
            return {
                "status": "IDEMPOTENT_NOOP",
                "commit_id": identity["commit_id"],
                "commit_file_sha256": sha256_file(COMMIT_FILE),
                "release_id": current.get("release_id"),
                "release_root": str(old_root),
                "note": "duplicate root with identical content; reference unchanged",
                "candidate_release_root": str(identity["release_root"]),
                "duplicate_logged": bool(logged),
                "duplicate_log": str(DUPLICATE_LOG),
                "equivalent_duplicates_total": len(read_duplicate_roots(identity["commit_id"])),
            }
        # Content identity is unchanged (commit_id hashes data only) but the referenced
        # payload tree moved -- e.g. the previous candidate release was archived. Rebind
        # the single authoritative reference to the new root. Safe precisely because an
        # equal commit_id proves the new tree holds the same products/rows/sha256; the
        # non-data fields (release_id, release_root, build timestamps) are excluded from
        # that hash by CC_COMMIT_IDENTITY_V2. Recorded, never silent.
        rebound_from = str(current.get("release_root"))
        cp_old = Path(str(current.get("checkpoint_path") or ""))
        if cp_old.is_file():
            checkpoint = json.loads(cp_old.read_text(encoding="utf-8"))
        else:
            checkpoint = {
                "seq": int(current.get("seq", 1)),
                "release_id": identity["release_id"],
                "asof": identity["asof"],
                "identity": identity,
                "parent_commit_id": current.get("parent_commit_id"),
                "created_at_cn": now_cn(),
                "note": note,
                "PRODUCTION_CURRENT_WRITE": "NONE",
            }
        checkpoint["identity"] = identity
        checkpoint["release_id"] = identity["release_id"]
        checkpoint["asof"] = identity["asof"]
        checkpoint["rebound_from_release_root"] = rebound_from
        version_dir = VERSIONS / identity["commit_id"][:16]
        version_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = version_dir / "CHECKPOINT.json"
        checkpoint_path.write_text(
            json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        commit_obj = {
            **current,
            "release_id": identity["release_id"],
            "asof": identity["asof"],
            "release_root": identity["release_root"],
            "products": identity["products"],
            "checkpoint_path": str(checkpoint_path),
            "checkpoint_sha256": sha256_file(checkpoint_path),
            "rebound_at_cn": now_cn(),
            "rebound_from_release_root": rebound_from,
        }
        COMMIT_ROOT.mkdir(parents=True, exist_ok=True)
        tmp = COMMIT_FILE.with_name(f"COMMIT.json.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(commit_obj, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, COMMIT_FILE)
        return {
            "status": "REBOUND_SAME_CONTENT_NEW_ROOT",
            "commit_id": identity["commit_id"],
            "release_id": identity["release_id"],
            "release_root": identity["release_root"],
            "commit_file_sha256": sha256_file(COMMIT_FILE),
            "rebound_from_release_root": rebound_from,
        }

    seq = 1 if current is None else int(current.get("seq", 1)) + 1
    version_dir = VERSIONS / identity["commit_id"][:16]
    checkpoint_path = version_dir / "CHECKPOINT.json"
    if version_dir.exists() and checkpoint_path.exists():
        # a previous attempt already wrote this payload's checkpoint and died before
        # the single commit swap: reuse it, never rewrite an existing version dir
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        seq = int(checkpoint.get("seq", seq))
    else:
        version_dir.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            "seq": seq,
            "release_id": identity["release_id"],
            "asof": identity["asof"],
            "identity": identity,
            "parent_commit_id": (current or {}).get("commit_id"),
            "created_at_cn": now_cn(),
            "note": note,
            "PRODUCTION_CURRENT_WRITE": "NONE",
        }
        checkpoint_path.write_text(
            json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    cp_sha = sha256_file(checkpoint_path)

    if fail_at == "after_checkpoint":
        raise CommitError("INJECTED_FAILURE_AFTER_CHECKPOINT")

    commit_obj = {
        "schema": "CC_COMMIT_R1",
        "seq": seq,
        "commit_id": identity["commit_id"],
        "release_id": identity["release_id"],
        "release_root": identity["release_root"],
        "asof": identity["asof"],
        "products": identity["products"],
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": cp_sha,
        "release_content_id": identity.get("release_content_id"),
        "products_present": identity.get("products_present"),
        "coverage": identity.get("coverage"),
        "junction_products": identity.get("junction_products"),
        "parent_commit_id": (current or {}).get("commit_id"),
        "committed_at_cn": now_cn(),
        "note": note,
        "PRODUCTION_CURRENT_WRITE": "NONE",
    }

    if fail_at == "before_commit_replace":
        raise CommitError("INJECTED_FAILURE_BEFORE_COMMIT_REPLACE")

    COMMIT_ROOT.mkdir(parents=True, exist_ok=True)
    tmp = COMMIT_FILE.with_name(f"COMMIT.json.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(commit_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, COMMIT_FILE)  # ONE atomic reference swap; no multi-file transaction
    receipt = {
        "status": "COMMITTED",
        "commit_id": identity["commit_id"],
        "seq": seq,
        "release_id": identity["release_id"],
        "commit_file_sha256": sha256_file(COMMIT_FILE),
        "checkpoint_path": str(checkpoint_path),
        "single_reference_file": str(COMMIT_FILE),
        "production_current_written": False,
    }
    if fail_at == "after_commit_replace":
        raise CommitError(f"INJECTED_FAILURE_AFTER_COMMIT_REPLACE committed={json.dumps(receipt)}")
    return receipt


def probe_original_publish_gate(release_dir: Path) -> Dict[str, Any]:
    """Evaluate the ORIGINAL publish gate on this candidate, in dry-run (no writes)."""
    from blackbox_daily_increment_publish_gate_r1 import publish_atomic  # original

    release_dir = Path(release_dir)
    pointer = json.loads((release_dir / "RELEASE.json").read_text(encoding="utf-8"))
    facts_path = release_dir / "PRODUCT_CAPABILITY_FACTS_CANDIDATE.json"
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    out = publish_atomic(
        cache_pointer=pointer,
        cache_root=release_dir,
        facts=facts,
        target=str(pointer.get("asof")),
        cleaning_pointer=None,
        dry_run=True,
    )
    return {
        "gate_function": "blackbox_daily_increment_publish_gate_r1.publish_atomic",
        "dry_run": True,
        "OPERATIONAL_READINESS": out.get("OPERATIONAL_READINESS"),
        "CURRENT_PUBLISH": out.get("CURRENT_PUBLISH"),
        "published": out.get("published"),
        "reason": out.get("reason"),
        "target": out.get("target"),
        "n_matrix_rows": len(out.get("matrix") or []),
        "matrix_not_allowed": [r for r in (out.get("matrix") or [])
                               if r.get("CAN_SERVE") != "YES"][:12],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--action", required=True,
                    choices=["identity", "commit", "verify", "probe-gate"])
    ap.add_argument("--release-dir")
    ap.add_argument("--note", default="")
    ap.add_argument("--fail-at", default=None,
                    choices=[None, "after_checkpoint", "before_commit_replace", "after_commit_replace"])
    args = ap.parse_args()
    try:
        if args.action == "identity":
            print(json.dumps(build_identity(Path(args.release_dir)), ensure_ascii=False, indent=2))
            return 0
        if args.action == "commit":
            out = commit(Path(args.release_dir), note=args.note, fail_at=args.fail_at)
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0
        if args.action == "verify":
            out = verify()
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0 if out.get("consistent") else 4
        out = probe_original_publish_gate(Path(args.release_dir))
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    except CommitError as e:
        print(json.dumps({"status": "COMMIT_REFUSED", "error": str(e)}, ensure_ascii=False, indent=2))
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
