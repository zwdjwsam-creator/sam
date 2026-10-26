# -*- coding: utf-8 -*-
"""R2 on the rcid patch: make equivalent-duplicate releases visible without touching the reference.

Problem this solves (measured on the desktop):
  * the compiler names each build by timestamp, so every run creates a NEW release directory;
  * when the content is identical, commit() correctly returns IDEMPOTENT_NOOP and does not move
    the reference;
  * therefore COMMIT.json.release_root stays on the first still-existing build while
    pipeline.bound_release_root reports the build of THIS round.
  Measured on the desktop: 4 equivalent release dirs (_181019 / _181143 / _181638 / _181756),
  COMMIT.json pointing at _181019, exactly ONE rebind ever (234902 -> 181019, 18:11:26), and the
  remaining three rounds all NOOP. So it is NOT a third rebind; it is "NOOP never moves the
  reference" plus "every round makes a new dir".

Doing it additively:
  * NOOP still writes nothing to COMMIT.json (idempotence and the reference stay byte-identical);
  * each equivalent duplicate is appended to `cc_commit/DUPLICATE_ROOTS.jsonl` (append-only, one
    JSON object per line: seen_at, commit_id, reference_root, duplicate_root, release_id);
  * verify() reports `equivalent_duplicates` (count + list) and `reference_root_present`, so the
    drift is visible instead of having to be discovered by hand-scanning the directory.

Deliberately NOT done: deleting or archiving duplicates (destructive, needs authorisation), and
writing COMMIT.json on NOOP (would break "NOOP means zero writes").
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

STAMP = "20261026"

# ---------------------------------------------------------------- helpers
HELPER_ANCHOR = '''def junction_audit(release_dir: Path) -> Dict[str, Any]:
'''

HELPER_NEW = '''DUPLICATE_LOG = COMMIT_ROOT / "DUPLICATE_ROOTS.jsonl"


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
        fh.write(json.dumps(rec, ensure_ascii=False) + "\\n")
    return rec


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
'''

# ---------------------------------------------------------------- call it on NOOP
NOOP_ANCHOR = '''            return {
                "status": "IDEMPOTENT_NOOP",
                "commit_id": identity["commit_id"],
                "commit_file_sha256": sha256_file(COMMIT_FILE),
                "release_id": current.get("release_id"),
                "release_root": str(old_root),
                "note": "duplicate root with identical content; reference unchanged",
                "candidate_release_root": str(identity["release_root"]),
            }
'''

NOOP_NEW = '''            logged = record_duplicate_root(
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
'''

# ---------------------------------------------------------------- report in verify()
VERIFY_ANCHOR = '''        "release_content_id_check": content_id_check,
'''

VERIFY_NEW = '''        "release_content_id_check": content_id_check,
        "reference_root_present": Path(str(commit.get("release_root"))).exists(),
        "equivalent_duplicates": len(read_duplicate_roots(commit.get("commit_id"))),
        "equivalent_duplicate_roots": [r.get("duplicate_root")
                                       for r in read_duplicate_roots(commit.get("commit_id"))],
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

    if "DUPLICATE_ROOTS.jsonl" in text:
        print(json.dumps({"file": str(p), "status": "ALREADY_PATCHED"}))
        return 0
    if "release_content_id" not in text:
        print("PREREQ_MISSING: apply patch_release_content_id_r1.py first")
        return 5

    applied = []
    for name, anchor, new in (
        ("duplicate_helpers", HELPER_ANCHOR, HELPER_NEW),
        ("log_on_noop", NOOP_ANCHOR, NOOP_NEW),
        ("verify_report_duplicates", VERIFY_ANCHOR, VERIFY_NEW),
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
    bak = p.with_name(p.name + f".bak_sam_led_{STAMP}_dup")
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
