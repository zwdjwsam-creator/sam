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
    identity = {
        "release_id": pointer.get("cache_release_id"),
        "release_root": str(release_dir),
        "asof": pointer.get("asof"),
        "source_cleaning_release": pointer.get("source_cleaning_release"),
        "parent_release_id": pointer.get("parent_release_id"),
        "products": products,
    }
    identity["commit_id"] = sha256_obj(identity)
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
    if deep:
        rel = Path(commit["release_root"])
        if not rel.exists():
            deep_ok = False
            deep_detail["missing_release_root"] = str(rel)
        else:
            for pid, rec in commit["products"].items():
                now = product_digest(rel / pid)
                same = now.get("sha256") == rec.get("sha256") and now.get("rows") == rec.get("rows")
                deep_detail[pid] = {"expected": rec.get("sha256"), "actual": now.get("sha256"), "match": same}
                deep_ok = deep_ok and same
    consistent = bool(cp_ok and identity_ok and deep_ok)
    return {
        **out,
        "status": "CONSISTENT" if consistent else "INCONSISTENT",
        "consistent": consistent,
        "checkpoint_path": str(cp_path),
        "checkpoint_sha_matches": cp_ok,
        "checkpoint_identity_matches": identity_ok,
        "release_id": commit["release_id"],
        "asof": commit["asof"],
        "payload_matches": deep_ok,
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
        return {
            "status": "IDEMPOTENT_NOOP",
            "commit_id": identity["commit_id"],
            "commit_file_sha256": sha256_file(COMMIT_FILE),
            "release_id": identity["release_id"],
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
